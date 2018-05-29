from setuptools import setup
import os


def generate_package_data(package_dir, data_dirs):
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


setup(
    name='Jumbo',
    version='0.4.1',
    install_requires=[
        'Click',
        'click-shell',
        'jinja2',
        'prettytable',
        'pyyaml',
        'ipaddress'
    ],
    packages=[
        'jumbo.cli',
        'jumbo.core',
        'jumbo.tests',
        'jumbo.utils'
    ],
    package_data={
        'jumbo.core': generate_package_data('jumbo/core', ['data', 'config']),
        'jumbo.utils':  generate_package_data('jumbo/utils', ['templates'])
    },
    entry_points='''
        [console_scripts]
        jumbo=jumbo.cli.main:jumbo
    '''
)
