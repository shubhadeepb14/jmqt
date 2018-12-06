# The MIT License (MIT)
# Copyright (c) 2018 Shubhadeep Banerjee
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated BaseModelation files (the "Software"), to deal
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
import os
from collections import namedtuple

import pyjmqt.server.logger as logger

from peewee import *

DB_PROXY = Proxy()

class BaseModel(Model):
    class Meta:
        database = DB_PROXY

class Connections(BaseModel):
    client_id = TextField()
    protocol = TextField()
    address = TextField()
    timestamp = DateTimeField()

class Subscriptions(BaseModel):
    client_id = TextField()
    channel = TextField()
    is_tmp = BooleanField(default=False)

class RetainedPackets(BaseModel):
    sender_id = TextField()
    channel = TextField()
    data = TextField()
    timestamp = DateTimeField()

class Packets(BaseModel):
    packet_id = TextField()
    sender_id = TextField()
    channel = TextField()
    data = TextField()
    timestamp = DateTimeField()

class Pubmaps(BaseModel):
    packet_id = TextField()
    client_id = TextField()
    channel = TextField()

subscription_entry = namedtuple('subscription_entry',['client_id','channel','is_tmp'])

class PeeweeBase():

    listRemovedPubmaps = []
    listRemoveChannelsWithClient = []
    subscriptions = []

    # return nothing
    async def check_connection(self, client_id):
        try:
            connections = Connections.select().where(Connections.client_id == client_id)
            if connections.count() > 0:
                return {'address': connections[0].address, 'protocol': connections[0].protocol}
        except Exception as ex:
            logger.log_error(ex, 'PeeweeBase(check_connection)')
        return None
    
    # return list of dict
    async def get_all_connections(self):
        try:
            connections = Connections.select()
            if connections.count() > 0:
                clients = []
                for c in connections:
                    clients.append({
                        c.client_id : {
                        'protocol': c.protocol,
                        'address': c.address
                    }})
                return clients
        except Exception as ex:
            logger.log_error(ex, 'PeeweeBase(get_all_connections)')
        return []

    # return nothing
    async def remove_connection(self, client_id):
        try:
            Connections.delete().where(Connections.client_id == client_id).execute()
        except Exception as ex:
            logger.log_error(ex, 'PeeweeBase(remove_connection)')

    # return nothing
    async def insert_or_update_connection(self, client_id, protocol, address):
        try:
            await self.remove_connection(client_id)
            Connections.create(client_id = client_id,
                                protocol = protocol,
                                address = address,
                                timestamp = datetime.datetime.utcnow())
        except Exception as ex:
            logger.log_error(ex, 'PeeweeBase(insert_or_update_connection)')
    
    def load_subscriptions(self):
        try:
            subscriptions = Subscriptions.select()
            for s in subscriptions:
                self.subscriptions.append(subscription_entry(s.client_id, s.channel, s.is_tmp))
        except Exception as ex:
            logger.log_error(ex, 'PeeweeBase(load_subscriptions)')

    # return string list
    async def get_subscription_by_channel(self, channel):
        try:
            clients = []
            for s in self.subscriptions:
                if s.channel == channel:
                    clients.append(s.client_id)
            return clients
        except Exception as ex:
            logger.log_error(ex, 'PeeweeBase(get_subscription_by_channel)')
        return []
    
    # return string list
    async def get_subscription_by_client(self, client_id):
        try:
            channels = {}
            for s in self.subscriptions:
                if s.client_id == client_id:
                    channels[s.channel] = 'temp' if s.is_tmp else 'persistent'
            return channels
        except Exception as ex:
            logger.log_error(ex, 'PeeweeBase(get_subscription_by_client)')
        return {}
    
    # return string list
    def get_all_subscriptions(self):
        try:
            channels = {}
            for s in self.subscriptions:
                if not s.client_id in channels:
                    channels[s.client_id] = {}
                channels[s.client_id][s.channel] = 'temp' if s.is_tmp else 'persistent'
            return channels
        except Exception as ex:
            logger.log_error(ex, 'PeeweeBase(get_subscription_by_client)')
        return []
        
    # return number
    async def check_subscription(self, client_id, channel):
        try:
            count = len([s.channel for s in self.subscriptions if (s.client_id == client_id and s.channel == channel)])
            # count = Subscriptions.select().where(Subscriptions.client_id == client_id, Subscriptions.channel == channel).count()
            return count
        except Exception as ex:
            logger.log_error(ex, 'PeeweeBase(check_subscription)')
        return 0

    # return nothing
    async def remove_subscription(self, client_id, channel, removefromdb = True):
        try:
            i = 0
            found = False
            for s in self.subscriptions:
                if s.channel == channel and s.client_id == client_id:
                    found = True
                    break
                i += 1
            if found:
                self.subscriptions.pop(i)
            if removefromdb:
                await self.remove_pubmap_by_channel(channel, client_id)
        except Exception as ex:
            logger.log_error(ex, 'PeeweeBase(remove_subscription)')

    # return nothing
    async def insert_subscription(self, client_id, channel, persistent_flag, addtodb = True):
        try:
            check = await self.check_subscription(client_id, channel)
            if check == 0:
                self.subscriptions.append(subscription_entry(client_id, channel, not persistent_flag))
                if addtodb:
                    Subscriptions.create(client_id = client_id,
                                            channel = channel,
                                            is_tmp = not persistent_flag)
        except Exception as ex:
            logger.log_error(ex, 'PeeweeBase(insert_subscription)')

    # return dict 
    async def get_packet(self, packet_id):
        try:
            packets = Packets.select().where(Packets.packet_id == packet_id)
            # to do order by timestamp
            if packets.count() > 0:
                p = packets[0]
                return ({
                    'packet_id' : p.packet_id,
                    'sender_id' : p.sender_id,
                    'channel' : p.channel,
                    'data' : json.loads(p.data)['d'],
                    'timestamp' : p.timestamp
                    })
        except Exception as ex:
            logger.log_error(ex, 'PeeweeBase(get_packet)')
        return None

    # return nothing 
    async def insert_packet(self, packet_id, sender_id, channel, data):
        try:
            Packets.create(packet_id = packet_id,
                            sender_id = sender_id,
                            channel = channel,
                            data = json.dumps({'d': data}),
                            timestamp = datetime.datetime.utcnow())
        except Exception as ex:
            logger.log_error(ex, 'PeeweeBase(insert_packet)')
    
    # return array of dict 
    async def get_retained_packets(self, channels):
        try:
            packets = RetainedPackets.select().where(RetainedPackets.channel << channels)
            result = []
            for p in packets:
                result.append({
                    'sender_id' : p.sender_id,
                    'channel' : p.channel,
                    'data' : json.loads(p.data)['d'],
                    'timestamp' : p.timestamp
                    })
            return result
        except Exception as ex:
            logger.log_error(ex, 'PeeweeBase(get_retained_packets)')
        return None

    # return nothing 
    async def insert_retained_packet(self, sender_id, channel, data):
        try:
            RetainedPackets.delete().where(RetainedPackets.channel == channel).execute()
            RetainedPackets.create(sender_id = sender_id,
                                    channel = channel,
                                    data = json.dumps({'d': data}),
                                    timestamp = datetime.datetime.utcnow())
        except Exception as ex:
            logger.log_error(ex, 'PeeweeBase(insert_retained_packet)')

    # return list of string 
    async def get_pubmap(self, client_id):
        try:
            pubmaps = Pubmaps.select().where(Pubmaps.client_id == client_id)
            packet_ids = []
            for p in pubmaps:
                packet_ids.append(p.packet_id)
            return packet_ids
        except Exception as ex:
            logger.log_error(ex, 'PeeweeBase(get_pubmap)')
        return []

    # return nothing 
    async def remove_packets_by_pubmap(self, packet_ids):
        try:
            for packet_id in packet_ids:
                count = Pubmaps.select().where(Pubmaps.packet_id == packet_id).count()
                if count == 0:
                    Packets.delete().where(Packets.packet_id == packet_id).execute()
        except Exception as ex:
            logger.log_error(ex, 'PeeweeBase(remove_packets_by_pubmap)')

    # return nothing 
    async def remove_pubmap(self, packet_id, client_id):
        _map = {
            'p': packet_id, 'c': client_id
        }
        self.listRemovedPubmaps.append(_map)
    
    # return list of string
    async def remove_pubmap_by_channel(self, channel, client_id):
        _map = {
            'ch': channel, 'c': client_id
        }
        self.listRemoveChannelsWithClient.append(_map)
    
    # return nothing 
    async def remove_pubmap_from_map(self):
        error = False
        if len(self.listRemovedPubmaps) > 0:
            logger.log_debug(('Removing {0} maps').format(len(self.listRemovedPubmaps)), 'PeeweeBase(remove_pubmap_from_map)')
            packet_ids = []
            for _map in self.listRemovedPubmaps:
                packet_id, client_id = _map['p'], _map['c']
                packet_ids.append(packet_id)
                # print (packet_id, client_id)
                try:
                    Pubmaps.delete().where(Pubmaps.packet_id == packet_id, Pubmaps.client_id == client_id).execute()
                except Exception as ex:
                    logger.log_error(ex, 'PeeweeBase(remove_pubmap_from_map)')
                    error = True
                    break
            await self.remove_packets_by_pubmap(packet_ids)
            if not error:
                self.listRemovedPubmaps.clear()
    
    # return nothing
    async def remove_pubmap_by_channel_from_map(self):
        error = False
        if len(self.listRemoveChannelsWithClient) > 0:
            logger.log_debug(('Removing {0} maps by channels').format(len(self.listRemoveChannelsWithClient)), 'PeeweeBase(remove_pubmap_by_channel_from_map)')
            for _map in self.listRemoveChannelsWithClient:
                try:
                    channel, client_id = _map['ch'], _map['c']
                    Subscriptions.delete().where(Subscriptions.client_id == client_id, Subscriptions.channel == channel).execute()
                    pubmaps = Pubmaps.select().where(Pubmaps.channel == channel, Pubmaps.client_id == client_id)
                    ids = []
                    for p in pubmaps:
                        ids.append(p.packet_id)
                    Pubmaps.delete().where(Pubmaps.channel == channel, Pubmaps.client_id == client_id).execute()
                    await self.remove_packets_by_pubmap(ids)
                except Exception as ex:
                    logger.log_error(ex, 'PeeweeBase(remove_pubmap_by_channel_from_map)')
                    error = True
                    break
            if not error:
                self.listRemoveChannelsWithClient.clear()

    # return nothing 
    async def insert_pubmap(self, packet_id, client_id, channel):
        try:
            Pubmaps.create(client_id = client_id,
                            packet_id = packet_id,
                            channel = channel)
        except Exception as ex:
            logger.log_error(ex, 'PeeweeBase(insert_pubmap)')