import json
import string

from jumbo.utils import session as ss, exceptions as ex
from jumbo.utils.checks import valid_cluster


@valid_cluster
def add_node(name, ip, ram, types, cpus=1, *,
             cluster):
    """Add a node to a cluster.

    :param name: Machine name
    :type name: str
    :param ip: Machine's IP address
    :type ip: str
    :param ram: Machine's allocated RAM in MB
    :type ram: int
    :param types: Machine's types
    :type types: list str
    :param cluster: Cluster in which to create the node
    :type cluster: str
    :param cpus: Machine's number of CPUs, defaults to 1
    :param cpus: int, optional
    :raises ex.LoadError: If the cluster doesn't exist or was not specified
    :raises ex.CreationError: If the node couldn't be created
    :return: True if the session context has changed
    :rtype: bool
    """
    if check_node(cluster=cluster, node=name):
        raise ex.CreationError('node', name, 'name', name, 'Exists')

    if check_ip(ip, cluster=cluster):
        raise ex.CreationError('node', name, 'IP', ip, 'Exists')

    if name[0] in string.digits:
        raise ex.CreationError('node', name, 'name',
                               'A node name cannot start with a digit.',
                               'NameNotAllowed')

    if 'ldap' in types:
        if len(types) > 1:
            raise ex.CreationError('node', name, 'type', 'ldap',
                                   'LDAPNotCompatible')

    m = {
        'name': name,
        'ip': ip,
        'ram': ram,
        'types': types,
        'cpus': cpus,
        'components': [],
        'groups': []
    }

    ss.load_config(cluster=cluster)
    ss.add_node(m)
    ss.dump_config()

@valid_cluster
def edit_node(name, ip, ram, cpus=1, *,
             cluster):
    """Modify an existing node in a cluster cluster.

    """
    if check_node(cluster=cluster, node=name):
        raise ex.CreationError('node', name, 'name', name, 'Exists')

    if check_ip(ip, cluster=cluster):
        raise ex.CreationError('node', name, 'IP', ip, 'Exists')

    if name[0] in string.digits:
        raise ex.CreationError('node', name, 'name',
                               'A node name cannot start with a digit.',
                               'NameNotAllowed')

    m = {
        'name': name,
        'ip': ip,
        'ram': ram,
        'cpus': cpus,
    }

    ss.load_config(cluster=cluster)
    ss.edit_node(m)
    ss.dump_config()


@valid_cluster
def remove_node(*, cluster, node):
    """Remove a node in a cluster.

    :param cluster: Cluster namee
    :type cluster: str
    :param name: Machine name
    :type name: str
    :raises ex.LoadError: If the node or the cluster couldn't be loaded
    :return: True if the session context has changed
    :rtype: bool
    """
    ss.load_config(cluster)

    if not check_node(cluster=cluster, node=node):
        raise ex.LoadError('node', node, 'NotExist')

    for i, m in enumerate(ss.svars['nodes']):
        if m['name'] == node:
            del(ss.svars['nodes'][i])

    ss.dump_config()


@valid_cluster
def check_node(*, cluster, node):
    """
    Check if a node with a specified name exists in a specific cluster.

    :param cluster: Cluster name
    :type cluster: str
    :param name: Machine name
    :type name: str
    :raises ex.LoadError: If the cluster couldn't be loaded
    :return: True if the node exists
    :rtype: bool
    """
    for m in ss.svars['nodes']:
        if m['name'] == node:
            return True

    return False


@valid_cluster
def check_ip(ip, *, cluster):
    """
    Check if a node with a specified ip is used in a specific cluster.

    :param cluster: Cluster name
    :type cluster: str
    :param ip: IP address to be tested
    :type name: str
    :raises ex.LoadError: If the cluster couldn't be loaded
    :return: True if the ip is used
    :rtype: bool
    """
    for m in ss.svars['nodes']:
        if m['ip'] == ip:
            return m['name']

    return False
