from jinja2 import Environment, PackageLoader
import json
import yaml

from jumbo.utils.settings import JUMBODIR
from jumbo.utils import exceptions as ex
from jumbo.core import clusters

svars = {
    'cluster': None,
    'domain': None,
    'machines': [],
    'services': []
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
        generate_ansible_groups()
        with open(JUMBODIR + svars['cluster'] + '/jumbo_config', 'w') as cfg:
            json.dump(svars, cfg)

        vagrant_temp = jinja_env.get_template('Vagrantfile.j2')
        with open(JUMBODIR + svars['cluster'] + '/Vagrantfile', 'w+') as vf:
            vf.write(vagrant_temp.render(hosts=svars['machines'],
                                         domain=svars['domain']))

        hosts_temp = jinja_env.get_template('hosts.j2')
        with open(JUMBODIR + svars['cluster'] + '/playbooks/inventory/hosts',
                  'w+') as vf:
            vf.write(hosts_temp.render(hosts=svars['machines']))

        with open(JUMBODIR + svars['cluster'] +
                  '/playbooks/inventory/group_vars/all', 'w+') as vf:
            yaml.dump(generate_ansible_vars(), vf, default_flow_style=False,
                      explicit_start=True)

    except IOError:
        return False


def load_config(cluster):
    """Load a cluster in the session.

    :param cluster: Cluster name
    :type cluster: str
    :return: True on success
    """
    global svars

    if not clusters.check_cluster(cluster):
        raise ex.LoadError('cluster', cluster, 'NotExist')

    if not clusters.check_config(cluster):
        raise ex.LoadError('cluster', cluster, 'NoConfFile')
    else:
        try:
            # not using 'with open()' because of a Python bug
            svars = json.load(open(JUMBODIR + cluster + '/jumbo_config', 'r'))
        except IOError as e:
            raise ex.LoadError('cluster', cluster, e.strerror)

    return True


def clear():
    '''Reset the sessions variables.

    '''

    global svars
    svars = {
        'cluster': None,
        'machines': [],
        'services': []
    }


def add_machine(m):
    '''Add a machine to the current session.

    :param m: Machine configuration
    :type m: dict
    '''

    added = False
    for i, machine in enumerate(svars['machines']):
        if machine['name'] == m['name']:
            svars['machines'][i] = m
            added = True
    if not added:
        svars['machines'].append(m)


def generate_ansible_groups():
    ansiblehost = None
    pgsqlserver = None
    ipaserver = None
    ambariserver = None

    for machine in svars['machines']:
        if 'PSQL_SERVER' in machine['components'] and not pgsqlserver:
            pgsqlserver = machine['name']
            if 'psqlserver' not in machine['groups']:
                machine['groups'].append('pgsqlserver')
        if 'ANSIBLE_CLIENT' in machine['components'] and not ansiblehost:
            ansiblehost = machine['name']
            if 'ansiblehost' not in machine['groups']:
                machine['groups'].append('ansiblehost')
        if 'AMBARI_SERVER' in machine['components'] and not ambariserver:
            ambariserver = machine['name']
            if 'ambariserver' not in machine['groups']:
                machine['groups'].append('ambariserver')

    if ambariserver:
        for machine in svars['machines']:
            if not machine['name'] == ambariserver \
                    and 'ldap' not in machine['types'] \
                    and 'ambariclients' not in machine['groups']:
                machine['groups'].append('ambariclients')

    # TODO: IPA groups


def generate_ansible_vars():
    return {
        'domain': svars['domain'],
        'realm': svars['domain'].upper(),
        'ipa_dm_password': 'dm_p4ssw0rd',
        'ipa_admin_password': 'adm1n_p4ssw0rd',
        'ambari_repo_url': ('http://public-repo-1.hortonworks.com/ambari/'
                            'centos7/2.x/updates/2.6.1.5/ambari.repo'),
        'use_blueprint': True,
        'blueprint_name': svars['domain'].replace('.', '-') + '-blueprint',
        'cluster_name': svars['domain'].replace('.', '') + 'cluster',
        'vdf_file_url': ('http://public-repo-1.hortonworks.com/HDP/centos7/'
                         '2.x/updates/2.6.4.0/HDP-2.6.4.0-91.xml'),
        'ambari': {
            'user': 'admin',
            'pwd': 'admin'
        }
    }


