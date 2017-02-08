#!/usr/bin/env python
import sys
import time
from pymongo import MongoClient

HOST = 'localhost'
PORT = 27017
INTERVAL = 5
CONTAINER_ID= "devenv_mongo_1" # TODO pass in environment variable

def connect_host():
    client = MongoClient(HOST, PORT)
    return client.admin

def connect_container():

    # TODO: What is the best way to determine what container I am??
    import platform
    AGENT_CONTAINER_NAME = platform.node()

    import docker
    client = docker.from_env()
    target = client.containers.get(CONTAINER_ID)

    # print "CONTAINER", target.name
    # TODO: detect port
    # target_port = target.attrs["HostConfig"]["PortBindings"]["27017/tcp"][0]["HostPort"]
    # print target_port

    # TODO: join network before proceeding
    (name, network) = target.attrs["NetworkSettings"]["Networks"].items()[0]
    target_network = client.networks.get(name)
    me = client.containers.get(AGENT_CONTAINER_NAME)

    # TODO: Only attempt to connect when not already connected
    try:
        target_network.connect(me)
    except:
        pass

    # print "NETWORK", name
    ip = network["IPAddress"]
    # print "IP", ip
    client = MongoClient(ip, PORT)
    return client.admin

try:
    if CONTAINER_ID:
        db = connect_container()
    else:
        db = connect_host()
except Exception, e:
    print "Plugin Failed! %s" % e
    sys.exit(2)

def flatten(d, result=None):
    if result is None:
        result = {}
    for key in d:
        value = d[key]
        if isinstance(value, dict):
            value1 = {}
            for keyIn in value:
                value1[".".join([key,keyIn])]=value[keyIn]
            flatten(value1, result)
        elif isinstance(value, (list, tuple)):
            for indexB, element in enumerate(value):
                if isinstance(element, dict):
                    value1 = {}
                    index = 0
                    for keyIn in element:
                        newkey = ".".join([key,keyIn])
                        value1[".".join([key,keyIn])]=value[indexB][keyIn]
                        index += 1
                    for keyA in value1:
                        flatten(value1, result)
        else:
            result[key]=value
    return result


def merge_dicts(*dict_args):
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result


def is_digit(d):
    if isinstance(d, bool):
        return False
    elif isinstance(d, int) or isinstance(d, float):
        return True
    return False


def normalize(d):
    new_dict = {}
    for k, v in d.iteritems():
        if is_digit(v):
            k = k.lower()
            k = k.replace(' ', '_')
            k = k.replace(',', '')
            k = k.replace('/', '')
            k = k.replace('(', '')
            k = k.replace(')', '')
            new_dict[k] = v
    return new_dict

def collect_metrics():
    db_stats = db.command('dbstats')
    server_status = flatten(db.command('serverStatus'))
    try:
        repl_set_get_status = db.command('replSetGetStatus')
    except:
        repl_set_get_status = {}
    return normalize(merge_dicts(db_stats, server_status, repl_set_get_status))


first_run = collect_metrics()
time.sleep(INTERVAL)
second_run = collect_metrics()

metrics = {}
for k, v in second_run.iteritems():
    metrics[k] = first_run[k]
    rate = (second_run[k] - first_run[k]) / INTERVAL
    if 'opcounters' in k:
        metrics[k + '_per_sec'] = rate

output = "OK | "
for k, v in metrics.iteritems():
    output += str(k) + '=' + str(v) + ';;;; '
print output
sys.exit(0)
