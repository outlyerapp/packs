#!/usr/bin/env python
import sys
import requests
import collections
import time

"""
Hit up the nodes stats url and pull back all the metrics for that node
TODO: clean up some of the kv pairs coming back and exclude the non-numeric
values (some come back as mb and have a byte equiv key
"""
HOST = 'localhost'
PORT = 9200
BASE_URL = "http://%s:%s" % (HOST, PORT)
LOCAL_URL = "/_nodes/_local"
HEALTH_URL = "/_cluster/health"
INTERVAL = 5

# Choose the elasticsearch stats to return
# Any of settings,os,process,jvm,thread_pool,network,transport,http,plugins
# OR leave empty for all statistics
STATS = ""
STATS_URL = "/_nodes/_local/stats/%s" % STATS
CLUSTER_STATS_URL = "/_cluster/stats"

def _get_es_stats(url):
    """ Get the node stats
    """
    data = requests.get(url)
    if data.status_code == 200:
        stats = data.json()
        return stats
    else:
        raise Exception("Cannot get Elasticsearch version")


def flatten(d, parent_key='', sep='.'):
    """ flatten a dictionary into a dotted string
    """
    items = []
    for key, value in d.items():
        new_key = parent_key + sep + key if parent_key else key
        if isinstance(value, collections.MutableMapping):
            items.extend(flatten(value, new_key, sep=sep).items())
        else:
            items.append((new_key, value))
    return dict(items)

try:
    es_health = flatten(_get_es_stats(BASE_URL + HEALTH_URL))
    cluster_stats = flatten(_get_es_stats(BASE_URL + CLUSTER_STATS_URL))

    # stats collected twice for rate calculation
    es_stats_before = flatten(_get_es_stats(BASE_URL + STATS_URL))
    time.sleep(INTERVAL)
    es_stats_after = flatten(_get_es_stats(BASE_URL + STATS_URL))

    perf_data = "OK | "
    es_stats = {}
    for k, v in es_stats_before.iteritems():
        if str(v)[0].isdigit():
            k = k.rsplit('.')[2::]
            es_stats['.'.join(k)] = v

        if 'query_total' in k:
            for k2, v2, in es_stats_after.iteritems():
                if 'query_total' in k2:
                    k2 = k2.rsplit('.')[2::]
                    k2[2] = 'queries_per_second'
                    es_stats['.'.join(k2)] = str((v2 - v) / INTERVAL)
                    k2[2] = 'query_total_diff'
                    es_stats['.'.join(k2)] = str((v2 - v))

        if 'index_total' in k:
            for k2, v2, in es_stats_after.iteritems():
                if 'index_total' in k2:
                    k2 = k2.rsplit('.')[2::]
                    k2[2] = 'index_per_second'
                    es_stats['.'.join(k2)] = str((v2 - v) / INTERVAL)
                    k2[2] = 'index_total_diff'
                    es_stats['.'.join(k2)] = str((v2 - v))

        if 'query_time_in_millis' in k:
            for k2, v2, in es_stats_after.iteritems():
                if 'query_time_in_millis' in k2:
                    k2 = k2.rsplit('.')[2::]
                    k2[2] = 'query_time_in_millis_diff'
                    es_stats['.'.join(k2)] = str((v2 - v))

        if 'index_time_in_millis' in k:
            for k2, v2, in es_stats_after.iteritems():
                if 'index_time_in_millis' in k2:
                    k2 = k2.rsplit('.')[2::]
                    k2[2] = 'index_time_in_millis_diff'
                    es_stats['.'.join(k2)] = str((v2 - v))

except Exception as e:
    print("Plugin Failed! Exception: " + str(e))
    sys.exit(2)


# calculate some additional metrics
try:
    es_stats['indices.search.query_time_avg_in_millis'] = round(float(es_stats['indices.search.query_time_in_millis_diff']) / float(es_stats['indices.search.query_total_diff']), 2)
except ZeroDivisionError, e:
    es_stats['indices.search.query_time_avg_in_millis'] = 0
except KeyError, e:
    pass

try:
    es_stats['indices.indexing.index_time_avg_in_millis'] = round(float(es_stats['indices.indexing.index_time_in_millis_diff']) / float(es_stats['indices.indexing.index_total_diff']), 2)
except ZeroDivisionError:
    es_stats['indices.indexing.index_time_avg_in_millis'] = 0
except KeyError, e:
    pass


for k, v in es_stats.iteritems():
    if str(v)[0].isdigit():
        perf_data += str(k) + "=" + str(v) + ';;;; '

for k, v in es_health.iteritems():
    if str(v)[0].isdigit():
        perf_data += str(k) + "=" + str(v) + ';;;; '

if es_health['status'] == 'green':
    exit_status = 0
elif es_health['status'] == 'yellow':
    exit_status = 1
elif es_health['status'] == 'red':
    exit_status = 2

for k, v in cluster_stats.iteritems():
    if str(v)[0].isdigit():
        perf_data += 'cluster.' + str(k) + "=" + str(v) + ';;;; '


print(perf_data)
sys.exit(exit_status)
