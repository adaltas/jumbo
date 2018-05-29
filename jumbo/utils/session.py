from jinja2 import Environment, PackageLoader
import json
import yaml

from jumbo.utils import exceptions as ex, checks
from jumbo.utils.settings import JUMBODIR, NOT_HADOOP_COMP
from jumbo.core import clusters

svars = {
    'cluster': None,
    'domain': None,
    'nodes': [],
    'services': [],
    'urls': {
        'ambari_repo': None,
        'vdf': None
    }
}

jinja_env = Environment(
    loader=PackageLoader('jumbo.utils', 'templates'),
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
            vf.write(vagrant_temp.render(hosts=svars['nodes'],
                                         domain=svars['domain'],
                                         cluster=svars['cluster']))

        hosts_temp = jinja_env.get_template('hosts.j2')
        with open(JUMBODIR + svars['cluster'] + '/playbooks/inventory/hosts',
                  'w') as vf:
            vf.write(hosts_temp.render(hosts=svars['nodes']))

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

        if 'KERBEROS' in svars['services']:
            with open(JUMBODIR + svars['cluster'] +
                      '/playbooks/roles/kerberos-part1/files/krb5-conf.json',
                      'w') as krbf:
                json.dump(generate_krb5_conf(), krbf)

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
            with open(JUMBODIR + cluster + '/jumbo_config', 'r') as jc:
                svars = json.load(jc)
        except IOError as e:
            raise ex.LoadError('cluster', cluster, e.strerror)

    return True


def clear():
    """Reset the sessions variables.
    """

    global svars, bp
    svars = {
        'cluster': None,
        'nodes': [],
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


def generate_ansible_vars():
    """Generate the group_vars/all variables for Ansible playbooks.

    :return: The variables to write in group_vars/all
    :rtype: dict
    """

    pgsqlserver = ''

    for m in svars['nodes']:
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
        },
        'kerberos_enabled': ('KERBEROS' in svars['services'])
    }


def bp_create_conf_section(section):
    bp.get('configurations').append({
        section: {
            'properties': {}
        }
    })


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


def bp_set_conf(section, prop_dict):
    for k, v in prop_dict.items():
        bp_set_conf_prop(section, k, v)


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

    bp_create_conf_section('core-site')

    bp_set_conf_prop('core-site', 'fs.trash.interval', '360')

    if 'HDFS' in serv_comp_hosts:
        bp_create_conf_section('hdfs-site')
        complete_conf_hdfs(serv_comp_hosts)

    if 'YARN' in serv_comp_hosts:
        bp_create_conf_section('yarn-site')
        complete_conf_yarn(serv_comp_hosts)

    if 'HIVE' in serv_comp_hosts:
        bp_create_conf_section('hive-site')
        bp_create_conf_section('hive-env')
        bp_create_conf_section('webhcat-site')
        complete_conf_hive(serv_comp_hosts)

    if 'HBASE' in serv_comp_hosts:
        bp_create_conf_section('hbase-site')
        bp_create_conf_section('hbase-env')
        complete_conf_hbase(serv_comp_hosts)

    if 'SPARK2' in serv_comp_hosts:
        bp_create_conf_section('spark2-defaults')
        bp_create_conf_section('spark2-env')
        complete_conf_spark2(serv_comp_hosts)

    if 'ZEPPELIN' in serv_comp_hosts:
        bp_create_conf_section('zeppelin-env')
        bp_create_conf_section('zeppelin-config')
        complete_conf_zeppelin(serv_comp_hosts)

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
        if len(serv_comp_hosts['HDFS']['NAMENODE']) == 2:
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
    prop_dict = {
        'dfs.namenode.http-address': '%s:50070' % nn,
        'dfs.namenode.https-address': '%s:50470' % nn,
        'dfs.namenode.rpc-addres': '%s:8020' % nn
    }
    if hdfs_comp.get('SECONDARY_NAMENODE'):
        snn = fqdn(hdfs_comp['SECONDARY_NAMENODE'][0])
        prop_dict['dfs.namenode.secondary.http-address'] = '%s:50090' % snn
    bp_set_conf('hdfs-site', prop_dict)


