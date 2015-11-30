#!/usr/bin/env python

import sys
import requests
import collections

"""
Hit up the cluster health url to get the cluster health
https://www.elastic.co/guide/en/elasticsearch/reference/current/cluster-health.html
then the stats url and pull back specific cluster_metrics for the cluster
https://www.elastic.co/guide/en/elasticsearch/reference/current/cluster-stats.html
"""

HOST = 'localhost'
PORT = 9200
BASE_URL = "http://%s:%s" % (HOST, PORT)
CLUSTER_HEALTH_URL = "/_cluster/health"
CLUSTER_STATS_URL = "/_cluster/stats"


cluster_metrics = [
            'indices.completion.size_in_bytes',
            'indices.count',
            'indices.docs.count',
            'indices.docs.deleted',
            'indices.fielddata.evictions',
            'indices.fielddata.memory_size_in_bytes',
            'indices.percolate.current',
            'indices.percolate.memory_size',
            'indices.percolate.memory_size_in_bytes',
            'indices.percolate.queries',
            'indices.percolate.time_in_millis',
            'indices.percolate.total',
            'indices.query_cache.cache_count',
            'indices.query_cache.cache_size',
            'indices.query_cache.evictions',
            'indices.query_cache.hit_count',
            'indices.query_cache.memory_size_in_bytes',
            'indices.query_cache.miss_count',
            'indices.query_cache.total_count',
            'indices.segments.count',
            'indices.segments.doc_values_memory_in_bytes',
            'indices.segments.fixed_bit_set_memory_in_bytes',
            'indices.segments.index_writer_max_memory_in_bytes',
            'indices.segments.index_writer_memory_in_bytes',
            'indices.segments.memory_in_bytes',
            'indices.segments.norms_memory_in_bytes',
            'indices.segments.stored_fields_memory_in_bytes',
            'indices.segments.term_vectors_memory_in_bytes',
            'indices.segments.terms_memory_in_bytes',
            'indices.segments.version_map_memory_in_bytes',
            'indices.shards.index.primaries.avg',
            'indices.shards.index.primaries.max',
            'indices.shards.index.primaries.min',
            'indices.shards.index.replication.avg',
            'indices.shards.index.replication.max',
            'indices.shards.index.replication.min',
            'indices.shards.index.shards.avg',
            'indices.shards.index.shards.max',
            'indices.shards.index.shards.min',
            'indices.shards.primaries',
            'indices.shards.replication',
            'indices.shards.total',
            'indices.store.size_in_bytes',
            'indices.store.throttle_time_in_millis',
            'nodes.count.total',
            'nodes.count.master_only',
            'nodes.count.data_only',
            'nodes.count.master_data',
            'nodes.count.client',
            'nodes.fs.available_in_bytes',
            'nodes.fs.free_in_bytes',
            # 'nodes.fs.spins',
            'nodes.fs.total_in_bytes',
            'nodes.jvm.max_uptime_in_millis',
            'nodes.jvm.mem.heap_max_in_bytes',
            'nodes.jvm.mem.heap_used_in_bytes',
            'nodes.jvm.threads',
            # 'nodes.jvm.versions',
            'nodes.os.allocated_processors',
            'nodes.os.available_processors',
            'nodes.os.mem.total_in_bytes',
            # 'nodes.os.names',
            # 'nodes.plugins',
            'nodes.process.cpu.percent',
            'nodes.process.open_file_descriptors.avg',
            'nodes.process.open_file_descriptors.max',
            'nodes.process.open_file_descriptors.min'
          ]


def _query_es(url):
    """ Get the node stats
    """
    data = requests.get(url)
    if data.status_code == 200:
        stats = data.json()
        return stats
    else:
        raise Exception("CRITICAL - Unable to return elasticsearch stats")


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
    cluster_health = flatten(_query_es(BASE_URL + CLUSTER_STATS_URL))

    cluster_stats = flatten(_query_es(BASE_URL + CLUSTER_HEALTH_URL))

    # define exit status based on the cluster health
    perf_data = "OK | "
    if cluster_health['status'] == 'green':
        exit_code = 0
        perf_data = "OK | "
    elif cluster_health['status'] == 'yellow':
        exit_code = 1
        perf_data = "WARNING | "
    elif cluster_health['status'] == 'red':
        exit_code = 2
        perf_data = "CRITICAL | "
    else:
        exit_code = 3
        perf_data = "UNKNOWN | "

    # Deal with the cluster health overview
    # Lazily remove non-numeric values
    for k, v in cluster_health.iteritems():
        if str(v)[0].isdigit():
            perf_data += str(k) + "=" + str(v) + ';;;; '

    # pull out the desired cluster_metrics and nothing more
    for path in cluster_metrics:
        # print path
        if path in cluster_stats:
            perf_data += "%s=%s;;;; " % (path, cluster_stats[path])

    print(perf_data)

except Exception as e:
    print("CRITICAL - Plugin Failed! Exception: " + str(e))
    sys.exit(2)

