from jumbo.core import clusters
from jumbo.utils import session as ss
from jumbo.utils import exceptions as ex


def valid_cluster(func):
    """Check if the cluster is valid.

    :raises ex.LoadError: if the cluster is not defined, does not exist, or is
    different from the currently managed cluster.
    """
    def check_and_call(*args, **kwargs):
        if not kwargs['cluster']:
            raise ex.LoadError('cluster', None, 'NoContext')
        elif kwargs['cluster'] != ss.svars['cluster']:
            if ss.svars['cluster']:
                raise ex.LoadError('cluster', ss.svars['cluster'], 'MustExit')
        elif not clusters.check_cluster(kwargs['cluster']):
            raise ex.LoadError('cluster', kwargs['cluster'], 'NotExist')

        return func(*args, **kwargs)
    return check_and_call

