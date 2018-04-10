from jumbo.utils import session as ss, exceptions as ex
from jumbo.utils.settings import JUMBODIR
from jumbo.core import clusters

import json


def add_machine(name, ip, ram, disk, types, cluster, cpus=1):
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
