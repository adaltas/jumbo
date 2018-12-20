import os

from jumbo.utils import exceptions as ex, session as ss
from jumbo.utils.settings import JUMBODIR
from jumbo.utils.checks import valid_cluster
from jumbo.core import services


def list_bundles():
    """List bundles of the current cluster and available bundles"""

    path_list = [f.path.split('/')[-1]
                 for f in os.scandir(JUMBODIR+'bundles') if f.is_dir()]
    return (ss.svars.get('bundles', []), path_list)


@valid_cluster
def add_bundle(*, name=None, git=None, cluster, position='last'):
    """Add a bundle to the current cluster"""

    if name is None and git is None:
        raise RuntimeError(
            'addbundle: invalid arguments. name or git required')

    (active, available) = list_bundles()

    if name is None:
        name = git.split('/')[-1].split('.git')[0]

    if name in active:
        raise Warning('addbundle: bundle `%s` already active.' % name)
    if name not in available:
        clone_bundle(name=name, git=git)

    if position == 'last':
        ss.svars['bundles'].append(name)
    elif position == 'first':
        ss.svars['bundles'].insert(0, name)
    else:
        if not position.isdigit():
            raise RuntimeError(
                'addbundle: invalid value for position. '
                'Can be `last` (default), `first`, or a number.')

        ss.svars['bundles'].insert(int(position), name)

    services.config = services.load_services_conf(cluster=cluster)
    ss.dump_config(services.get_services_components_hosts(),
                   services.config)


@valid_cluster
def rm_bundle(*, name, cluster):
    """Remove bundle from the current cluster"""

    (active, available) = list_bundles()
    if name not in available:
        raise RuntimeError('Bundle `%s` does not exist.' % name)

    if name in active:
        index = active.index(name)
        ss.svars['bundles'].remove(name)
        services.config = services.load_services_conf(cluster=cluster)

        available_serv = []
        for serv in services.config['services']:
            available_serv.append(serv['name'])

        for serv in ss.svars['services']:
            if serv not in available_serv:
                active.insert(index, name)
                services.config = services.load_services_conf(cluster=cluster)
                raise RuntimeError('Cannot remove bundle `%s`. '
                                   'Service `%s` belongs to this bundle '
                                   'and is present on the cluster.'
                                   % (name, serv))

        ss.dump_config(services.get_services_components_hosts(),
                       services.config)
    else:
        raise Warning('Bundle `%s` is not active.' % name)


def clone_bundle(*, name=None, git):
    """Clone bundle from git repository."""

    (_, available) = list_bundles()
    if name is None:
        name = git.split('/')[-1].split('.git')[0]

    if name in available:
        raise Warning(
            'registerbundle: a bundle with the name `%s` already exists. \
             Use `updatebundle` to update it.')

    # TODO


def update_bundle(name):
    """Update the given bundle (git pull)"""
    pass
