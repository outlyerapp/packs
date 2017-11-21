#!/usr/bin/env python
import os
import re
import sys
import time
import psutil
import StringIO
from datetime import datetime
from urlparse import urlparse
from collections import OrderedDict

LOGFILE = '/Users/tradel/Downloads/admin-nginx-log.log'
SINCE = 86400 * 7

COMBINED_FORMAT = '$remote_addr - $remote_user [$time_local] "$request" $status ' \
                  '$body_bytes_sent "$http_referer" "$http_user_agent" "$upstream_addr"'
TIMED_COMBINED_FORMAT = '$remote_addr - $remote_user [$time_local] "$request" $status ' \
                        '$body_bytes_sent "$http_referer" "$http_user_agent" "$request_time"'

TRANSACTION_TYPES = OrderedDict([
    ('dms_next_command', lambda x: x.startswith('/api/dms/') and x.endswith('/commands/next')),
    ('dms_command_complete', lambda x: x.startswith('/api/dms/') and x.endswith('/complete')),
    ('dms_sync', lambda x: x.startswith('/api/dms/') and x.endswith('/sync')),
    ('dms_heartbeat', lambda x: x.startswith('/api/dms/') and x.endswith('/heartbeat')),
    ('dms_apk', lambda x: x.startswith('/api/dms') and '/apk/' in x),
    ('admin_api_app_categories', lambda x: x == '/api/app-categories'),
    ('admin_api_app', lambda x: x.startswith('/api/apps/')),
    ('admin_api_dash_stats', lambda x: x == '/api/dashboard/stats'),
    ('admin_api_device_types', lambda x: x == '/api/device-types'),
    ('admin_api_device_variants', lambda x: x == '/api/device-variants'),
    ('admin_api_devices', lambda x: x == '/api/devices'),
    ('admin_api_firmware_file', lambda x: x.startswith('/api/firmware/file/')),
    ('admin_api_firmware_files', lambda x: x == '/api/firmware/files'),
    ('admin_api_firmware_types', lambda x: x == '/api/firmware/types'),
    ('admin_api_locales', lambda x: x == '/api/locales'),
    ('admin_api_login', lambda x: x == '/api/login'),
    ('admin_api_profile', lambda x: x == '/api/profile'),
    ('admin_api_users', lambda x: x == '/api/users'),
    ('admin_home', lambda x: x == '/'),
])

timezone = '+0000'  # timezone = time.strftime("%z", time.localtime())
start_time = datetime.now()
var_pattern = re.compile(r'\$(\w+)|(.)')

status_codes = {'2xx': 0, '3xx': 0, '4xx': 0, '5xx': 0, 'all': 0}
times = {'count': 0, 'total': 0, 'max': 0}

all_txn_stats = dict()
for key in TRANSACTION_TYPES.keys():
    all_txn_stats[key] = {'all': 0, '2xx': 0, '3xx': 0, '4xx': 0, '5xx': 0, 'count': 0, 'total': 0, 'max': 0}


def is_health_check(ua):
    if 'ELB-HealthChecker' in ua:
        return True
    elif 'StatusCake' in ua:
        return True
    elif 'UptimeRobot' in ua:
        return True
    elif 'python-requests' in ua:
        return True
    else:
        return False


def update_status_codes(stats, code):
    stats['all'] = stats.get('all', 0) + 1
    stats[code] = stats.get(code, 0) + 1
    stats[code[0] + 'xx'] += 1


def update_times(stats, request_time):
    try:
        time_taken = float(request_time)
        if 'min' not in stats.keys():
            stats['min'] = time_taken
            stats['count'] += 1
            stats['total'] += time_taken
        if time_taken > stats['max']:
            stats['max'] = time_taken
        if time_taken < stats['min']:
            stats['min'] = time_taken
    except ValueError:
        # Request time not castable to float (like '-')
        pass


