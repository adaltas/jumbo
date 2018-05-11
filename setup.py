from setuptools import setup

setup(
    name='Jumbo',
    version='0.1',
    install_requires=[
        'Click',
        'click-shell',
        'jinja2',
        'prettytable',
        'pyyaml',
        'ipaddress'
    ],
    py_modules=['jumbo'],
    entry_points='''
        [console_scripts]
        jumbo=jumbo.cli.main:jumbo
    '''
)
