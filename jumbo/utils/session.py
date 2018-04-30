from jinja2 import Environment, PackageLoader
import json
import yaml

from jumbo.utils import exceptions as ex, checks
from jumbo.utils.settings import JUMBODIR
from jumbo.core import clusters

svars = {
    'cluster': None,
    'domain': None,
    'machines': [],
    'services': [],
    'urls': {
        'ambari_repo': None,
        'vdf': None
    }
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
                      '/playbooks/roles/postblueprint/files/blueprint.json',
                      'w') as bpf:
                json.dump(bp, bpf)
            with open(JUMBODIR + svars['cluster'] +
                      '/playbooks/roles/postblueprint/files/cluster.json',
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

    if not checks.check_cluster(cluster):
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
    """Reset the sessions variables.
    """

    global svars, bp
    svars = {
        'cluster': None,
        'machines': [],
        'services': [],
        'urls': {
            'ambari_repo': None,
            'vdf': None
        }
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
    """Reset the blueprint configuration.
    """

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
        svars['machines'].append(m)


def generate_ansible_groups():
    """
    Fill the 'groups' property of each host depending on the components
    installed on it.
    """

    ansiblehost = None
    pgsqlserver = None
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


def get_pgsqlserver_host():
    """Return the fqdn of the machine hosting the PSQL_SERVER.
    """

    for machine in svars['machines']:
        if 'pgsqlserver' in machine['groups']:
            return fqdn(machine['name'])


def generate_ansible_vars():
    """Generate the group_vars/all variables for Ansible playbooks.

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
        'jdbc_driver': 'postgresql-42.2.1.jar',
        'ambari_repo_url': svars['urls']['ambari_repo'],
        'use_blueprint': True,
        'blueprint_name': svars['domain'].replace('.', '-') + '-blueprint',
        'cluster_name': svars['domain'].replace('.', ''),
        'vdf_file_url': svars['urls']['vdf'],
        'ambari': {
            'user': 'admin',
            'pwd': 'admin'
        }
    }


def bp_set_conf_prop(section, prop, value):
    """Set a property in a specified section of the blueprint 'configurations'.

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
    """Generate the fqdn of a host.

    :param host: The host name
    :type host: str
    :return: The fqdn of the host
    :rtype: str
    """

    return '{}.{}'.format(host, svars['domain'])


def generate_blueprint(serv_comp_hosts):
    """Complete the blueprint configuration.

    :param serv_comp_hosts: A list of services-components-hosts installed
    :type serv_comp_hosts: dict
    """

    generate_blueprint_conf(serv_comp_hosts)
    generate_blueprint_hostgroups()
    generate_blueprint_settings()


def generate_blueprint_conf(serv_comp_hosts):
    """Complete the 'configurations' section of the blueprint
    """

    bp.get('configurations').append({
        'core-site': {
            'properties': {}
        }
    })

    bp_set_conf_prop('core-site', 'fs.trash.interval', '360')

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

    if 'HIVE' in serv_comp_hosts:
        bp.get('configurations').append({
            'hive-site': {
                'properties': {}
            }
        })
        bp.get('configurations').append({
            'hive-env': {
                'properties': {}
            }
        })
        bp.get('configurations').append({
            'webhcat-site': {
                'properties': {}
            }
        })
        complete_conf_hive(serv_comp_hosts)

    if 'HBASE' in serv_comp_hosts:
        bp.get('configurations').append({
            'hbase-site': {
                'properties': {}
            }
        })
        bp.get('configurations').append({
            'hbase-env': {
                'properties': {}
            }
        })
        complete_conf_hbase(serv_comp_hosts)

    if 'ZOOKEEPER' in serv_comp_hosts:
        complete_conf_zookeeper(serv_comp_hosts)


def complete_conf_zookeeper(serv_comp_hosts):
    if 'ZOOKEEPER_SERVER' in serv_comp_hosts['ZOOKEEPER']:
        zk_quorum = generate_zookeeper_quorum(
            serv_comp_hosts['ZOOKEEPER']['ZOOKEEPER_SERVER'],
            True)
        zk_quorum_noport = generate_zookeeper_quorum(
            serv_comp_hosts['ZOOKEEPER']['ZOOKEEPER_SERVER'],
            False)
        bp_set_conf_prop('core-site',
                         'ha.zookeeper.quorum',
                         zk_quorum)
        if 'HIVE' in serv_comp_hosts:
            bp_set_conf_prop('hive-site',
                             'hive.zookeeper.quorum',
                             zk_quorum)
            bp_set_conf_prop('webhcat-site',
                             'templeton.zookeeper.hosts',
                             zk_quorum)
        if 'HBASE' in serv_comp_hosts:
            bp_set_conf_prop('hbase-site',
                             'hbase.zookeeper.quorum',
                             zk_quorum_noport)


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
    site = 'hdfs-site'
    bp_set_conf_prop(site,
                     'dfs.namenode.http-address',
                     '%s:50070' % nn)
    bp_set_conf_prop(site,
                     'dfs.namenode.https-address',
                     '%s:50470' % nn)
    bp_set_conf_prop(site,
                     'dfs.namenode.rpc-addres',
                     '%s:8020' % nn)
    if hdfs_comp.get('SECONDARY_NAMENODE'):
        snn = fqdn(hdfs_comp['SECONDARY_NAMENODE'][0])
        bp_set_conf_prop(site,
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
    site = 'yarn-site'
    bp_set_conf_prop(site,
                     'yarn.resourcemanager.ha.enabled',
                     'false')
    bp_set_conf_prop(site,
                     'yarn.resourcemanager.recovery.enabled',
                     'true')
    bp_set_conf_prop(site,
                     'yarn.resourcemanager.store.class',
                     'org.apache.hadoop.yarn.server.resourcemanager.'
                     'recovery.ZKRMStateStore')
    bp_set_conf_prop(site,
                     'yarn.resourcemanager.address',
                     '%s:8050' % rm)
    bp_set_conf_prop(site,
                     'yarn.resourcemanager.admin.address',
                     '%s:8141' % rm)
    bp_set_conf_prop(site,
                     'yarn.resourcemanager.hostname',
                     '%s' % rm)
    bp_set_conf_prop(site,
                     'yarn.resourcemanager.resource-tracker.address',
                     '%s:8025' % rm)
    bp_set_conf_prop(site,
                     'yarn.resourcemanager.scheduler.address',
                     '%s:8030' % rm)
    bp_set_conf_prop(site,
                     'yarn.resourcemanager.webapp.address',
                     '%s:8088' % rm)
    bp_set_conf_prop(site,
                     'yarn.resourcemanager.webapp.https.address',
                     '%s:8090' % rm)
    bp_set_conf_prop(site,
                     'yarn.log.server.url',
                     'http://%s:19888/jobhistory/logs' % rm)
    if yarn_comp.get('APP_TIMELINE_SERVER'):
        timeline = fqdn(yarn_comp['APP_TIMELINE_SERVER'][0])
        bp_set_conf_prop(site,
                         'yarn.timeline-service.address',
                         '%s:10200' % timeline)
        bp_set_conf_prop(site,
                         'yarn.timeline-service.webapp.address',
                         '%s:8188' % timeline)
        bp_set_conf_prop(site,
                         'yarn.timeline-service.webapp.https.address',
                         '%s:8190' % timeline)


def generate_yarnsite_ha(yarn_comp):
    raise ex.CreationError('service', 'YARN', 'mode', 'High Availability',
                           'NotSupported')


def complete_conf_hive(serv_comp_hosts):
    if 'HIVE_METASTORE' in serv_comp_hosts['HIVE'] and \
            'HIVE_SERVER' in serv_comp_hosts['HIVE']:
        if len(serv_comp_hosts['HIVE']['HIVE_METASTORE']) > 1 or \
                len(serv_comp_hosts['HIVE']['HIVE_SERVER']) > 1:
            generate_hivesite_ha(serv_comp_hosts['HIVE'])
        else:
            bp_set_conf_prop('core-site',
                             'hadoop.proxyuser.hive.hosts',
                             fqdn(serv_comp_hosts['HIVE']
                                  .get('HIVE_METASTORE')[0]))
            bp_set_conf_prop('core-site',
                             'hadoop.proxyuser.hcat.hosts',
                             fqdn(serv_comp_hosts['HIVE']
                                  .get('WEBHCAT_SERVER')[0]))
            generate_hivesite(serv_comp_hosts['HIVE'])
            generate_hiveenv(serv_comp_hosts['HIVE'])
            generate_webhcatsite(serv_comp_hosts['HIVE'])


def generate_hivesite(hive_comp):
    hm = fqdn(hive_comp['HIVE_METASTORE'][0])
    site = 'hive-site'
    bp_set_conf_prop(site,
                     'hive.exec.compress.output',
                     'false')
    bp_set_conf_prop(site,
                     'hive.merge.mapfiles',
                     'true')
    bp_set_conf_prop(site,
                     'hive.server2.tez.initialize.default.sessions',
                     'false')
    bp_set_conf_prop(site,
                     'hive.server2.transport.mode',
                     'binary')
    bp_set_conf_prop(site,
                     'javax.jdo.option.ConnectionDriverName',
                     'org.postgresql.Driver')
    bp_set_conf_prop(site,
                     'javax.jdo.option.ConnectionURL',
                     'jdbc:postgresql://%s:5432/hive' % get_pgsqlserver_host())
    bp_set_conf_prop(site,
                     'javax.jdo.option.ConnectionUserName',
                     'hive')
    bp_set_conf_prop(site,
                     'hive.metastore.uris',
                     'thrift://%s:9083' % hm)


def generate_hiveenv(hive_comp):
    env = 'hive-env'
    bp_set_conf_prop(env,
                     'hive_database',
                     'Existing PostgreSQL Database')
    bp_set_conf_prop(env,
                     'hive_database_name',
                     'hive')
    bp_set_conf_prop(env,
                     'hive_database_type',
                     'postgres')


def generate_webhcatsite(hive_comp):
    pass


def generate_hivesite_ha(hive_comp):
    raise ex.CreationError('service', 'HIVE', 'mode', 'High Availability',
                           'NotSupported')


def complete_conf_hbase(serv_comp_hosts):
    if 'HBASE_MASTER' in serv_comp_hosts['HBASE']:
        if len(serv_comp_hosts['HBASE']['HBASE_MASTER']) > 1:
            generate_hbasesite_ha(serv_comp_hosts['HBASE'])
        else:
            generate_hbasesite(serv_comp_hosts['HBASE'])
            generate_hbaseenv(serv_comp_hosts['HBASE'])


def generate_hbasesite(hbase_comp):
    site = 'hbase-site'
    bp_set_conf_prop(site,
                     'hbase.master.info.port',
                     '16010')
    bp_set_conf_prop(site,
                     'hbase.regionserver.handler.count',
                     '30')
    bp_set_conf_prop(site,
                     'hbase.regionserver.port',
                     '16020')
    bp_set_conf_prop(site,
                     'hbase.regionserver.info.port',
                     '16030')
    bp_set_conf_prop(site,
                     'hbase.rootdir',
                     '/apps/hbase/data')
    bp_set_conf_prop(site,
                     'hbase.rpc.protection',
                     'authentication')
    bp_set_conf_prop(site,
                     'hbase.security.authentication',
                     'simple')
    bp_set_conf_prop(site,
                     'hbase.security.authorization',
                     'false')
    bp_set_conf_prop(site,
                     'hbase.superuser',
                     'hbase')
    bp_set_conf_prop(site,
                     'hbase.tmp.dir',
                     '/tmp/hbase')
    bp_set_conf_prop(site,
                     'hbase.zookeeper.property.clientPort',
                     '2181')
    bp_set_conf_prop(site,
                     'zookeeper.znode.parent',
                     '/hbase-unsecure')


def generate_hbaseenv(hbase_comp):
    env = 'hbase-env'
    bp_set_conf_prop(env,
                     'hbase_user',
                     'hbase')


def generate_hbasesite_ha(hbase_comp):
    raise ex.CreationError('service', 'HBASE', 'mode', 'High Availability',
                           'NotSupported')


def generate_blueprint_hostgroups():
    """Complete the 'host_groups' section of the blueprint.

    """

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
    """Return the cluster file JSON.
    """

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
