from rpcserver.utils import log_dbg
from rpcserver.local.rpc import RPC

#Tuples of exposed (function, name, debug) RPCs
rpc_funcs = []

########DEBUG#########

@RPC(rpc_funcs, debug=True)
def rpc_print(v):
    print(repr(v))

######################


@RPC(rpc_funcs)
def do_foo(arg):
    log_dbg('do_foo({})'.format(arg))
    #TODO
    return True
