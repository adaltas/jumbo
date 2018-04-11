from jumbo.utils import session as ss, exceptions as ex
from jumbo.utils.settings import JUMBODIR
from jumbo.core import clusters

import json


def add_machine(name, ip, ram, disk, types, cluster, cpus=1):
    """Add a machine to a cluster.

    :param name: Machine name
    :type name: str
    :param ip: Machine's IP address
    :type ip: str
    :param ram: Machine's allocated RAM in MB
    :type ram: int
    :param disk: Machine's allocated disk in MB
    :type disk: int
    :param types: Machine's types
    :type types: dict
    :param cluster: Cluster in which to create the machine
    :type cluster: str
    :param cpus: Machine's number of CPUs, defaults to 1
    :param cpus: int, optional
    :raises ex.LoadError: If the cluster doesn't exist or was not specified
    :raises ex.CreationError: If the machine couldn't be created
    :return: True if the session context has changed
    :rtype: bool
    """

    switched = False

    if not cluster:
        raise ex.LoadError('cluster', None, 'NoContext')
    elif cluster != ss.svars['cluster']:
        if ss.svars['cluster']:
            raise ex.LoadError('cluster', ss.svars['cluster'], 'MustExit')
        else:
            switched = True

    if check_machine(cluster, name):
        raise ex.CreationError('machine', name, 'name', name)

    if check_ip(cluster, ip):
        raise ex.CreationError('machine', name, 'IP', ip)

    m = {
        'name': name,
        'ip': ip,
        'ram': ram,
        'disk': disk,
        'types': types,
        'cpus': cpus
    }

    clusters.load_cluster(cluster)

    ss.add_machine(m)
    ss.dump_config()

    return switched


def remove_machine(cluster, name):
    """Remove a machine in a cluster.

    :param cluster: Cluster namee
    :type cluster: str
    :param name: Machine name
    :type name: str
    :raises ex.LoadError: If the machine or the cluster couldn't be loaded
    :return: True if the session context has changed
    :rtype: bool
    """

    switched = False

    if not cluster:
        raise ex.LoadError('cluster', None, 'NoContext')
    elif cluster != ss.svars['cluster']:
        if ss.svars['cluster']:
            raise ex.LoadError('cluster', ss.svars['cluster'], 'MustExit')
        else:
            switched = True

    if not check_machine(cluster, name):
        raise ex.LoadError('machine', name, 'NotExist')

    clusters.load_cluster(cluster)

    for i, m in enumerate(ss.svars['machines']):
        if m['name'] == name:
            del(ss.svars['machines'][i])
    ss.dump_config()

    return switched


def check_machine(cluster, name):
    """
    Check if a machine with a specified name exists in a specific cluster.

    :param cluster: Cluster name
    :type cluster: str
    :param name: Machine name
    :type name: str
    :raises ex.LoadError: If the cluster couldn't be loaded
    :return: True if the machine exists
    :rtype: bool
    """

    if cluster != ss.svars['cluster']:
        if not clusters.check_cluster(cluster):
            raise ex.LoadError('cluster', cluster, 'NotExist')

        with open(JUMBODIR + cluster + '/jumbo_config', 'r') as clf:
            cluster_conf = json.load(clf)
    else:
        cluster_conf = ss.svars

    for m in cluster_conf['machines']:
        if m['name'] == name:
            return True

    return False


def check_ip(cluster, ip):
    """
    Check if a machine with a specified ip is used in a specific cluster.

    :param cluster: Cluster name
    :type cluster: str
    :param ip: IP address to be tested
    :type name: str
    :raises ex.LoadError: If the cluster couldn't be loaded
    :return: True if the ip is used
    :rtype: bool
    """

    if cluster != ss.svars['cluster']:
        if not clusters.check_cluster(cluster):
            raise ex.LoadError('cluster', cluster, 'NotExist')

        with open(JUMBODIR + cluster + '/jumbo_config', 'r') as clf:
            cluster_conf = json.load(clf)
    else:
        cluster_conf = ss.svars

    for m in cluster_conf['machines']:
        if m['ip'] == ip:
            return m['name']

    return False
