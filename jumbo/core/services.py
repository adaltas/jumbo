import os
import json

from jumbo.core import machines as vm, clusters
from jumbo.utils import exceptions as ex, session as ss
from jumbo.utils.settings import JUMBODIR
from jumbo.utils.checks import valid_cluster


def load_services_conf():
    with open(os.path.dirname(os.path.abspath(__file__)) +
              '/../config/services.json') as cfg:
        return json.load(cfg)


config = load_services_conf()


def check_service(name):
    for s in config['services']:
        if s['name'] == name:
            return True
    return False


def check_service_cluster(name):
    for s in ss.svars['services']:
        if s == name:
            return True
    return False


def check_component(name):
    for s in config['services']:
        for c in s['components']:
            if name == c['name']:
                return s['name']
    return False


def check_component_machine(name, machine):
    return name in machine['components']


@valid_cluster
def add_component(name, *, machine, cluster):
    switched = False

    if not vm.check_machine(cluster=cluster, machine=machine):
        raise ex.LoadError('machine', machine, 'NotExist')

    ss.load_config(cluster)

    service = check_component(name)
    if not service:
        raise ex.LoadError('component', name, 'NotExist')

    for i, m in enumerate(ss.svars['machines']):
        if m['name'] == machine:
            m_index = i

    missing_serv, missing_comp = check_service_req_service(service)
    if missing_serv:
        raise ex.CreationError('component', name, 'services', missing_serv,
                               'ReqNotMet')
    if missing_comp:
        print_missing = []
        for k, v in missing_comp.items():
            print_missing.append('{} {}'.format(v, k))
        raise ex.CreationError('component', name, 'components', print_missing,
                               'ReqNotMet')

    if check_component_machine(name, ss.svars['machines'][m_index]):
        raise ex.CreationError('machine', machine, 'component', name,
                               'Installed')

    ss.svars['machines'][m_index]['components'].append(name)
    ss.dump_config()

    return switched


@valid_cluster
def add_service(name, *, cluster):
    switched = False

    if not check_service(name):
        raise ex.LoadError('service', name, 'NotExist')

    ss.load_config(cluster)

    missing_serv, missing_comp = check_service_req_service(name)
    if missing_serv:
        raise ex.CreationError('service', name, 'services', missing_serv,
                               'ReqNotMet')
    if missing_comp:
        print_missing = []
        for k, v in missing_comp.items():
            print_missing.append('{} {}'.format(v, k))
        raise ex.CreationError('service', name, 'components', print_missing,
                               'ReqNotMet')

    ss.svars['services'].append(name)
    ss.dump_config()

    return switched


def check_service_req_service(name, ha=False):
    req = 'ha' if ha else 'default'
    missing_serv = []
    missing_comp = {}
    for s in config['services']:
        if s['name'] == name:
            for req_s in s['requirements']['services'][req]:
                if req_s not in ss.svars['services']:
                    missing_serv.append(req_s)
                missing_comp.update(check_service_req_comp(req_s))
            return missing_serv, missing_comp
    raise ex.LoadError('service', name, 'NotExist')


def check_service_req_comp(name, ha=False):
    req = 'ha' if ha else 'default'
    missing = {}
    comp_count = count_components()
    for s in config['services']:
        if s['name'] == name:
            for comp in s['components']:
                missing_count = comp['number'][req] - comp_count[comp['name']]
                if missing_count > 0:
                    missing[comp['name']] = missing_count
            return missing
    raise ex.LoadError('service', name, 'NotExist')


def count_components():
    components = get_available_components()
    for machine in ss.svars['machines']:
        for c in machine['components']:
            components[c] += 1
    return components


def get_available_components():
    components = {}
    for s in config['services']:
        for c in s['components']:
            components[c['name']] = 0
    return components


def get_service_components(name):
    components = []
    for s in config['services']:
        if s['name'] == name:
            for c in s['components']:
                components.append(c['name'])
    return components


@valid_cluster
def remove_service(service, *, cluster):
    switched = False

    if not check_service(service):
        raise ex.LoadError('service', service, 'NotExist')

    ss.load_config(cluster)

    if not check_service_cluster(service):
        raise ex.CreationError(
            'cluster', cluster, 'service', service, 'NotInstalled')

    serv_comp = get_service_components(service)
    for m in ss.svars['machines']:
        for c in m['components']:
            if c in serv_comp:
                m['components'].remove(c)

    ss.svars['services'].remove(service)
    ss.dump_config()

    return switched


@valid_cluster
def remove_component(component, *, machine, cluster):
    switched = False

    if not vm.check_machine(cluster=cluster, machine=machine):
        raise ex.LoadError('machine', machine, 'NotExist')

    ss.load_config(cluster)

    service = check_component(component)
    if not service:
        raise ex.LoadError('component', component, 'NotExist')

    for i, m in enumerate(ss.svars['machines']):
        if m['name'] == machine:
            m_index = i

    if not check_component_machine(component, ss.svars['machines'][m_index]):
        raise ex.CreationError('machine', machine, 'component', component,
                               'NotInstalled')

    ss.svars['machines'][m_index]['components'].remove(component)
    ss.dump_config()

    return switched


@valid_cluster
def list_components(*, machine, cluster):
    if not vm.check_machine(cluster=cluster, machine=machine):
        raise ex.LoadError('machine', machine, 'NotExist')

    if cluster != ss.svars['cluster']:
        try:
            with open(JUMBODIR + cluster + '/jumbo_config', 'r') as clf:
                cluster_conf = json.load(clf)
        except IOError as e:
            raise ex.LoadError('cluster', cluster, e.strerror)
    else:
        cluster_conf = ss.svars

    for m in cluster_conf['machines']:
        if m['name'] == machine:
            m_conf = m

    return m_conf['components']
