#!/usr/bin/env python
import os
import subprocess
import sys
import json
from datetime import datetime

# configure these settings

MYSQL_USER = 'root'
MYSQL_PASSWORD = ''
MYSQL_HOST = ''

# metrics collection

TMPDIR = '/opt/dataloop/tmp'
TMPFILE = 'mysql.json'
TIMESTAMP = datetime.now().strftime('%s')
status = {}

# MySQL 5.7 changes stats for innodb memory consumption

innodb_mem = ['innodb_mem_adaptive_hash', 'innodb_mem_dictionary', 'innodb_buffer_pool_bytes_data']

# No need to calculate rates on these

no_rates = ['binlog_snapshot_file', 'binlog_snapshot_position', 'binlog_cache_disk_use', 'binlog_cache_use', 'binlog_stmt_cache_disk_use',
            'binlog_stmt_cache_use', 'compression', 'innodb_buffer_pool_dump_status', 'innodb_buffer_pool_load_status',
            'innodb_buffer_pool_pages_data', 'innodb_buffer_pool_bytes_data', 'innodb_buffer_pool_pages_dirty', 'innodb_buffer_pool_bytes_dirty',
            'innodb_buffer_pool_pages_free', 'innodb_buffer_pool_pages_misc', 'innodb_buffer_pool_pages_old', 'innodb_buffer_pool_pages_total',
            'innodb_buffer_pool_wait_free', 'innodb_checkpoint_age', 'innodb_checkpoint_max_age', 'innodb_have_atomic_builtins',
            'innodb_history_list_length', 'innodb_ibuf_free_list', 'innodb_ibuf_segment_size', 'innodb_ibuf_size', 'innodb_lsn_current',
            'innodb_lsn_flushed', 'innodb_lsn_last_checkpoint', 'innodb_master_thread_active_loops', 'innodb_master_thread_idle_loops',
            'innodb_max_trx_id', 'innodb_mem_adaptive_hash', 'innodb_mem_dictionary', 'innodb_mem_total', 'innodb_oldest_view_low_limit_trx_id',
            'innodb_page_size', 'innodb_purge_trx_id', 'innodb_purge_undo_no', 'innodb_row_lock_time', 'innodb_row_lock_time_avg',
            'innodb_row_lock_time_max', 'innodb_num_open_files', 'innodb_read_views_memory', 'innodb_descriptors_memory', 'innodb_available_undo_logs',
            'key_blocks_not_flushed', 'key_blocks_unused', 'key_blocks_used', 'last_query_cost', 'last_query_partial_plans', 'max_statement_time_exceeded',
            'max_statement_time_set', 'max_statement_time_set_failed', 'max_used_connections', 'not_flushed_delayed_rows', 'open_files', 'open_streams',
            'open_table_definitions', 'open_tables', 'opened_files', 'opened_table_definitions', 'opened_tables', 'prepared_stmt_count',
            'qcache_free_blocks', 'qcache_free_memory', 'qcache_not_cached', 'qcache_queries_in_cache', 'qcache_total_blocks', 'rsa_public_key',
            'slave_heartbeat_period', 'slave_last_heartbeat', 'slave_open_temp_tables', 'slave_received_heartbeats', 'slave_running', 'slow_launch_threads',
            'ssl_cipher', 'ssl_cipher_list', 'ssl_client_connects', 'ssl_ctx_verify_depth', 'ssl_ctx_verify_mode', 'ssl_default_timeout',
            'ssl_server_not_after', 'ssl_server_not_before', 'ssl_session_cache_mode', 'ssl_session_cache_size', 'ssl_used_session_cache_entries',
            'ssl_verify_depth', 'ssl_verify_mode', 'ssl_version', 'tc_log_max_pages_used', 'tc_log_page_size', 'threadpool_idle_threads',
            'threadpool_threads', 'threads_cached', 'threads_connected', 'threads_running', 'uptime', 'uptime_since_flush_status',
            'innodb_mem_adaptive_hash', 'innodb_mem_dictionary', 'innodb_buffer_pool_bytes_data']

# Calculate kb/mb/gb on these

byte_metrics = ['binlog_cache_disk_use', 'binlog_cache_use', 'binlog_stmt_cache_disk_use', 'binlog_stmt_cache_use',
                'bytes_received', 'bytes_sent', 'innodb_buffer_pool_bytes_data', 'innodb_buffer_pool_bytes_dirty',
                'innodb_buffer_pool_wait_free', 'innodb_data_written', 'innodb_mem_adaptive_hash', 'innodb_mem_dictionary',
                'innodb_mem_total', 'qcache_free_memory']


def is_int(input):
    try:
        num = int(input)
    except ValueError:
        return False
    return True


def is_float(input):
    try:
        num = float(input)
    except ValueError:
        return False
    return True


