from install_utils import readme, find_data_files
from post_install import PostDownloadInstall, PostDownloadDevelop
from setuptools import setup, find_packages

description = (
    "Runs various cloud workloads and attempts "
    "to provide some measure of performance."
)

data_files = [('/etc/cloud_workloads', ['sample.yaml'])]
data_files += find_data_files('pillar', '/srv/pillar')
data_files += find_data_files('states', '/srv/salt')

setup(
    name="cloud_workloads",
    version="0.1",
    description=description,
    long_description=readme(),
    author="James Absalon, Daniel Curran",
    author_email="james.absalon@rackspace.com",
    license="MIT",
    packages=find_packages(),
    include_package_data=True,
    package_data={'cloud_workloads': ['views/*', 'assets/*']},
    zip_safe=True,
    install_requires=['argparse', 'Jinja2', 'netifaces', 'paramiko',
                      'PyYAML'],
    data_files=data_files,
    scripts=[
        'bin/cloud-workloads-runner',
        'bin/cloud-workloads-minion-installer'
    ],
    cmdclass={
        'install': PostDownloadInstall,
        'develop': PostDownloadDevelop
    }
)
