#!/usr/bin/env python
import sys
import subprocess

MONGO_HOST = '127.0.0.1'

try:
    ps = subprocess.Popen(('mongostat', '-n', '1', '--noheaders', '--host', MONGO_HOST), stdout=subprocess.PIPE)
    output = subprocess.check_output(('tail', '-1'), stdin=ps.stdout)
    ps.wait()

except Exception, e:
    print "Plugin Failed: %s" % e
    sys.exit(2)

line = output.split()
metrics = {
    'insert': line[0].replace('*', ''),
    'query': line[1].replace('*', ''),
    'update': line[2].replace('*', ''),
    'delete': line[3].replace('*', ''),
    'getmore': line[4],
    'command': line[5].split('|')[0],
    'flushes': line[6],
    'mapped': line[7],
    'vsize': line[8],
    'res': line[9],
    'faults': line[10],
    'locked': line[11].split(':')[1],
    'miss': line[12],
    'qrqw': line[13].split('|')[0],
    'araw': line[14].split('|')[0],
    'net_in': line[15],
    'net_out': line[16],
    'connections': line[17]
}

output = "OK | "
for k, v in metrics.iteritems():
    output += str(k) + '=' + str(v) + ';;;; '
print output
sys.exit(0)