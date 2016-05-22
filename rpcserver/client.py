import rpcserver.service

_proxy = rpcserver.service.get_proxy()

#***************************************
#               RPC proxies
#***************************************

def do_foo(arg):
    return _proxy.do_foo(arg)

#***************************************
#               Other interfaces
#***************************************
