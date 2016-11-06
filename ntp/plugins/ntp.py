#!/usr/bin/env python
from socket import AF_INET, SOCK_DGRAM
import sys
import socket
import struct
import time
from datetime import datetime

# Alert if more than 5 minutes
DRIFT = 300

try:
    def get_ntp_time(host="pool.ntp.org"):
        port = 123
        buf = 1024
        address = (host,port)
        msg = '\x1b' + 47 * '\0'
        time_1970 = 2208988800L
        client = socket.socket(AF_INET, SOCK_DGRAM)
        client.sendto(msg, address)
        msg, address = client.recvfrom(buf)
        t = struct.unpack("!12I", msg)[10]
        t -= time_1970
        return datetime.strptime(time.ctime(t).replace("  ", " "), '%a %b %d %H:%M:%S %Y')

    time_delta = datetime.now().date() - get_ntp_time().date()

    if int(time_delta.seconds) < DRIFT:
        print "OK | drift=%ds;;;;" % int(time_delta.seconds)
        sys.exit(0)
    else:
        print "Failed! | drift=%ds;;;;" % int(time_delta.seconds)
        sys.exit(2)

except Exception, e:
    print "Failed! %s" % e
    sys.exit(2)