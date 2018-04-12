from jinja2 import Environment, PackageLoader
import json

from jumbo.utils.settings import JUMBODIR

svars = {
    'cluster': None,
    'domain': None,
    'machines': []
}

jinja_env = Environment(
    loader=PackageLoader('jumbo', 'templates'),
    trim_blocks=True,
    lstrip_blocks=True
)


def dump_config():
    """Dump the session's cluster config and generates the project.

    :return: True on success
    """

    try:
        with open(JUMBODIR + svars['cluster'] + '/jumbo_config', 'w') as cfg:
            json.dump(svars, cfg)

        vagrant_temp = jinja_env.get_template('Vagrantfile.j2')
        with open(JUMBODIR + svars['cluster'] + '/Vagrantfile', 'w+') as vf:
            vf.write(vagrant_temp.render(hosts=svars['machines'],
                                         domain=svars['domain']))

        generate_ansible_groups()
        hosts_temp = jinja_env.get_template('hosts.j2')
        with open(JUMBODIR + svars['cluster'] + '/playbooks/inventory/hosts',
                  'w+') as vf:
            vf.write(hosts_temp.render(hosts=svars['machines']))

    except IOError:
        return False


def load_config(name):
    """Load a cluster in the session.

    :param name: Cluster name
    :type name: str
    :return: True on success
    """

    global svars
    # not using 'with open()' because of a Python bug
    svars = json.load(open(JUMBODIR + name + '/jumbo_config', 'r'))

    return True


def clear():
    """Reset the sessions variables.

    """

    global svars
    svars = {
        'cluster': None,
        'machines': []
    }


def add_machine(m):
    """Add a machine to the current session.

    :param m: Machine configuration
    :type m: dict
    """

    added = False
    for i, machine in enumerate(svars['machines']):
        if machine['name'] == m['name']:
            svars['machines'][i] = m
            added = True
    if not added:
        svars['machines'] += [
            m
        ]


def generate_ansible_groups():
    ansiblehost = None
    pgsqlserver = None
    ipaserver = None
    ambariserver = None

    for machine in svars['machines']:
        if 'PSQL_SERVER' in machine['components'] and not pgsqlserver:
            pgsqlserver = machine['name']
            machine['groups'] += ['pgsqlserver']
        if 'ANSIBLE_CLIENT' in machine['components'] and not ansiblehost:
            ansiblehost = machine['name']
            machine['groups'] += ['ansiblehost']
        if 'AMBARI_SERVER' in machine['components'] and not ambariserver:
            ambariserver = machine['name']
            machine['groups'] += ['ambariserver']

    if ambariserver:
        for machine in svars['machines']:
            if not machine['name'] == ambariserver \
                    and 'ldap' not in machine['types']:
                machine['groups'] += ['ambariclients']

    # TODO: IPA groups
