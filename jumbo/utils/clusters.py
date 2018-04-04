import click

import os
import pathlib
from distutils.dir_util import copy_tree

from jumbo.utils.settings import JUMBODIR

def check_cluster(name):
    return os.path.isdir(JUMBODIR + name)


def create_cluster(name):
    if check_cluster(name):
        click.echo(click.style('Cluster already exists!', fg='red'), err=True)
        return False

    pathlib.Path(JUMBODIR + name).mkdir(parents=True)
    copy_tree('data/empty', JUMBODIR+name)
    return True
