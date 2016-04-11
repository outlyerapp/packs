#!/usr/bin/env python
import requests
import sys


"""
This module requires the Wordpress Rest API V2 Module installed on your Wordpress Site to work. You can download
it here: http://v2.wp-api.org/
"""

# settings
HOST = ''          # e.g. https://blog.company.com


def _make_request(path):
    url = HOST + '/wp-json/wp/v2/' + path
    try:
        # Have to set header User-Agent to stop some web servers blocking request
        headers = {'User-Agent' : 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.101 Safari/537.36'}
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            print 'Unsuccessful Request for {0} - Response Code {1}: \n{2}'.format(url, resp.status_code, resp.text)
            sys.exit(2)
        return resp.json()
    except Exception, e:
        print 'Connection failed for {0}: {1}'.format(url, e)
        sys.exit(2)

totalUsers = len(_make_request('users'))
totalPages = len(_make_request('pages?per_page=100'))
totalPosts = len(_make_request('posts?per_page=100'))
totalComments = len(_make_request('comments?per_page=100'))

print 'OK | users=' + str(totalUsers) + ';;;; pages=' + str(totalPages) + ';;;; posts=' + str(totalPosts) + ';;;; comments=' + str(totalComments) + ';;;;'
sys.exit(0)