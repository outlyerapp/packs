#!/usr/bin/env python
import os
import sys
import time
import re
import psutil
import subprocess
import datetime
import StringIO

RATE_INTERVAL = 5


def _bytes_to_gb(num):
    return round(float(num) / 1024 / 1024 / 1024, 2)


def _get_counter_increment(before, after):
    value = after - before
    if value >= 0:
        return value
    for boundary in [1 << 16, 1 << 32, 1 << 64]:
        if (value + boundary) > 0:
            return value + boundary


def _string_to_float(num):
    non_decimal = re.compile(r'[^\d.]+')
    return round(float(non_decimal.sub('', num)), 2)


def exact_match(phrase, word):
    b = r'(\s|^|$)'
    res = re.match(b + word + b, phrase, flags=re.IGNORECASE)
    return bool(res)


def calculate_rate(present, past):
    try:
        return round((float(present) - float(past)) / RATE_INTERVAL, 2)
    except TypeError:
        return round((_string_to_float(present) - _string_to_float(past)) / RATE_INTERVAL, 2)


def check_disks():
    disk_usage = {}
    counters = {}
    max_usage = 0
    for partition in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            max_usage = max(max_usage, usage.percent)
            disk = re.sub(" ", "_", partition.mountpoint).replace(':', '').replace('\\', '').lower()
            if os.name == 'nt':
                counters[disk] = "LogicalDisk(%s)\Current Disk Queue Length" % partition.device.replace('\\', '')
            if 'cdrom' in partition.opts or partition.fstype == '':
                continue
            if 'Volumes' in partition.mountpoint:
                continue
            if 'libc.so' in partition.mountpoint:
                continue
            disk_usage.update({
                'disk.%s.percent_used' % disk: "%d%%" % int(usage.percent),
                'disk.%s.percent_free' % disk: "%d%%" % int(100 - usage.percent),
                'disk.%s.free' % disk: "%db" % usage.free,
                'disk.%s.used' % disk: "%db" % usage.used,
                'disk.%s.total' % disk: "%db" % usage.total,
                'disk.%s.free_gb' % disk: "%sGb" % _bytes_to_gb(usage.free),
                'disk.%s.used_gb' % disk: "%sGb" % _bytes_to_gb(usage.used),
                'disk.%s.total_gb' % disk: "%sGb" % _bytes_to_gb(usage.total)
            })

        except OSError:
            continue

    if os.name == 'nt':
        command = ['typeperf.exe', '-sc', '1']
        counters_list = counters.values()
        p = psutil.Popen(command + counters_list, stdout=subprocess.PIPE)
        output = p.communicate()[0]
        i = 1
        for disk, counter in counters.iteritems():
            value = output.splitlines()[2].split(',')[i].replace('"', '').strip()
            disk_usage['disk.%s.current_disk_queue_length' % disk] = round(float(value), 2)
            i += 1

    disk_usage.update({
        'disk.max_percent_used': max_usage
    })
    return disk_usage


def check_memory():
    return {
        'memory': "%d%%" % int(psutil.virtual_memory().percent),
        'swap': "%d%%" % int(psutil.swap_memory().percent)
    }


def check_swap_rates():
    return {
        'swap_in': psutil.swap_memory().sin,
        'swap_out': psutil.swap_memory().sout
    }


def check_cpu():
    return {
        'cpu': "%d%%" % int(psutil.cpu_percent(interval=5))
    }


def check_load():
    cores = psutil.cpu_count()
    load_avg = {'load_1_min': 0}
    if os.name != 'nt':
        load = os.getloadavg()
        load_avg.update({
            'load_1_min': load[0],
            'load_5_min': load[1],
            'load_15_min': load[2]
        })

    load_avg['load_fractional'] = round(float(load_avg['load_1_min']) / int(cores), 2)
    return load_avg


def check_netio():
    # total net counters
    net_all = psutil.net_io_counters()._asdict()
    net_map = {'network.%s' % k: v for k, v in net_all.iteritems()}

    # per net io counters
    net_per_nic = psutil.net_io_counters(pernic=True)
    for device, details in net_per_nic.iteritems():
        net_excludes = ['teredo', 'isatap', 'loopback']
        if not any(x in device.lower() for x in net_excludes):
            dev_name = device.replace(' ', '_').lower()
            for k, v in net_per_nic[device]._asdict().iteritems():
                net_map["network.%s.%s" % (dev_name, k)] = v

    return net_map


