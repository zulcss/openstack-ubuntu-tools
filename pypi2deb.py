#!/usr/bin/python

import requests
import optparse
import os
import tarfile
import stat
import xmlrpclib

import pymod2pkg
from jinja2 import Environment, FileSystemLoader

from lib import version
from lib import ubuntu
from lib import package as pypi

PACKAGE_EXCLUDES = [
    'pbr',
    'reno',
    'python-subunit'
]

def main():
    usage = 'usage: %prog [options]'
    parser = optparse.OptionParser(usage=usage)
    parser.add_option('-p', '--package', dest='package',
                      action='store', help='Projecct to convert to debian')
    parser.add_option('-s', '--source', dest='source_package',
                      action='store', help='Debian source package name.')
    parser.add_option('-v', '--version', dest='version',
                      action='store', help='version to use.')
    (opts, args) = parser.parse_args()

    if opts.package:
        to_package(opts)
    else:
        print "Specify a package to convert."

def to_package(opts):
    client = xmlrpclib.ServerProxy('https://pypi.python.org/pypi')
    if not opts.version:
        version = client.package_releases(opts.package)
    else:
        version = opts.version

    if opts.source_package:
        package = opts.source_package

    # Convert package version to Ubuntu
    ubuntu_version = "%s-0ubuntu1" % version[0]

    local_file = _download_file(client.release_urls(opts.package, version[0])[0]['url'])
    to_debian_tgz(local_file,  package, version[0])
    pkg_map = determine_dependencies(local_file, 
        ['requirements.txt', 'test-requirements.txt'])
    python_map = determine_dependencies(local_file,
        ['requirements.txt'])

    PATH = os.path.dirname(os.path.abspath(__file__))
    TEMPLATE_ENVIRONMENT = Environment(
        autoescape=False,
            loader=FileSystemLoader(os.path.join(PATH, 'templates')),
                trim_blocks=False)

    # Render the templates
    context = {
        'source_package': opts.source_package,
        'package': 'python-%s' % opts.package,
        'python3_package': 'python3-%s' % opts.package,
        'version': ubuntu_version,
        'maintainer': os.getenv('DEBEMAIL'),
        'deps': pkg_map,
        'python_deps': python_map,
        'python3_deps': python_map,
    }
    to_debian(local_file,
              render_template(TEMPLATE_ENVIRONMENT, 'changelog', context),
              'changelog')
    to_debian(local_file,
              render_template(TEMPLATE_ENVIRONMENT, 'control', context),
              'control')
    to_debian(local_file,
              render_template(TEMPLATE_ENVIRONMENT, 'rules', context),
              'rules')
    to_debian(local_file,
              render_template(TEMPLATE_ENVIRONMENT, 'watch', context),
              'watch')
    to_debian(local_file,
              render_template(TEMPLATE_ENVIRONMENT, 'copyright', context),
              'copyright')
    os.chmod(os.path.join(local_file.split('.tar.gz')[0], 
        'debian', 'rules'), 0775)

    # Create the source directory
    local_dir = local_file.split('.tar.gz')[0]
    source_dir = os.path.join(local_dir, 'debian', 'source')
    os.mkdir(source_dir)
    with open(os.path.join(source_dir, 'format'), 'w') as f:
        f.write('3.0 (quilt)\n')

    with open(os.path.join(source_dir, 'options'), 'w') as f:
        f.write('extend-diff-ignore = "^[^/]*[.]egg-info/"\n')

    with open(os.path.join(local_dir, 'debian', 'compat'), 'w') as f:
        f.write('10')

def to_debian(local_file, data, filename):
    local_dir = local_file.split('.tar.gz')[0]
    with open(os.path.join(local_dir, 'debian', filename), 'w') as f:
        f.write(data)

def render_template(template, template_filename, context):
    return template.get_template(template_filename).render(context)

def to_debian_tgz(local_file, package, version):
    debian_tarball = '%s_%s.orig.tar.gz' % (package, version)
    os.symlink(local_file, debian_tarball)
   
    tar = tarfile.open(local_file)
    tar.extractall()
    tar.close()

    local_file = local_file.split('.tar.gz')[0]
    os.mkdir(os.path.join(local_file, 'debian'))

    pkg = pypi.Package(package, version)

def determine_dependencies(local_file, requirements):
    # Generate the dependencies
    local_dir = local_file.split('.tar.gz')[0]
    reqs = {}

    for filename in requirements:
        req_path = os.path.join(local_dir, filename)
        with open(req_path, 'r') as f:
            reqs.update(version.get_requirements(f.readlines()))

    pkg_map = _convert_dependencies(reqs)
    pkgs = []
    for k, v in sorted(pkg_map.iteritems()):
        if k not in PACKAGE_EXCLUDES:
            pkg = ' %s (>= %s),' % (k, v)
            pkgs.append(pkg)
    return pkgs

def _to_python(packages):
    pkg = []
    for k in packages:
        if k.starswith('python-'):
            pkg.append(k)
    return pkg

def _to_python3(packages):
    pkg = []
    for k in packages:
        if k.starswith('python3-'):
            pkg.append(k)
    return pkg

def _convert_dependencies(packages):
    pkg_version_map = {}
    for k, v in packages.iteritems():
        if k not in PACKAGE_EXCLUDES:
            pkg = pymod2pkg.module2package(k, 'Ubuntu')
            if pkg in ubuntu.epochs:
                v = '%s:%s' % (ubuntu.epochs[pkg], v)
            pkg_version_map[pkg] = v
            pkg3 = pkg.replace('python','python3')
            pkg_version_map[pkg3] = v
    return pkg_version_map

def _download_file(url):
    local_filename = url.split('/')[-1]
    r = requests.get(url, stream=True)
    with open(local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024): 
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
    return local_filename

if __name__ == '__main__':
    main()
