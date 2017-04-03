#!/usr/bin/env python
import sys
import re
import StringIO
import psycopg2
import psycopg2.extras
from time import sleep

# settings
HOST = '172.18.0.19'
PORT = 5432
DB = 'postgres'
USER = 'postgres'
PASSWORD = 'password'


def query_post(curs, query):
    try:
        curs.execute(query)
        return curs.fetchall()
    except Exception as E:
        print "Failed to execute query: %s" % E
        sys.exit(2)


def get_pg_version(curs):
    result = query_post(curs, "select version()")[0][0]
    ver_match = re.match(r'^PostgreSQL (?P<ver>\d+\.\d+)', result)
    return float(ver_match.group('ver'))


# blank metrics dictionary
pg_metrics = {}
pg_dsn = "dbname=%s host=%s user=%s port=%s password=%s" % (DB, HOST, USER, PORT, PASSWORD)

# Open a connection to DB
try:
    db_conn = psycopg2.connect(pg_dsn)
except Exception as ex:
    print "Unable to connect to database: %s" % ex
    sys.exit(2)

# Open a database cursor
db_curs = db_conn.cursor()
pg_ver = get_pg_version(db_curs)

# single session state query avoids multiple scans of pg_stat_activity
# state is a different column name in postgres 9.2, previous versions will have to update this query accordingly
if pg_ver >= 9.6:
    # noinspection SqlResolve
    q_activity = '''
    SELECT state, (CASE wait_event WHEN NULL THEN FALSE ELSE TRUE END) AS waiting,
        extract(EPOCH FROM current_timestamp - xact_start)::INT,
        extract(EPOCH FROM current_timestamp - query_start)::INT 
    FROM pg_stat_activity
    '''
else:
    # noinspection SqlResolve
    q_activity = '''
    SELECT state, waiting, 
        extract(EPOCH FROM current_timestamp - xact_start)::INT, 
        extract(EPOCH FROM current_timestamp - query_start)::INT 
    FROM pg_stat_activity
    '''

results = query_post(db_curs, q_activity)
active_count = 0
idle_count = 0
idle_in_txn_count = 0
waiting_count = 0
active_results = []
for state, waiting, xact_start_sec, query_start_sec in results:
    if state == 'active':
        active_count = int(active_count + 1)
        # build a list of query start times where query is active
        active_results.append(query_start_sec)
    if state == 'idle':
        idle_count = int(idle_count + 1)
    if state == 'idle in transaction':
        idle_in_txn_count = int(idle_in_txn_count + 1)
    if waiting:
        waiting_count = int(waiting_count + 1)

# determine longest transaction in seconds
sorted_by_xact = sorted(results, key=lambda tup: tup[2], reverse=True)
longest_xact_in_sec = (sorted_by_xact[0])[2]

# determine longest active query in seconds
sorted_by_query = sorted(active_results, reverse=True)
longest_query_in_sec = sorted_by_query[0]

pg_metrics.update(
    {'pypg_idle_sessions': idle_count or 0,
     'pypg_active_sessions': active_count or 0,
     'pypg_waiting_sessions': waiting_count or 0,
     'pypg_idle_in_transaction_sessions': idle_in_txn_count or 0,
     'pypg_longest_xact': longest_xact_in_sec,
     'pypg_longest_query': longest_query_in_sec})

# locks query
# noinspection SqlResolve
q_locks = 'SELECT mode, locktype FROM pg_locks'
results = query_post(db_curs, q_locks)

access_exclusive = 0
other_exclusive = 0
shared = 0
for mode, lock_type in results:
    if mode == 'AccessExclusiveLock' and lock_type != 'virtualxid':
        access_exclusive = int(access_exclusive + 1)
    if mode != 'AccessExclusiveLock' and lock_type != 'virtualxid':
        if 'Exclusive' in mode:
            other_exclusive = int(other_exclusive + 1)
    if 'Share' in mode and lock_type != 'virtualxid':
        shared = int(shared + 1)
pg_metrics.update(
    {'pypg_locks_accessexclusive': access_exclusive,
     'pypg_locks_otherexclusive': other_exclusive,
     'pypg_locks_shared': shared})

# background writer query returns one row that needs to be parsed
# noinspection SqlResolve
q_bg_writer = '''
  SELECT checkpoints_timed, checkpoints_req, checkpoint_write_time, 
         checkpoint_sync_time, buffers_checkpoint, buffers_clean, 
         buffers_backend, buffers_alloc 
  FROM pg_stat_bgwriter
  '''
