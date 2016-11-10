#!/usr/bin/env python

"""
    Java Plugin - Monitors Java process via JMX
"""

import subprocess
import json

# Path to Java binary. On Windows, you should use forward slashes as the path separator
JAVA_BIN = "java"

# Set the JMX URL Endpoint to Connect To
JMX_URL = 'service:jmx:rmi:///jndi/rmi://localhost:9090/jmxrmi'

# Set JMX Username, if authentication required
JMX_USERNAME = ''

# Set JMX Password, if authentication required
JMX_PASSWORD = ''

# Define query of metrics you wish to pull with output names as they will appear in Dataloop when you browse metrics
METRICS = "jvm.classloading.loadedclasscount=java.lang:type=ClassLoading/LoadedClassCount;" + \
          "jvm.classloading.unloadedclasscount=java.lang:type=ClassLoading/UnloadedClassCount;" + \
          "jvm.classloading.totalloadedclasscount=java.lang:type=ClassLoading/TotalLoadedClassCount;" + \
          "jvm.gc.parnew.collectiontime=java.lang:type=GarbageCollector,name=ParNew/CollectionTime;" + \
          "jvm.gc.concurrentmarksweep.collectiontime=java.lang:type=GarbageCollector,name=ConcurrentMarkSweep/CollectionTime;" + \
          "jvm.gc.parnew.collectioncount=java.lang:type=GarbageCollector,name=ParNew/CollectionCount;" + \
          "jvm.gc.concurrentmarksweep.collectioncount=java.lang:type=GarbageCollector,name=ConcurrentMarkSweep/CollectionCount;" + \
          "jvm.memory.heap.committed=java.lang:type=Memory/HeapMemoryUsage/committed;" + \
          "jvm.memory.heap.init=java.lang:type=Memory/HeapMemoryUsage/max;" + \
          "jvm.memory.heap.used=java.lang:type=Memory/HeapMemoryUsage/used;" + \
          "jvm.memory.nonheap.committed=java.lang:type=Memory/NonHeapMemoryUsage/committed;" + \
          "jvm.memory.nonheap.init=java.lang:type=Memory/NonHeapMemoryUsage/init;" + \
          "jvm.memory.nonheap.max=java.lang:type=Memory/NonHeapMemoryUsage/max;" + \
          "jvm.memory.nonheap.used=java.lang:type=Memory/NonHeapMemoryUsage/used;" + \
          "jvm.os.openfiledescriptorcount=java.lang:type=OperatingSystem/OpenFileDescriptorCount;" + \
          "jvm.os.maxfiledescriptorcount=java.lang:type=OperatingSystem/MaxFileDescriptorCount;" + \
          "jvm.os.committedvirtualmemorysize=java.lang:type=OperatingSystem/CommittedVirtualMemorySize;" + \
          "jvm.os.totalswapspacesize=java.lang:type=OperatingSystem/TotalSwapSpaceSize;" + \
          "jvm.os.freeswapspacesize=java.lang:type=OperatingSystem/FreeSwapSpaceSize;" + \
          "jvm.os.processcputime=java.lang:type=OperatingSystem/ProcessCpuTime;" + \
          "jvm.os.freephysicalmemorysize=java.lang:type=OperatingSystem/FreePhysicalMemorySize;" + \
          "jvm.os.totalphysicalmemorysize=java.lang:type=OperatingSystem/TotalPhysicalMemorySize;" + \
          "jvm.os.systemcpuload=java.lang:type=OperatingSystem/SystemCpuLoad;" + \
          "jvm.os.processcpuload=java.lang:type=OperatingSystem/ProcessCpuLoad;" + \
          "jvm.os.freephysicalmemorysize=java.lang:type=OperatingSystem/FreePhysicalMemorySize;" + \
          "jvm.os.totalphysicalmemorysize=java.lang:type=OperatingSystem/TotalPhysicalMemorySize;" + \
          "jvm.os.systemcpuload=java.lang:type=OperatingSystem/SystemCpuLoad;" + \
          "jvm.os.processcpuload=java.lang:type=OperatingSystem/ProcessCpuLoad;" + \
          "jvm.os.systemloadaverage=java.lang:type=OperatingSystem/SystemLoadAverage;" + \
          "jvm.runtime.uptime=java.lang:type=Runtime/Uptime;" + \
          "jvm.threading.threadcount=java.lang:type=Threading/ThreadCount;" + \
          "jvm.threading.peakthreadcount=java.lang:type=Threading/PeakThreadCount;" + \
          "jvm.threading.daemonthreadcount=java.lang:type=Threading/DaemonThreadCount;" + \
          "jvm.threading.totalstartedthreadcount=java.lang:type=Threading/TotalStartedThreadCount;"


def getMetrics():
    command = [JAVA_BIN, '-jar', '../embedded/lib/jmxquery.jar', '-url', JMX_URL, '-metrics', METRICS, '-json']
    if JMX_USERNAME:
        command.extend(['-username', JMX_USERNAME, '-password', JMX_PASSWORD])
    jsonOutput = ""

    try:
        jsonOutput = subprocess.check_output(command)
    except:
        print "Error connecting to JMX URL '" + JMX_URL + "'. Please check URL and that JMX is enabled on Java process"
        exit(2)

    metrics = json.loads(jsonOutput)

    # Print Nagios output
    output = "OK | "
    for metric in metrics:
        if 'value' in metric.keys():
            output += metric['metricName'] + "=" + metric['value'] + ";;;; "
    print output


getMetrics()
