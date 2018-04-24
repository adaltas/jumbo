from jinja2 import Environment, PackageLoader
import json
import yaml

from jumbo.utils import exceptions as ex
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

bp = {
    'configurations': [],
    'host_groups': [],
    'settings': [],
    'Blueprints': {
        'stack_name': 'HDP',
        'stack_version': '2.6'
    }
}


def dump_config(services_components_hosts=None):
    """Dump the session's cluster config and generates the project.

    :return: True on success
    """

    try:
        generate_ansible_groups()
        with open(JUMBODIR + svars['cluster'] + '/jumbo_config', 'w') as cfg:
            json.dump(svars, cfg)

        vagrant_temp = jinja_env.get_template('Vagrantfile.j2')
        with open(JUMBODIR + svars['cluster'] + '/Vagrantfile', 'w') as vf:
            vf.write(vagrant_temp.render(hosts=svars['machines'],
                                         domain=svars['domain'],
                                         cluster=svars['cluster']))

        hosts_temp = jinja_env.get_template('hosts.j2')
        with open(JUMBODIR + svars['cluster'] + '/playbooks/inventory/hosts',
                  'w') as vf:
            vf.write(hosts_temp.render(hosts=svars['machines']))

        with open(JUMBODIR + svars['cluster'] +
                  '/playbooks/inventory/group_vars/all', 'w') as vf:
            yaml.dump(generate_ansible_vars(), vf, default_flow_style=False,
                      explicit_start=True)

        if services_components_hosts:
            clear_bp()
            generate_blueprint(services_components_hosts)
            with open(JUMBODIR + svars['cluster'] +
                      '/playbooks/roles/postblueprint/templates/blueprint.j2',
                      'w') as bpf:
                json.dump(bp, bpf)
            with open(JUMBODIR + svars['cluster'] +
                      '/playbooks/roles/postblueprint/templates/cluster.j2',
                      'w') as clf:
                json.dump(generate_cluster(), clf)

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

    global svars, bp
    svars = {
        'cluster': None,
        'machines': [],
        'services': []
    }
    bp = {
        'configurations': [],
        'host_groups': [],
        'settings': [],
        'Blueprints': {
            'stack_name': 'HDP',
            'stack_version': '2.6'
        }
    }


