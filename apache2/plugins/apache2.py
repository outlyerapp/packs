#!/usr/bin/env python
import sys
import psutil
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import re

HOST = 'localhost'
STATUS_URL = 'server-status?auto'
PORT = 443
SSL = True
PROC_CHECK = True

# disable any ssl insecurity warnings
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
        print "error accessing process name: %s" % E
    return None


if PROC_CHECK:
    running_processes = {}
    for p in psutil.process_iter():
        process_name = get_proc_name(p)
        if process_name == 'apache2':
            apache2_running = True

if not apache2_running:
    print "CRITICAL: Apache2 not running!"
    ERROR = 2
    sys.exit(2)

# Connect to
if SSL:
    PROTO = 'https'
else:
    PROTO = 'http'


req = requests.get('%s://%s:%s/%s' % (PROTO, HOST, PORT, STATUS_URL), verify=False)

if req.status_code != 200:
    print "Unable to connect to server status page"
    ERROR = 2

# Get some stats off the page
metrics={}
for line in req.iter_lines():
    print line
    if re.match('Total Accesses', line):
        metrics['total_accesses'] = line.split(':')[1].strip()
    elif re.match('Total kBytes', line):
        metrics['Total_kBytes'] = line.split(':')[1].strip()
    elif re.match('Load15', line):
        metrics['load15'] = line.split(':')[1].strip()
    elif re.match('Load5', line):
        metrics['load5'] = line.split(':')[1].strip()
    elif re.match('Load1', line):
        metrics['load1'] = line.split(':')[1].strip()
    elif re.match('ServerUptimeSeconds', line):
        metrics['ServerUptimeSeconds'] = line.split(':')[1].strip()
    elif re.match('CPUUser', line):
        metrics['CPUUser'] = line.split(':')[1].strip()
    elif re.match('CPUSystem', line):
        metrics['CPUSystem'] = line.split(':')[1].strip()
    elif re.match('CPUChildrenUser', line):
        metrics['CPUChildrenUser'] = line.split(':')[1].strip()
    elif re.match('CPUChildrenSystem', line):
        metrics['CPUChildrenSystem'] = line.split(':')[1].strip()
    elif re.match('CPULoad', line):
        metrics['CPULoad'] = line.split(':')[1].strip()
    elif re.match('Uptime', line):
        metrics['Uptime'] = line.split(':')[1].strip()
    elif re.match('ReqPerSec', line):
        metrics['ReqPerSec'] = line.split(':')[1].strip()
    elif re.match('BytesPerSec', line):
        metrics['BytesPerSec'] = line.split(':')[1].strip()
    elif re.match('BytesPerReq', line):
        metrics['BytesPerReq'] = line.split(':')[1].strip()
    elif re.match('IdleWorkers', line):
        metrics['IdleWorkers'] = line.split(':')[1].strip()
    elif re.match('BusyWorkers', line):
        metrics['BusyWorkers'] = line.split(':')[1].strip()
    elif re.match('ConnsTotal', line):
        metrics['ConnsTotal'] = line.split(':')[1].strip()
    elif re.match('ConnsAsyncWriting', line):
        metrics['ConnsAsyncWriting'] = line.split(':')[1].strip()
    elif re.match('ConnsAsyncKeepAlive', line):
        metrics['ConnsAsyncKeepAlive'] = line.split(':')[1].strip()
    elif re.match('ConnsAsyncClosing', line):
        metrics['ConnsAsyncClosing'] = line.split(':')[1].strip()
    elif re.match('Scoreboard', line):
        # print line
        name, value = line.split(': ')
        value = value.strip()
        #metrics['stats'] = {}
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
    elif re.match('CacheSharedMemory', line):
        metrics['CacheSharedMemory'] = line.split(':')[1].strip()
    elif re.match('CacheCurrentEntries', line):
        metrics['CacheCurrentEntries'] = line.split(':')[1].strip()
    elif re.match('CacheSubcaches', line):
        metrics['CacheSubcaches'] = line.split(':')[1].strip()
    elif re.match('CacheIndexesPerSubcaches', line):
        metrics['CacheIndexUsage'] = line.split(':')[1].strip()
    elif re.match('CacheUsage', line):
        metrics['CacheUsage'] = line.split(':')[1].strip()
    elif re.match('CacheStoreCount', line):
        metrics['CacheStoreCount'] = line.split(':')[1].strip()
    elif re.match('CacheReplaceCount', line):
        metrics['CacheReplaceCount'] = line.split(':')[1].strip()
    elif re.match('CacheExpireCount', line):
        metrics['CacheExpireCount'] = line.split(':')[1].strip()
    elif re.match('CacheDiscardCount', line):
        metrics['CacheDiscardCount'] = line.split(':')[1].strip()
    elif re.match('CacheRetrieveHitCount', line):
        metrics['CacheRetrieveHitCount'] = line.split(':')[1].strip()
    elif re.match('CacheRetrieveMissCount', line):
        metrics['CacheRetrieveMissCount'] = line.split(':')[1].strip()
    elif re.match('CacheRemoveHitCount', line):
        metrics['CacheRemoveHitCount'] = line.split(':')[1].strip()
    elif re.match('CacheRemoveMissCount', line):
        metrics['CacheRemoveMissCount'] = line.split(':')[1].strip()

message = "OK | "
for k,v in metrics.items():
    message += "%s=%s;;;; " % (k, v)

print message
