import click

import os
import json
import pathlib
from distutils.dir_util import copy_tree
from shutil import rmtree

from jumbo.utils.settings import JUMBODIR
from jumbo.utils import session as ss, exceptions as ex


def check_cluster(name):
    return os.path.isdir(JUMBODIR + name)


def check_config(name):
    return os.path.isfile(JUMBODIR + name + '/jumbo_config')


def create_cluster(name):
    if check_cluster(name):
        raise ex.CreationError('cluster', name, 'name', name)

    pathlib.Path(JUMBODIR + name).mkdir(parents=True)
    empty_dir = os.path.dirname(os.path.abspath(__package__)) + \
        '/jumbo/data/empty'
    copy_tree(empty_dir, JUMBODIR + name)
    ss.clear()
    ss.svars['cluster'] = name
    ss.dump_config()
    return True


def load_cluster(name):
    if not check_cluster(name):
        raise ex.LoadError('cluster', name, 'NotExist')

    if not check_config(name):
        raise ex.LoadError('cluster', name, 'NoConfFile')
    else:
        try:
            ss.load_config(name)
        except IOError as e:
            raise ex.LoadError('cluster', name, e.strerror)

    return True


def repair_cluster(name):
    if not check_config(name):
        ss.clear()
        ss.svars['cluster'] = name
        ss.dump_config()
        return True

    return False


def switch_cluster(name):
    switched = False
    loaded = True

    if ss.svars['cluster'] != name:
        if ss.load_config(name):
            switched = True
        else:
            loaded = False

    return switched, loaded


def delete_cluster(name):
    if not check_cluster(name):
        raise ex.LoadError('cluster', name, 'NotExist')
    try:
        rmtree(JUMBODIR + name)
    except IOError as e:
        raise ex.LoadError('cluster', name, e.strerror)

    ss.clear()
    return True


def list_clusters():
    path_list = [f.path for f in os.scandir(JUMBODIR) if f.is_dir()]
    clusters = []

    for p in path_list:
        if not check_config(p.split('/')[-1]):
            raise ex.LoadError('cluster', p.split('/')[-1], 'NoConfFile')

        with open(p + '/jumbo_config') as cfg:
            clusters += [json.load(cfg)]

    return clusters


def list_machines(cluster):
    if not cluster:
        raise ex.LoadError('cluster', None, 'NoContext')

    if not check_cluster(cluster):
        raise ex.LoadError('cluster', cluster, 'NotExist')

    if cluster != ss.svars['cluster']:
        try:
            with open(JUMBODIR + cluster + '/jumbo_config', 'r') as clf:
                cluster_conf = json.load(clf)
        except IOError as e:
            raise ex.LoadError('cluster', cluster, e.strerror)
    else:
        cluster_conf = ss.svars

    return cluster_conf['machines']
