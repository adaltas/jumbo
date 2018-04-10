import click

import os
import json
import pathlib
from distutils.dir_util import copy_tree
from shutil import rmtree

from jumbo.utils.settings import JUMBODIR
from jumbo.utils import session as ss


def check_cluster(name):
    return os.path.isdir(JUMBODIR + name)


def create_cluster(name):
    if check_cluster(name):
        return False

    pathlib.Path(JUMBODIR + name).mkdir(parents=True)
    empty_dir = os.path.dirname(os.path.abspath(__package__)) + \
        '/jumbo/data/empty'
    copy_tree(empty_dir, JUMBODIR + name)
    ss.clear()
    ss.svars['cluster'] = name
    ss.dump_config()
    return True


def load_cluster(name):
    exists = True
    loaded = True

    if not check_cluster(name):
        exists = False
        loaded = False
        return exists, loaded

    if not ss.load_config(name):
        loaded = False
        ss.svars['cluster'] = name
        ss.dump_config()

    return exists, loaded


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
    if check_cluster(name):
        rmtree(JUMBODIR + name)
        return True
    else:
        return False


def list_clusters():
    path_list = [f.path for f in os.scandir(JUMBODIR) if f.is_dir()]
    clusters = []

    for p in path_list:
        with open(p + '/jumbo_config') as cfg:
            clusters += [json.load(cfg)]

    return clusters
