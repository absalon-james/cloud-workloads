from install_utils import readme
from setuptools import setup, find_packages
from cloud_workloads.meta import version, license

description = (
    "Runs various cloud workloads and attempts "
    "to provide some measure of performance."
)

data_files = [('/etc/cloud_workloads', ['sample.yaml'])]

setup(
    name="cloud_workloads",
    version=version,
    description=description,
    long_description=readme(),
    author="James Absalon, Daniel Curran",
    author_email="james.absalon@rackspace.com",
    license=license,
    packages=find_packages(),
    include_package_data=True,
    package_data={'cloud_workloads': ['views/*', 'assets/*']},
    zip_safe=True,
    install_requires=['argparse', 'Jinja2', 'netifaces', 'paramiko',
                      'PyYAML'],
    data_files=data_files,
    scripts=[
        'bin/cloud-workloads-configure',
        'bin/cloud-workloads-runner',
        'bin/cloud-workloads-minion-installer'
    ]
)
