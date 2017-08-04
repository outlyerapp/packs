#!/usr/bin/env python

"""
    Java Plugin - Monitors Java process via JMX
    
    NOTE: Requires version 0.1.5 or later of JMXQuery.jar.
          See https://github.com/outlyerapp/JMXQuery.
"""

from cStringIO import StringIO
from io import BytesIO

import tarfile
import tempfile
import requests
import subprocess
import json
import time
import re
import os

# Time between samples. Used to calculate delta metrics (like thread starts/minute).
SAMPLE_TIME = 10

# Path to Java binary. On Windows, you should use forward slashes as the path separator.
JAVA_BIN = "java"

# Set the hostname where the JMX container lives.
JMX_HOST = "localhost"

# Plugin will try all of the port numbers listed below, looking for a JMX connection.
JMX_PORTS = (9010, 9011)

# If your JVM is set to require authentication for JMX, provide the
# username and password here.
JMX_USERNAME = ''
JMX_PASSWORD = ''

# This will be combined with (JMX_HOST, JMX_PORT) to form a URL.
JMX_URL = 'service:jmx:rmi:///jndi/rmi://%s:%d/jmxrmi'

# List any extra metrics you want to collect beyond the standard JVM health
# metrics (heap, GC, threads, etc). 
EXTRA_METRICS = [
          "tomcat.threads.8080.count=Catalina:type=ThreadPool,name=\"http-apr-8080\"/currentThreadCount",
          "tomcat.threads.8080.busy=Catalina:type=ThreadPool,name=\"http-apr-8080\"/currentThreadsBusy",
          "tomcat.threads.8080.connected=Catalina:type=ThreadPool,name=\"http-apr-8080\"/connectionCount",
          "tomcat.threads.8443.count=Catalina:type=ThreadPool,name=\"http-apr-8443\"/currentThreadCount",
          "tomcat.threads.8443.busy=Catalina:type=ThreadPool,name=\"http-apr-8443\"/currentThreadsBusy",
          "tomcat.threads.8443.connected=Catalina:type=ThreadPool,name=\"http-apr-8443\"/connectionCount",
    ]


MINOR_GC_ALGORITHMS = (
    lambda x: x.startswith('jvm.gc.copy.'),  # type: str
    lambda x: x.startswith('jvm.gc.parnew.'),  # type: str
    lambda x: x.startswith('jvm.gc.ps_scavenge.'),  # type: str
)

MAJOR_GC_ALGORITHMS = (
    lambda x: x.startswith('jvm.gc.marksweepcompact.'),  # type: str
    lambda x: x.startswith('jvm.gc.concurrentmarksweep.'),  # type: str
    lambda x: x.startswith('jvm.gc.ps_marksweep.'),  # type: str
)

DELTA_METRICS = (
    lambda x: x.startswith('jvm.gc.') and x.endswith('.collectioncount'),  # type: str
    lambda x: x.startswith('jvm.gc.') and x.endswith('.collectiontime'),  # type: str
    lambda x: x == 'jvm.threading.total_started_thread_count',  # type: str
)

PERCENTAGE_METRICS = (
    lambda x: x.startswith('jvm.memory.') and x.endswith('.used'),  # type: str
)


def delta_metrics(before, after):

    delta = {}

    for delta_func in DELTA_METRICS:
        for delta_metric in filter(delta_func, after.keys()):
            delta_val = float(after[delta_metric]['value']) - float(before[delta_metric]['value'])
            per_minute = delta_val / float(SAMPLE_TIME) * 60.0

            delta_metric += '_per_min'
            delta[delta_metric] = {'metricName': delta_metric, 'value': per_minute}

    return delta


def minor_gc_metrics(metrics):

    minor = {
        'jvm.gc._minor.collectioncount': 0.0,
        'jvm.gc._minor.collectioncount_per_min': 0.0,
        'jvm.gc._minor.collectiontime': 0.0,
        'jvm.gc._minor.collectiontime_per_min': 0.0
    }

    for minor_gc_func in MINOR_GC_ALGORITHMS:
        for minor_metric in filter(minor_gc_func, metrics.keys()):  # type: str
            value = metrics[minor_metric]['value']
            minor_metric = re.sub(r'jvm\.gc\.\w+\.', 'jvm.gc._minor.', minor_metric)
            minor[minor_metric] += float(value)

    return {k: {'metricName': k, 'value': v} for k, v in minor.iteritems()}


