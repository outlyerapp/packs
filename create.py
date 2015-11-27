#!/usr/bin/env python
import os
import sys
import errno


def make_node(node):
    try:
        os.makedirs(node)
    except OSError, e:
        if e.errno != errno.EEXIST:
            raise


def create_node(f, times=None):
    with open(f, 'a'):
        os.utime(f, times)


def create_tree(h, c):
    for dir, files in c.iteritems():
        parent = os.path.join(h, dir)
        make_node(parent)
        children = c[dir]
        for child in children:
            child = os.path.join(parent, child)
            create_node(child)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "Please specify a pack name"
        sys.exit(2)

    pack_name = sys.argv[1]
    home = os.path.join(os.getcwd(), pack_name)
    create_tree(home, {})

    content = {
        'plugins': [pack_name + '.py'],
        'dashboards': [pack_name + '.yaml'],
        'rules': [pack_name + '.yaml']
    }

    create_tree(home, content)

