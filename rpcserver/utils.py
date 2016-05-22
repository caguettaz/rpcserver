import traceback
import sys
from datetime import datetime

logfile = None
_debug = False

def set_debug():
    global _debug
    _debug = True

INFO = ''
WARN = ' [WARNING]'
ERR = ' [ERROR]'
DBG = ' [DEBUG]'

#TODO: use logging package
def log_err(*args):
    log(*args, level=ERR)
    
def log_warn(*args):
    log(*args, level=WARN)

def log_dbg(*args):
    log(*args, level=DBG)

def log(*args, level=INFO):
    if level == DBG and not _debug:
        return
    
    if logfile is None:
        print(str(datetime.now()) + level, *args, file=sys.stderr)
    else:
        print(str(datetime.now()) + level, *args, file=logfile)
        logfile.flush()

def err(*args):
    print('ERROR:', *args, file=sys.stderr)

class NullContextManager:
    '''Context manager that does nothing but possibly swallow exceptions.
    
    Useful when using a context variable whose type is decided dynamically, and a default
    do-nothing option is required.
    '''
    def __enter__(self, catch=True):
        self.catch = catch
    
    def __exit__(self, type, value, tb):
        return self.catch

class LogError:
    def __init__(self, catch=False):
        self.catch = catch
        
    def __enter__(self):
        pass
    
    def __exit__(self, type, value, tb):
        global _debug
        
        if type is None or type is TerminateException:
            return True
        
        if self.catch:
            log_err('Uncaught exception during execution:',
                '"' + traceback.format_exception_only(type, value)[0].rstrip('\n') + '"')
            if _debug:
                log('Traceback follows\n\n' +
                    ''.join(traceback.format_exception(type, value, tb)))
        else:
            log_err('Exception during execution:',
                '"' + traceback.format_exception_only(type, value)[0].rstrip('\n') + '"')
        return self.catch
    
    
    
class TerminateException(Exception):
    pass