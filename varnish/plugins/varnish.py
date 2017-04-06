#!/usr/bin/env python
import sys
import subprocess
import time
import json
import StringIO


def get_varnish_metrics():
    try:
        data = json.loads(subprocess.check_output('varnishstat -j'))
        m = {}
        for name, desc in data.iteritems():
            if isinstance(desc, dict):
                value = desc.get('value')
                m[name.lower()] = value
        return m
    except Exception, e:
        print "Plugin Failed! %s" % e
        sys.exit(2)

time_between = 5

metrics_before = get_varnish_metrics()
time.sleep(time_between)
metrics = get_varnish_metrics()

metric_rates = {}
for metric, value in metrics.iteritems():
    if value > metrics_before[metric]:
        metric_rates[metric + '_per_sec'] = (int(value) - int(metrics_before[metric])) / time_between
    else:
        metric_rates[metric + '_per_sec'] = 0

metrics.update(metric_rates)

buf = StringIO.StringIO()
buf.write('OK | ')
for k, v in metrics.iteritems():
    buf.write('{0}={1};;;; '.format(k, v))

print buf.getvalue()
sys.exit(0)