def generate_hdfssite_ha(hdfs_comp):
    nn = 'nn%s' % svars['domain'].replace('.', '')
    nn1 = '%s' % fqdn(hdfs_comp['NAMENODE'][0])
    nn2 = '%s' % fqdn(hdfs_comp['NAMENODE'][1])
    prop_dict = {
        'dfs.nameservices': nn,
        'dfs.namenode.http-address': '%s:50070' % nn1,
        'dfs.namenode.http-address.%s.nn1' % nn: '%s:50070' % nn1,
        'dfs.namenode.http-address.%s.nn2' % nn: '%s:50070' % nn2,
        'dfs.namenode.https-address': '%s:50470' % nn1,
        'dfs.namenode.https-address.%s.nn1' % nn: '%s:50470' % nn1,
        'dfs.namenode.https-address.%s.nn2' % nn: '%s:50470' % nn2,
        'dfs.namenode.rpc-address.%s.nn1' % nn: '%s:8020' % nn1,
        'dfs.namenode.rpc-address.%s.nn2' % nn: '%s:8020' % nn2,
        'dfs.ha.namenodes.%s' % nn: 'nn1,nn2',
        'dfs.ha.fencing.methods': 'shell(/bin/true)',
        'dfs.client.failover.proxy.provider.%s' % nn:
            'org.apache.hadoop.hdfs.server.namenode.'
            'ha.ConfiguredFailoverProxyProvider',
        'dfs.ha.automatic-failover.enabled': 'true'
    }
    if 'JOURNALNODE' in hdfs_comp:
        prop_dict.update({
            'dfs.namenode.shared.edits.dir':
                'qjournal://{}/{}'.format(
                    ';'.join('%s:8485'
                             % fqdn(jn) for jn in hdfs_comp['JOURNALNODE']),
                    nn)
        })
    bp_set_conf('hdfs-site', prop_dict)


def complete_conf_yarn(serv_comp_hosts):
    if 'RESOURCEMANAGER' in serv_comp_hosts['YARN']:
        if len(serv_comp_hosts['YARN']['RESOURCEMANAGER']) == 2:
            generate_yarnsite_ha(serv_comp_hosts['YARN'])
        else:
            bp_set_conf_prop('core-site',
                             'hadoop.proxyuser.yarn.hosts',
                             fqdn(serv_comp_hosts['YARN']
                                  .get('RESOURCEMANAGER')[0]))
            generate_yarnsite(serv_comp_hosts['YARN'])


def generate_yarnsite(yarn_comp):
    rm = fqdn(yarn_comp['RESOURCEMANAGER'][0])
    container_max_memory = 1536
    node_max_containers = 100
    if 'NODEMANAGER' in yarn_comp:
        for m in svars['nodes']:
            if m['name'] in yarn_comp['NODEMANAGER']:
                if node_max_containers > int(m['ram'] / 1536):
                    node_max_containers = int(m['ram'] / 1536)
    node_max_memory = node_max_containers * container_max_memory

    prop_dict = {
        'yarn.resourcemanager.ha.enabled': 'false',
        'yarn.resourcemanager.recovery.enabled': 'true',
        'yarn.resourcemanager.store.class':
            'org.apache.hadoop.yarn.server.resourcemanager.'
            'recovery.ZKRMStateStore',
        'yarn.resourcemanager.address': '%s:8050' % rm,
        'yarn.resourcemanager.admin.address': '%s:8141' % rm,
        'yarn.resourcemanager.scheduler.address': '%s:8030' % rm,
        'yarn.resourcemanager.hostname': '%s' % rm,
        'yarn.resourcemanager.resource-tracker.address': '%s:8025' % rm,
        'yarn.resourcemanager.webapp.address': '%s:8088' % rm,
        'yarn.resourcemanager.webapp.https.address': '%s:8090' % rm,
        'yarn.nodemanager.resource.memory-mb': '%d' % node_max_memory,
        'yarn.scheduler.maximum-allocation-mb': '%d' % container_max_memory,
        'yarn.log.server.url': 'http://%s:19888/jobhistory/logs' % rm
    }
    if yarn_comp.get('APP_TIMELINE_SERVER'):
        timeline = fqdn(yarn_comp['APP_TIMELINE_SERVER'][0])
        prop_dict.update({
            'yarn.timeline-service.address': '%s:10200' % timeline,
            'yarn.timeline-service.webapp.address': '%s:8188' % timeline,
            'yarn.timeline-service.webapp.https.address': '%s:8190' % timeline
        })
    bp_set_conf('yarn-site', prop_dict)


