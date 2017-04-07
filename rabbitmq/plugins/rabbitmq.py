#!/usr/bin/python
import sys
import requests
import StringIO
from urllib import quote

# Settings
HOST = "localhost"
USERNAME = "guest"
PASSWORD = "guest"
PORT = "15672"
PROTO = "http"

QUEUE_STATS = False
EXCHANGE_STATS = False
VERIFY_SSL = True


def request_data(path):
    if not VERIFY_SSL:
        requests.packages.urllib3.disable_warnings()
    return requests.get("%s://%s:%s%s" % (PROTO, HOST, PORT, path),
                        auth=(USERNAME, PASSWORD),
                        timeout=10,
                        verify=VERIFY_SSL).json()


def flatten(d, result=None):
    if result is None:
        result = {}
    for k in d:
        v = d[k]
        if isinstance(v, dict):
            value1 = {}
            for keyIn in v:
                value1[".".join([k, keyIn])] = v[keyIn]
            flatten(value1, result)
        elif isinstance(v, (list, tuple)):
            for indexB, element in enumerate(v):
                if isinstance(element, dict):
                    value1 = {}
                    index = 0
                    for keyIn in element:
                        new_key = ".".join([k, keyIn])
                        value1[new_key] = v[indexB][keyIn]
                        index += 1
                    for _ in value1:
                        flatten(value1, result)
        else:
            result[k] = v
    return result


def is_digit(d):
    if isinstance(d, bool):
        return False
    elif isinstance(d, int) or isinstance(d, float):
        return True
    return False


def prepend_dict(d, s):
    return dict(map(lambda (k, v): (s + str(k), v), d.items()))


def get_data(data, prefix):
    flattened_data = flatten(data)
    appended_data = prepend_dict(flattened_data, prefix)
    return appended_data


def get_overview():
    resp = request_data('/api/overview')
    return get_data(resp, 'overview.')


def get_queue_stats(vhost_name, queue_name):
    if vhost_name == '/':
        resp = request_data("/api/queues/%%2F/%s" % queue_name)
    else:
        resp = request_data("/api/queues/%s/%s" % (quote(vhost_name), queue_name))
    return get_data(resp, 'vhost.' + vhost_name + '.' + 'queue.' + queue_name + '.')


def get_exchange_stats(vhost_name, exchange_name):
    if vhost_name == '/':
        resp = request_data("/api/exchanges/%%2F/%s" % exchange_name)
    else:
        resp = request_data("/api/exchanges/%s/%s" % (quote(vhost_name), exchange_name))
    return get_data(resp, 'vhost.' + vhost_name + '.' + 'exchange.' + exchange_name + '.')


def get_vhosts():
    vhost_names = []
    resp = request_data("/api/vhosts")
    for v in resp:
        vhost_names.append(v['name'])
    return vhost_names


def get_queues(vhost_name):
    queue_names = []
    resp = request_data("/api/queues/%s" % vhost_name)
    for q in resp:
        queue_names.append(q['name'])
    return queue_names


def get_exchanges(vhost_name):
    exchange_names = []
    resp = request_data("/api/exchanges/%s" % vhost_name)
    for e in resp:
        exchange_names.append(e['name'])
    return exchange_names


def get_partitions(node):
    resp = request_data("/api/nodes/%s" % node)
    return len(resp['partitions'])


exit_code = 0
exit_message = "OK | "

try:
    # overview metrics
    metrics = {}
    metrics.update(get_overview())
    node_name = metrics['overview.node']
    if get_partitions(node_name) > 0:
        exit_code = 2
        exit_message = "CRITICAL - Rabbit cluster has a partition | "

    if QUEUE_STATS or EXCHANGE_STATS:
        vhosts = get_vhosts()

        # queue statistics
        if QUEUE_STATS:
            for vhost in vhosts:
                queues = get_queues(vhost)
                for queue in queues:
                    metrics.update(get_queue_stats(vhost, queue))

        # exchange statistics
        if EXCHANGE_STATS:
            for vhost in vhosts:
                exchanges = get_exchanges(vhost)
                for exchange in exchanges:
                    if exchange:
                        metrics.update(get_exchange_stats(vhost, exchange))

    # nagios format output
    buf = StringIO.StringIO()
    buf.write(exit_message)
    for key, value in metrics.iteritems():
        if is_digit(value):
            buf.write('{0}={1};;;; '.format(key, round(value, 2)))

    print buf.getvalue()
    sys.exit(exit_code)

except Exception as ex:
    print "CRITICAL - Plugin Failed! %s" % ex
    sys.exit(2)
