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

class StatusCode:
    UNKNOWN = -1
    OK = 1
    FAILED = 0
    SERVER_ERROR = 5
    INVALID_TOKEN = 6
    NOT_ALLOWED = 7
    CLIENT_OFFLINE = 8
    NETWORK_ERROR = 9
    INVALID_PACKET = 10
    INVALID_CHANNEL = 11


class Protocol:
    SOCKET = 'SOCKET'
    SSL_SOCKET = 'SSL_SOCKET'
    WEB_SOCKET = 'WEB_SOCKET'
    SSL_WEB_SOCKET = 'SSL_WEB_SOCKET'


class PacketTypes:
    __types = ['auth', 'authAck', 'conn', 'connAck', 'pub', 'pubAck', 'push', 'pushAck', 'sub', 'subAck', 'unsub', 'unsubAck','hb', 'hbAck', 'disconn']
    auth = __types[0]
    authAck = __types[1]
    conn = __types[2]
    connAck = __types[3]
    pub = __types[4]
    pubAck = __types[5]
    push = __types[6]
    pushAck = __types[7]
    sub = __types[8]
    subAck = __types[9]
    unsub = __types[10]
    unsubAck = __types[11]
    hb = __types[12]
    hbAck = __types[13]
    disconn = __types[14]
    
    @staticmethod
    def get_types_list():
        return PacketTypes.__types



class JSONKeys:
    # common
    data = 'dt'
    statusCode = 'st'
    timeoutSeconds = 'ts'
    authToken = 'at'
    channelName = 'cn'
    persistent = 'pr'
    message = 'mg'
    packetId = 'id'
    clientId = 'cl'
    retainFlag = 'rt'
    qos = 'q'

class QOS:
    ZERO = 0
    ONE = 1
