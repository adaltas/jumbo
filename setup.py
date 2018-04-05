from setuptools import setup

setup(
    name='Jumbo',
    version='0.1',
    install_requires=[
        'Click',
        'click-shell',
        'jinja2'
    ],
    py_modules=['jumbo'],
    entry_points='''
        [console_scripts]
        jumboshell=jumbo.main:jumbo_shell
        jumbo=jumbo.main:main
    ''',
)