results = query_post(db_curs, q_bg_writer)
bgwriter_values = results[0]
checkpoints_timed = int(bgwriter_values[0] or 0)
checkpoints_req = int(bgwriter_values[1] or 0)
checkpoint_write_time = int(bgwriter_values[2] or 0)
checkpoint_sync_time = int(bgwriter_values[3] or 0)
buffers_checkpoint = int(bgwriter_values[4] or 0)
buffers_clean = int(bgwriter_values[5] or 0)
buffers_backend = int(bgwriter_values[6] or 0)
buffers_alloc = int(bgwriter_values[7] or 0)
pg_metrics.update(
    {'pypg_bgwriter_checkpoints_timed': checkpoints_timed,
     'pypg_bgwriter_checkpoints_req': checkpoints_req,
     'pypg_bgwriter_checkpoint_write_time': checkpoint_write_time,
     'pypg_bgwriter_checkpoint_sync_time': checkpoint_sync_time,
     'pypg_bgwriter_buffers_checkpoint': buffers_checkpoint,
     'pypg_bgwriter_buffers_clean': buffers_clean,
     'pypg_bgwriter_buffers_backend': buffers_backend,
     'pypg_bgwriter_buffers_alloc': buffers_alloc})

# database statistics returns one row that needs to be parsed
# 5 seconds between metrics for rate calculation
time_between = 5

# noinspection SqlResolve
q_stats = '''
    SELECT (sum(xact_commit) + sum(xact_rollback)), sum(tup_inserted), 
           sum(tup_updated), sum(tup_deleted), (sum(tup_returned) + sum(tup_fetched)), 
           sum(blks_read), sum(blks_hit) 
    FROM pg_stat_database
    '''
results_past = query_post(db_curs, q_stats)
sleep(time_between)
# clear the stats
db_curs.execute("select pg_stat_clear_snapshot()")
results_present = query_post(db_curs, q_stats)

pg_stat_past_db_values = results_past[0]
pg_stat_db_values = results_present[0]

transactions = int(pg_stat_db_values[0] or 0)
transactions_per_sec = (transactions - int(pg_stat_past_db_values[0]) or 0) / time_between

inserts = int(pg_stat_db_values[1] or 0)
inserts_per_sec = (inserts - int(pg_stat_past_db_values[1]) or 0) / time_between

updates = int(pg_stat_db_values[2] or 0)
updates_per_sec = (updates - int(pg_stat_past_db_values[2]) or 0) / time_between

deletes = int(pg_stat_db_values[3] or 0)
deletes_per_sec = (deletes - int(pg_stat_past_db_values[3]) or 0) / time_between

reads = int(pg_stat_db_values[4] or 0)
reads_per_sec = (reads - int(pg_stat_past_db_values[4]) or 0) / time_between

disk_blocks = int(pg_stat_db_values[5] or 0)
disk_blocks_per_sec = (disk_blocks - int(pg_stat_past_db_values[5]) or 0) / time_between

mem_blocks = int(pg_stat_db_values[6] or 0)
mem_blocks_per_sec = (mem_blocks - int(pg_stat_past_db_values[6]) or 0) / time_between

pg_metrics.update(
    {'pypg_transactions': transactions,
     'pypg_inserts': inserts,
     'pypg_updates': updates,
     'pypg_deletes': deletes,
     'pypg_reads': reads,
     'pypg_blks_diskread': disk_blocks,
     'pypg_blks_memread': mem_blocks,
     'pypg_transactions_per_sec': transactions_per_sec,
     'pypg_inserts_per_sec': inserts_per_sec,
     'pypg_updates_per_sec': updates_per_sec,
     'pypg_deletes_per_sec': deletes_per_sec,
     'pypg_reads_per_sec': reads_per_sec,
     'pypg_blks_diskread_per_sec': disk_blocks_per_sec,
     'pypg_blks_memread_per_sec': mem_blocks_per_sec
     })

# table statistics returns one row that needs to be parsed
# noinspection SqlResolve
q_table_stats = '''
    SELECT sum(seq_tup_read), sum(idx_tup_fetch), 
           extract(EPOCH FROM now() - min(last_vacuum))::INT/60/60, 
           extract(EPOCH FROM now() - min(last_analyze))::INT/60/60 
    FROM pg_stat_all_tables
    '''
results = query_post(db_curs, q_table_stats)
pg_stat_table_values = results[0]
seqscan = int(pg_stat_table_values[0] or 0)
idxfetch = int(pg_stat_table_values[1] or 0)
hours_since_vacuum = int(pg_stat_table_values[2]) if pg_stat_table_values[2] else -1
hours_since_analyze = int(pg_stat_table_values[3]) if pg_stat_table_values[3] else -1
pg_metrics.update(
    {'pypg_tup_seqscan': seqscan,
     'pypg_tup_idxfetch': idxfetch,
     'pypg_hours_since_last_vacuum': hours_since_vacuum,
     'pypg_hours_since_last_analyze': hours_since_analyze})

# close db cursor and connection
db_curs.close()

# print out all the metrics, nagios style
buf = StringIO.StringIO()
buf.write('OK | ')
for metric, value in pg_metrics.iteritems():
    buf.write('{0}={1};;;; '.format(metric.lower(), value))

print buf.getvalue()
sys.exit(0)
