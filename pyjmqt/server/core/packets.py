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

import json
import pyjmqt.server.logger as logger
from pyjmqt.server.core.constants import *


# request packet class, return from PacketParser.parse_packet
class Packet:
    packetType = ''
    packetData = None
    protocol = ''

# parses an incoming request packet
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
                packet, msg = PacketParser.parse_packet(pck.decode('utf8'), Protocol.SOCKET)
                if msg == '':
                    parsed_packets.append((packet, msg))
                else:
                    logger.log_error(msg, 'read')
            return parsed_packets

    @staticmethod
    def get_arg(key, json_data, default=None):
        if key in json_data:
            return json_data[key]
        else:
            return default

    @staticmethod
    def parse_packet(str_data, protocol):
        packet = None
        msg = ''
        try:
            # load the json data
            json_data = json.loads(str_data)
            packet = Packet()
            packet.protocol = protocol
            keys = json_data.keys()
            if len(keys) == 1:
                pck_type = list(keys)[0]
                _PacketTypes = PacketTypes.get_types_list()
                if pck_type in _PacketTypes:
                    packet.packetType = pck_type
                    # set the packet data
                    packet.packetData = PacketParser.get_arg(pck_type, json_data)
                else:
                    raise Exception('malformed packet : invalid packet type')
            else:
                raise Exception('malformed packet : root element must be one')
        except Exception as ex:
            logger.log_error(ex, 'parse_packet')
            msg = str(ex)
        return (packet, msg)
        
# generates packets
class PacketGenerator:
    @staticmethod
    def __validate_string(_str, name, check_blank = True):
        if _str is not None:
            _str = str(_str).strip()
            if check_blank:
                if len(_str) > 0:
                    return _str
            else:
                return _str
        if check_blank:
            raise Exception("'" + str(name) + "' can not be None or empty")
        else:
            raise Exception("'" + str(name) + "' can not be None")


    @staticmethod
    def __validate_int(_val, name):
        if type(_val) == int:
            return _val
        raise Exception("'" + str(name) + "' has invalid value")

    @staticmethod
    def __validate_status(_status):
        if type(_status) == int:
            return _status
        raise Exception("'status' has invalid value")
    
    @staticmethod
    def __validate_qos(_qos):
        if type(_qos) == int:
            return _qos
        raise Exception("'qos' has invalid value")

    @staticmethod
    def __validate_flag(_val, name):
        if type(_val) == int or type(_val) == bool:
            return 1 if _val else 0
        raise Exception("'" + str(name) + "' has invalid value")


    # auth response
    @staticmethod
    def generate_auth_res(status_code, client_id, auth_token, message):
        resp_data = {}
        resp_data[JSONKeys.statusCode] = PacketGenerator.__validate_status(status_code)
        if status_code == StatusCode.OK:
            resp_data[JSONKeys.authToken] = PacketGenerator.__validate_string(auth_token, 'auth token')
            resp_data[JSONKeys.clientId] = PacketGenerator.__validate_string(client_id, 'client id')
        else:
            resp_data[JSONKeys.message] = PacketGenerator.__validate_string(message, 'message')
        pck = {}
        pck[PacketTypes.authAck] = resp_data
        return pck

    # connection response
    @staticmethod
    def generate_conn_res(status_code, timeout_seconds):
        resp_data = {}
        resp_data[JSONKeys.statusCode] = PacketGenerator.__validate_status(status_code)
        resp_data[JSONKeys.timeoutSeconds] = PacketGenerator.__validate_int(timeout_seconds, 'timeout seconds')
        pck = {}
        pck[PacketTypes.connAck] = resp_data
        return pck

    # pub response
    @staticmethod
    def generate_pub_res(status_code, pck_id, data = None):
        resp_data = {}
        resp_data[JSONKeys.statusCode] = PacketGenerator.__validate_status(status_code)
        resp_data[JSONKeys.packetId] = PacketGenerator.__validate_string(pck_id, 'packet id')
        if data != None:
            resp_data[JSONKeys.data] = data
        pck = {}
        pck[PacketTypes.pubAck] = resp_data
        return pck
    
    # push request
    @staticmethod
    def generate_push_req(channel_name, data, pck_id, client_id, retain_flag, qos):
        pck = {}
        pck[PacketTypes.push] = {
            JSONKeys.channelName: PacketGenerator.__validate_string(channel_name, 'channel name'),
            JSONKeys.data: data, 
            JSONKeys.clientId: PacketGenerator.__validate_string(client_id, 'client id', check_blank = False),
        }
        if retain_flag:
            pck[PacketTypes.push][JSONKeys.retainFlag] = PacketGenerator.__validate_flag(retain_flag, 'retain flag')
        if qos == QOS.ONE:
            pck[PacketTypes.push][JSONKeys.packetId] = PacketGenerator.__validate_string(pck_id, 'packet id')
            pck[PacketTypes.push][JSONKeys.qos] = PacketGenerator.__validate_qos(qos)
        return pck

    # sub response
    @staticmethod
    def generate_sub_res(status_code, channel_name):
        resp_data = {}
        resp_data[JSONKeys.statusCode] = PacketGenerator.__validate_status(status_code)
        resp_data[JSONKeys.channelName] = PacketGenerator.__validate_string(channel_name, 'channel name')
        pck = {}
        pck[PacketTypes.subAck] = resp_data
        return pck

    # unsub response
    @staticmethod
    def generate_unsub_res(status_code, channel_name):
        resp_data = {}
        resp_data[JSONKeys.statusCode] = PacketGenerator.__validate_status(status_code)
        resp_data[JSONKeys.channelName] = PacketGenerator.__validate_string(channel_name, 'channel name')
        pck = {}
        pck[PacketTypes.unsubAck] = resp_data
        return pck

    # heartbeat response
    @staticmethod
    def generate_heartbeat_res():
        pck = {}
        pck[PacketTypes.hbAck] = {
        }
        return pck