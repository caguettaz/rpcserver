#!/usr/bin/env python3

import argparse
import os
import rpcserver.service
from time import sleep
from rpcserver.utils import err
from rpcserver import settings

def get_service_state(pid=None):
    if pid is None:
        pid = rpcserver.service.get_service_pid()
    if pid is not None:
        try:
            # Hack: this allows us to check whether the process exists without requiring
            # the permissions that kill -0 requires
            os.getpgid(pid)
            return True, pid
        except ProcessLookupError:
            pass
        
    return False, None

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=settings.SERVICE_NAME + " service")
    parser.add_argument('-d', '--debug', action='store_true',
                        help='start in debug mode')
    parser.add_argument('--pid', type=int, help='PID for stop or restart if needed')
    parser.add_argument('action', type=str,
                        choices=('start', 'stop', 'restart', 'info'))
    args = parser.parse_args()
    
    action = args.action

    if action == 'start':
        if not args.debug:
            #In non-debug mode, the service process detaches itself by forking, then
            #exiting the parent process. This means we have to fork ourselves if we
            #want to do some monitoring after the service has started.
            if not os.fork():
                rpcserver.service.start()
            else:
                sleep(0.5)
                running, pid = get_service_state()
                if running:
                    print('Service running, pid', pid)
                else:
                    err('Service not running')
        else:
            rpcserver.service.start(True)
    elif action == 'stop':
        #running might be false for debug runs
        running, _ = get_service_state(args.pid)
        res = rpcserver.service.stop(args.pid)
        if res and running:
            sleep(0.5)
            new_running, new_pid = get_service_state(args.pid)
            if new_running:
                err('Service did not stop, running as pid', new_pid)
            else:
                print('Service stopped')
    elif action == 'info':
        running, pid = get_service_state(args.pid)
        if running:
            print('Service running, pid', pid)
        else:
            print('Service not running, or running in debug mode')
    else:
        assert False, "Unknown action '{}'".format(action)