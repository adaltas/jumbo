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

    try:
        temp = jinja_env.get_template('Vagrantfile.j2')
        with open(JUMBODIR + svars['cluster'] + '/Vagrantfile', 'w+') as vf:
            vf.write(temp.render(hosts=svars['machines']))
    except IOError:
        return False


def load_config(name):
    global svars
    # not using 'with open()' because of a Python bug
    svars = json.load(open(JUMBODIR + name + '/jumbo_config', 'r'))

    return True


def clear():
    global svars
    svars = {
        'cluster': None,
        'machines': []
    }


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
