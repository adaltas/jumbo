import os
import pathlib
import subprocess

from setuptools import setup
from shutil import which

POOLNAME = 'jumbo-storage'
POOLDIR = '/var/lib/libvirt/images/%s' % POOLNAME


def list_package_data(package_dir, data_dirs):
    """Return the list of all the data subdirectories for a package

    :param package_dir: The directory of the package
    :type package_dir: str
    :param data_dirs: The list of the top level data directories of the package
    :type data_dirs: list<str>
    :rtype: list<str>
    """

    data = []
    for d in data_dirs:
        for dir_name, _, _ in os.walk(package_dir + '/' + d):
            data.append('%s/*' % dir_name.split(package_dir + '/')[1])

    return data


def create_storage_pool():
    """Create a storage pool jumbo-storage to provision clusters using libvirt
    """

    if which('virsh'):
        if not os.path.isdir(POOLDIR):
            pathlib.Path(POOLDIR).mkdir()

        pool_test = subprocess.Popen([
            'sudo',
            'virsh',
            'pool-info',
            POOLNAME
        ])

        # If the storage pool doesn't exist
        if not pool_test.poll():
            res = subprocess.Popen([
                'sudo',
                'virsh',
                'pool-define-as',
                '--target', POOLDIR,
                '--name', POOLNAME,
                '--type', 'dir'
            ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
            )

            for line in res.stdout:
                print(line.decode('utf-8').rstrip())

            res = subprocess.Popen([
                'sudo',
                'virsh',
                'pool-autostart',
                POOLNAME
            ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
            )

            res = subprocess.Popen([
                'sudo',
                'virsh',
                'pool-start',
                POOLNAME
            ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
            )


setup(
    name='Jumbo',
    version='0.4.3',
    install_requires=[
        'Click',
        'click-shell',
        'jinja2',
        'prettytable',
        'pyyaml',
        'ipaddress',
        'ansible',
        'ansible-vault'
    ],
    packages=[
        'jumbo.cli',
        'jumbo.core',
        'jumbo.utils'
    ],
    package_data={
        'jumbo.core': list_package_data('jumbo/core', ['data', 'config']),
        'jumbo.utils':  list_package_data('jumbo/utils', ['templates'])
    },
    entry_points='''
        [console_scripts]
        jumbo=jumbo.cli.main:jumbo
    '''
)

create_storage_pool()
