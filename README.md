##About

This is a skeleton RPC server daemon for Linux, written in Python3.

Settings are located in settings.py  
Control it with ./scripts/rpcserver

e.g.:

    ./scripts/rpcserver -d start #Starts the server in debug mode

There is a cli client included for debugging purposes:

    ./scripts/rpcserver_client

Implement new functionality in rpcfuncs.py. Clients can be implemented easily by calling
the proxy functions in client.py.

##Dependencies

###lockfile:

    sudo pip3 install lockfile

###daemon:

    sudo pip3 install https://pypi.python.org/packages/2.7/p/python-daemon/python_daemon-2.0.6-py2.py3-none-any.whl#md5=6cc870f2eb72814f3cd9e79e7f0f588d

##License
GPLv3