def generate_yarnsite_ha(yarn_comp):
    rm1 = fqdn(yarn_comp['RESOURCEMANAGER'][0])
    rm2 = fqdn(yarn_comp['RESOURCEMANAGER'][1])
    container_max_memory = 1536
    node_max_containers = 100
    if 'NODEMANAGER' in yarn_comp:
        for m in svars['nodes']:
            if m['name'] in yarn_comp['NODEMANAGER']:
                if node_max_containers > int(m['ram'] / 1536):
                    node_max_containers = int(m['ram'] / 1536)
    node_max_memory = node_max_containers * container_max_memory

    prop_dict = {
        'yarn.resourcemanager.ha.enabled': 'true',
        'yarn.resourcemanager.ha.automatic-failover.zk-base-path':
            '/yarn-leader-election',
        'yarn.resourcemanager.cluster-id': 'yarn-cluster',
        'yarn.resourcemanager.ha.rm-ids': 'rm1,rm2',
        'yarn.resourcemanager.recovery.enabled': 'true',
        'yarn.resourcemanager.store.class':
            'org.apache.hadoop.yarn.server.resourcemanager.'
            'recovery.ZKRMStateStore',
        'yarn.resourcemanager.address': '%s:8050' % rm1,
        'yarn.resourcemanager.admin.address': '%s:8141' % rm1,
        'yarn.resourcemanager.scheduler.address': '%s:8030' % rm1,
        'yarn.resourcemanager.hostname': '%s' % rm1,
        'yarn.resourcemanager.hostname.rm1': '%s' % rm1,
        'yarn.resourcemanager.hostname.rm2': '%s' % rm2,
        'yarn.resourcemanager.resource-tracker.address': '%s:8025' % rm1,
        'yarn.resourcemanager.webapp.address': '%s:8088' % rm1,
        'yarn.resourcemanager.webapp.address.rm1': '%s:8088' % rm1,
        'yarn.resourcemanager.webapp.address.rm2': '%s:8088' % rm2,
        'yarn.resourcemanager.webapp.https.address': '%s:8090' % rm1,
        'yarn.resourcemanager.webapp.https.address.rm1': '%s:8090' % rm1,
        'yarn.resourcemanager.webapp.https.address.rm2': '%s:8090' % rm2,
        'yarn.nodemanager.resource.memory-mb': '%d' % node_max_memory,
        'yarn.scheduler.maximum-allocation-mb': '%d' % container_max_memory
    }
    if yarn_comp.get('APP_TIMELINE_SERVER'):
        timeline = fqdn(yarn_comp['APP_TIMELINE_SERVER'][0])
        prop_dict.update({
            'yarn.timeline-service.address': '%s:10200' % timeline,
            'yarn.timeline-service.webapp.address': '%s:8188' % timeline,
            'yarn.timeline-service.webapp.https.address': '%s:8190' % timeline,
            'yarn.log.server.url': 'http://%s:19888/jobhistory/logs' % timeline
        })
    bp_set_conf('yarn-site', prop_dict)


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
            if serv_comp_hosts['HIVE'].get('WEBHCAT_SERVER'):
                bp_set_conf_prop('core-site',
                                 'hadoop.proxyuser.hcat.hosts',
                                 fqdn(serv_comp_hosts['HIVE']
                                      .get('WEBHCAT_SERVER')[0]))
            generate_hivesite(serv_comp_hosts['HIVE'])
            generate_hiveenv(serv_comp_hosts['HIVE'])
            generate_webhcatsite(serv_comp_hosts['HIVE'])


def generate_hivesite(hive_comp):
    hm = fqdn(hive_comp['HIVE_METASTORE'][0])
    prop_dict = {
        'hive.exec.compress.output': 'false',
        'hive.merge.mapfiles': 'true',
        'hive.server2.tez.initialize.default.sessions': 'false',
        'hive.server2.transport.mode': 'binary',
        'javax.jdo.option.ConnectionDriverName': 'org.postgresql.Driver',
        'javax.jdo.option.ConnectionURL':
            'jdbc:postgresql://%s:5432/hive' % get_pgsqlserver_host(),
        'javax.jdo.option.ConnectionUserName': 'hive',
        'hive.metastore.uris': 'thrift://%s:9083' % hm
    }
    bp_set_conf('hive-site', prop_dict)


