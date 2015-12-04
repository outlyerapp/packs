#!/usr/bin/env python
import re
import os
import sys
import re

LOGFILE = '/var/log/nginx/access.log'

TMPDIR = '/opt/dataloop/tmp'
TMPFILE = 'nginx'

combined = '$remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent "$http_referer" "$http_user_agent"'
timed_combined = '$remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent "$http_referer" "$http_user_agent" "$request_time"'

status_codes = {'2xx': 0,
                '3xx': 0,
                '4xx': 0,
                '5xx': 0}
times = {
    'count': 0,
    'total': 0,
    'max': 0
}

offset = 0


def tmp_file():
    if not os.path.isdir(TMPDIR):
        os.makedirs(TMPDIR)
    if not os.path.isfile(TMPDIR + '/' + TMPFILE):
        os.mknod(TMPDIR + '/' + TMPFILE)


def get_offset():
    with open(TMPDIR + '/' + TMPFILE, 'r') as off:
        try:
            offset = int(off.read())
        except Exception, e:
            offset = 0
    return offset


def write_offset(offset):
    with open(TMPDIR + '/' + TMPFILE, 'w') as off:
        off.write("%s" % offset)

tmp_file()
position = get_offset()
file_size = os.stat(LOGFILE).st_size
if file_size < position:
    position = 0

with open(LOGFILE) as fp:
    if position > 0:
        fp.seek(position)

    for line in fp.xreadlines():
        regex = ''.join('(?P<' + g + '>.*?)' if g else re.escape(c) for g, c in re.findall(r'\$(\w+)|(.)', timed_combined))
        m = re.match(regex, line)
        if not m:
            regex = ''.join('(?P<' + g + '>.*?)' if g else re.escape(c) for g, c in re.findall(r'\$(\w+)|(.)', combined))
            m = re.match(regex, line)
        data = m.groupdict()

        code = data['status']
        if code not in status_codes.keys():
            status_codes[code] = 1
        else:
            status_codes[code] += 1
        if code.startswith('2'):
            status_codes['2xx'] += 1
        if code.startswith('3'):
            status_codes['3xx'] += 1
        if code.startswith('4'):
            status_codes['4xx'] += 1
        if code.startswith('5'):
            status_codes['5xx'] += 1
        if 'request_time' in data.iterkeys():
            time_taken = data['request_time']
            if 'min' not in times.iterkeys():
                times['min'] = time_taken
            times['count'] += 1
            times['total'] += float(time_taken)
            if time_taken > times['max']:
                times['max'] = time_taken
            if time_taken < times['min']:
                times['min'] = time_taken

    write_offset(fp.tell())
    fp.close()

message = "OK | "
for k, v in status_codes.iteritems():
    message += "%s=%s;;;; " % (k, v)

if times['count'] > 0:
    message += "avg_time=%0.2fs;;;; " % (float(times['total'])/float(times['count']))

if 'request_time' in data.iterkeys():
    message += "max_time=%0.2fs;;;; min_time=%0.2fs;;;;" % (float(times['max']), float(times['min']))

print message
sys.exit(0)