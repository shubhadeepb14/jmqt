# The MIT License (MIT)
# Copyright (c) 2018 Shubhadeep Banerjee
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
# OR OTHER DEALINGS IN THE SOFTWARE.

import uuid
import collections
import time
import queue
import json
import redis
import asyncio
import threading

import pyjmqt.server.logger as logger
from pyjmqt.server.core.services.cache import CacheService
from pyjmqt.server.core.packets import *
from pyjmqt.server.core.constants import *

class ConnectionHandler:
    # constructor
    def __init__(self, settings, eventLoop):
        self.server_id = str(uuid.uuid4())
        self.settings = settings
        self.loop = eventLoop
        self.peers = {}
        self.pubmap = {}
        if not self.settings.ENABLE_MYSQL and self.settings.ENABLE_REDIS:
            logger.log_warning("MySQL/MariaDb is disbled, but Redis is enabled. Distributed system won't work without MySQL/MariaDb", 'ConnectionHandler')
        if self.settings.ENABLE_MYSQL:
            logger.log_info('MySQL/MariaDb is enabled. Initiating MySQL/MariaDb..', 'ConnectionHandler')
            from pyjmqt.server.core.services.dbservice import MySQLService
            self.dbService = MySQLService(self.settings)
        else:
            logger.log_info('MySQL/MariaDb is disabled. Switching to SQLite..', 'ConnectionHandler')
            from pyjmqt.server.core.services.dbservice import SQLiteService
            self.dbService = SQLiteService(self.settings)
        self.cacheService = CacheService(self.settings, self.loop, self.server_id, self.dbService, self.__process_pub, self.disconnect_client)

    # called when server is started (called by the Server class in server module)
    def start(self):
        self.remove_all_non_persistent_channels()

    # called when server is stopped (called by the Server class in server module)
    def stop(self):
        self.cacheService.run = False    

    '''
    SECTION #1 : This section is for handling connection and disconnections
    '''

    # called when a client connects (called by the packet_handler)
    async def connect_client(self, token, client_id, protocol, peer):
        if client_id in self.peers:
            await self.disconnect_client(client_id)
        
        if client_id in self.peers:
            old_peer = self.peers[client_id]['peer']
            await old_peer.disconnect()
        
        await self.remove_non_persistent_channels(client_id)
        await self.dbService.insert_or_update_connection(client_id, protocol, peer.address)

        self.peers[client_id] = {
            'peer': peer,
            'protocol': protocol
        }
        await self.cacheService.process_connection(client_id)
        return True
    
    # called when a client connects (called by the socket layer)
    async def disconnect_client(self, client_id, has_client_disconnected = False):
        if client_id in self.peers:
            peer = self.peers[client_id]['peer']
            await peer.disconnect()
            if client_id in self.peers:
                del self.peers[client_id]
            if client_id in self.pubmap:
                del self.pubmap[client_id]
            await self.cacheService.process_disconnection(client_id)
            await self.remove_non_persistent_channels(client_id)
            await self.dbService.remove_connection(client_id)
            asyncio.Task(peer.callbackWrapper.conn_close_callback(client_id, peer.address, peer.protocol))
            if has_client_disconnected:
                asyncio.Task(peer.callbackWrapper.disconnection_callback(client_id, peer.address, peer.protocol))
            
    # called when a client send a heartbeat (called by the packet_handler)
    async def heartbeat(self, client_id):
        pass
        
    # checks if a client is connected, if connected, return the protocol (called by the Server class in server module)
    async def is_connected(self, client_id):
        return self.dbService.check_connection(client_id)

    '''
    END SECTION #1
    '''

    '''
    SECTION #2 : This section is for handling sub/unsub requests
    '''
    
    # checks if a channel is a p2p channel
    def is_channel_p2p(self, channel):
        channel = str(channel)
        if channel.startswith('#'):
            return True
        return False
    
    # checks if a channel is a control channel
    def is_channel_control(self, channel):
        channel = str(channel)
        if channel.startswith('$'):
            return True
        return False
    
    # checks if a channel is a valid string
    def is_channel_valid(self, channel):
        channel = str(channel).strip()
        if channel.startswith('$') or channel.startswith('#'):
            if len(channel) > 1:
                return (True, channel)
        elif len(channel) > 0:
            return (True, channel)
        return (False, channel)

    # fetches all subscriptions for a channel from redis
    async def __fetch_subscribed_clients(self, channel_name):
        return await self.dbService.get_subscription_by_channel(channel_name)

    # fetches all subscribed channels for a client from redis
    async def __fetch_subscribed_channels(self, client_id):
        return await self.dbService.get_subscription_by_client(client_id)
    
    # private method, enters a new channel to the subscriptions against a client
    async def __put_subscription(self, client_id, channel_name, persistent_flag):
        asyncio.Task(self.cacheService.handle_sub(client_id, channel_name, persistent_flag))

    # private method, removes channel from the subscriptions against a client
    async def __remove_subscription(self, client_id, channel_name):
        asyncio.Task(self.cacheService.handle_unsub(client_id, channel_name))

    # remove non-persistent channels for a client
    async def remove_non_persistent_channels(self, client_id):
        all_channels = await self.__fetch_subscribed_channels(client_id)
        for ch in all_channels:
            if all_channels[ch] == 'temp':
                await self.__remove_subscription(client_id, ch)

    # remove non-persistent channels for a client
    def remove_all_non_persistent_channels(self):
        all_channels = self.dbService.get_all_subscriptions()
        for client_id in all_channels:
            channels = all_channels[client_id]
            for ch in channels:
                if channels[ch] == 'temp':
                    asyncio.Task(self.__remove_subscription(client_id, ch))

    # called when a client subscribes to a channel
    async def sub(self, sender_client_id, channel_name, persistent_flag):
        if not self.is_channel_p2p(channel_name) and not self.is_channel_control(channel_name):
            asyncio.Task(self.__put_subscription(sender_client_id, channel_name, persistent_flag))
            return StatusCode.OK
        logger.log_warning(('Security warning : subscribe to secure channel {0} from client {1}').format(channel_name, sender_client_id), 'ConnectionHandler(sub)')
        return StatusCode.NOT_ALLOWED
    
    # called when a client unsubscribes to a channel
    async def unsub(self, sender_client_id, channel_name):
        if not self.is_channel_p2p(channel_name) and not self.is_channel_control(channel_name):
            asyncio.Task(self.__remove_subscription(sender_client_id, channel_name))
            return StatusCode.OK
        logger.log_warning(('Security warning : unsubscribe to secure channel {0} from client {1}').format(channel_name, sender_client_id), 'ConnectionHandler(unsub)')
        return StatusCode.NOT_ALLOWED

    '''
    END SECTION #2
    '''

    '''
    SECTION #3 : This section is for handling pub requests
    '''
    
    # called when a client publishes a data to a channel (called by the packet_handler)
    async def pub(self, sender_client_id, channel_name, data, retain_flag, qos):
        clients = await self.__fetch_subscribed_clients(channel_name)
        pck_id = await self.cacheService.get_next_packet_pck_id()
        pub_data = {
            'c': channel_name, 'd' : data, 'f' : sender_client_id, 'q' : qos, 'id': pck_id
        }
        # pub_str = json.dumps(pub_data)
        save = False
        # loop over the clients
        if len(clients) > 0:
            for client_id in clients:
                # only proceed if the client is not the sender
                if client_id != sender_client_id:
                    # check qos, only put the pck_id in client map if qos is 1
                    if qos == QOS.ONE:
                        save = True
                        await self.__put_pub_map(client_id, pck_id, channel_name)
                        
                    await self.cacheService.handle_pub(client_id, pub_data)

        # check retain, put the packet into retain cache if true
        if retain_flag and not self.is_channel_p2p(channel_name):
            asyncio.Task(self.dbService.insert_retained_packet(sender_client_id, channel_name, data))
        if save:
            asyncio.Task(self.dbService.insert_packet(pck_id, sender_client_id, channel_name, data))
            if self.is_channel_p2p(channel_name):
                p2p_client = clients[0]
                if await self.dbService.check_connection(p2p_client) is None:
                    return StatusCode.CLIENT_OFFLINE
        elif self.is_channel_p2p(channel_name):
            return StatusCode.CLIENT_OFFLINE
        return StatusCode.OK

    # proceeses a pub data (called by __redis_sub_thread)
    async def __process_pub(self, channel_name, data, sender_client_id, qos, pub_pck_id, client_id):
        proceed = True
        clients = await self.__fetch_subscribed_clients(channel_name)
        if not client_id in clients:
            proceed = False
        if proceed:
            if client_id in self.peers:
                client = self.peers[client_id]
                peer = client['peer']
                pushPck = PacketGenerator.generate_push_req(channel_name, data, pub_pck_id, sender_client_id, False, qos)
                await peer.send(pushPck)
                log_msg = ('Push [id {4}] channel {0} to client {1} , qos {3} {2}').format(channel_name, peer.client_id, peer.id, qos, pub_pck_id)
                logger.log_debug(log_msg, peer.tag)
    
    '''
    END SECTION #3
    '''

    '''
    SECTION #4 : This section is for retained, pending packets and push ack
    Retained packets : packets with reatin flag set to 1 (to be sent when a client connects again or subscribes a channel)
    Pending packets : packets with qos = 1 which could not be sent when a client was offline (to be sent when a client connects again)
    '''

    # called when a client connects, it sends the pending packets with qos 1 to the client (called by the socket layer)
    async def send_pending_pub(self, client_id):
        self.pubmap[client_id] = await self.__get_pub_maps(client_id)
        await self.__send_next_pending(client_id)
    
    async def __send_next_pending(self, client_id):
        if client_id in self.pubmap:
            if len(self.pubmap[client_id]) > 0:
                next_pck_id = self.pubmap[client_id][0]
                packet = await self.dbService.get_packet(next_pck_id)
                if packet is not None:
                    asyncio.Task(self.__process_pub(packet['channel'], packet['data'], packet['sender_id'], 1, packet['packet_id'], client_id))
            else:
                del self.pubmap[client_id]

    # called when a client connects or subscribes to a channel, it sends the retained packets to the client
    async def send_retained(self, client_id, channel = None):
        channels = []
        if channel is None:
            channels = await self.__fetch_subscribed_channels(client_id)
            channels = list(channels.keys())
        else:
            channels.append(channel)
        retained_packets = await self.dbService.get_retained_packets(channels)
        if retained_packets is not None:
            for packet in retained_packets:
                channel_name, data, sender_client_id= packet['channel'], packet['data'], packet['sender_id']
                if client_id in self.peers:
                    pck_id = 0
                    client = self.peers[client_id]
                    peer = client['peer']
                    pushPck = PacketGenerator.generate_push_req(channel_name, data, pck_id, sender_client_id, True, 0)
                    await peer.send(pushPck)

    # fetches a list of pending qos 1 packets
    async def __get_pub_maps(self, client_id):
        return await self.dbService.get_pubmap(client_id)

    # maps a packet with qos 1 to a client 
    async def __put_pub_map(self, client_id, pub_pck_id, channel):
        asyncio.Task(self.dbService.insert_pubmap(pub_pck_id, client_id, channel))

    # removes a client and packet mapping
    async def __remove_pub_map(self, client_id, pub_pck_id):
        await self.dbService.remove_pubmap(pub_pck_id, client_id)
    
    # processes a push ack (called by packet_handler module)
    async def process_push_ack(self, pck_id, client_id):
        # remove the pub pck_id from client map
        await self.__remove_pub_map(client_id, pck_id)
        # check if the packet is in pending packets, then send the next one
        if client_id in self.pubmap:
            if pck_id in self.pubmap[client_id]:
                self.pubmap[client_id].remove(pck_id)
                await self.__send_next_pending(client_id)

    '''
    END SECTION #4
    '''


    '''
    SECTION #5 : Functions to be called from api (JMQT.server.api)
    '''

    # returns a list of subscribed channels for a client e.g. [{"ch1": "persistent"}, {"ch2": "temp"}]
    async def get_subscribed_channels(self, client_id):
        return await self.__fetch_subscribed_channels(client_id)
    
    # forcefully subscribes a channel to a client
    async def force_sub(self, client_id, channel, persistent_flag):
        await self.__put_subscription(client_id, channel, persistent_flag)
    
    # forcefully unsubscribes a channel from a client
    async def force_unsub(self, client_id, channel):
        await self.__remove_subscription(client_id, channel)
    
    # forcefully publish a data to a channel
    async def force_pub(self, channel, data, qos, retain):
        await self.pub("", channel, data, retain, qos)

    '''
    END SECTION #5
    '''

    '''
    SECTION #6 : Parses a packet and creates appropriate response
    '''

    async def create_response(self, packet, peer):
        response = None
        data = {}
        if (packet != None):
            #auth handler
            if packet.packetType == PacketTypes.auth:
                auth_data = PacketParser.get_arg(JSONKeys.data, packet.packetData)
                status_code, client_id, auth_token, message = await peer.callbackWrapper.validate_auth_callback(auth_data, peer.address, packet.protocol)
                if status_code != StatusCode.OK:
                    log_msg = ('Auth FAILED: auth Data {1}, message {0} [{2}]').format(message, auth_data, peer.id)
                    logger.log_warning(log_msg, peer.tag)
                response = PacketGenerator.generate_auth_res(status_code, client_id, auth_token, message)
            #conn handler
            elif packet.packetType == PacketTypes.conn:
                auth_token = PacketParser.get_arg(JSONKeys.authToken, packet.packetData)
                client_id = PacketParser.get_arg(JSONKeys.clientId, packet.packetData)
                status_code = await peer.callbackWrapper.validate_conn_callback(client_id, auth_token, peer.address, packet.protocol)
                if status_code == StatusCode.OK:
                    connected = await self.connect_client(auth_token, client_id, packet.protocol, peer)
                    if connected:
                        status_code = StatusCode.OK
                        data = {'client_id' : client_id}
                        info_msg = ('Connnected: client {0} {1}').format(client_id, peer.id)
                        logger.log_info(info_msg, peer.tag)
                    else:
                        status_code = StatusCode.NOT_ALLOWED
                if status_code != StatusCode.OK:
                    log_msg = ('Conn FAILED: token {1}, status {0} {2}').format(status_code, auth_token, peer.id)
                    logger.log_warning(log_msg, peer.tag)
                response = PacketGenerator.generate_conn_res(status_code, self.settings.TIMEOUT_SECONDS)
            elif peer.client_id != None:
                #disconn handler
                if packet.packetType == PacketTypes.disconn:
                    pck_id = PacketParser.get_arg(JSONKeys.packetId, packet.packetData)
                    await self.disconnect_client(peer.client_id, has_client_disconnected = True)
                    log_msg = ('disconn from client {0} {1}').format(peer.client_id, peer.id)
                    logger.log_info(log_msg, peer.tag)
                #pub handler
                elif packet.packetType == PacketTypes.pub:
                    channel_name = PacketParser.get_arg(JSONKeys.channelName, packet.packetData)
                    channel_valid, channel_name = self.is_channel_valid(channel_name)
                    pck_id = PacketParser.get_arg(JSONKeys.packetId, packet.packetData)
                    if channel_valid:
                        data = PacketParser.get_arg(JSONKeys.data, packet.packetData)
                        retain_flag = PacketParser.get_arg(JSONKeys.retainFlag, packet.packetData, False)
                        qos = PacketParser.get_arg(JSONKeys.qos, packet.packetData, QOS.ZERO)
                        if not self.is_channel_control(channel_name):
                            status_code = await peer.callbackWrapper.validate_pub_callback(peer.client_id, channel_name, data, qos, peer.address, packet.protocol)
                            if status_code != StatusCode.OK:
                                log_msg = ('Pub FAILED channel {0} from client {1} , qos {3}, retain {4} {2} : status {5}').format(channel_name, peer.client_id, peer.id, qos, retain_flag, status_code)
                                logger.log_warning(log_msg, peer.tag)
                            else:
                                log_msg = ('Pub OK channel {0} from client {1} , qos {3}, retain {4} {2}').format(channel_name, peer.client_id, peer.id, qos, retain_flag)
                                logger.log_debug(log_msg, peer.tag)
                            if status_code == StatusCode.OK:
                                status_code = await self.pub(peer.client_id, channel_name, data, retain_flag, qos)
                            # check qos, only send pub ack if qos is 1
                            if qos == QOS.ONE:
                                response = PacketGenerator.generate_pub_res(status_code, pck_id)
                        else:
                            status_code, response_data = await peer.callbackWrapper.control_data_callback(peer.client_id, channel_name, data, peer.address, packet.protocol)
                            response = PacketGenerator.generate_pub_res(status_code, pck_id, response_data)
                            log_msg = ('Control Pub channel {0} from client {1} {2} : status {3}').format(channel_name, peer.client_id, peer.id, status_code)
                            logger.log_info(log_msg, peer.tag)
                    else:
                        status_code = StatusCode.INVALID_CHANNEL
                        response = PacketGenerator.generate_pub_res(status_code, pck_id)
                        msg = ('Pub INVALID channel {0} from client {1} {2}').format(channel_name, peer.client_id, peer.id)
                        logger.log_warning(msg, peer.tag)
                    
                #pushAck handler
                elif packet.packetType == PacketTypes.pushAck:
                    pck_id = PacketParser.get_arg(JSONKeys.packetId, packet.packetData)
                    await self.process_push_ack(pck_id, peer.client_id)
                    log_msg = ('PushAck for pck id {2} from client {0} {1}').format(peer.client_id, peer.id, pck_id)
                    logger.log_debug(log_msg, peer.tag)
                #sub handler
                elif packet.packetType == PacketTypes.sub:
                    channel_name = PacketParser.get_arg(JSONKeys.channelName, packet.packetData)
                    persistent_flag = PacketParser.get_arg(JSONKeys.persistent, packet.packetData, False)
                    channel_valid, channel_name = self.is_channel_valid(channel_name)
                    if channel_valid:
                        status_code = await peer.callbackWrapper.validate_sub_callback(peer.client_id, channel_name, persistent_flag, peer.address, packet.protocol)
                    else:
                        status_code = StatusCode.INVALID_CHANNEL
                    if status_code == StatusCode.OK:
                        status_code = await self.sub(peer.client_id, channel_name, persistent_flag)
                    response = PacketGenerator.generate_sub_res(status_code, channel_name)
                    if status_code != StatusCode.OK:
                        log_msg = ('Sub FAILED channel {0} with persistent {4} from client {1} {2} : status {3}').format(channel_name, peer.client_id, peer.id, status_code, persistent_flag)
                        logger.log_warning(log_msg, peer.tag)
                    else:
                        log_msg = ('Sub OK channel {0} with persistent {3} from client {1} {2}').format(channel_name, peer.client_id, peer.id, persistent_flag)
                        logger.log_debug(log_msg, peer.tag)
                #unsub handler
                elif packet.packetType == PacketTypes.unsub:
                    channel_name = PacketParser.get_arg(JSONKeys.channelName, packet.packetData)
                    channel_valid, channel_name = self.is_channel_valid(channel_name)
                    if channel_valid:
                        status_code = await peer.callbackWrapper.validate_unsub_callback(peer.client_id, channel_name, peer.address, packet.protocol)
                    else:
                        status_code = StatusCode.INVALID_CHANNEL
                    if status_code == StatusCode.OK:
                        status_code = await self.unsub(peer.client_id, channel_name)
                    response = PacketGenerator.generate_unsub_res(status_code, channel_name)
                    if status_code != StatusCode.OK:
                        log_msg = ('Unsub FAILED channel {0} from client {1} {2} : status {3}').format(channel_name, peer.client_id, peer.id, status_code)
                        logger.log_warning(log_msg, peer.tag)
                    else:
                        log_msg = ('Unsub OK channel {0} from client {1} {2}').format(channel_name, peer.client_id, peer.id)
                        logger.log_debug(log_msg, peer.tag)
                #hb handler
                elif packet.packetType == PacketTypes.hb:
                    await self.heartbeat(peer.client_id)
                    log_msg = ('Heartbeat from client {0} {1}').format(peer.client_id, peer.id)
                    logger.log_debug(log_msg, peer.tag)
                    if peer.client_id != None:
                        response = PacketGenerator.generate_heartbeat_res()
            else:
                logger.log_info('WARNING: access without connecting from peer ' + str(peer.id), 'create_response')
                response = None
        return (response, data)
    
    '''
    END SECTION #6
    '''