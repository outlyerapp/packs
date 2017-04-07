#!/usr/bin/env python
import sys
import requests
import StringIO

URL = 'http://127.0.0.1:8098/stats'


try:
    resp = requests.get(URL).json()
except Exception, e:
    print "connection failed: %s" % e
    sys.exit(2)

buf = StringIO.StringIO()
buf.write('OK | ')
for k, v in resp.iteritems():
    if isinstance(v, int) or isinstance(v, float):
            if 'time' in k or 'latency' in k:
                buf.write('{0}={1}ms;;;; '.format(k, v / 1000))
            else:
                buf.write('{0}={1};;;; '.format(k, v))

print buf.getvalue()
sys.exit(0)
