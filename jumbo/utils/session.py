from jinja2 import Environment, PackageLoader
import json
import yaml
import os

from distutils import dir_util

from jumbo.utils import exceptions as ex, checks, versions as vs
from jumbo.utils.settings import JUMBODIR, POOLNAME
from jumbo.core import clusters

svars = {
    'cluster': None,
    'domain': None,
    'realm': None,
    'nodes': [],
    'bundles': [],
    'services': [],
    'configurations': []
}

jinja_env = Environment(
    loader=PackageLoader('jumbo.utils', 'templates'),
    trim_blocks=True,
    lstrip_blocks=True
)


def dump_config(services_components_hosts=None, services_config=None):
    """Dump the session's cluster config and generates the project.

    :return: True on success
    """

    try:
        with open(JUMBODIR + 'clusters/' + svars['cluster']
                  + '/jumbo_config', 'w') as cfg:
            json.dump(svars, cfg)

        if svars["location"] == "local":
            vagrant_temp = jinja_env.get_template('Vagrantfile.j2')
            with open(JUMBODIR + 'clusters/' + svars['cluster']
                      + '/Vagrantfile', 'w') as vf:
                vf.write(vagrant_temp.render(hosts=svars['nodes'],
                                             domain=svars['domain'],
                                             cluster=svars['cluster'],
                                             pool_name=POOLNAME))

        if services_config:
            generate_ansible_groups(services_config)

        if services_components_hosts and services_config:
            generate_ansible_vars(services_components_hosts,
                                  services_config)

    except IOError as e:
        print(str(e))
        return False


def load_config(cluster):
    """Load a cluster in the session.

    :param cluster: Cluster name
    :type cluster: str
    :return: True on success
    """
    global svars

    if not checks.check_cluster(cluster):
        raise ex.LoadError('cluster', cluster, 'NotExist')

    if not clusters.check_config(cluster):
        raise ex.LoadError('cluster', cluster, 'NoConfFile')
    else:
        try:
            with open(JUMBODIR + 'clusters/' + cluster + '/jumbo_config', 'r') as jc:
                svars = json.load(jc)
        except IOError as e:
            raise ex.LoadError('cluster', cluster, e.strerror)

    vs.update_versions_file()

    return True


def clear():
    """Reset the sessions variables.
    """

    global svars
    svars = {
        'cluster': None,
        'domain': None,
        'realm': None,
        'location': None,
        'nodes': [],
        'bundles': [],
        'services': [],
        'configurations': [],
    }


def fqdn(host):
    """Generate the fqdn of a host.

    :param host: The host name
    :type host: str
    :return: The fqdn of the host
    :rtype: str
    """

    return '{}.{}'.format(host, svars['domain'])


def generate_ansible_groups(serv_conf):
    """
    Fill the 'groups' property of each host depending on the components
    installed on it.
    """

    groups = {}
    for serv in serv_conf['services']:
        for comp in serv['components']:
            for group in comp.get('ansible_groups', []):
                if group not in groups:
                    groups[group] = []
                for node in svars['nodes']:
                    for node_comp in node['components']:
                        if node_comp == comp['name']:
                            groups[group].append(node['name'])

    hosts = []
    for node in svars['nodes']:
        hosts.append(node['name'])

    hosts_temp = jinja_env.get_template('hosts.j2')
    with open(JUMBODIR + 'clusters/' + svars['cluster'] +
              '/inventory/hosts',
              'w+') as vf:
        vf.write(hosts_temp.render(hosts=svars['nodes'],
                                   groups=groups,
                                   ansible_user="vagrant" if svars['location'] == 'local'
                                   else svars.get('ansible_user', 'root')))


def generate_ansible_vars(serv_comp_hosts, serv_conf):
    generate_group_vars(serv_comp_hosts, serv_conf)
    generate_host_vars()


def generate_host_vars():
    """Complete host related variables in inventory/host_vars/[hostname]
    Builds `compononents` array containing all compononents on the host
    """

    for m in svars['nodes']:
        with open(JUMBODIR + 'clusters/' + svars['cluster']
                  + '/inventory/host_vars/' + m['name'], 'w+') as host_file:
            content = {}
            content['components'] = []
            for c in m['components']:
                content['components'].append(c)

            yaml.dump(content, host_file, default_flow_style=False,
                      explicit_start=True)


def generate_group_vars(serv_comp_hosts, serv_conf):
    """Generate the group_vars/all variables for Ansible playbooks.

    :return: The variables to write in group_vars/all
    :rtype: dict
    """

    ansible_vars = {
        'domain': svars['domain'],
        'realm': svars.get('realm', None) or svars['domain'].upper(),
        'cluster_name': svars['domain'].replace('.', ''),  # real cluster name
        'jumbo_cluster': svars['cluster'],  # cluster name in Jumbo
        'serv_comp_host': serv_comp_hosts,
    }

    # Add versions variables (repository urls...)
    ansible_vars.update(vs.get_yaml_config(svars['cluster']))

    # Add variables defines in json service definitions and config files
    for conf in svars['configurations']:
        ansible_vars.update(conf['config'])

    with open(JUMBODIR + 'clusters/' + svars['cluster']
              + '/inventory/group_vars/all/vars', 'w+') as gva:
        yaml.dump(ansible_vars, gva, default_flow_style=False,
                  explicit_start=True)


def add_node(m):
    """Add a node to the current session.

    :param m: Machine configuration
    :type m: dict
    """

    added = False
    for i, node in enumerate(svars['nodes']):
        if node['name'] == m['name']:
            svars['nodes'][i] = m
            added = True
    if not added:
        svars['nodes'].append(m)
