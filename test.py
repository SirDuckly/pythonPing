from netaddr import IPNetwork
for ip in IPNetwork('192.168.0.0/16'):
    print ('%s' % ip)