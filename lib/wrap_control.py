# Copyright (C) 2010-2014, Benjamin Drung <bdrung@debian.org>
#               2010, Stefano Rivera <stefanor@ubuntu.com>
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.


import re

# This code was copied from wrap-and-sort, it's helpful when converting a
# package relation from the structured deb822.PkgRelation to string, because
# deb822.PkgRelation.str(relation_structured) returns a string in a single line
# so it's nice to get it in the wrap-and-sort-like format again

def sort_list(unsorted_list):
    packages = [x for x in unsorted_list if re.match("[a-z0-9]", x)]
    special = [x for x in unsorted_list if not re.match("[a-z0-9]", x)]
    return sorted(packages) + sorted(special)

def wrap_field(control, entry, wrap_always, short_indent,
                    trailing_comma, sort=True):
        max_line_length = 79 #wrap-and-sort current default
        packages = [x.strip() for x in control[entry].split(",")]

        # Sanitize alternative packages. E.g. "a|b  |c" -> "a | b | c"
        packages = [" | ".join([x.strip() for x in p.split("|")]) for p in packages]

        if sort:
            # Remove duplicate entries
            packages = set(packages)
            # Not explicitly disallowed by Policy but known to break QA tools:
            if "" in packages:
                packages.remove("")
            packages = sort_list(packages)

        length = len(entry) + sum([2 + len(package) for package in packages])
        if wrap_always or length > max_line_length:
            indentation = " "
            if not short_indent:
                indentation *= len(entry) + 2
            packages_with_indention = [indentation + x for x in packages]
            packages_with_indention = ",\n".join(packages_with_indention)
            if trailing_comma:
                packages_with_indention += ','
            if short_indent:
                control[entry] = "\n" + packages_with_indention
            else:
                control[entry] = packages_with_indention.strip()
        else:
            control[entry] = ", ".join(packages).strip()

# vim: expandtab ts=4
