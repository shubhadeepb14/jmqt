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

from socket import socket, SO_REUSEADDR, SOL_SOCKET
import asyncio
import ssl
import time
import datetime
from collections import OrderedDict
import json

import pyjmqt.server.logger as logger
from pyjmqt.server.core.packets import *
from pyjmqt.server.core.constants import *

class Peer(object):
    def __init__(self, reader, writer, remoteHost, callbackWrapper, connectionHandler, settings, tag):
        self.settings = settings
        self.protocol = Protocol.SOCKET
        self.tag = tag
        self.address = str(remoteHost)
        self.id = str(remoteHost)
        self.callbackWrapper = callbackWrapper
        self.reader = reader
        self.writer = writer
        self.client_id = None
        self.connectionHandler = connectionHandler
        self.run = True

    async def disconnect(self):
        self.run = False
        self.writer.close()
        if self.client_id != None:
            logger.log_info(('Conn closed: client {0}, peer {1}'.format(self.client_id, self.id)), self.tag)
        else:
            logger.log_info(('Conn closed: peer {0}'.format(self.id)), self.tag)

    async def _peer_loop(self):
        buffer = bytes()
        while self.run:
            disconnect = False
            try:
                part = await asyncio.wait_for(self.reader.read(1024), timeout=self.settings.TIMEOUT_SECONDS)
                if part == b'':
                    disconnect = True
                if self.run:                 
                    buffer += part
                    packets = buffer.split(b'\0')
                    last_index = len(packets) - 1
                    buffer = packets[last_index]
                    if len(packets) > 1:
                        if len(buffer) == 0:
                            del packets[last_index]
                        asyncio.Task(self.send_response(packets))
                else:
                    break
            except asyncio.TimeoutError:
                logger.log_error(('TImeout: client {0}, peer {1}'.format(self.client_id, self.id)), self.tag)
                disconnect = True
            if disconnect:
                if self.run and self.client_id is None:
                    await self.disconnect()
                else:
                    await self.connectionHandler.disconnect_client(self.client_id)
                break
                
    async def parse_and_respond(self, pck):
        body = pck.decode('utf8')
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
            if not message.endswith('\0'):
                message += '\0'
            self.writer.write(message.encode('utf8'))
            await self.writer.drain()
        except Exception as e:
            logger.log_error(e, '[sender] ' + self.tag)

    async def send_response(self, packets):
        for pck in packets:
            await self.parse_and_respond(pck)


class SocketServer(object):
    TAG = Protocol.SOCKET
    def __init__(self, eventLoop, __callbackWrapper, connectionHandler, settings):
        self.settings = settings
        self.loop = eventLoop
        self.__callbackWrapper = __callbackWrapper
        self.connectionHandler = connectionHandler

    def start(self):
        logger.log_info(('Listening on tcp {0}'.format(self.settings.SOCKET_PORT)), self.TAG)
        self.coro = asyncio.start_server(self.handle_client, '', self.settings.SOCKET_PORT, loop=self.loop)
        self.server = self.loop.run_until_complete(self.coro)

    def handle_client(self, reader, writer):
        remoteIP, remotePort =  writer.get_extra_info('peername')
        remoteHost = str(remoteIP) + ':' + str(remotePort)
        peer = Peer(reader, writer, remoteHost, self.__callbackWrapper, self.connectionHandler, self.settings, self.TAG)
        asyncio.Task(peer._peer_loop())

class SSLSocketServer(object):
    TAG = Protocol.SSL_SOCKET
    def __init__(self, eventLoop, __callbackWrapper, connectionHandler, settings):
        self.settings = settings
        self.loop = eventLoop
        self.__callbackWrapper = __callbackWrapper
        self.connectionHandler = connectionHandler

    def start(self):
        logger.log_info(('Listening on tcp {0}'.format(self.settings.SSL_SOCKET_PORT)), self.TAG)
        sc = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        sc.load_cert_chain(self.settings.SSL_CERT_PATH, self.settings.SSL_KEY_PATH)
        self.coro = asyncio.start_server(self.handle_client, '', self.settings.SSL_SOCKET_PORT,  ssl=sc, loop=self.loop)
        self.server = self.loop.run_until_complete(self.coro)

    def handle_client(self, reader, writer):
        remoteIP, remotePort =  writer.get_extra_info('peername')
        remoteHost = str(remoteIP) + ':' + str(remotePort)
        peer = Peer(reader, writer, remoteHost, self.__callbackWrapper, self.connectionHandler, self.settings, self.TAG)
        asyncio.Task(peer._peer_loop())