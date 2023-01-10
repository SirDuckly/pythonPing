from netaddr import IPNetwork

def networkAddrs():
    for ip in IPNetwork('192.168.0.0/16'):
        print ('%s' % ip)

def processJob():
    print("Process")

def startProcess():
    print("Not started")