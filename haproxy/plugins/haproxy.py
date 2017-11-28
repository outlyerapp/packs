#!/usr/bin/env python
import socket
import csv
import StringIO
import sys
import time

"""
Requirements:
Add the following line to haproxy.cfg under the global section (and restart haproxy):
stats socket /var/run/haproxy.sock user dataloop group root level operator
"""

HAPROXY_SOCK = "/var/run/haproxy.sock"
INTERVAL = 5

RATE_METRICS = [
    'stot', 'bin', 'bout', 'dreq', 'dresp', 'ereq', 'econ', 'eresp', 'wretr', 'wredis',
    'hrsp_1xx', 'hrsp_2xx', 'hrsp_3xx', 'hrsp_4xx', 'hrsp_5xx', 'hrsp_other',
    'req_tot', 'cli_abrt', 'srv_abrt', 'comp_in', 'comp_out', 'comp_byp', 'comp_rsp',
    ]

def get_stats():
    in_buf = StringIO.StringIO()
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.connect(HAPROXY_SOCK)
        s.send('show stat\n')
        while True:
            data = s.recv(4096)
            in_buf.write(data)
            if data == '':
                break
        s.close()
    except:
        print "CRITICAL | connection failure"
        sys.exit(2)

    stats = dict()

    in_buf.seek(0, 0)
    reader = csv.DictReader(in_buf)
    for row in reader:
        row.pop('')
        pxname = row.pop('# pxname')
        svname = row.pop('svname')
        row['status'] = status_code(row['status'])
        stats[(pxname, svname)] = row

    return stats


def status_code(status):
    if status == 'UP':
        return 0
    elif status == 'DOWN':
        return 1
    else:
        return 2


def calc_rates(s1, s2):
    delta = dict()
    rates = dict()
    for k, v in s2.iteritems():
        for k2, v2 in v.iteritems():
            try:
                delta.setdefault(k, dict())[k2] = float(s2[k][k2]) - float(s1[k][k2])
                rates.setdefault(k, dict())[k2] = delta[k][k2] * 60 / INTERVAL
            except ValueError:
                pass

    return delta, rates


stats1 = get_stats()
time.sleep(INTERVAL)
stats2 = get_stats()

out_buf = StringIO.StringIO()
delta, rates = calc_rates(stats1, stats2)
in_per_min = 0.0

for k in stats2.iterkeys():

    pxname, svname = k

    for k2, v2 in stats2[k].iteritems():
        try:
            out_buf.write('%s.%s.%s=%f;;;; ' % (pxname, svname, k2, float(v2)))
        except ValueError:
            pass

    for k2 in RATE_METRICS:
        try:
            out_buf.write('%s.%s.%s_delta=%f;;;; ' % (pxname, svname, k2, delta[k][k2]))
            out_buf.write('%s.%s.%s_per_min=%f;;;; ' % (pxname, svname, k2, rates[k][k2]))
            out_buf.write('%s.%s.%s_per_hr=%f;;;; ' % (pxname, svname, k2, rates[k][k2] * 60.0))
        except ValueError:
            pass
        except KeyError:
            pass

    pct = dict()
    if svname == 'FRONTEND':
        req_tot = delta[k]['req_tot']
        pct['dreq_pct'] = round(delta[k]['dreq'] / req_tot * 100.0, 2) if req_tot else 0.0
        pct['ereq_pct'] = round(delta[k]['ereq'] / req_tot * 100.0, 2) if req_tot else 0.0
        pct['hrsp_2xx_pct'] = round(delta[k]['hrsp_2xx'] / req_tot * 100.0, 2) if req_tot else 0.0
        pct['hrsp_3xx_pct'] = round(delta[k]['hrsp_3xx'] / req_tot * 100.0, 2) if req_tot else 0.0
        pct['hrsp_4xx_pct'] = round(delta[k]['hrsp_4xx'] / req_tot * 100.0, 2) if req_tot else 0.0
        pct['hrsp_5xx_pct'] = round(delta[k]['hrsp_5xx'] / req_tot * 100.0, 2) if req_tot else 0.0
        pct['hrsp_other_pct'] = round(delta[k]['hrsp_other'] / req_tot * 100.0, 2) if req_tot else 0.0
        pct['failed_pct'] = pct['ereq_pct'] + pct['hrsp_4xx_pct'] + pct['hrsp_5xx_pct']
        in_per_min += rates[k]['req_tot']
    elif svname == 'BACKEND':
        stot = float(delta[k]['stot'])
        pct['econ_pct'] = round(delta[k]['econ'] / stot * 100.0, 2) if stot else 0.0
        pct['eresp_pct'] = round(delta[k]['eresp'] / stot * 100.0, 2) if stot else 0.0
        pct['failed_pct'] = pct['eresp_pct'] + pct['econ_pct']

    for k, v in pct.iteritems():
            out_buf.write('%s.%s.%s=%f;;;; ' % (pxname, svname, k, pct[k]))

out_buf.write('requests_per_min=%f;;;; ' % in_per_min)
out_buf.write('requests_per_hr=%f;;;; ' % (in_per_min * 60.0))

print 'OK |', out_buf.getvalue()
sys.exit(0)
