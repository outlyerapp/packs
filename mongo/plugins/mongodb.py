#!/usr/bin/env python
import sys
import subprocess
import platform
import socket
import fcntl
import struct

def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])

if platform.node() == 'dlovhstagn1':
    net_int = "lo"
elif platform.node() == 'nagios':
    net_int = "lo"
else:
    net_int = "eth1"

MONGO_HOST = get_ip_address(net_int)

try:
    ps = subprocess.Popen(('mongostat', '-n', '1', '--noheaders', '--host', MONGO_HOST), stdout=subprocess.PIPE)
    output = subprocess.check_output(('tail', '-1'), stdin=ps.stdout)
    ps.wait()
except Exception, e:
    print "pl"
    sys.exit(2)

metrics = output.split()

insert = metrics[0].replace('*', '')
query = metrics[1].replace('*', '')
update = metrics[2].replace('*', '')
delete = metrics[3].replace('*', '')
getmore = metrics[4]
command = metrics[5].split('|')[0]
flushes = metrics[6]
mapped = metrics[7]
vsize = metrics[8]
res = metrics[9]
faults = metrics[10]
locked = metrics[11].split(':')[1]
miss = metrics[12]
qrqw = metrics[13].split('|')[0]
araw = metrics[14].split('|')[0]
net_in = metrics[15]
net_out = metrics[16]
connections = metrics[17]

print "OK | insert=%s;;;; query=%s;;;; update=%s;;;; delete=%s;;;; getmore=%s;;;; command=%s;;;; " \
      "flushes=%s;;;; mapped=%s;;;; vsize=%s;;;; res=%s;;;; faults=%s;;;; locked=%s;;;; " \
      "miss=%s;;;; qrqw=%s;;;; araw=%s;;;; net_in=%s;;;; net_out=%s;;;; connections=%s;;;;" \
      % (insert,
         query,
         update,
         delete,
         getmore,
         command,
         flushes,
         mapped,
         vsize,
         res,
         faults,
         locked,
         miss,
         qrqw,
         araw,
         net_in,
         net_out,
         connections)
sys.exit(0)