def get_mysql_status(version):
    command = ['/usr/bin/mysql', '-s', '-N']
    status['innodb_mem_total'] = 0
    if MYSQL_USER:
        command.append('-u%s' % MYSQL_USER)
    if MYSQL_PASSWORD:
        command.append('-p%s' % MYSQL_PASSWORD)
    if MYSQL_HOST:
        command.append('-h%s' % MYSQL_HOST)
    command += ['-e', 'show global status']
    try:
        resp = subprocess.check_output(command)
    except Exception, e:
        print "connection failure for show global status: %s" % e
        sys.exit(2)
    metric_list = resp.split('\n')
    metric_list.sort()
    for line in metric_list:
        if line:
            metric = line.split('\t')
            k = metric[0].strip().lower()
            k = k.replace('com_', '',1)
            v = metric[1]
            if is_int(v) or is_float(v):
                status[k] = v
            # MySQL 5.7 does not calculate total innodb mem usage for us
            if "5.7" in version:
                if k in innodb_mem:
                    status['innodb_mem_total'] = str(int(status['innodb_mem_total']) + int(v))
    return status

#
# Determine MySQL version
#


def get_version():
    instance_version = 0
    command = ['/usr/bin/mysql', '-N', '-s']
    if MYSQL_USER:
        command.append('-u%s' % MYSQL_USER)
    if MYSQL_PASSWORD:
        command.append('-p%s' % MYSQL_PASSWORD)
    if MYSQL_HOST:
        command.append('-h%s' % MYSQL_HOST)
    command += ['-e', "show global variables like 'version'"]
    try:
        resp = subprocess.check_output(command)
    except Exception, e:
        print "connection failure for show global versions: %s" % e
        sys.exit(2)

    metric_list = resp.split('\n')
    for line in metric_list:
        if line:
            metric = line.split('\t')
            instance_version = metric[1]
    return instance_version

#
# Convert Size Metrics from Bytes
#


def convert_sizes_from_bytes(k, v):
    if 'bytes' in k:
        kb = k.replace('bytes', 'kb')
        mb = k.replace('bytes', 'mb')
        gb = k.replace('bytes', 'gb')
    else:
        kb = k + '_kb'
        mb = k + '_mb'
        gb = k + '_gb'
    size_metrics[kb] = str(int(v) / 1024)
    size_metrics[mb] = str(int(v) / 1024 / 1024)
    size_metrics[gb] = str(int(v) / 1024 / 1024 / 1024)

#
# rate calculation
#


def tmp_file():
    if not os.path.isdir(TMPDIR):
        os.makedirs(TMPDIR)
    if not os.path.isfile(TMPDIR + '/' + TMPFILE):
        os.mknod(TMPDIR + '/' + TMPFILE)


def get_cache():
    with open(TMPDIR + '/' + TMPFILE, 'r') as json_fp:
        try:
            json_data = json.load(json_fp)
        except Exception, e:
            print "Not a valid json file. rates calculations impossible: %s" % e
            json_data = []
    return json_data


def write_cache(cache):
    with open(TMPDIR + '/' + TMPFILE, 'w') as json_fp:
        try:
            json.dump(cache, json_fp)
        except Exception, e:
            print "Unable to write cache file, future rates will be hard to calculate: %s" % e


def cleanse_cache(cache):
    try:
        while (int(TIMESTAMP) - int(cache[0]['timestamp'])) >= 3600:
            cache.pop(0)
        while len(cache) >= 120:
            cache.pop(0)
        return cache
    except:
        os.remove(TMPDIR + '/' + TMPFILE)


def delete_cache():
    try:
        os.remove(TMPDIR + '/' + TMPFILE)
    except Exception, e:
        print "failed to delete cache file: %s" % e


def calculate_rates(data_now, json_data, rateme):
    if len(json_data) > 1:
        try:
            history = json_data[0]
            if len(history) < 20:
                delete_cache()
            seconds_diff = int(TIMESTAMP) - int(history['timestamp'])
            rate_diff = float(data_now[rateme]) - float(history[rateme])
            data_per_second = "{0:.2f}".format(rate_diff / seconds_diff)
            return data_per_second
        except Exception, e:
            return None

tmp_file()
json_data = get_cache()

if len(json_data) > 0:
    json_data = cleanse_cache(json_data)

version = get_version()
result = get_mysql_status(version)

# Calculate kb/mb/gb for byte metrics

size_metrics = {}
for k, v in result.iteritems():
    if k in byte_metrics:
        convert_sizes_from_bytes(k, v)
result.update(size_metrics)

# Only calculate rates for metrics that have rates

all_rates = list(result.keys())
rates = list(set(all_rates) - set(no_rates))

for rate in rates:
    _ = calculate_rates(result, json_data, rate)
    if _ is not None:
        result[rate + "_per_sec"] = _


dated_result = result
dated_result['timestamp'] = TIMESTAMP
json_data.append(dated_result)
write_cache(json_data)

perf_data = "OK | "
for k, v in result.iteritems():
    try:
        _ = float(v)
        perf_data += "%s=%s;;;; " % (k, v)
    except ValueError:
        continue

print perf_data
sys.exit(0)