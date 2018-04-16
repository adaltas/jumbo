from jumbo.utils import session as ss, exceptions as ex
from jumbo.utils.settings import JUMBODIR
from jumbo.utils.checks import valid_cluster
from jumbo.core import clusters

import json


@valid_cluster
def add_machine(name, ip, ram, disk, types, cpus=1, *,
                cluster=ss.svars['cluster']):
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

    if check_machine(cluster=cluster, machine=name):
        raise ex.CreationError('machine', name, 'name', name, 'Exists')

    if check_ip(ip, cluster=cluster):
        raise ex.CreationError('machine', name, 'IP', ip, 'Exists')

    m = {
        'name': name,
        'ip': ip,
        'ram': ram,
        'disk': disk,
        'types': types,
        'cpus': cpus,
        'components': [],
        'groups': []
    }

    ss.load_config(cluster=cluster)

    ss.add_machine(m)
    ss.dump_config()

    return switched


@valid_cluster
def remove_machine(*, cluster, machine):
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
    ss.load_config(cluster)

    if not check_machine(cluster=cluster, machine=machine):
        raise ex.LoadError('machine', machine, 'NotExist')

    for i, m in enumerate(ss.svars['machines']):
        if m['name'] == machine:
            del(ss.svars['machines'][i])
    ss.dump_config()

    return switched


@valid_cluster
def check_machine(*, cluster, machine):
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
    for m in ss.svars['machines']:
        if m['name'] == machine:
            return True

    return False


@valid_cluster
def check_ip(ip, *, cluster):
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

    for m in ss.svars['machines']:
        if m['ip'] == ip:
            return m['name']

    return False
