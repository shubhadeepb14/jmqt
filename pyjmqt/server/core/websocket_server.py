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

import websockets
import asyncio
import ssl
import time
import datetime
from collections import OrderedDict
import json
import uuid

import pyjmqt.server.logger as logger
from pyjmqt.server.core.packets import *
from pyjmqt.server.core.constants import *


class Peer(object):
    def __init__(self, websocket, remoteHost, callbackWrapper, connectionHandler, settings, tag):
        self.settings = settings
        self.protocol = Protocol.WEB_SOCKET
        self.tag = tag
        self.address = str(remoteHost)
        self.id = str(remoteHost)
        self.callbackWrapper = callbackWrapper
        self.websocket = websocket
        self.client_id = None
        self.connectionHandler = connectionHandler
        self.run = True

    async def disconnect(self):
        try:
            self.run = False
            self.websocket.close()
        except Exception as e:
            logger.log_error(e, '[disconnect] ' + self.tag)
                
    async def parse_and_respond(self, message):
        body = message
        packet, msg = PacketParser.parse_packet(body, self.protocol)
        response, data = await self.connectionHandler.create_response(packet, self)
        if response != None:
            await self.send(response)
            if packet.packetType == PacketTypes.conn:
                pckData = response[PacketTypes.connAck]
                status = PacketParser.get_arg(JSONKeys.statusCode, pckData)
                if 'client_id' in data and status == StatusCode.OK:
                    self.client_id = data['client_id']
                    # clearing the pending and retained messages
                    asyncio.Task(self.connectionHandler.send_pending_pub(self.client_id))
                    asyncio.Task(self.connectionHandler.send_retained(self.client_id))
            elif packet.packetType == PacketTypes.sub:
                pckData = response[PacketTypes.subAck]
                status = PacketParser.get_arg(JSONKeys.statusCode, pckData)
                channel_name = PacketParser.get_arg(JSONKeys.channelName, pckData)
                if status == StatusCode.OK:
                    # clearing the pending messages
                    asyncio.Task(self.connectionHandler.send_retained(self.client_id, channel = channel_name))

    async def send(self, data):
        try:
            message = json.dumps(data)
            await self.websocket.send(message)
        except Exception as e:
            logger.log_error(e, '[sender] ' + self.tag)

    async def send_response(self, message):
        await self.parse_and_respond(message)


class WebSocketServer(object):
    c = 0
    TAG = Protocol.WEB_SOCKET
    def __init__(self, eventLoop, __callbackWrapper, connectionHandler, settings):
        self.settings = settings
        self.loop = eventLoop
        self.__callbackWrapper = __callbackWrapper
        self.connectionHandler = connectionHandler

    def start(self):
        logger.log_info(('Listening on tcp {0}'.format(self.settings.WEBSOCKET_PORT)), self.TAG)
        self.server = self.loop.run_until_complete(websockets.serve(self.handler, '0.0.0.0', self.settings.WEBSOCKET_PORT))

    async def handler(self, websocket, path):
        remoteIP, remotePort = websocket.remote_address
        remoteHost = str(remoteIP) + ':' + str(remotePort)
        peer = Peer(websocket, remoteHost, self.__callbackWrapper, self.connectionHandler, self.settings, self.TAG)
        try:
            while peer.run:
                message = await asyncio.wait_for(websocket.recv(), timeout=self.settings.TIMEOUT_SECONDS)
                if peer.run:
                    asyncio.Task(peer.send_response(message))
                else:
                    break
        except asyncio.TimeoutError:
            logger.log_error(('TImeout: client {0}, peer {1}'.format(peer.client_id, peer.id)), self.TAG)
        finally:
            if peer.client_id != None:
                if peer.run:
                    await self.connectionHandler.disconnect_client(peer.client_id)
                logger.log_info(('Conn closed: client {0}, peer {1}'.format(peer.client_id, peer.id)), self.TAG)
            else:
                logger.log_info(('Conn closed: peer {0}'.format(peer.id)), self.TAG)
            try:
                websocket.close()
            except:
                pass


class SSLWebSocketServer(object):
    c = 0
    TAG = Protocol.WEB_SOCKET
    def __init__(self, eventLoop, __callbackWrapper, connectionHandler, settings):
        self.settings = settings
        self.loop = eventLoop
        self.__callbackWrapper = __callbackWrapper
        self.connectionHandler = connectionHandler

    def start(self):
        logger.log_info(('Listening on tcp {0}'.format(self.settings.SSL_WEBSOCKET_PORT)), self.TAG)
        sc = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        sc.load_cert_chain(self.settings.SSL_CERT_PATH, self.settings.SSL_KEY_PATH)
        self.server = self.loop.run_until_complete(websockets.serve(self.handler, '0.0.0.0', self.settings.SSL_WEBSOCKET_PORT, ssl=sc))

    async def handler(self, websocket, path):
        remoteIP, remotePort = websocket.remote_address
        remoteHost = str(remoteIP) + ':' + str(remotePort)
        peer = Peer(websocket, remoteHost, self.__callbackWrapper, self.connectionHandler, self.settings, self.TAG)
        try:
            while peer.run:
                message = await asyncio.wait_for(websocket.recv(), timeout=self.settings.TIMEOUT_SECONDS)
                if peer.run:
                    asyncio.Task(peer.send_response(message))
                else:
                    break
        except asyncio.TimeoutError:
            logger.log_error(('TImeout: client {0}, peer {1}'.format(peer.client_id, peer.id)), self.TAG)
        finally:
            if peer.client_id != None:
                if peer.run:
                    await self.connectionHandler.disconnect_client(peer.client_id)
                logger.log_info(('Conn closed: client {0}, peer {1}'.format(peer.client_id, peer.id)), self.TAG)
            else:
                logger.log_info(('Conn closed: peer {0}'.format(peer.id)), self.TAG)
            try:
                websocket.close()
            except:
                pass
            return