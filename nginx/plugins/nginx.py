#!/usr/bin/env python
import os
import re
import sys
import time
import subprocess
import tempfile
import StringIO
from datetime import datetime

from outlyer.plugin_helper.container import patch_all, is_container, get_container_id
patch_all()

LOGFILE = '/var/log/nginx/access.log'


# nginx health check

nginx_running = False
worker_count = 0

output = subprocess.check_output("ps awux")
if re.search(r'nginx: master process', output, re.MULTILINE):
    nginx_running = True
    worker_count = len(re.findall(r'nginx: worker process', output))

if not nginx_running:
    print "CRITICAL - nginx master process is not running"
    sys.exit(2)


# log file parsing

COMBINED_FORMAT = '$remote_addr - $remote_user [$time_local] "$request" $status ' \
           '$body_bytes_sent "$http_referer" "$http_user_agent" '
TIMED_COMBINED_FORMAT = '$remote_addr - $remote_user [$time_local] "$request" $status ' \
                        '$body_bytes_sent "$http_referer" "$http_user_agent" "$request_time"'

timezone = time.strftime("%z", time.localtime())
start_time = datetime.now()
var_pattern = re.compile(r'\$(\w+)|(.)')

status_codes = {'2xx': 0,
                '3xx': 0,
                '4xx': 0,
                '5xx': 0}
times = {
    'count': 0,
    'total': 0,
    'max': 0
}


def reverse_read(fname, separator=os.linesep):
    with file(fname) as f:
        f.seek(0, 2)
        fsize = f.tell()
        r_cursor = 1
        while r_cursor <= fsize:
            a_line = ''
            while r_cursor <= fsize:
                f.seek(-1 * r_cursor, 2)
                r_cursor += 1
                c = f.read(1)
                if c == separator and a_line:
                    r_cursor -= 1
                    break
                a_line += c
            a_line = a_line[::-1]
            yield a_line


def find_vars(text):
    return var_pattern.findall(text)


def log_format_2_regex(text):
    return ''.join('(?P<' + g + '>.*?)' if g else re.escape(c) for g, c in find_vars(text))


logfile = LOGFILE
temp_file = ''

if is_container():

    import docker
    client = docker.from_env()
    target = client.containers.get(get_container_id())

    temp_file = tempfile.mkstemp()[1]
    log_stream, _ = target.get_archive(logfile)
    with open(temp_file, 'w') as temp:
        temp.write(log_stream.read())

    logfile = temp_file


timed_combined_regex = re.compile(log_format_2_regex(TIMED_COMBINED_FORMAT))
combined_regex = re.compile(log_format_2_regex(COMBINED_FORMAT))

for line in reverse_read(logfile):
    try:
        m = timed_combined_regex.match(line)
        if not m:
            m = combined_regex.match(line)

        data = m.groupdict()

        line_time = datetime.strptime(data['time_local'], '%d/%b/%Y:%H:%M:%S ' + timezone)
        delta = start_time - line_time
        if delta.seconds < 30:
            code = data['status']
            status_codes[code] = status_codes.get(code, 0) + 1
            status_codes[code[0] + 'xx'] += 1
            try:
                if 'request_time' in data.iterkeys():
                    time_taken = float(data['request_time'])
                    if 'min' not in times.iterkeys():
                        times['min'] = time_taken
                    times['count'] += 1
                    times['total'] += time_taken
                    if time_taken > times['max']:
                        times['max'] = time_taken
                    if time_taken < times['min']:
                        times['min'] = time_taken
            except ValueError:
                # Request time not castable to float (like '-')
                pass
        else:
            break
    except (AttributeError, ValueError):
        continue

buf = StringIO.StringIO()
buf.write('OK | ')
buf.write('worker_count={0};;;; '.format(worker_count))

for k, v in status_codes.iteritems():
    buf.write('{0}={1};;;; '.format(k, v))

if times['count'] > 0:
    buf.write('avg_time={0:0.2f}s;;;; '.format(float(times['total'])/float(times['count'])))

if all(key in times for key in ("max", "min")):
    buf.write('max_time={0:0.2f}s;;;; min_time={1:0.2f}s;;;;'.format(float(times['max']), float(times['min'])))

if is_container():
    os.remove(temp_file)

print buf.getvalue()
sys.exit(0)
