#!/usr/bin/env python

import re
import sys
import psutil
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Settings
HOST = 'localhost'
STATUS_URL = 'server-status?auto'
PORT = 80
SSL = False
PROC_CHECK = True


requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
apache2_running = True
ERROR = 0


def get_proc_name(proc):
    try:
        return proc.name()
    except psutil.AccessDenied:
        # IGNORE no permission to access this proc
        pass
    except psutil.NoSuchProcess:
        # IGNORE proc died between listing and naming
        pass
    except Exception as E:
        print "Error accessing process name: %s" % E
    return None


if PROC_CHECK:
    running_processes = {}
    for p in psutil.process_iter():
        process_name = get_proc_name(p)
        if process_name == 'apache2':
            apache2_running = True

if not apache2_running:
    print "CRITICAL: apache2 not running"
    ERROR = 2
    sys.exit(2)

# Connect to
PROTO = 'https' if SSL else 'http'

try:
    req = requests.get('%s://%s:%s/%s' % (PROTO, HOST, PORT, STATUS_URL), verify=False)
except Exception, e:
    print "Plugin Failed! Check the settings at the top of the plugin. For Apache2 configuration see " \
          "https://github.com/dataloop/packs/blob/master/apache2/README.md"
    sys.exit(2)


# Get some stats off the page
metrics = {}
for line in req.iter_lines():
    if ': ' in line:
        key, value = line.split(': ')
        if key == 'Scoreboard':
            metrics['stats.open'] = value.count('.')
            metrics['stats.waiting'] = value.count('_')
            metrics['stats.starting'] = value.count('S')
            metrics['stats.reading'] = value.count('R')
            metrics['stats.sending'] = value.count('W')
            metrics['stats.keepalive'] = value.count('K')
            metrics['stats.dnslookup'] = value.count('D')
            metrics['stats.closing'] = value.count('C')
            metrics['stats.logging'] = value.count('L')
            metrics['stats.finishing'] = value.count('G')
            metrics['stats.idle_cleanup'] = value.count('I')
            metrics['stats.total'] = len(value)
        else:
            key = re.sub('(?!^)([A-Z]+)', r'_\1', key).lower()
            try:
                metrics[key] = float(value)
            except ValueError:
                pass

if metrics:
    message = "OK | "
    for k,v in metrics.items():
        message += "%s=%s;;;; " % (k.lower(), v)
    print message
    sys.exit(0)
else:
    print "Plugin Failed! Check the settings at the top of the plugin. For Apache2 configuration see " \
          "https://github.com/dataloop/packs/blob/master/apache2/README.md"
    sys.exit(2)
