#!/usr/bin/env python
import os
import re
import subprocess
import sys
import time
import json
from datetime import datetime

"""
Change the user name and password below to match one already setup or run:

GRANT USAGE ON *.* TO 'dataloop'@'localhost' IDENTIFIED BY PASSWORD 'password'

To setup a dataloop user with the password set to password (change this to something more suitable).
"""

MYSQL_USER = 'root'
MYSQL_PASSWORD = ''



TMPDIR = '/opt/dataloop/tmp'
TMPFILE = 'mysql.json'
TIMESTAMP = datetime.now().strftime('%s')
status = {}


# metrics collection
def get_mysql_status():
    command = ['/usr/bin/mysql', '-s', '-N', '-s', '-e', 'show global status']
    if MYSQL_USER:
        command.append('-u%s' % MYSQL_USER)
    if MYSQL_PASSWORD:
        command.append('-p%s' % MYSQL_PASSWORD)

    try:
        resp = subprocess.check_output(command)
    except Exception, e:
        print "connection failure: %s" % e
        sys.exit(2)

    metric_list = resp.split('\n')
    metric_list.sort()
    for line in metric_list:
        if line:
            metric = line.split('\t')
            k =  metric[0].strip().lower()
            k = k.replace('com_', '',1)
            v = metric[1]
            if isinstance(v, int) or isinstance(v, float):
                status[k] = v
    return status


# rate calculation
def tmp_file():
    if not os.path.isdir(TMPDIR):
        os.makedirs(TMPDIR)
    if not os.path.isfile(TMPDIR + '/' + TMPFILE):
        os.mknod(TMPDIR + '/' + TMPFILE)


def get_cache():
    with open(TMPDIR + '/' + TMPFILE, 'r') as json_fp:
        try:
            json_data = json.load(json_fp)
        except:
            print "not a valid json file. rates calculations impossible"
            json_data = []
    return json_data


def write_cache(cache):
    with open(TMPDIR + '/' + TMPFILE, 'w') as json_fp:
        try:
            json.dump(cache, json_fp)
        except:
            print "unable to write cache file, future rates will be hard to calculate"


def cleanse_cache(cache):
    try:
        while (int(TIMESTAMP) - int(cache[0]['timestamp'])) >= 3600:
            cache.pop(0)
        while len(cache) >= 120:
            cache.pop(0)
        return cache
    except:
        os.remove(TMPDIR + '/' + TMPFILE)


def calculate_rates(data_now, json_data, rateme):
    if len(json_data) > 1:
        try:
            history = json_data[0]
            seconds_diff = int(TIMESTAMP) - int(history['timestamp'])
            rate_diff = float(data_now[rateme]) - float(history[rateme])
            data_per_second = "{0:.2f}".format(rate_diff / seconds_diff)
            return data_per_second
        except:
            return None

tmp_file()

json_data = get_cache()

if len(json_data) > 0:
    json_data = cleanse_cache(json_data)

result = get_mysql_status()

all_rates = list(result.keys())
rates = list(set(all_rates) - set(no_rates))

for rate in rates:
    _ = calculate_rates(result, json_data, rate)
    if _ is not None:
        result[rate + "_per_sec"] = _


dated_result = result
dated_result['timestamp'] = TIMESTAMP
json_data.append(dated_result)
write_cache(json_data)

perf_data = "OK | "
for k, v in result.iteritems():
    try:
        _ = float(v)
        perf_data += "%s=%s;;;; " % (k, v)
    except ValueError:
        continue

print perf_data
sys.exit(0)