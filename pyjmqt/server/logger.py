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

import datetime
import logging

global log_path
log_path = ''

log_levels = {
    'DBG' : 10, 'INF': 20, 'WRN': 30, 'ERR': 40, 'DISABLED': 0
}

global log_mode
log_mode = ''

global logger
logger = None

def set_logger(path, mode = 'DBG'):
    if path is not None:
        path = str(path).strip()
        if len(path) < 3:
            path = None
    if path is None:
        raise Exception("path too short or None!")
    global log_path
    log_path = path
    
    global log_mode
    if mode in log_levels:
        log_mode = log_levels[mode]
    else:
        raise Exception('Config Error: Unknown LOG_MODE')

    global logger
    maxbytes = 1024 * 200
    logger = logging.getLogger('jmqt-server')
    logger.addHandler(logging.FileHandler(log_path))
    logger.setLevel(log_levels[mode])
    logger.propagate = False

def log_error(e, func_name = None):
    msg = log(func_name, str(e), 'ERR')
    logger.error(msg)

def log_debug(msg, func_name = None):
    msg = log(func_name, str(msg), 'DBG')
    logger.debug(msg)

def log_info(msg, func_name = None):
    msg = log(func_name, str(msg), 'INF')
    logger.info(msg)

def log_warning(msg, func_name = None):
    msg = log(func_name, str(msg), 'WRN')
    logger.warn(msg)

def log(func_name, msg, tag):
    if log_path == '':
        raise Exception('Logger not set')
    if func_name == None or len(str(func_name).strip()) == 0:
            func_name = 'JMQTServer'
    else:
        func_name = 'JMQTServer:' + func_name
    msg = (('[{0}] {2} : {1}').format(func_name, msg, tag))
    msg = datetime.datetime.now().strftime("%m-%d %H:%M:%S") + ' ' + msg
    do_print = False
    if log_mode != 0 and log_levels[tag] >= log_mode:
        do_print = True

    if do_print:
        print(msg)
    return msg