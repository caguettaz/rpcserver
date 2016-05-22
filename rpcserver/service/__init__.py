'''
Skeleton RPC server daemon.

The implementation uses the daemon package, documented here:
https://www.python.org/dev/peps/pep-3143/#python-daemon

Use service.py to manage the service, client.py to communicate with the service
via RPC.
'''

import daemon
import lockfile
from lockfile import LockFailed, LockTimeout
import xmlrpc
from xmlrpc.server import SimpleXMLRPCRequestHandler, SimpleXMLRPCServer
from xmlrpc.client import Fault
import signal
import os
import sys
import pwd
import daemon.daemon
import subprocess
import copy
from threading import Thread
from time import sleep
from rpcserver import utils, settings
from rpcserver.utils import *
from rpcserver.settings import *
from rpcserver.local.rpc import PublicFault, RPC
from rpcserver.local.rpcfuncs import rpc_funcs
import re

def get_proxy():
    return xmlrpc.client.ServerProxy('http://localhost:' + str(LOCAL_SERVER_PORT))

class RequestHandler(SimpleXMLRPCRequestHandler):
    pass

server = None
server_is_running = False

class Cleanup:
    def __init__(self):
        self.lock = None
        self.cleandir = None
        
    def __enter__(self):
        return self
    
    def __exit__(self, type, value, tb):
        if self.lock is not None:
            self.lock.release()
        if self.cleandir is not None:
            subprocess.call("rm", os.path.join(self.cleandir, "*"))
            

def start(debug=False):
    with Cleanup() as cleanup:
        _start(debug, cleanup)
            
def _start(debug, cleanup):
    global server, logfile
    
    if debug:
        utils.set_debug()
    
    context = daemon.DaemonContext(files_preserve=[])
    
    if debug:
        context.prevent_core = True
        context.detach_process = False
        context.stdin = sys.stdin
        context.stdout = sys.stdout
        context.stderr = sys.stderr

    try:
        # We don't close sockets to preserve the pdb socket.
        for i in os.listdir("/proc/self/fd"):
            if re.match("socket:\[\d+\]", os.readlink("/proc/self/fd/" + i)):
                context.files_preserve.append(os.fdopen(int(i), 'r'))
    except OSError:
        pass
    
    if not debug:
        try:
            pwnam = pwd.getpwnam(settings.USER_NAME)
            context.uid = pwnam.pw_uid
            context.gid = pwnam.pw_gid
        except KeyError:
            err("user " + settings.USER_NAME + " doesn't exist")
            exit(1)
        
        lockdir = os.path.dirname(LOCKFILE_PATH)
        if not os.path.exists(lockdir):
            os.mkdir(lockdir, mode=0o755)
        
        try:
            os.chown(lockdir, context.uid, context.gid)
        except PermissionError:
            err('cannot change owner of {}, operation not permitted'.format(lockdir))
            exit(1)
            
        lock = lockfile.FileLock(LOCKFILE_PATH)
        try:
            # We handle the lock ourselves, since daemon does it too late
            # (i.e. after changing the process' owner)
            lock.acquire(timeout=0.1)
            cleanup.lock = lock
            cleanup.cleandir = lockdir
        except LockFailed:
            err('could not lock {}, are you root?'.format(LOCKFILE_PATH))
            exit(1)
        except LockTimeout:
            err('could not lock {}, already locked'.format(LOCKFILE_PATH))
            exit(1)
    
    try:
        logfile = open(LOGFILE_PATH, 'a')
        context.files_preserve.append(logfile)
    except PermissionError:
        print('Cannot open {}, no log will be written'.format(LOGFILE_PATH),
              file=sys.stderr)
    
    # Do whatever you need to do before the process transitions to its user
    # and possibly loses e.g. read write to key files here.
    
    context.signal_map = {signal.SIGTERM : handler}
    
    if debug:
        print('Running in Debug mode, ', end='')
    else:
        print('Starting daemon listening on localhost:{}'.format(LOCAL_SERVER_PORT))
    
    with context:
        if debug:
            print('pid {} listening on localhost:{}'.format(os.getpid(), LOCAL_SERVER_PORT))
        else:
            with open(LOCKFILE_PATH, 'w') as pidfile:
                print(os.getpid(), file=pidfile)
        
        try:
            with LogError():
                server = SimpleXMLRPCServer(("localhost", LOCAL_SERVER_PORT),
                                            requestHandler=RequestHandler,
                                            allow_none=True)
        except:
            log_err('Could not create server, exiting')
            exit(1)
        
        server.register_introspection_functions()
        for f in rpc_funcs:
            # func tuple: (function, name, debug)
            if debug or not f[2]:
                server.register_function(f[0], f[1])
                
        try:
            with LogError(catch=True):
                _start_loop()
        except:
            pass
        
        if not debug:
            os.remove(LOCKFILE_PATH)
            
        log('Exiting')

def _start_loop():
    log('Starting xmlrpc server on localhost:{}'.format(LOCAL_SERVER_PORT))
    server.serve_forever()


def handler(signum, frame):
    if (signum == signal.SIGTERM):
        log('Received SIGTERM')
        raise TerminateException
    assert False, 'received unexpected signal {}'.format(signum)

def get_service_pid():
    try:
        with open(LOCKFILE_PATH) as pidfile:
            return int(pidfile.readline())
    except FileNotFoundError:
        return None

def _check_pid(pid):
    if pid is None:
        pid = get_service_pid()
    
    if pid is None:
        err('no PID provided, and no service detected')
        exit(1)
        
    return pid

def stop(pid=None):
    pid = _check_pid(pid)
    print('Stopping service, pid', pid)
    try:
        os.kill(pid, signal.SIGTERM)
        return True
    except ProcessLookupError:
        err("no such process:", pid)
    except PermissionError:
        err("cannot stop service: Operation not permitted")
    return False
