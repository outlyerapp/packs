#!/usr/bin/env python
import os
import re
import sys
import time
import psutil
import StringIO
from datetime import datetime

LOGFILE = '/var/log/nginx/access.log'  # change this to 'stdout' 
# if you log to stdout on a container

SINCE = 30


# log file parsing

def reverse_read(fname, separator=os.linesep, since=None):
    with file(fname) as f:
        f.seek(0, 2)  # go to end of file
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

try:
    if not read:
        read = reverse_read
except NameError:
    read = reverse_read

def update_stats(line):
    m = timed_combined_regex.match(line)
    if not m:
        m = combined_regex.match(line)

    data = m.groupdict()

    line_time = datetime.strptime(data['time_local'], '%d/%b/%Y:%H:%M:%S ' + timezone)
    delta = start_time - line_time
    if delta.seconds < SINCE:
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
        return True

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

def find_vars(text):
    return var_pattern.findall(text)


def log_format_2_regex(text):
    return ''.join('(?P<' + g + '>.*?)' if g else re.escape(c) for g, c in find_vars(text))

timed_combined_regex = re.compile(log_format_2_regex(TIMED_COMBINED_FORMAT))
combined_regex = re.compile(log_format_2_regex(COMBINED_FORMAT))

for line in read(LOGFILE, since=SINCE):
    try:
        stop = update_stats(line)
        if stop:
            break
    except (AttributeError, ValueError):
        continue

# nginx health check
def get_proc_name(proc):
    try:
        return proc.name()
    except psutil.AccessDenied:
        # IGNORE: we don't have permission to access this process
        pass
    except psutil.NoSuchProcess:
        # IGNORE: process has died between listing and getting info
        pass
    except Exception as e:
        print "error accessing process info: %s" % e
    return None

def find_nginx_process_psutil():
    for p in psutil.process_iter():
        process_name = get_proc_name(p)
        if process_name == 'nginx':
            return True

try:
    if not find_nginx_process:
        find_nginx_process = find_nginx_process_psutil
except NameError:
    find_nginx_process = find_nginx_process_psutil

nginx_running = False
nginx_running = find_nginx_process()

if not nginx_running:
    print "CRITICAL - nginx master process is not running"
    sys.exit(2)

buf = StringIO.StringIO()
buf.write('OK | ')

for k, v in status_codes.iteritems():
    buf.write('{0}={1};;;; '.format(k, v))

if times['count'] > 0:
    buf.write('avg_time={0:0.2f}s;;;; '.format(float(times['total'])/float(times['count'])))

if all(key in times for key in ("max", "min")):
    buf.write('max_time={0:0.2f}s;;;; min_time={1:0.2f}s;;;;'.format(float(times['max']), float(times['min'])))

print buf.getvalue()
sys.exit(0)
