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

import math
import multiprocessing
import os
import platform
import socket
import sys
import signal
import threading
import traceback
import time

from pumpkinlb import __version__ as pumpkin_version

from pumpkinlb.config import PumpkinConfig, PumpkinMapping, PumpkinConfigException
from pumpkinlb.usage import printUsage, printConfigHelp, getVersionStr
from pumpkinlb.listener import PumpkinListener
from pumpkinlb.constants import GRACEFUL_SHUTDOWN_TIME

from pumpkinlb.log import logmsg, logerr


root_path = os.path.dirname(os.path.realpath(__file__))

if __name__ == '__main__':

    configFilename = os.path.join(root_path, 'config.conf')
    for arg in sys.argv[1:]:
        if arg == '--help':
            printUsage(sys.stdout)
            sys.exit(0)
        elif arg == '--help-config':
            printConfigHelp(sys.stdout)
            sys.exit(0)
        elif arg == '--version':
            sys.stdout.write(getVersionStr() + '\n')
            sys.exit(0)
        elif configFilename is not None:
            sys.stderr.write('Too many arguments.\n\n')
            printUsage(sys.stderr)
            sys.exit(0)
        else:
            configFilename = arg

    if not configFilename:
        sys.stderr.write('No config file provided\n\n')
        printUsage(sys.stderr)
        sys.exit(1)

    pumpkinConfig = PumpkinConfig(configFilename)
    try:
        pumpkinConfig.parse()
    except PumpkinConfigException as configError:
        sys.stderr.write(str(configError) + '\n\n\n')
        printConfigHelp()
        sys.exit(1)
    except Exception as e:
        traceback.print_exc(file=sys.stderr)
        printConfigHelp(sys.stderr)
        sys.exit(1)

    bufferSize = pumpkinConfig.getOptionValue('buffer_size')
    logmsg('Configured buffer size = %d bytes\n' %(bufferSize,))

    mappings = pumpkinConfig.getMappings()
    listeners = []
    for mappingAddr, mapping in mappings.items():
        logmsg('Starting up listener on %s:%d with mappings: %s\n' %(mapping.localAddr, mapping.localPort, str(mapping.workers)))
        listener = PumpkinListener(mapping.localAddr, mapping.localPort, mapping.workers, bufferSize)
        listener.start()
        listeners.append(listener)


    globalIsTerminating = False

    def handleSigTerm(*args):
        global listeners
        global globalIsTerminating
#        sys.stderr.write('CALLED\n')
        if globalIsTerminating is True:
            return # Already terminating
        globalIsTerminating = True
        logerr('Caught signal, shutting down listeners...\n')
        for listener in listeners:
            try:
                os.kill(listener.pid, signal.SIGTERM)
            except:
                pass
        logerr('Sent signal to children, waiting up to 4 seconds then trying to clean up\n')
        time.sleep(1)
        startTime = time.time()
        remainingListeners = listeners
        remainingListeners2 = []
        for listener in remainingListeners:
            logerr('Waiting on %d...\n' %(listener.pid,))
            listener.join(.05)
            if listener.is_alive() is True:
                remainingListeners2.append(listener)
        remainingListeners = remainingListeners2
        logerr('Remaining (%d) listeners are: %s\n' %(len(remainingListeners), [listener.pid for listener in remainingListeners]))

        afterJoinTime = time.time()

        if remainingListeners:
            delta = afterJoinTime - startTime
            remainingSleep = int(GRACEFUL_SHUTDOWN_TIME - math.floor(afterJoinTime - startTime))
            if remainingSleep > 0:
                anyAlive = False
                # If we still have time left, see if we are just done or if there are children to clean up using remaining time allotment
                if threading.activeCount() > 1 or len(multiprocessing.active_children()) > 0:
                    logerr('Listener closed in %1.2f seconds. Waiting up to %d seconds before terminating.\n' %(delta, remainingSleep))
                    thisThread = threading.current_thread()
                    for i in range(remainingSleep):
                        allThreads = threading.enumerate()
                        anyAlive = False
                        for thread in allThreads:
                            if thread is thisThread or thread.name == 'MainThread':
                                continue
                            thread.join(.05)
                            if thread.is_alive() == True:
                                anyAlive = True

                        allChildren = multiprocessing.active_children()
                        for child in allChildren:
                            child.join(.05)
                            if child.is_alive() == True:
                                anyAlive = True
                        if anyAlive is False:
                            break
                        time.sleep(1)

                if anyAlive is True:
                    logerr('Could not kill in time.\n')
                else:
                    logerr('Shutdown successful after %1.2f seconds.\n' %( time.time() - startTime))

            else:
                logerr('Listener timed out in closing, exiting uncleanly.\n')
                time.sleep(.05) # Why not? :P

        logmsg('exiting...\n')
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        sys.exit(0)
        os.kill(os.getpid(), signal.SIGTERM)
        return 0
    # END handleSigTerm


    signal.signal(signal.SIGTERM, handleSigTerm)
    signal.signal(signal.SIGINT, handleSigTerm)

    while True:
        try:
            time.sleep(2)
        except:
            os.kill(os.getpid(), signal.SIGTERM)

# vim: set ts=4 sw=4 expandtab