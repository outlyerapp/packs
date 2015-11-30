#!/usr/bin/env python

import sys
import requests
import collections

"""
Hit up the local node's stats url
https://www.elastic.co/guide/en/elasticsearch/reference/current/cluster-nodes-stats.html
Any failure will give the health of the node
"""

HOST = 'localhost'
PORT = 9200
BASE_URL = "http://%s:%s" % (HOST, PORT)
NODE_STATS_URL = "/_nodes/_local/stats/"


cluster_metrics = [
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
            # hack out leading 'nodes.<nodename>
            new_key = '.'.join(new_key.split('.')[2::])
            items.append((new_key, value))
    return dict(items)


try:
    node_stats = flatten(_query_es(BASE_URL + NODE_STATS_URL))

    # exclude a pointless metric
    if 'timestamp' in node_stats.keys():
        node_stats.pop('timestamp', None)

    # define exit status based on the cluster health
    perf_data = "OK | "
    exit_code = 0

    # Deal with the node stats
    # Lazily remove non-numeric values
    for k, v in node_stats.iteritems():
        if isinstance(v, int) or isinstance(v, float):
            perf_data += str(k) + "=" + str(v) + ";;;; "

    print(perf_data)

except Exception as e:
    print("CRITICAL - Plugin Failed! Exception: " + str(e))
    sys.exit(2)