def major_gc_metrics(metrics):

    major = {
        'jvm.gc._major.collectioncount': 0.0,
        'jvm.gc._major.collectioncount_per_min': 0.0,
        'jvm.gc._major.collectiontime': 0.0,
        'jvm.gc._major.collectiontime_per_min': 0.0
    }

    for major_gc_func in MAJOR_GC_ALGORITHMS:
        for major_metric in filter(major_gc_func, metrics.keys()):  # type: str
            value = metrics[major_metric]['value']
            major_metric = re.sub(r'jvm\.gc\.\w+\.', 'jvm.gc._major.', major_metric)
            major[major_metric] += float(value)

    return {k: {'metricName': k, 'value': v} for k, v in major.iteritems()}


def percentage_metrics(metrics):

    percentages = {}

    for percent_func in PERCENTAGE_METRICS:
        for used_metric in filter(percent_func, metrics.keys()):  # type: str
            total_metric = used_metric.replace('.used', '.max')
            percent_val = float(metrics[used_metric]['value']) / float(metrics[total_metric]['value']) * 100.0

            if percent_val >= 0:
                used_metric += '_pct'
                percentages[used_metric] = {'metricName': used_metric, 'value': percent_val}

    return percentages


def get_metrics():

    user_metrics = ';'.join(EXTRA_METRICS)

    output = ""

    for port in JMX_PORTS:
        jmx_url = JMX_URL % (JMX_HOST, port)
        command = [JAVA_BIN, '-jar', jar_file, '-url', jmx_url, '-incjvm', '-metrics', user_metrics, '-json']
        if JMX_USERNAME:
            command.extend(['-username', JMX_USERNAME, '-password', JMX_PASSWORD])
        try:
            output = subprocess.check_output(command)
            break
        except subprocess.CalledProcessError:
            pass

    if not output:
        msg = "Error connecting to JMX. Tried all of the following ports: ["
        msg += ', '.join([str(port) for port in JMX_PORTS])
        msg += "]. Please check URL and that JMX is enabled on Java processx."
        print msg
        exit(2)

    try:
        metrics = json.loads(output)
        metrics = {m['metricName']: m for m in metrics}
    except ValueError:
        print "Error executing Java plugin: " + output
        exit(2)

    return metrics


def download_jar():
    os.makedirs(os.path.dirname(jar_file))
    r = requests.get('https://download.dataloop.io/jmxquery/v0.1.5/jmxquery.jar', stream=True)
    r.raise_for_status()
    with open(jar_file, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=8192):
            if chunk: # filter out keepalive chunks
                fd.write(chunk)


def read_jar():
    if not os.path.isfile(jar_file):
        download_jar()

    jar_bytes = BytesIO()
    with open(jar_file, 'rb') as fd:
        jar_bytes.write(fd.read())

    jar_len = jar_bytes.tell()
    jar_bytes.seek(0)

    return (jar_bytes, jar_len)
    

def build_tar(jar_bytes, jar_len):
    tar_bytes = BytesIO()
    tar = tarfile.TarFile(fileobj=tar_bytes, mode='w')

    tar_info = tarfile.TarInfo(name='jmxquery.jar')
    tar_info.size = jar_len
    tar_info.mtime = time.time()
    tar_info.mode = 0755

    tar.addfile(tar_info, jar_bytes)
    tar.close()
    tar_bytes.seek(0)

    return tar_bytes
    

jar_file = '/opt/dataloop/embedded/lib/jmxquery.jar'
is_docker_env = False

try:
    from outlyer.plugin_helper.container import is_container, get_container_id
    if is_container():
        is_docker_env = True
        import docker
        client = docker.from_env(assert_hostname=False, version="auto", timeout=5)
        target = client.containers.get(get_container_id())
        target.put_archive('/tmp', build_tar(*read_jar()))
        jar_file = '/tmp/jmxquery.jar'
except ImportError:
    pass


p1 = get_metrics()
time.sleep(SAMPLE_TIME)
p2 = get_metrics()

p2.update(delta_metrics(p1, p2))
p2.update(major_gc_metrics(p2))
p2.update(minor_gc_metrics(p2))
p2.update(percentage_metrics(p2))

# Print Nagios output
output = StringIO()
output.write("OK | ")
for name in sorted(p2.keys()):
    metric = p2[name]
    if 'value' in metric.keys():
        output.write(metric['metricName'] + "=" + str(metric['value']) + ";;;; ")

print output.getvalue()

