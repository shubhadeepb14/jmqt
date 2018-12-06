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
import os
root_path = os.path.dirname(os.path.realpath(__file__))
# path where pyjmqt.server package is saved
modules_root_path = os.path.dirname(root_path)
import json
import threading
import asyncio
import sys
# if the modules_root_path is not in sys.path, we have to insert it to sys.path before importing pyjmqt.server
if modules_root_path not in sys.path:
    sys.path.insert(0, modules_root_path)
from pyjmqt.server.api import Server

# defines and implements the main application
class MyJMQTApp():
    def __init__(self, loop):
        self.loop = loop
        # setup the JMQT server
        self.configFile = os.path.join(root_path, 'server.conf')

         # create the object of JMQT Server
        self.server = Server(self.loop, self.configFile)

        # register the callbacks, all are mandatory
        # validation callbacks
        self.server.set_authentication_validator(self.validate_auth)
        self.server.set_connection_validator(self.validate_conn)
        self.server.set_subscription_validator(self.validate_sub)
        self.server.set_publish_validator(self.validate_pub)
        # handler callbacks
        self.server.set_control_channel_handler(self.control_packet_handler)
        # notifier callbacks
        self.server.set_unsubscription_validator(self.validate_unsub)
        self.server.set_disconnection_notifier(self.disconnection_notifier)
        self.server.set_conn_close_notifier(self.conn_close_notifier)

        # gets the server logger (may be used to log all information at a place)
        self.logger = self.server.get_logger()
        # 4 methods are available for logging, i.e:
        # log_info, log_debug, log_warning, and log_error
        self.logger.log_info('Server Start', 'MyJMQTApp')
        # gets the server config in a dictionary
        self.serverConfig = self.server.get_server_config()
        # to access a config item, we can use self.serverConfig['<item name>']
        # e.g. self.serverConfig['MONGO_HOST']
        # update channel will be used to inform other clients when a client is online or offline
        self.UpdateChannel = 'update'

    async def validate_auth(self, auth_data, remote_host, protocol):
        """
        Validates authentication request.

        Called when a client sends auth request. This function must authenticate the client and return
        authentication status with client id and optional message (reason why authenctication is not OK)

        :param auth_data: Authentication data sent by the client (any, usually dictionary)
        :param remote_host: <IP>:<Port> the client is connecting from (string)
        :param protocol: Protocol which the client is connecting from (string)
        :return: returns a tuple with status code (boolean), client id (string), auth token(string) and messagse (string)
                message can be blank, it must contain the reason if the authentication failes
        """
        status_code, client_id, token, message = self.server.StatusCodes.FAILED, '', '', ''
        # for the sample server, we will use the client_name field to authenticate a client
        # here we are authentiating all clients, this authentication will be application specific
        if 'client_name' in auth_data:
            uid = auth_data['client_name']
            client_id = str(uid)
            status_code = self.server.StatusCodes.OK
            token = "test-token"
        else:
            status_code = self.server.StatusCodes.INVALID_PACKET
            message = "Invalid auth data, client_name is missing"
        return (status_code, client_id, token, message)

    async def validate_conn(self, client_id, auth_token, remote_host, protocol):
        """
        Validates connection request.

        Called when a client sends conn request. This function must allow or deny the client to connect

        :param client_id: Client id of the client (string)
        :param auth_token: Auth token previously sent from validate_auth function (string)
        :param remote_host: <IP>:<Port> the client is connecting from (string)
        :param protocol: Protocol which the client is connecting from (string)
        :return: returns status code (boolean)
        """
        if auth_token == "test-token":
            # here we need to add the default channels for the client
            # for example, we are adding the p2p channel here
            await self.server.force_sub(client_id, '#' + client_id, persistent_flag = 1)
            # next we will add the update channel
            await self.server.force_sub(client_id, self.UpdateChannel, persistent_flag = 1)
            # now we will send the connection info to the update channel
            await self.server.force_pub(self.UpdateChannel, {'online': client_id}, qos = 0, retain = 0)
            return self.server.StatusCodes.OK
        else:
            return self.server.StatusCodes.INVALID_TOKEN
    
    async def validate_sub(self, client_id, channel, persistent_flag, remote_host, protocol):
        """
        Validates subscription request.

        Called when a client sends sub request. This function must allow or deny the subscription

        :param client_id: Client id of the client (string)
        :param channel: channel name which the client wants to subscribe to (string)
        :param persistent_flag: indicates the subscription if persistent or not (boolean)
        :param remote_host: <IP>:<Port> the client is connecting from (string)
        :param protocol: Protocol which the client is connecting from (string)
        :return: returns status code (boolean)
        """
        # here we will reject any subscription to update channel
        # this channel is reserved for the server
        if channel == self.UpdateChannel:
            return self.server.StatusCodes.NOT_ALLOWED
        return self.server.StatusCodes.OK
    
    async def validate_unsub(self, client_id, channel, remote_host, protocol):
        """
        Validates unsubscription request.

        Called when a client sends sub request. This function must allow or deny the unsubscription

        :param client_id: Client id of the client (string)
        :param channel: channel name which the client wants to subscribe to (string)
        :param remote_host: <IP>:<Port> the client is connecting from (string)
        :param protocol: Protocol which the client is connecting from (string)
        :return: returns status code (boolean)
        """
        # here we will reject any unsubscription from update channel
        # this channel is reserved for the server
        if channel == self.UpdateChannel:
            return self.server.StatusCodes.NOT_ALLOWED
        return self.server.StatusCodes.OK
    
    async def validate_pub(self, client_id, channel, data, qos, remote_host, protocol):
        """
        Validates publish request.

        Called when a client sends pub request. This function must allow or deny the publish

        :param client_id: Client id of the client (string)
        :param channel: channel name which the client wants to publish the data (string)
        :param data: published data by the client (any, usually dictionary)
        :param remote_host: <IP>:<Port> the client is connecting from (string)
        :param protocol: Protocol which the client is connecting from (string)
        :return: returns status code (boolean)
        """
        # here we will reject any publish to update channel
        # this channel is reserved for the server
        if channel == self.UpdateChannel:
            return self.server.StatusCodes.NOT_ALLOWED
        return self.server.StatusCodes.OK   

    async def control_packet_handler(self, client_id, channel, data, remote_host, protocol):
        """
        Handles publish requests to control channels.

        Called when a client sends a control data request(pub request to control channels starts with $ sign).
        This function must return the relevant data with status code

        :param client_id: Client id of the client (string)
        :param channel: control channel name (string)
        :param data: request data by the client (any, usually dictionary)
        :param remote_host: <IP>:<Port> the client is connecting from (string)
        :param protocol: Protocol which the client is connecting from (string)
        :return: returns tuple with status code (boolean) and response data (any)
        """
        # returns a list of subscribed channels by the client
        if channel == '$mySubscriptions':
            response_data = {'channels' : await self.server.get_subscriptions(client_id)}
        # e.g. response_data = {'msg': 'hi'}
        return (self.server.StatusCodes.OK, response_data)
    
    async def disconnection_notifier(self, client_id, remote_host, protocol):
        """
        Notifies when a client sends the disconn packet

        Called when a client sends the disconn packet

        :param client_id: Client id of the client (string)
        :param remote_host: <IP>:<Port> the client was connected from (string)
        :param protocol: Protocol which the client was connected from (string)
        :return: returns nothing
        """
        # now we will send the connection info to the update channel
        await self.server.force_pub(self.UpdateChannel, {'offline': client_id}, qos = 0, retain = 0)

    async def conn_close_notifier(self, client_id, remote_host, protocol):
        """
        Notifies when a client closes the socket

        Called when a client closes the socket

        :param client_id: Client id of the client (string)
        :param remote_host: <IP>:<Port> the client was connected from (string)
        :param protocol: Protocol which the client was connected from (string)
        :return: returns nothing
        """
        # we can notify the other clients about this event using force_pub message
        await self.server.force_pub(self.UpdateChannel, {'offline': client_id}, qos = 0, retain = 0)

    def start(self):
        """
        call the start server function
        """
        self.logger.log_info('Server start', 'MyJMQTApp')
        self.server.start()
    
    def stop(self):
        """
        call the stop server function
        """
        self.logger.log_info('Server stop', 'MyJMQTApp')
        self.server.stop()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    myApp = MyJMQTApp(loop)
    myApp.start()
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    myApp.stop()