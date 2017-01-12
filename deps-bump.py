#!/usr/bin/python

# Bump version dependencies in debian/control.

from debian import deb822

import re
import tempfile
import shutil
import os

import pymod2pkg

from lib.wrap_control import *
from lib.control_edit import *
from lib import version
from lib import ubuntu

def main():
    # Grab the most up to date requirements
    reqs = {}
    for filename in ['requirements.txt', 'test-requirements.txt']:
        with open(filename, 'r') as f:
            reqs.update(version.get_requirements(f.readlines()))

    # Sanitize the control file
    sanitize_control_file('./debian/control')

    # Open the control file
    src_pkg, bin_pkg_list, bin_pkg_map = parse_control('./debian/control')

    # Ubuntuize dependencies from requirements
    pkg_version_map = {}
    for k, v in reqs.iteritems():
        pkg = pymod2pkg.module2package(k, 'Ubuntu')
        if pkg in ubuntu.epochs:
            v = '%s:%s' % (ubuntu.epochs[pkg], v)
        pkg_version_map[pkg] = v
        pkg3 = pkg.replace('python','python3')
        pkg_version_map[pkg3] = v

    # Bump the build depends using the requirements dictionary
    if 'Build-Depends-Indep' in src_pkg:
        build_deps(src_pkg, 'Build-Depends-Indep', pkg_version_map)

    # Bump the binary dependencies
    for bin_pkg_name in bin_pkg_list:
        bin_pkg_to_change = bin_pkg_map[bin_pkg_name]
        if 'Depends' in bin_pkg_to_change:
            build_deps(bin_pkg_to_change, 'Depends', pkg_version_map)

    new_control_file = open('./debian/control', 'w')
    new_control_file.write(src_pkg.dump())
    for i in bin_pkg_list:
        new_control_file.write('\n')
        new_control_file.write(bin_pkg_map[i].dump())
    new_control_file.close()

def build_deps(package, relation, pkg_version_map):
    relation_structured = deb822.PkgRelation.parse_relations(package[relation])
    for i in range(len(relation_structured)):
        alternatives_list = relation_structured[i]
        for j in range(len(alternatives_list)):
            pkg_name = alternatives_list[j]['name']
            if pkg_name in pkg_version_map:
                alternatives_list[j]['version'] = ( '>=', pkg_version_map[pkg_name] )
    package[relation] = deb822.PkgRelation.str(relation_structured)
    wrap_field(package,relation,False,False,False)

if __name__ == '__main__':
    main()
