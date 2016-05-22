from rpcserver.utils import LogError
from xmlrpc.client import Fault
from rpcserver.local.faults import GenericRPCErrorInfo, GenericExceptionInfo, \
ObjectNotFoundExceptionInfo
from django.core.exceptions import ObjectDoesNotExist

class PublicFault(Fault):
    """Represents faults that we're OK with exposing to clients.
    
    Faults are by default not exposed to clients, to avoid leaking internal state.
    PublicFaults, on the other hand, are passed to clients unaltered.
    
    First param is FaultCode, second is FaultString
    """
    def __init__(self, faultCode, faultString, *args, **kwargs):
        super().__init__(faultCode, faultString, *args, **kwargs)

class ObjectNotFoundException(PublicFault):
    def __init__(self):
        super().__init__(*ObjectNotFoundExceptionInfo)

class _RPCCaller:
    """
    Encapsulates an RPC method, adding local state initialization checks.
    """
    def __init__(self, f):
        self.f = f
        
    def __call__(self, *args, **kwargs):
        try:
            with LogError():
                return self.f(*args, **kwargs)
        except PublicFault:
            raise
        except Fault:
            raise PublicFault(*GenericRPCErrorInfo)
        except ObjectDoesNotExist:
            raise ObjectNotFoundException()
        except:
            # We raise a generic PublicFault to avoid leaking information
            raise PublicFault(*GenericExceptionInfo)
        
class RPC:
    """
    RPC function decorator that registers the function as available and filters
    exceptions so that only PublicFault instances are raised.
    """
    def __init__(self, rpc_funcs, debug=False):
        self.debug = debug
        self.rpc_funcs = rpc_funcs
        
    def __call__(self, f):
        caller = _RPCCaller(f)
        caller.__doc__ = f.__doc__
        self.rpc_funcs.append((caller, f.__name__, self.debug))
        return caller