#!/usr/bin/env python
import sys
import subprocess

try:
    output = subprocess.check_output(('redis-cli', 'info'))
except Exception, e:
    print "Plugin Failed! %s" % e
    sys.exit(2)


def is_number(s):
    try:
        float(s)
    except ValueError:
        try:
            complex(s)
        except ValueError:
            return False
    return True

metrics = output.split()
perf_data = "OK | "

for m in metrics:
    if 'db0' in m:
        keys = m[9:].split(',')[0]
        perf_data += "keys=%s;;;; " % keys
    elif ":" in m:
        k = m.split(':')[0]
        v = m.split(':')[1]
        if is_number(v):
            perf_data += "%s=%s;;;; " % (k, v)

print perf_data
sys.exit(0)
