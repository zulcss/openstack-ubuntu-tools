#!/usr/bin/python

# Compare ubuntu version with what is in upper-constraints
# * master branch (default)
# curl -OJ http://git.openstack.org/cgit/openstack/requirements/plain/upper-constraints.txt?h=master
# * stable/newton
# curl -OJ http://git.openstack.org/cgit/openstack/requirements/plain/upper-constraints.txt?h=stable/newton

import pymod2pkg
from prettytable import PrettyTable
from launchpadlib.launchpad import Launchpad

EXCLUDED_PROJECTS = [
    'diskimage-builder',
    'os-apply-config',
    'os-cloud-config',
    'os-collect-config',
    'os-net-config',
    'os-refresh-config',
    'tripleo-common',
    'backports.ssl-match-hostname',
    'ndg-httpsclient',
    'packaging',
    'python-editor',
    'qpid-python',
    'restructuredtext-lint',
    'virtualenv',
    'xvfbwrapper',
]

UC = 'upper-constraints.txt'
def filter_openstack_projects(project):
    return project not in EXCLUDED_PROJECTS \
        and not project.startswith('XStatic')

def load_uc(projects_filter):
    uc = {}
    with open(UC, 'rb') as ucfiles:
        for line in ucfiles.readlines():
            name, version_spec = line.rstrip().split('===')
            if name and projects_filter(name):
                version = version_spec.split(';')[0]
                if version:
                    uc[name] = version
    return uc

def get_ubuntu_list(lp, package):
    ubuntu = lp.distributions['ubuntu']
        
    primary, partner = ubuntu.archives
    releases = ubuntu.getSeries(name_or_version='zesty')
                    
    try:
        upload_version = primary.getPublishedBinaries(exact_match=True, source_name=package, pocket="Release", distro_series=releases)[0].binary_package_version
    except:
        upload_version = "n/a"

    return upload_version
if __name__ == '__main__':
    uc = load_uc(filter_openstack_projects)

    x = PrettyTable(['Package', 'Debian', 'Upper Constraints', 'Ubuntu Version'])
    lp = Launchpad.login_with('openstack', service_root='production')

    for pkg, version in uc.iteritems():
        ubuntu = lp.distributions['ubuntu']
        primary, partner = ubuntu.archives
        releases = ubuntu.getSeries(name_or_version='zesty')
        package = pymod2pkg.module2package(pkg, 'ubuntu')
        x.add_row([pkg,
                  pymod2pkg.module2package(pkg, 'ubuntu'),
                  version,
                  get_ubuntu_list(lp, package)])

    print x