def check_cputime():
    # total cpu counters
    cputime_all = psutil.cpu_times_percent()._asdict()
    cpu_map = {'cpu.%s' % k: v for k, v in cputime_all.iteritems()}

    # per cpu counters
    cputime_per_cpu = psutil.cpu_times_percent(percpu=True)
    for i in range(len(cputime_per_cpu)):
        cpu_map.update({'cpu.%s.%s' % (i, k): v for k, v in cputime_per_cpu[i]._asdict().iteritems()})
    cpu_map['cpu.cores'] = psutil.cpu_count(logical=True)

    # get the cpu speed on linux
    if sys.platform == 'linux2':
        with open('/proc/cpuinfo', 'r') as f:
            for line in f:
                if "model name" in line:
                    speed = re.sub(".*model name.*:", "", line, 1).split(' ')[-1]
                    cpu_map['cpu.speed'] = speed.strip()

    return cpu_map


def check_diskio():
    dm = False
    disk_map = {}
    try:
        # total io counters
        diskio_all = psutil.disk_io_counters()
        for k, v in diskio_all._asdict().iteritems():
            disk_map["disk.%s" % k] = v

        # per disk io counters
        diskio_per_disk = psutil.disk_io_counters(perdisk=True)
        for device, details in diskio_per_disk.iteritems():
            for k, v in diskio_per_disk[device]._asdict().iteritems():
                disk_map["disk.%s.%s" % (device.lower(), k)] = v

        # check for any device mapper partitions
        for partition in psutil.disk_partitions():
            if 'mapper' in os.listdir('/dev'):
                dm = True

        # per device mapper friendly name io counters
        if dm:
            device_mapper = {}
            for name in os.listdir('/dev/mapper'):
                path = os.path.join('/dev/mapper', name)
                if os.path.islink(path):
                    device_mapper[os.readlink(os.path.join('/dev/mapper', name)).replace('../', '')] = name
            for device, details in diskio_per_disk.iteritems():
                for k, v in diskio_per_disk[device]._asdict().iteritems():
                    if device in device_mapper:
                        disk_map["disk.%s.%s" % (device_mapper[device], k)] = v

        return disk_map
    except RuntimeError:  # Windows needs disk stats turned on with 'diskperf -y'
        return disk_map


def check_virtmem():
    virtmem = psutil.virtual_memory()._asdict()
    virt_map = {'vmem.%s' % k: v for k, v in virtmem.iteritems()}
    virt_map.update({
        'vmem.total_gb': "%sGb" % _bytes_to_gb(virtmem['total']),
        'vmem.available_gb': "%sGb" % _bytes_to_gb(virtmem['available']),
        'vmem.used_gb': "%sGb" % _bytes_to_gb(virtmem['used'])
    })

    return virt_map


def check_uptime():
    boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
    now_time = datetime.datetime.now()
    uptime = now_time - boot_time
    uptime_hours = (uptime.days * 24) + (uptime.seconds // 3600)
    return {'uptime.hours': uptime_hours}


def check_processes():
    process_map = {
        'processes.total': len(psutil.pids()),
        'processes.zombie': sum([1 for proc in psutil.process_iter() if proc.status() == psutil.STATUS_ZOMBIE])
    }
    return process_map


checks = [
    check_disks,
    check_cpu,
    check_memory,
    check_swap_rates,
    check_load,
    check_cputime,
    check_netio,
    check_diskio,
    check_virtmem,
    check_processes,
    check_uptime
]

rates = [
    check_swap_rates,
    check_diskio,
    check_netio
]

past_output = {}
for check in checks:
    past_output.update(check())

time.sleep(RATE_INTERVAL)

present_output = {}
for check in rates:
    present_output.update(check())

raw_output = {}
for present_key, present_value in present_output.iteritems():
    if present_key in past_output:
        if 'per_sec' not in present_key:
            raw_output[present_key + '_per_sec'] = calculate_rate(present_value, past_output[present_key])

        if exact_match(present_key, 'network.bytes_sent'):
            raw_output['net_upload'] = str((_get_counter_increment(past_output[present_key], present_value)
                                            / 1024) / RATE_INTERVAL) + 'Kps'

        if exact_match(present_key, 'network.bytes_recv'):
            raw_output['net_download'] = str((_get_counter_increment(past_output[present_key], present_value)
                                              / 1024) / RATE_INTERVAL) + 'Kps'

raw_output.update(past_output)

buf = StringIO.StringIO()
buf.write('OK | ')
for key, val in raw_output.iteritems():
    buf.write('%s=%s;;;; ' % (key.lower(), val))
buf.write('count=1;;;; ')
buf.write('metrics=%d;;;; ' % len(raw_output.keys()))
buf.write('interval=%d;;;; ' % RATE_INTERVAL)
print buf.getvalue()

sys.exit(0)

