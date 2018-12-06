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

# JMQT protocol version 1.0

import json
import threading
import time
import datetime
import socket
import ssl
import os

from pyjmqt.client.client_settings import ClientSettings
import pyjmqt.client.logger as logger

root_path = os.path.dirname(os.path.realpath(__file__))

class Client() :
    JMQT_VERSION = '1.0'
    class statusCodes:
        UNKNOWN= -1
        OK= 1
        FAILED= 0
        MALFORMED_PACKET= 3
        SERVER_ERROR= 5
        INVALID_TOKEN= 6
        NOT_ALLOWED= 7
        CLIENT_OFFLINE = 8
        NETWORK_ERROR= 9
        INVALID_PACKET= 10

    __configFile = ''
    def __init__(self, configFile):
        self.__configFile = configFile
        self.__parse_settings()        

        self.__socket = None

        self.__timeoutSeconds = 0
        self.__hbGap = 0
        self.__lastHbAck = None
        self.__lastHbSent = None

        self.__authJson = None
        self.__isAuthPending = False
        self.__clientId = None
        self.__authToken = None
        self.__isConnectPending = False
        self.__opened = False
        self.__connected = False
        self.__subCallbacks = {}
        self.__unsubCallbacks = {}
        self.__pubCallbacks = {}
        self.__authCallback = None
        self.__connectCallback = None
        self.__disconnectCallback = None
        self.__dataCallback = None
    
        self.__packetCounter = 1

    def __parse_settings(self):
        settings = {}
        default = False
        if self.__configFile is None or len(self.__configFile) == 0:
            self.__configFile = os.path.join(root_path, 'default.conf')
            default = True
        with open(self.__configFile) as fin:
            for line in fin:
                if not str(line).startswith('#'):
                    configStrs = line.split('=', 1)
                    if len(configStrs) == 2:
                        key = configStrs[0].strip()
                        value = str(configStrs[1]).strip('\n').strip()
                        try:
                            value = int(value)
                        except:
                            value = str(value).replace('"','').replace("'","")
                        # setattr(self.__settings, key, value)
                        settings[key] = value
                        # logger.log_info (key, value, getattr(self.__settings, key))
        
        self.__settings = ClientSettings(settings)

        logger.set_logger(self.__settings.LOG_PATH, mode = self.__settings.LOG_MODE)
        if default:
            logger.log_info('No config file passed, falling back to default config "' + self.__configFile + '"')
        else:
            logger.log_info('Loading config "' + self.__configFile + '"')
    
    def get_client_config(self):
        return dict(self.__settings)
    
    def get_logger(self):
        return logger

    def __increaseCounter(self):
        self.__packetCounter += 1
        if self.__packetCounter == 99999:
            self.__packetCounter = 1

    def __open(self):
        if not self.__opened:
            try:
                logger.log_info('Opening socket ' + self.__settings.REMOTE_HOST + ':' + str(self.__settings.REMOTE_PORT))
                self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                if self.__settings.ENABLE_SSL:
                    self.__socket = ssl.wrap_socket(self.__socket, keyfile=self.__settings.SSL_KEY_PATH, certfile=self.__settings.SSL_CERT_PATH)
                self.__socket.connect((self.__settings.REMOTE_HOST, self.__settings.REMOTE_PORT))
                self.__opened = True
                t = threading.Thread(target=self.__read)
                t.daemon = True
                t.start()
                self.__openHandler()
            except Exception as ex:
                logger.log_error('Socket Error ' + str(ex))
                self.__disconnectHandler()

    
    def __read(self):
        logger.log_info ('Read started')
        buffer = bytes()
        try:
            while self.__opened:
                part = self.__socket.recv(1024)
                if part == b'':
                    break
                buffer += part
                packets = PacketParser.get_packets_from_buffer(buffer)
                if len(packets) > 0:
                    buffer = bytes()
                    t = threading.Thread(target=self.__handle_packets, args=[packets])
                    t.daemon = True
                    t.start()
        except Exception as ex:
            logger.log_error('Socket Read Error ' + str(ex))
        self.__disconnectHandler()
        logger.log_info ('Read stopped')

    def __handle_packets(self, packets):
        for packet in packets:
            self.__incomingHandler(packet)

    def __send(self, msg):
        try:
            msg = msg + '\0'
            self.__socket.send(msg.encode())
        except Exception as ex:
            logger.log_error('Socket Send Error ' + str(ex))
            self.__disconnectHandler()
            raise Exception(ex)

    def __openHandler(self):
        logger.log_info('Socket opened ' + self.__settings.REMOTE_HOST + ':' + str(self.__settings.REMOTE_PORT))
        if self.__isAuthPending:
            # time.sleep(1)
            self.auth(self.__authJson, self.__authCallback)
        elif self.__isConnectPending:
            # time.sleep(1)
            self.conn(self.__clientId, self.__authToken, self.__connectCallback)

    def __disconnectHandler(self, send_disconn = False):
        if self.__connected or self.__opened:
            self.__disconnect(send_disconn)
            self.__connected = False
            self.__opened = False
            logger.log_info('Disconnected from ' + self.__settings.REMOTE_HOST + ':' + str(self.__settings.REMOTE_PORT), 'disconnect')
            if self.__disconnectCallback is not None:
                self.__disconnectCallback()
        else:
            logger.log_info('Client already disconnected!', 'disconnect')
        if self.__isAuthPending:
            self.__authCallback(self.statusCodes.NETWORK_ERROR, '', '', '')
        elif self.__isConnectPending:
            self.__connectCallback(self.statusCodes.NETWORK_ERROR)
    
    def stop(self, send_disconn = False):
        self.__disconnectHandler(send_disconn)
        

    # handles all incoming socket data
    def __incomingHandler(self, data):
        packet = json.loads(data)
        if 'authAck' in packet:
            data = packet['authAck']
            logger.log_info(('authAck, status {0}').format(data['st']))
            token = ''
            client = ''
            msg = ''
            if data['st'] == self.statusCodes.OK:
                token = data['at']
                client = data['cl']
            else:
                msg = data['mg']
            self.__isAuthPending = False
            # call auth callback
            self.__authCallback(data['st'], token, client, msg)

        elif 'connAck' in packet:
            data = packet['connAck']
            logger.log_info(('connAck, status {0}').format(data['st']))
            if data['st'] == self.statusCodes.OK:
                self.__timeoutSeconds = data['ts']
                self.__hbGap = data['ts'] - 2
                self.__lastHbAck = None
                self.__lastHbSent = None
                self.__isConnectPending = False
                self.__connected = True
                self.__heartbeat()
            # call conn callback
            self.__connectCallback(data['st'])
        
        elif 'hbAck' in packet:
            self.__lastHbAck = time.time()
            logger.log_debug('hbAck')
        
        elif 'subAck' in packet:
            data = packet['subAck']
            # call sub callback
            if data['cn'] in self.__subCallbacks:
                logger.log_debug(('subAck for {1} status {0}').format(data['st'],  data['cn']))
                self.__subCallbacks[data['cn']](data['st'], data['cn'])
            else:
                logger.log_warning(('subAck for unknown channel {1} status {0}').format(data['st'],  data['cn']))
        
        elif 'unsubAck' in packet:
            data = packet['unsubAck']
            # call sub callback
            if data['cn'] in self.__unsubCallbacks:
                logger.log_debug(('unsubAck for {1} status {0}').format(data['st'],  data['cn']))
                self.__unsubCallbacks[data['cn']](data['st'], data['cn'])
            else:
                logger.log_warning(('unsubAck for unknown channel {1} status {0}').format(data['st'],  data['cn']))
            
        elif 'pubAck' in packet:
            data = packet['pubAck']
            # call sub callback
            if data['id'] in self.__pubCallbacks:
                logger.log_debug(('pubAck for packet # {1} status {0}').format(data['st'],  data['id']))
                pubAckData = None
                if 'dt' in data:
                    pubAckData = data['dt']
                self.__pubCallbacks[data['id']](data['st'], data['id'], pubAckData)
            else:
                logger.log_warning(('pubAck for unknown packet # {1} status {0}').format(data['st'],  data['id']))

        elif 'push' in packet:
            data = packet['push']
            channel = data['cn']
            client = data['cl']
            pushData = data['dt']
            qos = 0
            retainFlag = 0
            packetId = ''
            if 'q' in data:
                qos = data['q']
            if 'rt' in data:
                retainFlag = data['rt']
            if qos == 1 and not retainFlag:
                packetId = data['id']
                self.pushAck(packetId)
            self.__dataCallback(channel, client, pushData, qos, retainFlag)

    def __createAuthRequest(self, authJson):
        return json.dumps({ 'auth': { 'dt': authJson } })

    def __createConnRequest(self, authToken, clientId):
        return json.dumps({ 'conn': { 'at': authToken, 'cl': clientId } })

    def __createDisconnRequest(self):
        return json.dumps({ 'disconn': {} })

    def __createSubRequest(self, channelName, persistentFlag):
        persistentFlag = 1 if persistentFlag else 0
        return json.dumps({ 'sub': { 'cn': channelName, 'pr': persistentFlag } })

    def __createUnsubRequest(self, channelName):
        return json.dumps({ 'unsub': { 'cn': channelName } })

    def __createPubRequest(self, channelName, payload, retainFlag, qos, packetId):
        data = {
            'cn': channelName, 'dt': payload
        }

        if str(channelName).startswith('$'):
            data['id'] = packetId
        elif qos > 0:
            data['q'] = qos
            data['id'] = packetId

        if retainFlag:
            data['rt'] = 1

        return json.dumps({ 'pub': data })

    def __createPushResponse(self, packetId):
        return json.dumps({ 'pushAck': { 'id': packetId } })

    def __createHeartbeatRequest(self):
        return json.dumps({ 'hb': {} })

    #jmqt heartbeat
    def __heartbeat(self):
        t = threading.Thread(target=self.__heartbeat_thread)
        t.daemon = True
        t.start()
    
    def __heartbeat_thread(self):
        c = 1
        logger.log_info ('HB started')
        while self.__connected:
            if self.__lastHbAck == None:
                self.__lastHbAck = time.time()
            if c == self.__hbGap:
                c = 1
                proceed = False
                diff = 0
                diff = abs(int(time.time() - self.__lastHbAck))
                if diff <= self.__timeoutSeconds:
                    logger.log_debug('Heartbeat! Differnece with last HbAck ' + str(diff))
                    proceed = True
                try:
                    if proceed:
                        self.__send(self.__createHeartbeatRequest())
                    else:
                        raise Exception('Heartbeat timeout error')
                except Exception as ex:
                    logger.log_error('Heartbeat Error ' + str(ex))
                    self.stop()
                    break
            time.sleep(1)
            c += 1
        logger.log_info ('HB stopped')

    # registers the data callback function
    def registerPushcallback(self, callback):
        self.__dataCallback = callback
    
    # registers the disconnect callback function
    def registerDisconnectcallback(self, callback):
        self.__disconnectCallback = callback

    # jmqt auth
    def auth(self, authJson, callback):
        try:
            self.__authCallback = callback
            self.__authJson = authJson
            if self.__opened:
                logger.log_info('auth..')
                self.__send(self.__createAuthRequest(authJson))
            else:
                self.__isAuthPending = True
                self.__open()
        except Exception as e:
            logger.log_error('in auth: ' + str(e))
            callback(self.statusCodes.NETWORK_ERROR, '', '', '')

    # jmqt connect
    def conn(self, clientId, authToken, callback):
        if self.__connected:
            logger.log_info('already connected..')
            callback(self.statusCodes.OK)
            return

        try:
            self.__connectCallback = callback
            self.__clientId = clientId
            self.__authToken = authToken
            if self.__opened:
                logger.log_info('conn..')
                self.__send(self.__createConnRequest(authToken, clientId))
            else:
                self.__isConnectPending = True
                self.__open()
        except Exception as e:
            logger.log_error('in conn: ' + str(e))
            callback(self.statusCodes.NETWORK_ERROR)
    

    # jmqt subscribe
    def sub(self, channelName, persistentFlag, callback):
        try:
            if (not self.__connected):
                raise Exception('client not connected')
        
            self.__subCallbacks[channelName] = callback
            logger.log_info(("sub '{0}' persistent {1}").format(channelName, persistentFlag))
            self.__send(self.__createSubRequest(channelName, persistentFlag))
        except Exception as e:
            logger.log_error('in sub: ' + str(e))
            callback(self.statusCodes.NETWORK_ERROR, channelName)
        
    # jmqt unsubscribe
    def unsub(self, channelName, callback):
        try:
            if (not self.__connected):
                raise Exception('client not connected')
            self.__unsubCallbacks[channelName] = callback
            logger.log_info(("sub '{0}'").format(channelName))
            self.__send(self.__createUnsubRequest(channelName))
        except Exception as e:
            logger.log_error('in unsub: ' + str(e))
            callback(self.statusCodes.NETWORK_ERROR, channelName)

    # jmqt publish
    def pub(self, channelName, data, retainFlag, qos, callback):
        packetId = str(self.__packetCounter)
        self.__increaseCounter()
        try:
            if (not self.__connected):
                raise Exception('client not connected')
    
            self.__pubCallbacks[packetId] = callback
            logger.log_debug(("pub packet # '{0}' qos {1} retain {2}").format(packetId, qos, retainFlag))
            self.__send(self.__createPubRequest(channelName, data, retainFlag, qos, packetId))
        except Exception as e:
            logger.log_error('in pub: ' + str(e))
            callback(self.statusCodes.NETWORK_ERROR, packetId, None)
        return packetId

    # jmqt push ack
    def pushAck(self, packetId):
        try:
            logger.log_info(("pushAck packet # '{0}'").format(packetId))
            self.__send(self.__createPushResponse(packetId))
        except Exception as e:
            logger.log_error('in pushAck: ' + str(e))

    def __disconnect(self, send_disconn = False):
        if self.__socket is not None:
            if send_disconn:
                logger.log_info('Sending disconn..')
                self.__send(self.__createDisconnRequest())
            logger.log_info('Closing socket ' + self.__settings.REMOTE_HOST + ':' + str(self.__settings.REMOTE_PORT))
            try:
                self.__socket.shutdown(socket.SHUT_RDWR)
            except:
                pass
            self.__socket = None

class PacketParser:

    @staticmethod
    def get_packets_from_buffer(buffer):
        packets = buffer.split(b'\0')
        last_index = len(packets) - 1
        buffer = packets[last_index]
        parsed_packets = []
        if len(packets) > 1:
            if len(buffer) == 0:
                del packets[last_index]
            parsed_packets = []
            for pck in packets:
                parsed_packets.append(pck)
            return parsed_packets