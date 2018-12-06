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
# path where pyjmqt.client package is saved
modules_root_path = os.path.dirname(root_path)
import time
import datetime
import sys
# if the modules_root_path is not in sys.path, we have to insert it to sys.path before importing pyjmqt.client
if modules_root_path not in sys.path:
    sys.path.insert(0, modules_root_path)
from pyjmqt.client.api import Client

class Main:
    __do_run = False
    __loop_count = 0

    # path to the client config file
    __configFile = os.path.join(root_path, 'client.conf')
    __authenticated = False
    __connected = False
    
    # jmqt channel name for the sample client
    __test_channel = 'ch'
    
    def initiate_program(self, client_name):
        self.__client_name = client_name
        self.__do_run = True
        # create the pyjmqt client 
        self.__client = Client(self.__configFile)
        self.logger = self.__client.get_logger()
        self.logger.log_info ("[MAIN] Start initiated..")
        # register the callbacks for push messages and disconnection
        self.__client.registerPushcallback(self.push_callback)
        self.__client.registerDisconnectcallback(self.disconnect_callback)
        self.__loop_count = 9
    
    # the main loop
    def run(self):
        while self.__do_run:
            if self.__connected:
                # publish dummy data in every 10 seconds
                if self.__loop_count % 10 == 0:
                    self.logger.log_info ("[MAIN] Pub dummy data on '" + self.__test_channel + "'")
                    self.__loop_count = 0
                    try:
                        # we will publish the data with retain ON and QOS 1
                        retain = 1
                        qos = 1
                        # self.pub_callback is the function which receives the pub ack
                        pck_id = self.__client.pub(self.__test_channel, str(datetime.datetime.now()), retain, qos, self.pub_callback)
                    except Exception as ex:
                        self.logger.log_error ("[MAIN] Pub Error " + str(ex))
            elif self.__loop_count % 10 == 0:
                # if server not connected, retry in every 10 seconds
                self.__loop_count = 0
                # if client is not authenticated, we will do the authentication first
                # and then proceed to create a new session
                if self.__authenticated:
                    self.logger.log_info ("[MAIN] Retry connect..")
                    self.connect()
                else:
                    self.logger.log_info ("[MAIN] Retry auth..")
                    self.auth()
            if not self.wait(1):
                break
            self.__loop_count += 1

    # authenticates the client (auth packet)
    def auth(self):
        self.logger.log_info ("[MAIN] Requesting auth with client name '" + str(self.__client_name) + "'")
        authData = {'client_name': self.__client_name}
        # self.auth_callback is the function where the auth ack will be received
        self.__client.auth(authData, self.auth_callback)
    
    # receives the auth ack
    def auth_callback(self, status, auth_token, client_id, msg):
        self.__auth_token = auth_token
        self.__client_id = client_id
        if status == self.__client.statusCodes.OK:
            self.logger.log_info ("[MAIN] Auth status OK")
            self.__authenticated = True
            # if status is OK, we will proceed to connect (creating a session)
            self.connect()
        else:
            self.logger.log_error ("[MAIN] Auth status " + str(status) + ", message '" + msg + "'")
            # if status is not OK, we will notify the disconnect callback function
            self.disconnect_callback()

    # creates a new session
    def connect(self):
        self.logger.log_info ("[MAIN] Requesting conn with client id '" + str(self.__client_id) + "'")
        # self.connect_callback is the function where the conn ack will be received
        self.__client.conn(self.__client_id, self.__auth_token, self.connect_callback)

    # receives the conn ack
    def connect_callback(self, status):
        self.logger.log_info ("[MAIN] Conn status " + str(status))
        if status == self.__client.statusCodes.OK:
            self.__connected = True
            self.logger.log_info ("[MAIN] Requesting sub to channel '" + self.__test_channel + "'")
            # if status is OK, we will proceed to subscribe the test channel with persistent flag ON
            persistent = 1
            # self.sub_callback is the function where the sub ack will be received
            self.__client.sub(self.__test_channel, persistent, self.sub_callback)
        else:
            # if status is not OK, we will notify the disconnect callback function
            self.disconnect_callback()
    
    # receives the sub ack
    def sub_callback(self, status, channel_name):
        self.logger.log_info ("[MAIN] Sub to channel '" + self.__test_channel + "'" + " status " + str(status))

    # receives the push packets
    def push_callback(self, channel_name, client_id, data, qos, retain_flag):
        self.logger.log_info(("[Main] Data on '{0}' from {1} : {2} (QOS {3}, RETAIN {4})").format( channel_name, client_id, data , qos, retain_flag))

    # receives the pub callback
    def pub_callback(self, status, packet_id, data):
        if data is None and status != self.__client.statusCodes.OK:
            self.logger.log_info ("[MAIN] Pub for packet # " + packet_id + " status " + str(status))
        elif data is not None:
            self.logger.log_error ("[MAIN] Pub for packet # " + packet_id + " status " + str(status) + ", resp data " + str(data))
            
    # called when the JMQT server sends an error or gets disconnected
    def disconnect_callback(self):
        self.logger.log_info ("[MAIN] Disconnected from server! Will retry after 10 seconds")
        self.__connected = False
        self.__loop_count = 0
        
    # waits for an interrupt (e.g. ctrl + C)
    # and terminates the program on interrupt
    def wait(self, seconds):
        if self.__do_run:
            try:
                time.sleep(seconds)
                return True
            except:
                self.__do_run = False
                self.terminate_program()
                return False
        else:
            return False

    # terminates the program        
    def terminate_program(self):
        try:
            self.logger.log_info ("[MAIN] Interrupt received..")
            # stop all the modules created in initiate_program
            self.__client.stop()
            self.logger.log_info ("[MAIN] Stopped!")
        except Exception as e:
            self.logger.log_error ("[MAIN] Termination error! " + str(e))    

if __name__ == "__main__":
    # initiate the main program
    _Main = Main()
    # pass an arbitrary client name
    _Main.initiate_program('pyclient1')
    # run the program
    _Main.run()
    # if interrupt, terminate the main program
    _Main.terminate_program()
