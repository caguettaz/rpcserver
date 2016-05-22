import rpcserver.service
import sys
import imp

p = rpcserver.service.get_proxy()

def rld():
    global p
    imp.reload(rpcserver.service)
    p = rpcserver.service.get_proxy()
    greet()
    
def greet():
    try:
        method_list = p.system.listMethods()
        print('Supported methods:')
        for m in method_list:
            print('\t', m)
    except ConnectionRefusedError:
        print("<Server does not seems to be running>")
    except:
        print('<Unknown error fetching supported method list: >', sys.exc_info()[0])

print("""Proxy ready, type 'p.method_name(args)' to talk to the RPC server
rld() reloads the rpcserver module
""")

greet()