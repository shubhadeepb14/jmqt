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

from mongoengine import *

class Connections(Document):
    client_id = StringField(required=True)
    protocol = StringField(required = True)
    address = StringField(required = True)
    timestamp = DateTimeField(required = True)
    meta = {
        'indexes': [
            'client_id',
        ]
    }

class Subscriptions(Document):
    client_id = StringField(required=True)
    channel = StringField(required=True)
    is_tmp = BooleanField(default=False)
    meta = {
        'indexes': [
            'client_id',
            ('client_id', 'channel'),
            ('client_id', 'channel', 'is_tmp'),
        ]
    }

class RetainedPackets(Document):
    sender_id = StringField(required=True)
    channel = StringField(required = True)
    data = DictField(required = True)
    timestamp = DateTimeField(required = True)
    meta = {
        'indexes': [
            'sender_id',
            ('sender_id', 'channel'),
            'channel',
            'timestamp'
        ]
    }

class Packets(Document):
    packet_id = StringField(required=True)
    sender_id = StringField(required=True)
    channel = StringField(required = True)
    data = DictField(required = True)
    timestamp = DateTimeField(required = True)
    meta = {
        'indexes': [
            'packet_id',
            'sender_id',
            ('sender_id', 'channel'),
            'channel',
            'timestamp'
        ]
    }

class Pubmaps(Document):
    packet_id = StringField(required=True)
    client_id = StringField(required = True)
    channel = StringField(required = True)
    meta = {
        'indexes': [
            'packet_id',
            ('packet_id', 'client_id'),
            ('packet_id', 'client_id', 'channel')
        ]
    }