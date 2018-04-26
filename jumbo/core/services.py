import os
import json

from jumbo.core import machines as vm, clusters
from jumbo.utils import exceptions as ex, session as ss
from jumbo.utils.settings import JUMBODIR
from jumbo.utils.checks import valid_cluster


def load_services_conf():
    """Load the global services configuration.

    :return: The configuration JSON file
    :rtype: json
    """

    with open(os.path.dirname(os.path.abspath(__file__)) +
              '/../config/services.json') as cfg:
        return json.load(cfg)


config = load_services_conf()


def check_service(name):
    """Check if a service exists.

    :param name: Service name
    :type name: str
    :return: True if the service exists
    """

    for s in config['services']:
        if s['name'] == name:
            return s
    return False


def check_service_cluster(name):
    """Check if a service is installed on the session cluster.

    :param name: Service name
    :type name: str
    :return: True if the service is installed
    """

    for s in ss.svars['services']:
        if s == name:
            return True
    return False


def check_component(name):
    """Check if a component exists.

    :param name: Component name
    :type name: str
    :return: The service of the component if the component exists
    """

    for s in config['services']:
        for c in s['components']:
            if name == c['name']:
                return s['name']
    return False


def add_component(name, machine, cluster):
    """Add a component to a specified machine of a specified.

    :param name: Component name
    :type name: str
    :param machine: Machine name
    :type machine: str
    :param cluster: Cluster name
    :type cluster: str
    :raises ex.LoadError: [description]
    :raises ex.CreationError: [description]
    """

    for i, m in enumerate(ss.svars['machines']):
        if m['name'] == machine:
            m_index = i
            break
    else:
        raise ex.LoadError('machine', machine, 'NotExist')

    service = check_component(name)
    if not service:
        raise ex.LoadError('component', name, 'NotExist')

    if not check_service_cluster(service):
        raise ex.CreationError(
            'cluster', cluster, 'service', service, 'NotInstalled')

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

    if name in ss.svars['machines'][m_index]['components']:
        raise ex.CreationError('machine', machine, 'component', name,
                               'Installed')

    ss.svars['machines'][m_index]['components'].append(name)
    auto_install_component(name, machine, service, cluster)
    ss.dump_config(get_services_components_hosts())


@valid_cluster
def add_service(name, *, cluster):
    """Add a service to a specified cluster.

    :param name: Service name
    :type name: str
    :param cluster: Cluster name
    :type cluster: str
    :raises ex.LoadError: [description]
    :raises ex.CreationError: [description]
    """

    ss.load_config(cluster)

    if not check_service(name):
        raise ex.LoadError('service', name, 'NotExist')

    if name in ss.svars['services']:
        raise ex.CreationError('cluster', cluster,
                               'service', name,
                               'Installed')

    if check_service_cluster(name):
        raise ex.CreationError(
            'cluster', cluster, 'service', name, 'Installed')

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
    auto_install_service(name, cluster)
    ss.dump_config(get_services_components_hosts())


def check_service_req_service(name, ha=False):
    """Check if a service requirements are satisfied.

    :param name: Service name
    :type name: str
    :param ha: Weither the service is in HA, defaults to False
    :raises ex.LoadError: If the service doesn't exist
    :return: The misssing services and components needed to install the service
    :rtype: dict
    """

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
    """Check if all the components required are installed for a service.

    :param name: Service name
    :type name: str
    :param ha: Weither the service is in HA, defaults to False
    :raises ex.LoadError: If the service doesn't exist
    :return: The missing components needed to install the service
    :rtype: dict
    """

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


def check_service_complete(name, ha=False):
    print_missing = []

    missing_comp = check_service_req_comp(name, ha)
    if missing_comp:
        for k, v in missing_comp.items():
            print_missing.append('{} {}'.format(v, k))

    return print_missing


def count_components():
    """Count the number of instance for each component.

    :return: The components and their cardinality
    :rtype: dict
    """

    components = get_available_components()
    for machine in ss.svars['machines']:
        for c in machine['components']:
            components[c] += 1
    return components


def get_available_components():
    """Get the available components (based on services config file).

    :return: The list of available components
    :rtype: dict
    """

    components = {}
    for s in config['services']:
        for c in s['components']:
            components[c['name']] = 0
    return components


def get_service_components(name):
    """Get the components of a specified service.

    :param name: Service name
    :type name: str
    :return: The list of components of this service
    :rtype: list
    """

    components = []
    for s in config['services']:
        if s['name'] == name:
            for c in s['components']:
                components.append(c['name'])
    return components


