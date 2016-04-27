#!/usr/bin/env python
import psycopg2
import psycopg2.extras
import sys
from time import sleep

# settings
HOST = '/var/run/postgresql/'
PORT = '5432'
DB = ''
USER = ''
PASSWORD = ''


def query_post(curs, query):
    try:
        curs.execute(query)
        return curs.fetchall()
    except Exception as E:
        print "Failed to execute query: %s" % E
        sys.exit(2)

# blank metrics dictionary
pg_metrics = {}
pgdsn = "dbname=%s host=%s user=%s port=%s password=%s" % (DB, HOST, USER, PORT, PASSWORD)

# Open a connection to DB
try:
    db_conn = psycopg2.connect(pgdsn)
except Exception as E:
    print "Unable to connect to database: %s" %E
    sys.exit(2)

# Open a database cursor
db_curs = db_conn.cursor()


# single session state query avoids multiple scans of pg_stat_activity
# state is a different column name in postgres 9.2, previous versions will have to update this query accordingly
q_activity = 'select state, waiting, \
    extract(epoch from current_timestamp - xact_start)::int, \
    extract(epoch from current_timestamp - query_start)::int from pg_stat_activity;'
results = query_post(db_curs, q_activity)
active = 0
idle = 0
idleintxn = 0
waiting = 0
waitingtrue = 0
active_results = []
for state, waiting, xact_start_sec, query_start_sec in results:
    if state == 'active':
        active = int(active + 1)
        # build a list of query start times where query is active
        active_results.append(query_start_sec)
    if state == 'idle':
        idle = int(idle + 1)
    if state == 'idle in transaction':
        idleintxn = int(idleintxn + 1)
    if waiting == True:
        waitingtrue = int(waitingtrue + 1)

# determine longest transaction in seconds
sorted_by_xact = sorted(results, key=lambda tup: tup[2], reverse=True)
longest_xact_in_sec = (sorted_by_xact[0])[2]

# determine longest active query in seconds
sorted_by_query = sorted(active_results, reverse=True)
longest_query_in_sec = sorted_by_query[0]

pg_metrics.update(
    {'Pypg_idle_sessions':idle or 0,
     'Pypg_active_sessions':active or 0,
     'Pypg_waiting_sessions':waiting or 0,
     'Pypg_idle_in_transaction_sessions':idleintxn or 0,
     'Pypg_longest_xact':longest_xact_in_sec,
     'Pypg_longest_query':longest_query_in_sec})


# locks query
q_locks = 'select mode, locktype from pg_locks;'
results = query_post(db_curs, q_locks)
accessexclusive = 0
otherexclusive = 0
shared = 0
for mode, locktype in results:
    if (mode == 'AccessExclusiveLock' and locktype != 'virtualxid'):
        accessexclusive = int(accessexclusive + 1)
    if (mode != 'AccessExclusiveLock' and locktype != 'virtualxid'):
        if 'Exclusive' in mode:
            otherexclusive = int(otherexclusive + 1)
    if ('Share' in mode and locktype != 'virtualxid'):
        shared = int(shared + 1)
pg_metrics.update(
    {'Pypg_locks_accessexclusive':accessexclusive,
     'Pypg_locks_otherexclusive':otherexclusive,
     'Pypg_locks_shared':shared})

# background writer query returns one row that needs to be parsed
q_bgwriter = 'select checkpoints_timed, checkpoints_req, checkpoint_write_time, \
              checkpoint_sync_time, buffers_checkpoint, buffers_clean, \
              buffers_backend, buffers_alloc from pg_stat_bgwriter;'
results = query_post(db_curs, q_bgwriter)
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
    {'Pypg_bgwriter_checkpoints_timed':checkpoints_timed,
     'Pypg_bgwriter_checkpoints_req':checkpoints_req,
     'Pypg_bgwriter_checkpoint_write_time':checkpoint_write_time,
     'Pypg_bgwriter_checkpoint_sync_time':checkpoint_sync_time,
     'Pypg_bgwriter_buffers_checkpoint':buffers_checkpoint,
     'Pypg_bgwriter_buffers_clean':buffers_clean,
     'Pypg_bgwriter_buffers_backend':buffers_backend,
     'Pypg_bgwriter_buffers_alloc':buffers_alloc})


# database statistics returns one row that needs to be parsed
# 5 seconds between metrics for rate calculation

time_between = 5
q_stats = 'select (sum(xact_commit) + sum(xact_rollback)), sum(tup_inserted), \
           sum(tup_updated), sum(tup_deleted), (sum(tup_returned) + sum(tup_fetched)), \
           sum(blks_read), sum(blks_hit) from pg_stat_database;'
results_past = query_post(db_curs, q_stats)
sleep(time_between)
# clear the stats
db_curs.execute("select pg_stat_clear_snapshot();")
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

blksdisk = int(pg_stat_db_values[5] or 0)
blksdisk_per_sec = (blksdisk - int(pg_stat_past_db_values[5]) or 0) / time_between

blksmem = int(pg_stat_db_values[6] or 0)
blksmem_per_sec = (blksmem - int(pg_stat_past_db_values[6]) or 0) / time_between

pg_metrics.update(
    {'Pypg_transactions':transactions,
     'Pypg_transactions_per_sec':transactions_per_sec,
     'Pypg_inserts':inserts,
     'Pypg_inserts_per_sec':inserts_per_sec,
     'Pypg_updates':updates,
     'Pypg_updates_per_sec':updates_per_sec,
     'Pypg_deletes':deletes,
     'Pypg_deletes_per_sec':deletes_per_sec,
     'Pypg_reads':reads,
     'Pypg_reads_per_sec':reads_per_sec,
     'Pypg_blks_diskread':blksdisk,
     'Pypg_blks_diskread_per_sec':blksdisk_per_sec,
     'Pypg_blks_memread':blksmem,
     'Pypg_blks_memread_per_sec':blksmem_per_sec
    })

# table statistics returns one row that needs to be parsed
q_table_stats = 'select sum(seq_tup_read), sum(idx_tup_fetch), \
                 extract(epoch from now() - min(last_vacuum))::int/60/60, \
                 extract(epoch from now() - min(last_analyze))::int/60/60 \
                 from pg_stat_all_tables;'
results = query_post(db_curs, q_table_stats)
pg_stat_table_values = results[0]
seqscan = int(pg_stat_table_values[0] or 0)
idxfetch = int(pg_stat_table_values[1] or 0)
hours_since_vacuum = int(pg_stat_table_values[2]) if pg_stat_table_values[2] != None else -1
hours_since_analyze = int(pg_stat_table_values[3]) if pg_stat_table_values[3] != None else -1
pg_metrics.update(
    {'Pypg_tup_seqscan':seqscan,
     'Pypg_tup_idxfetch':idxfetch,
     'Pypg_hours_since_last_vacuum':hours_since_vacuum,
     'Pypg_hours_since_last_analyze':hours_since_analyze})

# close db cursor and connection
db_curs.close()

# print out all the metrics, nagios style
message = "OK | "
for metric, value in pg_metrics.iteritems():
    message += str(metric.lower()) + '=' + str(value) + ';;;; '

print message
sys.exit(0)
