import os

from jumbo.core import clusters
from jumbo.utils import session as ss
from jumbo.utils import exceptions as ex
from jumbo.utils.settings import JUMBODIR


def valid_cluster(func):
    """Check if the cluster is valid.

    :raises ex.LoadError: if the cluster is not defined, does not exist, or is
    different from the currently managed cluster.
    """
    def check_and_call(*args, **kwargs):
        if not kwargs['cluster']:
            raise ex.LoadError('cluster', None, 'NoContext')
        elif not check_cluster(kwargs['cluster']):
            raise ex.LoadError('cluster', kwargs['cluster'], 'NotExist')
        elif kwargs['cluster'] != ss.svars['cluster']:
            if ss.svars['cluster']:
                raise ex.LoadError('cluster', ss.svars['cluster'], 'MustExit')

        return func(*args, **kwargs)
    return check_and_call


def check_cluster(name):
    """Return true if the cluster exists.

    :param name: Cluster name
    :type name: str
    """

    return os.path.isdir(JUMBODIR + 'clusters/' + name)