@valid_cluster
def remove_service(service, *, cluster):
    """Remove a service of a specified cluster.

    :param name: Service name
    :type name: str
    :param cluster: Cluster name
    :type cluster: str
    :raises ex.LoadError: [description]
    :raises ex.CreationError: [description]
    """

    ss.load_config(cluster)

    if not check_service(service):
        raise ex.LoadError('service', service, 'NotExist')

    if not check_service_cluster(service):
        raise ex.CreationError(
            'cluster', cluster, 'service', service, 'NotInstalled')

    serv_comp = get_service_components(service)
    for m in ss.svars['machines']:
        to_remove = []
        for c in m['components']:
            if c in serv_comp:
                to_remove.append(c)
        for c in to_remove:
            m['components'].remove(c)

    ss.svars['services'].remove(service)
    ss.dump_config(get_services_components_hosts())


@valid_cluster
def remove_component(component, *, machine, cluster):
    """Remove a service of a specified machine in a specified cluster.

    :param name: Service name
    :type name: str
    :param machine: Machine name
    :type machine: str
    :param cluster: Cluster name
    :type cluster: str
    :raises ex.LoadError: [description]
    :raises ex.CreationError: [description]
    """

    ss.load_config(cluster)

    if not vm.check_machine(cluster=cluster, machine=machine):
        raise ex.LoadError('machine', machine, 'NotExist')

    service = check_component(component)
    if not service:
        raise ex.LoadError('component', component, 'NotExist')

    for i, m in enumerate(ss.svars['machines']):
        if m['name'] == machine:
            m_index = i

    if component not in ss.svars['machines'][m_index]['components']:
        raise ex.CreationError('machine', machine, 'component', component,
                               'NotInstalled')

    ss.svars['machines'][m_index]['components'].remove(component)
    ss.dump_config(get_services_components_hosts())


@valid_cluster
def list_components(*, machine, cluster):
    """List the components installed on a machine of a specified cluster.

    :param machine: Machine name
    :type machine: str
    :param cluster: Cluster name
    :type cluster: str
    :raises ex.LoadError: [description]
    :return: The list of the components installed on the machine
    :rtype: list
    """

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
            break

    return m_conf['components']


def get_services_components_hosts():
    """Generate the list services->components->hosts of the session cluster.

    :return: The list services->components->hosts
    :rtype: dict
    """

    services_components_hosts = {}
    for s in ss.svars['services']:
        services_components_hosts[s] = {}
        components = get_service_components(s)
        for c in components:
            services_components_hosts[s][c] = []
            for m in ss.svars['machines']:
                if c in m['components']:
                    services_components_hosts[s][c].append(m['name'])
            if not len(services_components_hosts[s][c]):
                services_components_hosts[s].pop(c)
    return services_components_hosts


@valid_cluster
def auto_assign(service, *, cluster):
    ss.load_config(cluster)

    scfg = check_service(service)
    if not scfg:
        raise ex.LoadError('service', service, 'NotExist')

    # dist is 'default' or 'ha'
    dist = 'default'
    # Check loop for atomicity
    for component in scfg['components']:
        left = auto_assign_service_comp(component, dist, cluster, check=True)
        if left == -1:
            raise ex.CreationError('component', component['name'],
                                   'hosts type (need at least 1 of them)',
                                   component['hosts_types'],
                                   'ReqNotMet')
        elif left > 0:
            raise ex.CreationError('component', component['name'],
                                   'hosts type (need ' + str(left) +
                                   ' of them)',
                                   component['hosts_types'],
                                   'ReqNotMet')

    for component in scfg['components']:
        auto_assign_service_comp(component, dist, cluster, check=False)


def auto_assign_service_comp(component, dist, cluster, check):
    """
    :param component: component dict from services.json
    :type component dict
    :param dist:
    :param cluster
    """
    count = component['number'][dist]  # -1 = everywhere
    if count == 0:
        return 0
    for host_type in component['hosts_types']:
        for m in ss.svars['machines']:
            if host_type in m['types']:
                try:
                    if not check:
                        add_component(component['name'],
                                      machine=m['name'],
                                      cluster=cluster)
                # Ignore error when adding already existing component
                except ex.CreationError:
                    pass
                count -= 1
                if count == 0:
                    return 0

    return count


def auto_install_service(service, cluster):
    for s in config['services']:
        if s['name'] == service:
            for c in s['components']:
                if c['name'] in s['auto_install']:
                    auto_assign_service_comp(c, 'default', cluster,
                                             check=False)


def auto_install_component(component, machine, service, cluster):
    for s in config['services']:
        if s['name'] == service:
            for c in s['components']:
                if c['name'] == component:
                    if c.get('auto_install'):
                        for auto in c['auto_install']:
                            add_component(auto, machine=machine,
                                          cluster=cluster)


def auto_install_machine(machine, cluster):
    count = 0
    for s in config['services']:
        if s['name'] in ss.svars['services']:
            for c in s['auto_install']:
                add_component(c, machine=machine,
                              cluster=cluster)
                count += 1

    return count
