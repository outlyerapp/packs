#!/usr/bin/env python
import sys
import requests
import time

# settings
HOST = 'www.example.com'
PORT = 80
URL = "http://%s:%s/fpm-status" % (HOST, PORT)


RATE_INTERVAL = 5
excludes = ['pool', 'process_manager', 'start_time']


def calculate_rate(present, past):
    return round((float(present) - float(past)) / RATE_INTERVAL, 2)


def get_metrics():
    metrics = {}
    try:
        resp = requests.get(URL).content.split('\n')
    except:
        print "connection failed"
        sys.exit(2)

    for metric in resp:
        if len(metric) > 0:
            key = metric.split(':')[0].replace(' ', '_').lower().strip()
            if not any(x in key.lower() for x in excludes):
                value = metric.split(':')[1].strip()
                metrics[key] = value

    return metrics

past_output = get_metrics()
time.sleep(RATE_INTERVAL)
present_output = get_metrics()

raw_output = {}
for present_key, present_value in present_output.iteritems():
    if present_key in past_output:
        if 'per_sec' not in present_key:
            raw_output[present_key + '_per_sec'] = calculate_rate(present_value, past_output[present_key])

raw_output.update(past_output)

output = "OK | "
for k, v in raw_output.iteritems():
    output += "%s=%s;;;; " % (k, v)
print output