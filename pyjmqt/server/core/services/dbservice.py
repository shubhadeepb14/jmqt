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

import pyjmqt.server.logger as logger
from pyjmqt.server.core.services.peewee_base import DB_PROXY, PeeweeBase, Connections, Subscriptions, RetainedPackets, Packets, Pubmaps

from peewee import *

class SQLiteService(PeeweeBase):
    def __init__(self, settings):
        self.settings = settings
        self.connect_sqlite()
    
    def connect_sqlite(self):
        root_path = os.path.dirname(os.path.realpath(__file__))
        db_path = os.path.join(root_path, 'jmqt.db')
        logger.log_info('Connecting SQLite Db ' + db_path, 'SQLiteService')
        db = SqliteDatabase(db_path)
        DB_PROXY.initialize(db)
        db.connect()
        db.create_tables([Connections, Subscriptions, RetainedPackets, Packets, Pubmaps], safe = True)

class MySQLService(PeeweeBase):
    def __init__(self, settings):
        self.settings = settings
        self.connect_mysql()
    
    def connect_mysql(self):
        logger.log_info(('Connecting MySQL/MariaDb {0} on {1}:{2}').format(self.settings.MYSQL_DB, self.settings.MYSQL_HOST, self.settings.MYSQL_PORT), 'MySQLService')
        db = MySQLDatabase(self.settings.MYSQL_DB, user=self.settings.MYSQL_USER, password=self.settings.MYSQL_PSWD,
                         host=self.settings.MYSQL_HOST, port=self.settings.MYSQL_PORT)
        DB_PROXY.initialize(db)
        db.connect()
        db.create_tables([Connections, Subscriptions, RetainedPackets, Packets, Pubmaps])