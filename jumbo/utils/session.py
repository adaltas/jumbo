from jinja2 import Environment, PackageLoader
import json

from jumbo.utils.settings import JUMBODIR

svars = {
    'cluster': None,
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


def clear():
    global svars
    svars = {
        'cluster': None,
        'machines': []
    }


def check_machine(name):
    """Check if machine already exists

    :param m: machine name
    :type m: string
    :return: machine exists
    :rtype: bool
    """

    for machine in svars['machines']:
        if machine['name'] == name:
            return True
    return False


def check_ip(ip):
    """Check if ip not already used

    :param ip: ip address
    :type ip: string
    :return: name of the machine using the ip or False
    :rtype: string or bool
    """

    for machine in svars['machines']:
        if machine['ip'] == ip:
            return machine['name']
    return False


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
