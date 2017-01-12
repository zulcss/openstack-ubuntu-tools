#!/usr/bin/python

# Demonstrates requirements.txt and test-requirements.txt parsing

import os
import sys

from lib import version

def main():
    tree = sys.argv[1]

    reqs ={}
    for filename in ['requirements.txt', 'test-requirements.txt']:
        with open(os.path.join(tree, filename), 'r') as f:
            reqs.update(version.get_requirements(f.readlines()))

    print reqs

if __name__ == '__main__':
    sys.exit(main())
