import os
from setuptools import setup, find_packages


def readme():
    """
    Returns contents of README.md

    @return - String

    """
    with open('README.md') as f:
        return f.read()


def find_data_files(starting_path, prefix):
    """
    Traverses the directory starting at starting path
    finding all subdirectories and files.  Useful when
    building complex data_files list. Strips off the first
    directory and replaces with prefix
    Example:
        prefix = '/srv/pillar'
        path = 'pillar/drupal
        fixed path will be /srv/pillar/drupal

        prfix = /srv/salt
        path = states/drupal
        fixed parth will be /srv/salt/drupal

    @param starting_path - String starting path
    @param prefix - String prefix to prepend to each file path

    """
    data_files = []
    for path, dirs, files in os.walk(starting_path):
        files = [os.path.join(path, f) for f in files]
        start, _, rest = path.partition(os.path.sep)
        data_files.append((os.path.join(prefix, rest), files))
    return data_files

description = (
    "Runs various cloud workloads and attempts "
    "to provide some measure of performance."
)

data_files = []
data_files += find_data_files('pillar', '/srv/pillar')
data_files += find_data_files('states', '/srv/salt')

packages = find_packages()

setup(
    name="cloud_workloads",
    version="0.1",
    description=description,
    long_description=readme(),
    author="James Absalon, Daniel Curran",
    author_email="james.absalon@rackspace.com",
    license="MIT",
    packages=packages,
    zip_safe=True,
    install_requires=['argparse', 'Jinja2', 'netifaces', 'paramiko',
                      'PyYAML'],
    data_files=data_files,
    scripts=['bin/cloud-workloads-runner', 'bin/cloud-workloads-minion-installer']
)
