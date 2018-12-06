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

from pyjmqt.server.core.socket_server import SocketServer, SSLSocketServer
from pyjmqt.server.core.websocket_server import WebSocketServer, SSLWebSocketServer
from pyjmqt.server.core.connection_handler import ConnectionHandler
from pyjmqt.server.core.constants import StatusCode, Protocol
from pyjmqt.server.core.settings import ServerSettings
import pyjmqt.server.logger as logger

import asyncio
import os

root_path = os.path.dirname(os.path.realpath(__file__))

class Server():
    '''
    Server class provides an API to start, stop the underlying servers 
    '''
    StatusCodes = StatusCode()
    Protocols = Protocol()
    __configFile = ''
    
    JMQT_VERSION = '1.0'
    
    class CallbackWrapper():
        '''
        CallbackWrapper class contains all the callback methods required to run the server
        '''
        # validation callbacks
        validate_auth_callback = None
        validate_sub_callback = None
        validate_pub_callback = None
        validate_conn_callback = None
        
        # control channel handler
        control_data_callback = None
        
        # notification callbacks
        validate_unsub_callback = None
        disconnection_callback = None
        conn_close_callback = None

        def validate_callbacks(self):
            msg = ''
            if not asyncio.iscoroutinefunction(self.validate_auth_callback):
                msg = "<authentication validator> is not set or not an 'async' function. Call 'set_authentication_validator' and pass an async function."
            elif not asyncio.iscoroutinefunction(self.validate_conn_callback):
                msg = "<connection validator> is not set or not an 'async' function. Call 'set_connection_validator' and pass an async function."
            elif not asyncio.iscoroutinefunction(self.disconnection_callback):
                msg = "<disconnection notifier> is not set or not an 'async' function. Call 'set_disconnection_notifier' and pass an async function."
            elif not asyncio.iscoroutinefunction(self.conn_close_callback):
                msg = "<connection close notifier> is not set or not an 'async' function. Call 'set_conn_close_notifier' and pass an async function."
            elif not asyncio.iscoroutinefunction(self.validate_sub_callback):
                msg = "<subscription validator> is not set or not an 'async' function. Call 'set_subscription_validator' and pass an async function."
            elif not asyncio.iscoroutinefunction(self.validate_unsub_callback):
                msg = "<unsubscription validator> is not set or not an 'async' function. Call 'set_unsubscription_validator' and pass an async function."
            elif not asyncio.iscoroutinefunction(self.validate_pub_callback):
                msg = "<publish validator> is not set or not an 'async' function. Call 'set_publish_validator' and pass an async function."
            elif not asyncio.iscoroutinefunction(self.control_data_callback):
                msg = "<control channel handler> is not set or not an 'async' function. Call 'set_control_channel_handler' and pass an async function."
            
            return msg

    def __init__(self, eventLoop, configFile):
        """
        constructor for the server
        :param eventLoop: ayncio event loop
        :param configFile: path to the config file
        """
        self.__configFile = configFile
        self.__parse_settings()        
        # create an object of the CallbackWrapper class
        self.__callbackWrapper = Server.CallbackWrapper()
        
        # create an object of the ConnectionHandler class
        self.__connectionHandler = ConnectionHandler(self.__settings, eventLoop)
        
        
        self.__servers = []

        # creating the socket server (without SSL)
        self.__socketServer = SocketServer(eventLoop, self.__callbackWrapper, self.__connectionHandler, self.__settings)
        self.__servers.append(self.__socketServer)

        # creating the websocket server (without SSL)
        self.__webSocketServer = WebSocketServer(eventLoop, self.__callbackWrapper, self.__connectionHandler, self.__settings)
        self.__servers.append(self.__webSocketServer)

        # check if SSL is enabled
        if self.__settings.ENABLE_SSL:
            # creating the socket server (with SSL)
            self.__sslSocketServer = SSLSocketServer(eventLoop, self.__callbackWrapper, self.__connectionHandler, self.__settings)
            self.__servers.append(self.__sslSocketServer)

            # creating the web socket server (with SSL)
            self.__sslWebsocketServer = SSLWebSocketServer(eventLoop, self.__callbackWrapper, self.__connectionHandler, self.__settings)
            self.__servers.append(self.__sslWebsocketServer)


    def __parse_settings(self):
        # self.__settings = ServerSettings()
        settings = {}
        default = False
        if self.__configFile is None or len(self.__configFile) == 0:
            self.__configFile = os.path.join(root_path, 'core', 'default.conf')
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
                        settings[key] = value
        
        self.__settings = ServerSettings(settings)
        # create the JMQT logger (get_logger function returns this logger)
        logger.set_logger(self.__settings.LOG_PATH, mode = self.__settings.LOG_MODE)
        if default:
            logger.log_info('No config file passed, falling back to default config "' + self.__configFile + '"')
        else:
            logger.log_info('Loading config "' + self.__configFile + '"')
    
    def get_server_config(self):
        return dict(self.__settings)
    '''
    SECTION #1 : API to retreive information from lower jmqt layers
    '''
    
    async def get_subscriptions(self, client_id):
        """
        returns a list of subscribed channels by a client

        :param client_id: client id (string)
        :return: returns a list of channels (list of dict, e.g. [{"ch1": "persistent"}, {"ch2": "temp"}])
        """
        return await self.__connectionHandler.get_subscribed_channels(client_id)

    async def force_sub(self, client_id, channel, persistent_flag):
        """
        forcefully subscribes a channel to a client

        :param client_id: client id (string)
        :param channel: channel name (string)
        :param persistent_flag: indicates if the subscription is persistent (boolean)
        :return: returns nothing
        """
        await self.__connectionHandler.force_sub(client_id, channel, persistent_flag)
    
    async def force_unsub(self, client_id, channel):
        """
        forcefully unsubscribes a channel from a client

        :param client_id: client id (string)
        :param channel: channel name (string)
        :return: returns nothing
        """
        return await self.__connectionHandler.force_unsub(client_id, channel)

    async def force_pub(self, channel, data, qos, retain):
        """
        forcefully publish a data to a channel

        :param channel: channel name (string)
        :param channel: data to publish (string)
        :param channel: qos of the packet (0 / 1)
        :param channel: retain flag (boolean)
        :return: returns nothing
        """
        return await self.__connectionHandler.force_pub(channel, data, qos, retain)


    '''
    END SECTION #1
    '''

    '''
    SECTION #2 : functions to register callbacks
    '''
    def set_authentication_validator(self, _callback):
        """
        sets the authentication validator callback
        """
        self.__callbackWrapper.validate_auth_callback = _callback

    def set_subscription_validator(self, _callback):
        """
        sets the subscription validator callback
        """
        self.__callbackWrapper.validate_sub_callback = _callback
    
    def set_unsubscription_validator(self, _callback):
        """
        sets the unsubscription callback
        """
        self.__callbackWrapper.validate_unsub_callback = _callback

    def set_publish_validator(self, _callback):
        """
        sets the publish validator callback
        """
        self.__callbackWrapper.validate_pub_callback = _callback
    
    def set_control_channel_handler(self, _callback):
        """
        sets the control channel handler callback
        """
        self.__callbackWrapper.control_data_callback = _callback
    
    def set_connection_validator(self, _callback):
        """
        sets the connection validator callback
        """
        self.__callbackWrapper.validate_conn_callback = _callback
    
    def set_disconnection_notifier(self, _callback):
        """
        sets the disconnection callback
        """        
        self.__callbackWrapper.disconnection_callback = _callback
    
    def set_conn_close_notifier(self, _callback):
        """
        sets the connection close callback
        """        
        self.__callbackWrapper.conn_close_callback = _callback
    
    '''
    END SECTION #2
    '''

    '''
    SECTION #3 : manage the server
    '''
    
    def get_logger(self):
        """
        Returns the server's logger module

        :return: returns logger object
        """
        return logger

    def start(self):
        """
        starts the server
        """
        
        # validates that all required callbacks are set
        msg = self.__callbackWrapper.validate_callbacks()
        if msg != '':
            raise Exception(msg)
        self.__connectionHandler.start()
        for _server in self.__servers:
            _server.start()
    
    def stop(self):
        """
        stops the server
        """
        self.__connectionHandler.stop()
    
    '''
    END SECTION #3
    '''
