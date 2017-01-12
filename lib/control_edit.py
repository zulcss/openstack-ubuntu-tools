# -*- coding: utf8 -*-

############################################################################
#   Copyright © 2015 José Manuel Santamaría Lema <panfaust@gmail.com>      #
#                                                                          #
#   This program is free software; you can redistribute it and/or modify   #
#   it under the terms of the GNU General Public License as published by   #
#   the Free Software Foundation; either version 2 of the License, or      #
#   (at your option) any later version.                                    #
############################################################################

from debian import deb822

import re
import tempfile
import shutil
import os

from lib.wrap_control import *

#Sanitizes a debian/control file so it won't trigger bugs from python-debian
#or wrap-and-sort, see, for instance:
# https://git.launchpad.net/~kubuntu-packagers/kubuntu-packaging/+git/cantor/commit/?id=7422c21f
# https://git.launchpad.net/~kubuntu-packagers/kubuntu-packaging/+git/cantor/commit/?id=a90b3e90
def sanitize_control_file(filename):
    orig_control_file = open(filename, 'r')
    new_control_fd, new_control_path = tempfile.mkstemp(text=True)
    new_control_file = os.fdopen(new_control_fd, 'w')
    for line in orig_control_file:
        #Replace lines containing only whitespaces or tabs with blank lines
        line = re.sub('^[ \t]*$', '', line)
        #Write the line to the new control file only if it's not a comment
        if re.match('^[ \t]*#', line) is None:
            new_control_file.write(line)
    #Close files
    orig_control_file.close()
    new_control_file.close()
    #Move and delete the temporary file
    shutil.copy(new_control_path, filename)
    os.remove(new_control_path)

#Parses a control file and returns a tuple(src_pkg,bin_pkg_list,bin_pkg_map) where
# * src_pkg is the deb822 paragraph object of the source package
# * bin_pkg_list is a list of the binary packages file listed in the same order
#   they appear in the control file
# * bin_pkg_map is a hash indexed by binary package name which returns the
#   corresponding deb822 paragraph object for each binary package
def parse_control(filename):
    control_file = deb822.Packages.iter_paragraphs(open(filename, 'r'));
    bin_pkg_list = []
    bin_pkg_map = {}
    for pkg in control_file:
        if 'Source' in pkg:
            src_pkg = pkg
        else:
            pkg_name = pkg['Package']
            bin_pkg_list.append(pkg_name)
            bin_pkg_map[pkg_name] = pkg
    control_file.close()
    return (src_pkg, bin_pkg_list, bin_pkg_map)

# Dumps the content of a control file.
def dump_control(filename,src_pkg,bin_pkg_list,bin_pkg_map):
    new_control_file = open(filename, "w")
    new_control_file.write(src_pkg.dump())
    for i in bin_pkg_list:
        new_control_file.write('\n')
        new_control_file.write(bin_pkg_map[i].dump())
    new_control_file.close()

#          Examples of deb822.PkgRelation.parse_relations() output
#
#          "emacs | emacsen, make, debianutils (>= 1.7)"     becomes
#          [ [ {'name': 'emacs'}, {'name': 'emacsen'} ],
#            [ {'name': 'make'} ],
#            [ {'name': 'debianutils', 'version': ('>=', '1.7')} ] ]
#
#          "tcl8.4-dev, procps [!hurd-i386]"                 becomes
#          [ [ {'name': 'tcl8.4-dev'} ],
#            [ {'name': 'procps', 'arch': (false, 'hurd-i386')} ] ]


def remove_from_relations( package, relation, target, wrap_relation=False, operator=None, version=None):
    if relation in package:
        relation_structured = deb822.PkgRelation.parse_relations(package[relation])
        list_to_delete = []
        for i in range(len(relation_structured)):
            alternatives_list = relation_structured[i]
            for j in range(len(alternatives_list)):
                if alternatives_list[j]['name'] == target:
                    relop, relversion = alternatives_list[j]['version']
                    if (operator == None) or (operator == relop):
                        if (version == None) or (version == relversion):
                            list_to_delete.append( (i,j) )
        for i, j in list_to_delete:
            del relation_structured[i][j]
        #Delete empty lists.
        relation_structured = filter(None, relation_structured)
        #Convert to string
        package[relation] = deb822.PkgRelation.str(relation_structured)
        #Delete the relation completely if it's empty.
        if package[relation].strip() == "":
            del package[relation]
        else:
            if wrap_relation:
                wrap_field(package,relation,False,False,False)

def add_to_relations( package, relation, target, wrap_relation=False):
    if relation in package:
        #Search the target in the relation.
        target_found = False
        relation_structured = deb822.PkgRelation.parse_relations(package[relation])
        for i in range(len(relation_structured)):
            alternatives_list = relation_structured[i]
            for j in range(len(alternatives_list)):
                if alternatives_list[j]['name'] == target:
                    target_found = True
                    break
        #If the target wasn't found, add it.
        if not target_found:
            package[relation] += ", " + target
    else:
        package[relation] = target
    if wrap_relation:
        wrap_field(package,relation,False,False,False)

def bump_version( package, relation, target, version, operator='>='):
    relation_structured = deb822.PkgRelation.parse_relations(package[relation])
    for i in range(len(relation_structured)):
        alternatives_list = relation_structured[i]
        for j in range(len(alternatives_list)):
            if alternatives_list[j]['name'] == target:
                alternatives_list[j]['version'] = ( operator, version )
    package[relation] = deb822.PkgRelation.str(relation_structured)
    wrap_field(package,relation,True,False,False)

def bump_version_with_map( package, relation, pkg_version_map ):
    relation_structured = deb822.PkgRelation.parse_relations(package[relation])
    for i in range(len(relation_structured)):
        alternatives_list = relation_structured[i]
        for j in range(len(alternatives_list)):
            pkg_name = alternatives_list[j]['name']
            if pkg_name in pkg_version_map:
                alternatives_list[j]['version'] = ( '>=', pkg_version_map[pkg_name] )
    package[relation] = deb822.PkgRelation.str(relation_structured)
    wrap_field(package,relation,False,False,False)

# vim: expandtab ts=4
