from jinja2 import Environment, PackageLoader
import json

from jumbo.utils.settings import JUMBODIR

svars = {
    'cluster': '',
    'machines': []
}

jinja_env = Environment(
    loader=PackageLoader('jumbo', 'templates')
)


def dump_config():
    with open(JUMBODIR + svars['cluster'] + '/jumbo_config', 'w') as cfg:
        json.dump(svars, cfg)


def load_config(name):
    global svars
    try:
        # not using 'with open()' because of a Python bug
        svars = json.load(open(JUMBODIR + name + '/jumbo_config', 'r'))
    except IOError:
        return False
    return True


def add_machine(m):
    added = False
    for i, machine in enumerate(svars['machines']):
        if machine['name'] == m['name']:
            svars['machines'][i] = m
            added = True
    if not added:
        svars['machines'] += [
            m
        ]
