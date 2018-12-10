from jinja2 import Environment, PackageLoader
import json
import yaml
import os

from distutils import dir_util

from jumbo.utils import exceptions as ex, checks, versions as vs
from jumbo.utils.settings import JUMBODIR, NOT_HADOOP_COMP, POOLNAME
from jumbo.core import clusters

svars = {
    'cluster': None,
    'domain': None,
    'nodes': [],
    'services': [],
}

jinja_env = Environment(
    loader=PackageLoader('jumbo.utils', 'templates'),
    trim_blocks=True,
    lstrip_blocks=True
)


def dump_config(services_components_hosts=None):
    """Dump the session's cluster config and generates the project.

    :return: True on success
    """

    try:
        generate_ansible_groups()

        with open(JUMBODIR + svars['cluster'] + '/jumbo_config', 'w') as cfg:
            json.dump(svars, cfg)

        if svars["location"] == "local":
            vagrant_temp = jinja_env.get_template('Vagrantfile.j2')
            with open(JUMBODIR + svars['cluster'] + '/Vagrantfile', 'w') as vf:
                vf.write(vagrant_temp.render(hosts=get_ordered_nodes(),
                                             domain=svars['domain'],
                                             cluster=svars['cluster'],
                                             pool_name=POOLNAME))

        hosts_temp = jinja_env.get_template('hosts.j2')
        with open(JUMBODIR + svars['cluster'] +
                  '/jumbo-services/playbooks/inventory/hosts',
                  'w') as vf:
            vf.write(hosts_temp.render(hosts=svars['nodes']))

        if services_components_hosts:
            generate_ansible_vars(services_components_hosts)

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
            with open(JUMBODIR + cluster + '/jumbo_config', 'r') as jc:
                svars = json.load(jc)
        except IOError as e:
            raise ex.LoadError('cluster', cluster, e.strerror)

    vs.update_versions_file()

    return True


def update_files(cluster, services_components_hosts):
    data_dir = os.path.dirname(os.path.abspath(__file__)) + '/../core/data/'

    dir_util.copy_tree(data_dir, JUMBODIR + cluster)
    dir_util._path_created = {}

    dump_config(services_components_hosts)
    return True


def clear():
    """Reset the sessions variables.
    """

    global svars
    svars = {
        'cluster': None,
        'nodes': [],
        'services': []
    }


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


def get_ordered_nodes():
    ordered = [n for n in svars['nodes'] if 'ansiblehost' not in n['groups']]
    ordered.extend(n for n in svars['nodes'] if 'ansiblehost' in n['groups'])

    return ordered


def fqdn(host):
    """Generate the fqdn of a host.

    :param host: The host name
    :type host: str
    :return: The fqdn of the host
    :rtype: str
    """

    return '{}.{}'.format(host, svars['domain'])


def generate_ansible_groups():
    """
    Fill the 'groups' property of each host depending on the components
    installed on it.
    """

    ansiblehost = None
    pgsqlserver = None
    ambariserver = None
    ipaserver = None

    for node in svars['nodes']:
        node['groups'] = []
        if 'PSQL_SERVER' in node['components'] and not pgsqlserver:
            pgsqlserver = node['name']
            if 'psqlserver' not in node['groups']:
                node['groups'].append('pgsqlserver')
        if 'ANSIBLE_CLIENT' in node['components'] and not ansiblehost:
            ansiblehost = node['name']
            if 'ansiblehost' not in node['groups']:
                node['groups'].append('ansiblehost')
        if 'AMBARI_SERVER' in node['components'] and not ambariserver:
            ambariserver = node['name']
            if 'ambariserver' not in node['groups']:
                node['groups'].append('ambariserver')
        if 'IPA_SERVER' in node['components'] and not ipaserver:
            ipaserver = node['name']
            if 'ipaserver' not in node['groups']:
                node['groups'].append('ipaserver')

    if ambariserver:
        for node in svars['nodes']:
            if 'ldap' not in node['types'] \
                    and 'ambariclient' not in node['groups']:
                node['groups'].append('ambariclient')

    if ipaserver:
        for node in svars['nodes']:
            if 'ldap' not in node['types'] \
                    and 'ipaclient' not in node['groups']:
                node['groups'].append('ipaclient')


def get_pgsqlserver_host():
    """Return the fqdn of the node hosting the PSQL_SERVER.
    """

    for node in svars['nodes']:
        if 'pgsqlserver' in node['groups']:
            return fqdn(node['name'])


def get_ipaserver_host():
    """Return the fqdn of the node hosting the IPA_SERVER.
    """

    for node in svars['nodes']:
        if 'ipaserver' in node['groups']:
            return fqdn(node['name'])


def generate_ansible_vars(serv_comp_hosts):
    generate_group_vars(serv_comp_hosts)
    generate_host_vars()


def generate_host_vars():
    """Complete the 'host_groups' section of the blueprint.
    """

    for m in svars['nodes']:
        with open(JUMBODIR + svars['cluster']
                  + '/jumbo-services/playbooks/inventory/host_vars/' + m['name'], 'w') as host_file:
            content = {}
            content['components'] = []
            for c in m['components']:
                if blueprint_component(c):
                    content['components'].append(c)

            yaml.dump(content, host_file, default_flow_style=False,
                      explicit_start=True)


