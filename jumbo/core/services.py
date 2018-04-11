import os
import json

from jumbo.core import machines as vm, clusters
from jumbo.utils import exceptions as ex, session as ss


def load_services_conf():
    with open(os.path.dirname(os.path.abspath(__package__)) +
              '/jumbo/config/services.json') as cfg:
        return json.load(cfg)


config = load_services_conf()


def check_component(name):
    for s in config['services']:
        for c in s['components']:
            if name == c['name']:
                return s['name']
    return False


def check_component_machine(name, machine):
    if name in machine['components']:
        return True
    else:
        return False


def add_component(name, machine, cluster):

    switched = False

    if not cluster:
        raise ex.LoadError('cluster', None, 'NoContext')
    elif cluster != ss.svars['cluster']:
        if ss.svars['cluster']:
            raise ex.LoadError('cluster', ss.svars['cluster'], 'MustExit')
        else:
            switched = True

    if not vm.check_machine(cluster, machine):
        raise ex.LoadError('machine', machine, 'NotExist')

    clusters.load_cluster(cluster)

    service = check_component(name)
    if not service:
        raise ex.LoadError('component', name, 'NotExist')

    for i, m in enumerate(ss.svars['machines']):
        if m['name'] == machine:
            m_index = i

    if check_component_machine(name, ss.svars['machines'][m_index]):
        raise ex.CreationError('machine', machine, 'component', name,
                               'Installed')

    ss.svars['machines'][m_index]['components'] += [name]
    ss.dump_config()

    return switched
