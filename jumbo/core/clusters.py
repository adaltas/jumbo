import os
import json
import pathlib
import string
import subprocess
import time
from distutils import dir_util
from shutil import rmtree

from jumbo.utils.settings import JUMBODIR
from jumbo.utils import session as ss, exceptions as ex
from jumbo.utils import checks
from jumbo.utils import vagrant
from jumbo.utils import ambari
from jumbo.core import services


def check_config(name):
    """Return true if the cluster has a 'jumbo_config' file.

    :param name: Cluster name
    :type name: str
    """
    return os.path.isfile(JUMBODIR + 'clusters/' + name + '/jumbo_config')


def create_cluster(domain, template=None,
                   remote=None, realm=None, *, cluster):
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

    # clear current session
    ss.clear()

    if template:
        # Load template is session var
        try:
            with open(JUMBODIR + 'templates/' + template + '.json') \
                    as template_file:
                ss.svars = json.load(template_file)
        except:
            raise ex.LoadError('template', template, 'NotExist')

    pathlib.Path(JUMBODIR + 'clusters/' + cluster +
                 '/inventory/group_vars').mkdir(parents=True)
    pathlib.Path(JUMBODIR + 'clusters/' + cluster +
                 '/inventory/host_vars').mkdir(parents=True)

    ss.svars['cluster'] = cluster
    ss.svars['domain'] = domain or '%s.local' % cluster
    ss.svars['realm'] = realm or ss.svars['domain'].upper()
    ss.svars['location'] = 'remote' if remote else 'local'
    # Add basic bundle if no bundle is set via templates
    if not ss.svars['bundles']:
        ss.svars['bundles'].append('jumbo-services')

    services_components_hosts = services.get_services_components_hosts() \
        if template else None

    # Save session in jumbo_config
    ss.dump_config(services_components_hosts, services.config)
    # Load services configurations from [bundles]/services/*.json
    services.config = services.load_services_conf(cluster=cluster)

    return True


@checks.valid_cluster
def repair_cluster(domain, remote=None, *, cluster):
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
        ss.svars['location'] = 'remote' if remote else 'local'
        if not ss.svars['bundles']:
            ss.svars['bundles'].append('jumbo-services')

        ss.dump_config()
        services.config = services.load_services_conf(cluster=cluster)
        return True

    return False


@checks.valid_cluster
def delete_cluster(*, cluster):
    """Delete a cluster.

    :param name: Cluster name
    :type name: str
    :raises ex.LoadError: If the cluster doesn't exist
    """
    try:
        ss.load_config(cluster=cluster)
        if ss.svars['location'] == 'local':
            vagrant.delete(cluster=cluster)
        rmtree(JUMBODIR + 'clusters/' + cluster)
    except IOError as e:
        raise ex.LoadError('cluster', cluster, e.strerror)

    ss.clear()


def list_clusters():
    """List all the clusters managed by Jumbo.

    :raises ex.LoadError: If a cluster doesn't have a 'jumbo_config' file
    :return: The list of clusters' configurations
    :rtype: dict
    """
    path_list = [f.path for f in os.scandir(JUMBODIR+'clusters') if f.is_dir()]
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
def start(no_provision, *, cluster):
    ss.load_config(cluster)

    if ss.svars["location"] == "remote":
        # TODO
        # start_services()
        pass
    else:  # local
        already_created = vagrant.vms_created(cluster=cluster)
        vagrant.start(cluster=cluster)
        if no_provision is False:
            if already_created is False:
                provision(cluster=cluster)
        start_services(cluster)


@checks.valid_cluster
def stop(*, cluster):
    ss.load_config(cluster)

    if ss.svars["location"] == "remote":
        # TODO
        pass
    else:  # local
        vagrant.stop(cluster=cluster)


@checks.valid_cluster
def status(*, cluster):
    ss.load_config(cluster)

    if ss.svars["location"] == "remote":
        # TODO
        pass
    else:  # local
        vagrant.status(cluster=cluster)


@checks.valid_cluster
def restart(*, cluster):
    ss.load_config(cluster)

    if ss.svars["location"] == "remote":
        # TODO
        pass
    else:  # local
        vagrant.restart(cluster=cluster)


@checks.valid_cluster
def provision(*, cluster):
    """Provision the cluster.

    Calls `deploy.yml` master plabyooks of each bundle
    """

    ss.load_config(cluster)

    for bundle in ss.svars['bundles']:
        cmd = ['ansible-playbook', 'playbooks/deploy.yml',
               '-i', os.path.join(JUMBODIR, 'clusters',
                                  cluster, 'inventory/')]
        try:
            res = subprocess.Popen(cmd,
                                   cwd=os.path.join(
                                       JUMBODIR, 'bundles', bundle),
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT)

            for line in res.stdout:
                print(line.decode('utf-8').rstrip())

        except KeyboardInterrupt:
            res.kill()


def start_services(cluster):
    """ Start all services on the loaded cluster.
    """
    if "AMBARI" in ss.svars['services']:
        ambari.start_services(cluster)
    else:
        raise ex.Error("Only Ambari is supported at the moment.")