def generate_hiveenv(hive_comp):
    prop_dict = {
        'hive_database': 'Existing PostgreSQL Database',
        'hive_database_name': 'hive',
        'hive_database_type': 'postgres'
    }
    bp_set_conf('hive-env', prop_dict)


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
    prop_dict = {
        'hbase.master.info.port': '16010',
        'hbase.regionserver.handler.count': '30',
        'hbase.regionserver.port': '16020',
        'hbase.regionserver.info.port': '16030',
        'hbase.rootdir': '/apps/hbase/data',
        'hbase.rpc.protection': 'authentication',
        'hbase.security.authentication': 'simple',
        'hbase.security.authorization': 'false',
        'hbase.superuser': 'hbase',
        'hbase.tmp.dir': '/tmp/hbase',
        'hbase.zookeeper.property.clientPort': '2181',
        'zookeeper.znode.parent': '/hbase-unsecure'
    }
    bp_set_conf('hbase-site', prop_dict)


def generate_hbaseenv(hbase_comp):
    env = 'hbase-env'
    bp_set_conf_prop(env,
                     'hbase_user',
                     'hbase')


def generate_hbasesite_ha(hbase_comp):
    raise ex.CreationError('service', 'HBASE', 'mode', 'High Availability',
                           'NotSupported')


def complete_conf_spark2(serv_comp_hosts):
    if 'SPARK2_JOBHISTORYSERVER' in serv_comp_hosts['SPARK2']:
        generate_spark2defaults(serv_comp_hosts['SPARK2'])
        generate_spark2env(serv_comp_hosts['SPARK2'])


def generate_spark2defaults(spark2_comp):
    history_server = spark2_comp['SPARK2_JOBHISTORYSERVER'][0]
    ui_port = '18081'
    prop_dict = {
        'spark.history.ui.port': '%s' % ui_port,
        'spark.eventLog.dir': 'hdfs:///spark2-history/',
        'spark.eventLog.enabled': 'true',
        'hbase.regionserver.info.port': '16030',
        'spark.history.provider':
            'org.apache.spark.deploy.history.FsHistoryProvider',
        'spark.yarn.historyServer.address':
            '{}:{}'.format(history_server, ui_port),
        'spark.history.fs.logDirectory': 'hdfs:///spark2-history/'
    }
    bp_set_conf('spark2-defaults', prop_dict)


def generate_spark2env(spark2_comp):
    prop_dict = {
        'spark_user': 'spark',
        'spark_group': 'spark',
        'spark_pid_dir': '/var/run/spark2',
        'spark_log_dir': '/var/log/spark2',
        'spark_daemon_memory': '1024'
    }
    bp_set_conf('spark2-env', prop_dict)


def complete_conf_zeppelin(serv_comp_hosts):
    if 'ZEPPELIN_MASTER' in serv_comp_hosts['ZEPPELIN']:
        generate_zeppelinconfig()
        generate_zeppelinenv()


def generate_zeppelinconfig():
    prop_dict = {
        'zeppelin.server.port': '9995',
        'zeppelin.server.ssl.port': '9995',
        'zeppelin.server.addr': '0.0.0.0',
        'zeppelin.notebook.dir': 'notebook',
        'zeppelin.interpreters':
            'org.apache.zeppelin.spark.SparkInterpreter,'
            'org.apache.zeppelin.spark.PySparkInterpreter,'
            'org.apache.zeppelin.spark.SparkSqlInterpreter,'
            'org.apache.zeppelin.spark.DepInterpreter,'
            'org.apache.zeppelin.markdown.Markdown,'
            'org.apache.zeppelin.angular.AngularInterpreter,'
            'org.apache.zeppelin.shell.ShellInterpreter,'
            'org.apache.zeppelin.jdbc.JDBCInterpreter,'
            'org.apache.zeppelin.phoenix.PhoenixInterpreter,'
            'org.apache.zeppelin.livy.LivySparkInterpreter,'
            'org.apache.zeppelin.livy.LivyPySparkInterpreter,'
            'org.apache.zeppelin.livy.LivySparkRInterpreter,'
            'org.apache.zeppelin.livy.LivySparkSQLInterpreter',
        'zeppelin.ssl': 'false',
        'zeppelin.notebook.storage':
            'org.apache.zeppelin.notebook.repo.FileSystemNotebookRepo',
        'zeppelin.interpreter.dir': 'interpreter',
        'zeppelin.config.fs.dir': 'conf'
    }
    bp_set_conf('zeppelin-config', prop_dict)


