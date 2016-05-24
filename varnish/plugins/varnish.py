#!/usr/bin/env python
import subprocess
import sys
import time


def get_varnish_metrics():
    try:
        ps = subprocess.Popen(('/usr/bin/varnishstat', '-1'), stdout=subprocess.PIPE)
        data = subprocess.check_output(('awk', '{print $1,$2}'), stdin=ps.stdout)
        ps.wait()
        if ps.returncode != 0:
            print "Plugin Failed!"
            sys.exit(2)
        m = {}
        for line in data.splitlines():
            if len(line.split()) > 0:
                name = line.split()[0].lower().replace('(', '_').replace(')', '_').replace(',,', '_')
                m[name] = line.split()[1]
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

output = "OK | "
for k, v in metrics.iteritems():
    output += str(k) + '=' + str(v) + ';;;; '

print output
sys.exit(0)