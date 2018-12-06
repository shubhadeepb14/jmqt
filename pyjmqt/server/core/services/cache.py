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

import datetime
import threading
import asyncio
import uuid
import json

import pyjmqt.server.logger as logger

# from mongoengine import *
# from pyjmqt.server.core.services.models import *

global redisApi
redisApi = None

class CacheService():
    REDIS_ENABLED = False
    MONGO_ENABLED = False
    REDIS_PUB_CHANNEL = 'JMQTPub_{client_id}'
    REDIS_DISCONNECT_CHANNEL = 'JMQTDisc_{client_id}'
    REDIS_SUB_CHANNEL = 'JMQTSub'
    REDIS_UNSUB_CHANNEL = 'JMQTUnsub'
    REDIS_PUSH_COUNTER = 'JMQTPckCount'

    REDIS_PUB_CHANNEL_PACKET = 'p'
    REDIS_PUB_CHANNEL_CLIENT = 'c'
    REDIS_SUB_CHANNEL_CLIENT = 'c'
    REDIS_SUB_CHANNEL_CHANNEL = 'ch'
    REDIS_SUB_CHANNEL_PERSISTENT = 'p'
    REDIS_DISCONNECT_CHANNEL_CLIENT = 'c'
    REDIS_DISCONNECT_CHANNEL_SERVER_ID = 's'

    def __init__(self, settings, eventLoop, serverId, dbService, pubCallback, disconnectCallback):
        self.settings = settings
        self.dbService = dbService
        self.REDIS_ENABLED = settings.ENABLE_REDIS
        if self.REDIS_ENABLED:
            global redisApi
            import redis
            redisApi = redis

        self.loop = eventLoop
        self.run = True
        self.serverId = serverId
        self.pubCallback = pubCallback
        self.disconnectCallback = disconnectCallback
        self.pubChannels = []
        self.disconnectionChannels = []
        self.connect_redis()
    
    def connect_redis(self):
        if self.REDIS_ENABLED:
            self.redisConn = redisApi.Redis(
                    host=self.settings.REDIS_HOST, 
                    port=self.settings.REDIS_PORT, 
                    db=self.settings.REDIS_DB_INDEX, 
                    password=self.settings.REDIS_PASSWORD)
            response = self.redisConn.client_list()            
            # creates a redis pubsub object
            self.redisPubSub = self.redisConn.pubsub()
            # subscribes to a test channel (needed to execute get_message)
            self.redisPubSub.subscribe('test')
            self.redisPubSub.subscribe(self.REDIS_SUB_CHANNEL)
            self.redisPubSub.subscribe(self.REDIS_UNSUB_CHANNEL)
        else:
            logger.log_info('Redis is disabled. Skip connection..', 'CacheService')
        # runs a thread to read published data from redis and to clear buffered packets
        if self.REDIS_ENABLED:
            t1 = threading.Thread(target=self.__run_redis_thread, args=())
            t1.start()
        t2 = threading.Thread(target=self.__run_remove_buffer_thread, args=())
        t2.start()

    def __run_redis_thread(self):        
        loop = asyncio.new_event_loop()
        loop.run_until_complete(self.__redis_sub_thread(loop))

    def __run_remove_buffer_thread(self):
        self.dbService.load_subscriptions()
        loop = asyncio.new_event_loop()
        loop.run_until_complete(self.__clear_remove_buffer(loop))

    # thread for redis based subscriptions
    async def __redis_sub_thread(self, loop):
        asyncio.set_event_loop(self.loop)
        logger.log_info('Starting redis subscription reader..', 'CacheService(redis_sub_thread)')
        while self.run:
            if self.redisPubSub != None:
                message = self.redisPubSub.get_message()
                try:
                    if message:
                        if message['type'] != 'subscribe' and message['type'] != 'unsubscribe':
                            channel_name = message['channel'].decode("utf-8")
                            data = json.loads(message['data'])
                            if channel_name in self.pubChannels:
                                packet = data[self.REDIS_PUB_CHANNEL_PACKET]
                                client_id = data[self.REDIS_PUB_CHANNEL_CLIENT]
                                await self.pubCallback(packet['c'], packet['d'], packet['f'], packet['q'], packet['id'], client_id)
                            elif channel_name in self.disconnectionChannels:
                                client_id = data[self.REDIS_DISCONNECT_CHANNEL_CLIENT]
                                server_id = data[self.REDIS_DISCONNECT_CHANNEL_SERVER_ID]
                                if server_id != self.serverId:
                                    asyncio.Task(self.disconnectCallback(client_id))
                            elif channel_name == self.REDIS_SUB_CHANNEL:
                                client_id, channel, persistent_flag = data[self.REDIS_SUB_CHANNEL_CLIENT], data[self.REDIS_SUB_CHANNEL_CHANNEL], data[self.REDIS_SUB_CHANNEL_PERSISTENT]
                                await self.dbService.insert_subscription(client_id, channel, persistent_flag, addtodb = False)
                            elif channel_name == self.REDIS_UNSUB_CHANNEL:
                                client_id, channel = data[self.REDIS_SUB_CHANNEL_CLIENT], data[self.REDIS_SUB_CHANNEL_CHANNEL]
                                await self.dbService.remove_subscription(client_id, channel, removefromdb = False)
                except Exception as ex:
                    logger.log_error(ex, 'CacheService(redis_sub_thread)')
            else:
                await asyncio.sleep(1)
    
    # thread for clearing remove buffer from dbService
    async def __clear_remove_buffer(self, loop):
        asyncio.set_event_loop(self.loop)
        c = 0
        while self.run:
            if c == 8:
                c = 0
                await self.dbService.remove_pubmap_by_channel_from_map()
                await self.dbService.remove_pubmap_from_map()
            c += 1
            await asyncio.sleep(2)

    # gets the packet counter from redis, increases in exsists, creates if not
    async def get_next_packet_pck_id(self):
        return str(uuid.uuid1())

    async def process_connection(self, client_id):
        if self.REDIS_ENABLED:
            disconnect_data = json.dumps({
                    self.REDIS_DISCONNECT_CHANNEL_CLIENT: client_id,
                    self.REDIS_DISCONNECT_CHANNEL_SERVER_ID: self.serverId
                })
            # build the disconnect and pub channel names
            disconnect_channel = self.REDIS_DISCONNECT_CHANNEL.format(client_id=client_id)
            pub_channel = self.REDIS_PUB_CHANNEL.format(client_id=client_id)
            # broadcast to all other server instances to disconnect the client
            self.redisConn.publish(disconnect_channel, disconnect_data)
            # subscribe to the pub and disconnect channel for the client to receive data from __redis_sub_thread
            self.redisPubSub.subscribe(disconnect_channel)
            self.redisPubSub.subscribe(pub_channel)
            self.pubChannels.append(pub_channel)
            self.disconnectionChannels.append(disconnect_channel)

    async def process_disconnection(self, client_id):
        if self.REDIS_ENABLED:
            # build the disconnect and pub channel names
            disconnect_channel = self.REDIS_DISCONNECT_CHANNEL.format(client_id=client_id)
            pub_channel = self.REDIS_PUB_CHANNEL.format(client_id=client_id)
            # unsubscribe from the pub and disconnect channel for the client to receive data from __redis_sub_thread
            self.redisPubSub.unsubscribe(disconnect_channel)
            self.redisPubSub.unsubscribe(pub_channel)
            if pub_channel in self.pubChannels:
                self.pubChannels.remove(pub_channel)
            if disconnect_channel in self.disconnectionChannels:
                self.disconnectionChannels.remove(disconnect_channel)
    
    async def handle_pub(self, client_id, pub_data):
        if self.REDIS_ENABLED:
            # build the pub data
            pub_data = json.dumps({
                self.REDIS_PUB_CHANNEL_PACKET : pub_data,
                self.REDIS_PUB_CHANNEL_CLIENT: client_id
                })
            # build the pub channel name
            pub_channel = self.REDIS_PUB_CHANNEL.format(client_id=client_id)
            # broadcast the data (to be read by __redis_sub_thread)
            self.redisConn.publish(pub_channel, pub_data)
        else:
            asyncio.Task(self.pubCallback(pub_data['c'], pub_data['d'], pub_data['f'], pub_data['q'], pub_data['id'], client_id))

    async def handle_sub(self, client_id, channel, persistent_flag):
        if self.REDIS_ENABLED:
            # build the sub data
            sub_data = json.dumps({
                self.REDIS_SUB_CHANNEL_CHANNEL : channel,
                self.REDIS_SUB_CHANNEL_CLIENT: client_id,
                self.REDIS_SUB_CHANNEL_PERSISTENT: persistent_flag
                })
            # broadcast the data (to be read by __redis_sub_thread)
            self.redisConn.publish(self.REDIS_SUB_CHANNEL, sub_data)
        await self.dbService.insert_subscription(client_id, channel, persistent_flag, addtodb = True)
    
    async def handle_unsub(self, client_id, channel):
        if self.REDIS_ENABLED:
            # build the sub data
            unsub_data = json.dumps({
                self.REDIS_SUB_CHANNEL_CHANNEL : channel,
                self.REDIS_SUB_CHANNEL_CLIENT: client_id
                })
            # broadcast the data (to be read by __redis_sub_thread)
            self.redisConn.publish(self.REDIS_UNSUB_CHANNEL, unsub_data)
        await self.dbService.remove_subscription(client_id, channel, removefromdb = True)