def clear_bp():
    global bp
    bp = {
        'configurations': [],
        'host_groups': [],
        'settings': [],
        'Blueprints': {
            'stack_name': 'HDP',
            'stack_version': '2.6'
        }
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
    """
    Fill the 'groups' property of each host depending on the components
    installed on it.

    """

    ansiblehost = None
    pgsqlserver = None
    ipaserver = None
    ambariserver = None

    for machine in svars['machines']:
        machine['groups'] = []
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
            if 'ldap' not in machine['types'] \
                    and 'ambariclient' not in machine['groups']:
                machine['groups'].append('ambariclient')

    # TODO: IPA groups


def generate_ansible_vars():
    """Generate the group_vars/all variables for Ansible playbooks

    :return: The variables to write in group_vars/all
    :rtype: dict
    """

    pgsqlserver = ''

    for m in svars['machines']:
        if 'pgsqlserver' in m['groups']:
            pgsqlserver = m['name']

    return {
        'domain': svars['domain'],
        'realm': svars['domain'].upper(),
        'ipa_dm_password': 'dm_p4ssw0rd',
        'ipa_admin_password': 'adm1n_p4ssw0rd',
        'pgsqlserver': fqdn(pgsqlserver),
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


def bp_set_conf_prop(section, prop, value):
    """Set a property in a specified section of the blueprint 'configurations'

    :param section: Section in which the property to set is
    :type section: str
    :param prop: The property to set
    :type prop: str
    :param value: The value of the property
    :type value: str
    :return: True on success
    """

    for i, item in enumerate(bp.get('configurations')):
        if item.get(section):
            bp.get('configurations')[i] \
                .get(section) \
                .get('properties')[prop] = value
            return True
    return False


def fqdn(host):
    """Generate the fqdn of a host

    :param host: The host name
    :type host: str
    :return: The fqdn of the host
    :rtype: str
    """

    return '{}.{}'.format(host, svars['domain'])


def generate_blueprint(serv_comp_hosts):
    generate_blueprint_conf(serv_comp_hosts)
    generate_blueprint_hostgroups()
    generate_blueprint_settings()


def generate_blueprint_conf(serv_comp_hosts):
    bp.get('configurations').append({
        'core-site': {
            'properties': {}
        }
    })

    bp_set_conf_prop('core-site', 'fs.trash.interval', '360')

    if 'ZOOKEEPER' in serv_comp_hosts:
        complete_conf_zookeeper(serv_comp_hosts)

    if 'HDFS' in serv_comp_hosts:
        bp.get('configurations').append({
            'hdfs-site': {
                'properties': {}
            }
        })
        complete_conf_hdfs(serv_comp_hosts)

    if 'YARN' in serv_comp_hosts:
        bp.get('configurations').append({
            'yarn-site': {
                'properties': {}
            }
        })
        complete_conf_yarn(serv_comp_hosts)


def complete_conf_zookeeper(serv_comp_hosts):
    if 'ZOOKEEPER_SERVER' in serv_comp_hosts['ZOOKEEPER']:
        bp_set_conf_prop('core-site', 'ha.zookeeper.quorum',
                         generate_zookeeper_quorum(
                             serv_comp_hosts['ZOOKEEPER']['ZOOKEEPER_SERVER'],
                             True))


def generate_zookeeper_quorum(zk_hosts, add_port=False):
    zk_quorum = []
    for h in zk_hosts:
        zk_quorum.append('{}{}'.format(fqdn(h), ':2181' if add_port else ''))
    return ', '.join(zk_quorum)


def complete_conf_hdfs(serv_comp_hosts):
    if 'NAMENODE' in serv_comp_hosts['HDFS']:
        if len(serv_comp_hosts['HDFS']['NAMENODE']) > 1:
            bp_set_conf_prop('core-site', 'fs.defaultFS',
                             'hdfs://nn%s' % svars['domain'].replace('.', ''))
            generate_hdfssite_ha(serv_comp_hosts['HDFS'])
        else:
            bp_set_conf_prop('core-site', 'fs.defaultFS',
                             'hdfs://{}:8020'.format(
                                 fqdn(serv_comp_hosts['HDFS']['NAMENODE'][0])))
            generate_hdfssite(serv_comp_hosts['HDFS'])


def generate_hdfssite(hdfs_comp):
    nn = fqdn(hdfs_comp['NAMENODE'][0])
    snn = fqdn(hdfs_comp['SECONDARY_NAMENODE'][0])
    bp_set_conf_prop('hdfs-site',
                     'dfs.namenode.http-address',
                     '%s:50070' % nn)
    bp_set_conf_prop('hdfs-site',
                     'dfs.namenode.https-address',
                     '%s:50470' % nn)
    bp_set_conf_prop('hdfs-site',
                     'dfs.namenode.rpc-addres',
                     '%s:8020' % nn)
    if hdfs_comp.get('SECONDARY_NAMENODE'):
        bp_set_conf_prop('hdfs-site',
                         'dfs.namenode.secondary.http-address',
                         '%s:50090' % snn)


def generate_hdfssite_ha(hdfs_comp):
    raise ex.CreationError('service', 'HDFS', 'mode', 'High Availability',
                           'NotSupported')


def complete_conf_yarn(serv_comp_hosts):
    if 'RESOURCEMANAGER' in serv_comp_hosts['YARN']:
        if len(serv_comp_hosts['YARN']['RESOURCEMANAGER']) > 1:
            generate_yarnsite_ha(serv_comp_hosts['YARN'])
        else:
            bp_set_conf_prop('core-site',
                             'hadoop.proxyuser.yarn.hosts',
                             fqdn(serv_comp_hosts['YARN']
                                  .get('RESOURCEMANAGER')[0]))
            generate_yarnsite(serv_comp_hosts['YARN'])


def generate_yarnsite(yarn_comp):
    rm = fqdn(yarn_comp['RESOURCEMANAGER'][0])
    bp_set_conf_prop('yarn-site',
                     'yarn.resourcemanager.ha.enabled',
                     'false')
    bp_set_conf_prop('yarn-site',
                     'yarn.resourcemanager.recovery.enabled',
                     'true')
    bp_set_conf_prop('yarn-site',
                     'yarn.resourcemanager.store.class',
                     'org.apache.hadoop.yarn.server.resourcemanager.'
                     'recovery.ZKRMStateStore')
    bp_set_conf_prop('yarn-site',
                     'yarn.resourcemanager.address',
                     '%s:8050' % rm)
    bp_set_conf_prop('yarn-site',
                     'yarn.resourcemanager.admin.address',
                     '%s:8141' % rm)
    bp_set_conf_prop('yarn-site',
                     'yarn.resourcemanager.hostname',
                     '%s' % rm)
    bp_set_conf_prop('yarn-site',
                     'yarn.resourcemanager.resource-tracker.address',
                     '%s:8025' % rm)
    bp_set_conf_prop('yarn-site',
                     'yarn.resourcemanager.scheduler.address',
                     '%s:8030' % rm)
    bp_set_conf_prop('yarn-site',
                     'yarn.resourcemanager.webapp.address',
                     '%s:8088' % rm)
    bp_set_conf_prop('yarn-site',
                     'yarn.resourcemanager.webapp.https.address',
                     '%s:8090' % rm)
    bp_set_conf_prop('yarn-site',
                     'yarn.log.server.url',
                     'http://%s:19888/jobhistory/logs' % rm)
    if yarn_comp.get('APP_TIMELINE_SERVER'):
        timeline = fqdn(yarn_comp['APP_TIMELINE_SERVER'][0])
        bp_set_conf_prop('yarn-site',
                         'yarn.timeline-service.address',
                         '%s:10200' % timeline)
        bp_set_conf_prop('yarn-site',
                         'yarn.timeline-service.webapp.address',
                         '%s:8188' % timeline)
        bp_set_conf_prop('yarn-site',
                         'yarn.timeline-service.webapp.https.address',
                         '%s:8190' % timeline)


def generate_yarnsite_ha(yarn_comp):
    raise ex.CreationError('service', 'YARN', 'mode', 'High Availability',
                           'NotSupported')


def generate_blueprint_hostgroups():
    for m in svars['machines']:
        comp = []
        for c in m['components']:
            if blueprint_component(c):
                comp.append({
                    'name': c
                })
        if comp:
            bp.get('host_groups').append({
                "cardinality": "1",
                "components": comp,
                "configurations": [],
                "name": "%s_group" % m['name']
            })


def blueprint_component(component):
    not_bp_comp = [
        'ANSIBLE_CLIENT',
        'PSQL_SERVER',
        'AMBARI_SERVER'
    ]
    if component in not_bp_comp:
        return False
    return True


def generate_blueprint_settings():
    pass


def generate_cluster():
    host_groups = []
    for hg in bp['host_groups']:
        host_groups.append({
            'name': '%s' % hg['name'],
            'hosts': [
                {
                    'fqdn': fqdn(hg['name'].split('_')[0])
                }
            ]
        })

    return {
        'blueprint': svars['domain'].replace('.', '-') + '-blueprint',
        'repository_version_id': 1,
        'host_groups': host_groups,
        'config_recommendation_strategy':
        'ALWAYS_APPLY_DONT_OVERRIDE_CUSTOM_VALUES',
        'configurations': [
            {
                "hive-site": {
                    "properties": {
                        "javax.jdo.option.ConnectionPassword": "hive"
                    }
                }
            },
            {
                "oozie-site": {
                    "properties": {
                        "oozie.service.JPAService.jdbc.password": "oozie"
                    }
                }
            }
        ]
    }
