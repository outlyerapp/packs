#!/usr/bin/env python
import sys
import subprocess
import psutil

required_processes = ['smtpd', 'qmgr']


# wrap getting the process name with exception handling
def get_proc_name(proc):
    try:
        return proc.name()
    except psutil.AccessDenied:
        # IGNORE: we don't have permission to access this process
        pass
    except psutil.NoSuchProcess:
        # IGNORE: process has died between listing and getting info
        pass
    except Exception, e:
        print "error accessing process info: %s" % e
    return None


# get all of the process counts
running_processes = {}
for p in psutil.process_iter():
    process_name = get_proc_name(p)
    process_memory = p.memory_percent()
    process_cpu = p.cpu_percent()
    if get_proc_name(p) in running_processes:
        running_processes[process_name] += 1
        if running_processes.has_key(process_name + '.mem'):
            running_processes[process_name + '.mem'] += process_memory
        if running_processes.has_key(process_name + '.cpu'):
            running_processes[process_name + '.cpu'] += process_cpu
    else:
        running_processes[process_name] = 1
        running_processes[process_name + '.mem'] = process_memory
        running_processes[process_name + '.cpu'] = process_cpu


# print the counts and exit correctly
output = ""
exit_status = 0
for process in required_processes:
    if process in running_processes:
        output += str(process) + '.count=' + str(running_processes[process]) + ';;;; ' + \
                  str(process) + '.mem_percent=' + str(round(running_processes[process + '.mem'], 2)) + '%;;;; ' + \
                  str(process) + '.cpu_percent=' + str(round(running_processes[process + '.cpu'], 2)) + '%;;;; '
    else:
        output += str(process) + '.count=0;;;; '
        exit_status = 2

if exit_status == 0:
    # get the current postfix queue size
    try:
        ps = subprocess.Popen('mailq', stdout=subprocess.PIPE)
        queue_id = '^[A-F0-9][A-F0-9][A-F0-9][A-F0-9][A-F0-9][A-F0-9][A-F0-9][A-F0-9][A-F0-9][A-F0-9]'
        queue_size = subprocess.check_output(('egrep', '-c', queue_id), stdin=ps.stdout)
        ps.wait()
        output += "queue_size=" + queue_size.strip() + ";;;;"
    except:
        pass
    print "OK | " + output
    sys.exit(0)
else:
    print "FAIL | " + output
    sys.exit(2)