def generate_group_vars(serv_comp_hosts):
    """Generate the group_vars/all variables for Ansible playbooks.

    :return: The variables to write in group_vars/all
    :rtype: dict
    """

    pgsqlserver = ''

    for m in svars['nodes']:
        if 'pgsqlserver' in m['groups']:
            pgsqlserver = m['name']

    ansible_vars = {
        'domain': svars['domain'],
        'realm': svars.get('realm', None) or svars['domain'].upper(),
        'ipa_dm_password': 'dm_p4ssw0rd',
        'ipa_admin_password': 'adm1n_p4ssw0rd',
        'pgsqlserver': fqdn(pgsqlserver),
        'use_blueprint': True,
        'blueprint_name': svars['domain'].replace('.', '-') + '-blueprint',
        'cluster_name': svars['domain'].replace('.', ''),
        'ambari': {
            'user': 'admin',
            'pwd': 'admin',
            'ssl': {
                'enabled': False,
                'port': 8442
            }
        },
        'ambari_url': ("{{ 'https' if ambari.ssl.enabled else 'http' }}://"
                       "{{ hostvars[groups['ambariserver'][0]]['ansible_all_ipv4_addresses'][0] }}"
                       ":{{ ambari.ssl.port if ambari.ssl.enabled else '8080' }}"),
        'kerberos_enabled': ('KERBEROS' in svars['services'])
    }

    # Add versions variables (repository urls...)
    ansible_vars.update(vs.get_yaml_config(svars['cluster']))

    # Add blueprint templates variables
    if 'HDFS' in serv_comp_hosts:
        ansible_vars.update(generate_groupvars_hdfs(serv_comp_hosts['HDFS']))
    if 'YARN' in serv_comp_hosts:
        ansible_vars.update(generate_groupvars_yarn(serv_comp_hosts['YARN']))
    if 'HIVE' in serv_comp_hosts:
        ansible_vars.update(generate_groupvars_hive(serv_comp_hosts['HIVE']))

    with open(JUMBODIR + svars['cluster'] +
              '/jumbo-services/playbooks/inventory/group_vars/all', 'w') as gva:
        yaml.dump(ansible_vars, gva, default_flow_style=False,
                  explicit_start=True)


def generate_groupvars_hdfs(hdfs_comp):
    ret = {}
    ret['HDFS'] = {}

    if 'NAMENODE' in hdfs_comp:
        ret['HDFS']['namenodes_FQDN'] = []

        if len(hdfs_comp['NAMENODE']) == 2:
            ret['HDFS']['namenodes_FQDN'].append(
                fqdn(hdfs_comp['NAMENODE'][0]))
            ret['HDFS']['namenodes_FQDN'].append(
                fqdn(hdfs_comp['NAMENODE'][1]))
            ret['HDFS']['nameservice'] = 'nn%s' % svars['domain'].replace(
                '.', '')
        else:
            ret['HDFS']['namenodes_FQDN'].append(
                fqdn(hdfs_comp['NAMENODE'][0]))
            if hdfs_comp.get('SECONDARY_NAMENODE'):
                ret['HDFS']['snamenode_FQDN'] = fqdn(
                    hdfs_comp['SECONDARY_NAMENODE'][0])

    return ret


def generate_groupvars_yarn(yarn_comp):
    ret = {}
    ret['YARN'] = {}

    if 'APP_TIMELINE_SERVER' in yarn_comp:
        ret['YARN']['timeline_service_FQDN'] = yarn_comp['APP_TIMELINE_SERVER'][0]
    if 'RESOURCEMANAGER' in yarn_comp:
        ret['YARN']['resourcemanagers_FQDN'] = []
        ret['YARN']['resourcemanagers_FQDN'].append(
            fqdn(yarn_comp['RESOURCEMANAGER'][0]))

        # HA
        if len(yarn_comp['RESOURCEMANAGER']) == 2:
            ret['YARN']['resourcemanagers_FQDN'].append(
                fqdn(yarn_comp['RESOURCEMANAGER'][1]))

        if 'NODEMANAGER' in yarn_comp:
            container_max_memory = 1536
            node_max_containers = 100
            for m in svars['nodes']:
                if m['name'] in yarn_comp['NODEMANAGER']:
                    if node_max_containers > int(m['ram'] / 1536):
                        node_max_containers = int(m['ram'] / 1536)
            node_max_memory = node_max_containers * container_max_memory
            ret['YARN']['nodemanager_resource_memory'] = node_max_memory
            ret['YARN']['container_max_memory'] = container_max_memory

    return ret


def generate_groupvars_hive(hive_comp):
    ret = {}
    ret['HIVE'] = {}

    if 'HIVE_METASTORE' in hive_comp:
        ret['HIVE']['metastores_FQDN'] = []
        ret['HIVE']['metastores_FQDN'].append(hive_comp['HIVE_METASTORE'][0])
    if 'WEBHCAT_SERVER' in hive_comp:
        ret['HIVE']['webhcat_FQDN'] = hive_comp['WEBHCAT_SERVER'][0]

    return ret


def blueprint_component(component):
    if component in NOT_HADOOP_COMP:
        return False
    return True


def generate_blueprint_settings():
    pass
