import os
import json
import pathlib
import string
import subprocess
from distutils import dir_util
from shutil import rmtree, copyfile

from jumbo.utils.settings import JUMBODIR, DEFAULT_URLS
from jumbo.utils import session as ss, exceptions as ex
from jumbo.utils import checks
from jumbo.core import services


def check_config(name):
    """Return true if the cluster has a 'jumbo_config' file.

    :param name: Cluster name
    :type name: str
    """
    return os.path.isfile(JUMBODIR + name + '/jumbo_config')


def create_cluster(domain, ambari_repo, vdf, template=None, *, cluster):
    """Create a new cluster and load it in the session.

    :param name: New cluster name
    :type name: str
    :param domain: New cluster domain name
    :type domain: str
    :raises ex.CreationError: If name already used
    :return: True on creation success
    """

    if checks.check_cluster(cluster):
        raise ex.CreationError('cluster', cluster, 'name', cluster, 'Exists')

    allowed_chars = string.ascii_letters + string.digits + '-'
    for l in cluster:
        if l not in allowed_chars:
            raise ex.CreationError('cluster', cluster, 'name',
                                   'Allowed characters: ' + allowed_chars,
                                   'NameNotAllowed')

    ss.clear()
    data_dir = os.path.dirname(os.path.abspath(__file__)) + '/data/'
    config_dir = os.path.dirname(os.path.abspath(__file__)) + '/config/'
    if template:
        try:
            with open(config_dir + 'templates/' + template + '.json') \
                    as template_file:
                ss.svars = json.load(template_file)
        except:
            raise ex.LoadError('template', template, 'NotExist')

    pathlib.Path(JUMBODIR + cluster).mkdir(parents=True)

    if not os.path.isfile(JUMBODIR + 'versions.json'):
        copyfile(config_dir + 'versions.json', JUMBODIR + 'versions.json')

    dir_util.copy_tree(data_dir, JUMBODIR + cluster)
    dir_util._path_created = {}
    ss.svars['cluster'] = cluster
    ss.svars['domain'] = domain if domain else '%s.local' % cluster
    ss.svars['urls']['ambari_repo'] = ambari_repo if ambari_repo \
        else DEFAULT_URLS['ambari_repo']
    ss.svars['urls']['vdf'] = vdf if vdf \
        else DEFAULT_URLS['vdf']

    services_components_hosts = None
    if template:
        services_components_hosts = services.get_services_components_hosts()

    ss.dump_config(services_components_hosts)
    return True


@checks.valid_cluster
def repair_cluster(domain,  ambari_repo, vdf, *, cluster):
    """Recreate the cluster 'jumbo_config' file if it doesn't exist.

    :param name: Cluster name
    :type name: str
    :param domain: Cluster domaine name
    :type domain: str
    :return: True if the 'jumbo_config' has been recreated
    """
    if not check_config(cluster):
        ss.clear()
        ss.svars['cluster'] = cluster
        ss.svars['domain'] = domain if domain else '%s.local' % cluster
        ss.svars['urls']['ambari_repo'] = ambari_repo if ambari_repo \
            else DEFAULT_URLS['ambari_repo']
        ss.svars['urls']['vdf'] = vdf if vdf \
            else DEFAULT_URLS['vdf']
        ss.dump_config()
        return True

    return False


@checks.valid_cluster
def delete_cluster(*, cluster):
    """Delete a cluster.

    :param name: Cluster name
    :type name: str
    :raises ex.LoadError: If the cluster doesn't exist
    :return: True if the deletion was successfull
    """
    try:
        # Vagrant destroy
        current_dir = os.getcwd()
        os.chdir(JUMBODIR + cluster + '/')
        subprocess.check_output(['vagrant', 'destroy', '-f'])
        os.chdir(current_dir)
        rmtree(JUMBODIR + cluster)
    except IOError as e:
        raise ex.LoadError('cluster', cluster, e.strerror)

    ss.clear()
    return True


def list_clusters():
    """List all the clusters managed by Jumbo.

    :raises ex.LoadError: If a cluster doesn't have a 'jumbo_config' file
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


@checks.valid_cluster
def list_nodes(*, cluster):
    """List the nodes of a cluster.

    :param cluster: Cluster name
    :type cluster: str
    :return: The list of the cluster's nodes
    :rtype: dict
    """
    ss.load_config(cluster)
    return ss.svars['nodes']


@checks.valid_cluster
def set_url(url, value, *, cluster):
    if url not in DEFAULT_URLS:
        raise ex.LoadError('URL', url, 'NotExist')

    if cluster != ss.svars['cluster']:
        ss.load_config(cluster)

    ss.svars['urls'][url] = value
    ss.dump_config()
