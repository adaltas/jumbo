import click

import os
import json
import pathlib
from distutils.dir_util import copy_tree
from shutil import rmtree

from jumbo.utils.settings import JUMBODIR
from jumbo.utils import session as ss, exceptions as ex
from jumbo.utils.checks import valid_cluster


def check_cluster(name):
    """Return true if the cluster exists.

    :param name: Cluster name
    :type name: str
    """
    return os.path.isdir(JUMBODIR + name)


def check_config(name):
    """Return true if the cluster has a `jumbo_config` file.

    :param name: Cluster name
    :type name: str
    """
    return os.path.isfile(JUMBODIR + name + '/jumbo_config')


def create_cluster(cluster, domain):
    """Create a new cluster and load it in the session.

    :param name: New cluster name
    :type name: str
    :param domain: New cluster domain name
    :type domain: str
    :raises ex.CreationError: If name already used
    :return: True on creation success
    """
    if check_cluster(cluster):
        raise ex.CreationError('cluster', cluster, 'name', cluster, 'Exists')

    pathlib.Path(JUMBODIR + cluster).mkdir(parents=True)
    data_dir = os.path.dirname(os.path.abspath(__file__)) + '/../data/'
    copy_tree(data_dir, JUMBODIR + cluster)
    ss.clear()
    ss.svars['cluster'] = cluster
    ss.svars['domain'] = domain if domain else '%s.local' % cluster
    ss.dump_config()
    return True


@valid_cluster
def repair_cluster(domain, *, cluster):
    """Recreate the cluster `jumbo_config` file if it doesn't exist.

    :param name: Cluster name
    :type name: str
    :param domain: Cluster domaine name
    :type domain: str
    :return: True if the `jumbo_config` has been recreated
    """
    if not check_config(cluster):
        ss.clear()
        ss.svars['cluster'] = cluster
        ss.svars['domain'] = domain if domain else '%s.local' % cluster
        ss.dump_config()
        return True

    return False


@valid_cluster
def delete_cluster(*, cluster):
    """Delete a cluster.

    :param name: Cluster name
    :type name: str
    :raises ex.LoadError: If the cluster doesn't exist
    :return: True if the deletion was successfull
    """
    try:
        rmtree(JUMBODIR + cluster)
    except IOError as e:
        raise ex.LoadError('cluster', cluster, e.strerror)

    ss.clear()
    return True


def list_clusters():
    """List all the clusters managed by Jumbo.

    :raises ex.LoadError: If a cluster doesn't have a `jumbo_config` file
    :return: The list of clusters' configurations
    :rtype: dict
    """
    path_list = [f.path for f in os.scandir(JUMBODIR) if f.is_dir()]
    clusters = []

    for p in path_list:
        if not check_config(p.split('/')[-1]):
            raise ex.LoadError('cluster', p.split('/')[-1], 'NoConfFile')

        with open(p + '/jumbo_config') as cfg:
            clusters += [json.load(cfg)]

    return clusters


@valid_cluster
def list_machines(*, cluster):
    """List the machines of a cluster.

    :param cluster: Cluster name
    :type cluster: str
    :return: The list of the cluster's machines
    :rtype: dict
    """
    ss.load_config(cluster)
    return ss.svars['machines']