def generate_zeppelinenv():
    prop_dict = {
        'zeppelin.executor.instances': '2',
        'zeppelin.executor.mem': '512m',
        'zeppelin_user': 'zeppelin',
        'zeppelin_group': 'zeppelin'
    }
    bp_set_conf('zeppelin-env', prop_dict)


def generate_blueprint_hostgroups():
    """Complete the 'host_groups' section of the blueprint.

    """

    for m in svars['nodes']:
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
    if component in NOT_HADOOP_COMP:
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


def generate_krb5_conf():
    krb5_conf_json = [
        {
            'Clusters': {
                'desired_configs': {
                    'type': 'krb5-conf',
                    'tag': 'version1',
                    'properties': {
                        'type': 'krb5-conf',
                        'tag': 'version1',
                        'properties': {
                            'domains': '',
                            'manage_krb5_conf': 'true',
                            'conf_dir': '/etc',
                            'content': '''
              [libdefaults]
                renew_lifetime = 7d
                forwardable = true
                default_realm = {{realm}}
                ticket_lifetime = 24h
                dns_lookup_realm = false
                dns_lookup_kdc = false
                default_ccache_name = /tmp/krb5cc_%{uid}
                #default_tgs_enctypes = {{encryption_types}}
                #default_tkt_enctypes = {{encryption_types}}
              {% if domains %}
              [domain_realm]
              {%- for domain in domains.split(',') %}
                {{domain|trim()}} = {{realm}}
              {%- endfor %}
              {% endif %}
              [logging]
                default = FILE:/var/log/krb5kdc.log
                admin_server = FILE:/var/log/kadmind.log
                kdc = FILE:/var/log/krb5kdc.log

              [realms]
                {{realm}} = {
              {%- if master_kdc %}
                  master_kdc = {{master_kdc|trim()}}
              {%- endif -%}
              {%- if kdc_hosts > 0 -%}
              {%- set kdc_host_list = kdc_hosts.split(',')  -%}
              {%- if kdc_host_list and kdc_host_list|length > 0 %}
                  admin_server = {{admin_server_host|default(kdc_host_list[0]|trim(), True)}}
              {%- if kdc_host_list -%}
              {%- if master_kdc and (master_kdc not in kdc_host_list) %}
                  kdc = {{master_kdc|trim()}}
              {%- endif -%}
              {% for kdc_host in kdc_host_list %}
                  kdc = {{kdc_host|trim()}}
              {%- endfor -%}
              {% endif %}
              {%- endif %}
              {%- endif %}
                }

              {# Append additional realm declarations below #}
              '''
                        }
                    }
                }
            }
        },
        {
            'Clusters': {
                'desired_config': {
                    'type': 'kerberos-env',
                    'tag': 'version1',
                    'properties': {
                        'kdc_type': 'ipa',
                        'manage_identities': 'false',
                        'create_ambari_principal': 'false',
                        'manage_auth_to_local': 'true',
                        'install_packages': 'true',
                        'encryption_types':
                            'aes des3-cbc-sha1 rc4 des-cbc-md5',
                        'realm': svars['domain'].upper(),
                        'kdc_hosts': get_ipaserver_host(),
                        'admin_server_host': get_ipaserver_host(),
                        'executable_search_paths': '/usr/bin, '
                        '/usr/kerberos/bin, '
                        '/usr/sbin, '
                        '/usr/lib/mit/bin, '
                        '/usr/lib/mit/sbin',
                        'password_length': '20',
                        'password_min_lowercase_letters': '1',
                        'password_min_uppercase_letters': '1',
                        'password_min_digits': '1',
                        'password_min_punctuation': '1',
                        'password_min_whitespace': '0',
                        'service_check_principal_name':
                            '${cluster_name}-${short_date}',
                        'case_insensitive_username_rules': 'false',
                        'preconfigure_services': 'DEFAULT',
                        'set_password_expiracy': 'false',
                        'group': 'ambari-managed-principals'
                    }
                }
            }
        }
    ]

    return krb5_conf_json
