import click

import os
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


def delete_cluster(name):
    rmtree(JUMBODIR + name)
