#!/usr/bin/env python

"""
    Java Plugin - Monitors Java process via JMX
"""

import subprocess
import json

# Path to Java home directory. If you want to use JVM discovery functions must point to a valid JDK with tools.jar embedded
# By default will just run as default java runtime, however '-list jvms' option will not work if this is not a JDK
JAVA_HOME = 'java'
# Set the JMX URL Endpoint to Connect To
JMX_URL = 'service:jmx:rmi:///jndi/rmi://localhost:9090/jmxrmi'

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
          "jvm.os.OpenFileDescriptorCount=java.lang:type=OperatingSystem/OpenFileDescriptorCount;" + \
          "jvm.os.MaxFileDescriptorCount=java.lang:type=OperatingSystem/MaxFileDescriptorCount;" + \
          "jvm.os.CommittedVirtualMemorySize=java.lang:type=OperatingSystem/CommittedVirtualMemorySize;" + \
          "jvm.os.TotalSwapSpaceSize=java.lang:type=OperatingSystem/TotalSwapSpaceSize;" + \
          "jvm.os.FreeSwapSpaceSize=java.lang:type=OperatingSystem/FreeSwapSpaceSize;" + \
          "jvm.os.ProcessCpuTime=java.lang:type=OperatingSystem/ProcessCpuTime;" + \
          "jvm.os.FreePhysicalMemorySize=java.lang:type=OperatingSystem/FreePhysicalMemorySize;" + \
          "jvm.os.TotalPhysicalMemorySize=java.lang:type=OperatingSystem/TotalPhysicalMemorySize;" + \
          "jvm.os.SystemCpuLoad=java.lang:type=OperatingSystem/SystemCpuLoad;" + \
          "jvm.os.ProcessCpuLoad=java.lang:type=OperatingSystem/ProcessCpuLoad;" + \
          "jvm.os.FreePhysicalMemorySize=java.lang:type=OperatingSystem/FreePhysicalMemorySize;" + \
          "jvm.os.TotalPhysicalMemorySize=java.lang:type=OperatingSystem/TotalPhysicalMemorySize;" + \
          "jvm.os.SystemCpuLoad=java.lang:type=OperatingSystem/SystemCpuLoad;" + \
          "jvm.os.ProcessCpuLoad=java.lang:type=OperatingSystem/ProcessCpuLoad;" + \
          "jvm.os.systemloadaverage=java.lang:type=OperatingSystem/SystemLoadAverage;" + \
          "jvm.runtime.uptime=java.lang:type=Runtime/Uptime;" + \
          "jvm.threading.threadcount=java.lang:type=Threading/ThreadCount;" + \
          "jvm.threading.peakthreadcount=java.lang:type=Threading/PeakThreadCount;" + \
          "jvm.threading.daemonthreadcount=java.lang:type=Threading/DaemonThreadCount;" + \
          "jvm.threading.totalstartedthreadcount=java.lang:type=Threading/TotalStartedThreadCount;"


def getMetrics():
    command = [JAVA_HOME, '-jar', '../embedded/lib/jmxquery.jar', '-url', JMX_URL, '-metrics', METRICS, '-json']
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
        output += metric['metricName'] + "=" + metric['value'] + ";;;; "
    print output


getMetrics()