def update_stats(line):
    m = timed_combined_regex.match(line)
    if not m:
        m = combined_regex.match(line)
    if not m:
        raise ValueError("unable to parse log line: " + line)
    data = m.groupdict()

    line_time = datetime.strptime(data['time_local'], '%d/%b/%Y:%H:%M:%S ' + timezone)
    delta = start_time - line_time
    if delta.seconds < SINCE:

        update_status_codes(status_codes, data['status'])

        if 'request_time' in data.keys():
            update_times(times, data['request_time'])

        user_agent = data['http_user_agent']
        if not is_health_check(user_agent):
            request = data['request'].split(' ')
            scheme, netloc, path, params, query, fragment = urlparse(request[1])
            for txn_name, func in TRANSACTION_TYPES.items():
                if func(path):
                    txn_stats = all_txn_stats[txn_name]
                    update_status_codes(txn_stats, data['status'])
                    if 'request_time' in data.keys():
                        update_times(txn_stats, data['request_time'])

    else:
        return True


def find_vars(text):
    return var_pattern.findall(text)


def log_format_2_regex(text):
    return ''.join('(?P<' + g + '>.*?)' if g else re.escape(c) for g, c in find_vars(text))


# nginx health check
# def get_proc_name(proc):
#     try:
#         return proc.name()
#     except psutil.AccessDenied:
#         # IGNORE: we don't have permission to access this process
#         pass
#     except psutil.NoSuchProcess:
#         # IGNORE: process has died between listing and getting info
#         pass
#     except Exception as e:
#         print "error accessing process info: %s" % e
#     return None
#
#
# def find_nginx_process_psutil():
#     for p in psutil.process_iter():
#         process_name = get_proc_name(p)
#         if process_name == 'nginx':
#             return True
#
#
# nginx_running = find_nginx_process_psutil()
# if not nginx_running:
#     print "CRITICAL - nginx master process is not running"
#     sys.exit(2)


timed_combined_regex = re.compile(log_format_2_regex(TIMED_COMBINED_FORMAT))
combined_regex = re.compile(log_format_2_regex(COMBINED_FORMAT))

for line in open(LOGFILE, 'r').readlines():
    try:
        stop = update_stats(line)
        if stop:
            break
    except (AttributeError, ValueError):
        continue

buf = StringIO.StringIO()
buf.write('OK | ')

for k, v in status_codes.iteritems():
    buf.write('{0}={1};;;; '.format(k, v))

if status_codes['all'] > 0:
    for k in '2xx', '3xx', '4xx', '5xx':
        buf.write('{0}_pct={1:0.2f}%;;;; '.format(k, float(status_codes[k]) / float(status_codes['all']) * 100.0))

if times['count'] > 0:
    buf.write('avg_time={0:0.2f}s;;;; '.format(float(times['total']) / float(times['count'])))

if all(key in times for key in ("max", "min")):
    buf.write('max_time={0:0.2f}s;;;; min_time={1:0.2f}s;;;; '.format(float(times['max']), float(times['min'])))

for txn_name, txn_stats in all_txn_stats.iteritems():
    if txn_stats['all'] > 0:
        for k in txn_stats.iterkeys():
            if k[0].isdigit():
                buf.write('{0}.{1}={2};;;; '.format(txn_name, k, txn_stats[k]))
        for k in '2xx', '3xx', '4xx', '5xx':
            buf.write('{0}.{1}_pct={2:0.2f}%;;;; '.format(txn_name, k, float(txn_stats[k]) / float(txn_stats['all']) * 100.0))
        if txn_stats['count'] > 0:
            buf.write('{0}.avg_time={1:0.2f}s;;;; '.format(txn_name, float(txn_stats['total']) / float(txn_stats['count'])))
        if all(key in times for key in ("max", "min")):
            buf.write('{0}.max_time={1:0.2f}s;;;; {0}.min_time={2:0.2f}s;;;; '.format(txn_name, float(txn_stats['max']), float(txn_stats['min'])))

print buf.getvalue()
sys.exit(0)
