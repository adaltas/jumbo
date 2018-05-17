import os
import json

from jumbo.core import nodes
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


def add_component(name, machine, cluster, ha=None):
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

    if ha is None:
        ha = check_comp_number(service, name)

    missing_serv, missing_comp = check_service_req_service(service, ha)
    if missing_serv:
        raise ex.CreationError('component', name, 'services', missing_serv,
                               'ReqNotMet')
    if missing_comp:
        print_missing = []
        print_missing.append('Default:')
        for k, v in missing_comp['default'].items():
            print_missing.append(' - {} {}'.format(v, k))
        print_missing.append('or High Availability:')
        for k, v in missing_comp['ha'].items():
            print_missing.append(' - {} {}'.format(v, k))
        raise ex.CreationError('service', name, 'components', print_missing,
                               'ReqNotMet')

    if name in ss.svars['machines'][m_index]['components']:
        raise ex.CreationError('machine', machine, 'component', name,
                               'Installed')

    ss.svars['machines'][m_index]['components'].append(name)
    ss.dump_config(get_services_components_hosts())


@valid_cluster
def add_service(name, ha=False, *, cluster):
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

    missing_serv, missing_comp = check_service_req_service(name, ha)
    if missing_serv:
        raise ex.CreationError('service', name, 'services',
                               (' - %s' % s for s in missing_serv),
                               'ReqNotMet')
    if missing_comp:
        print_missing = []
        print_missing.append('Default:')
        for k, v in missing_comp['default'].items():
            print_missing.append(' - {} {}'.format(v, k))
        print_missing.append('or High Availability:')
        for k, v in missing_comp['ha'].items():
            print_missing.append(' - {} {}'.format(v, k))
        raise ex.CreationError('service', name, 'components', print_missing,
                               'ReqNotMet')

    ss.svars['services'].append(name)
    auto_install_service(name, cluster, ha)
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


def check_service_req_comp(name):
    """Check if all the components required are installed for a service.

    :param name: Service name
    :type name: str
    :param ha: Weither the service is in HA, defaults to False
    :raises ex.LoadError: If the service doesn't exist
    :return: The missing components needed to install the service
    :rtype: dict
    """

    missing = {
        'default': {},
        'ha': {}
    }
    comp_count = count_components()
    for s in config['services']:
        if s['name'] == name:
            for comp in s['components']:
                req = 'default'
                req_number = comp['number'][req] if comp['number'][req] != -1 \
                    else 1
                missing_count = req_number - comp_count[comp['name']]
                if missing_count > 0:
                    missing['default'][comp['name']] = missing_count
                req = 'ha'
                req_number = comp['number'][req] if comp['number'][req] != -1 \
                    else 1
                missing_count = req_number - comp_count[comp['name']]
                if missing_count > 0:
                    missing['ha'][comp['name']] = missing_count
            if not missing['ha'] or not missing['default']:
                return {}
            return missing
    raise ex.LoadError('service', name, 'NotExist')


@valid_cluster
def check_service_complete(name, *, cluster):
    """Check if all the components required are installed for a service

    :param name: Service name
    :type name: str
    :param ha: If the service is in HA mode, defaults to False
    :param ha: bool, optional
    :return: A list of the components missing and their cardinalities
    :rtype: dict
    """

    print_missing = []

    missing_comp = check_service_req_comp(name)

    if missing_comp:
        print_missing = []
        print_missing.append('Default:')
        for k, v in missing_comp['default'].items():
            print_missing.append(' - {} {}'.format(v, k))
        print_missing.append('or High Availability:')
        for k, v in missing_comp['ha'].items():
            print_missing.append(' - {} {}'.format(v, k))

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


def get_available_types():
    return config['node_types']


def get_available_services():
    """Get the available services (based on services config file).

    :return: The list of available services
    :rtype: dict
    """

    services = {}
    for s in config['services']:
        services[s['name']] = 0
    return services


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


def check_dependent_services(service, ha=False):
    """Return the services depending on a specified service.

    :param service: Service name
    :type service: str
    :param ha: True if the service is in HA mode, defaults to False
    :return: The list of dependent services
    """

    req = 'ha' if ha else 'default'
    dependent = []
    for s in config['services']:
        if s['name'] in ss.svars['services']:
            if service in s['requirements']['services'][req]:
                dependent.append(s['name'])
    return dependent


def check_comp_number(service, component):
    """Check the maximum number of a component is not already reached.

    :param service: Service name
    :type service: str
    :param component: Component name
    :type component: str
    :return: True if the service is in HA mode, false otherwise
    """

    ha = 'ha' if check_ha(service) else 'default'
    serv_comp_host = get_services_components_hosts()
    number_comp = 1
    if serv_comp_host[service].get(component):
        number_comp = len(serv_comp_host[service][component]) + 1
    for s in config['services']:
        if s['name'] == service:
            for c in s['components']:
                if c['name'] == component:
                    if number_comp > c['number'][ha] \
                            and c['number'][ha] != -1:
                        raise ex.CreationError('cluster',
                                               ss.svars['cluster'],
                                               'components',
                                               component,
                                               'MaxNumber')
                    elif number_comp == c['number']['ha']:
                        to_remove = {}
                        for comp in s['components']:
                            n = 0
                            max_n = comp['number']['ha']
                            if serv_comp_host[service].get(comp['name']):
                                n = len(serv_comp_host[service][comp['name']])
                            if n > max_n and max_n != -1:
                                to_remove[comp['name']] = n - max_n
                        if to_remove:
                            print_remove = []
                            for k, v in to_remove.items():
                                print_remove.append('{} {}'.format(v, k))
                            raise ex.CreationError('service',
                                                   service,
                                                   'components',
                                                   print_remove,
                                                   'TooManyHA')
                        return True
                    return False
            raise ex.LoadError('component', component, 'NotExist')
    raise ex.LoadError('service', service, 'NotExist')


def check_ha(service):
    """Check if a service is in HA mode.

    :param service: Service name
    :type service: str
    :return: True if the service is in HA mode, False otherwise
    """

    serv_comp_host = get_services_components_hosts()
    for s in config['services']:
        if s['name'] == service:
            for c in s['components']:
                if serv_comp_host[service].get(c['name']):
                    number_comp = len(serv_comp_host[service][c['name']])
                    if number_comp > c['number']['default'] \
                            and c['number']['ha'] > c['number']['default']:
                        return True
            return False
    raise ex.LoadError('service', service, 'NotExist')


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

    dependent = check_dependent_services(service)
    if dependent:
        raise ex.CreationError(
            'service', service, 'services', dependent, 'Dependency'
        )

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

    if not nodes.check_machine(cluster=cluster, machine=machine):
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

    if not nodes.check_machine(cluster=cluster, machine=machine):
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


def get_abbr(component, service):
    """Return the abbreviation of a component.

    :param component: Component name
    :type component: str
    :param service: Service name of the component
    :type service: str
    """

    if not check_component(component):
        raise ex.LoadError('component', component, 'NotExist')

    for s in config['services']:
        if s['name'] == service:
            for c in s['components']:
                if c['name'] == component:
                    return c['abbr']


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
            if not services_components_hosts[s][c]:
                services_components_hosts[s].pop(c)
    return services_components_hosts


@valid_cluster
def auto_assign(service, ha, *, cluster):
    """Auto-install a service and its components on the best fitting hosts.

    :param service: Service name
    :type service: str
    :param cluster: Cluster name
    :type cluster: str
    :raises ex.LoadError: If the cluster doesn't exist
    :raises ex.CreationError: If the requirements are not met to install
    """

    ss.load_config(cluster)

    scfg = check_service(service)
    if not scfg:
        raise ex.LoadError('service', service, 'NotExist')

    # dist is 'default' or 'ha'
    dist = 'ha' if ha else 'default'
    # Check loop for atomicity
    for component in scfg['components']:
        left = auto_assign_service_comp(component, dist, cluster, check=True)
        if left == -1:
            raise ex.CreationError('component', component['name'],
                                   'hosts type (need at least 1 of them)',
                                   (' - %s'
                                    % c for c in component['hosts_types']),
                                   'ReqNotMet')
        elif left > 0:
            raise ex.CreationError('component', component['name'],
                                   'hosts type (need ' + str(left) +
                                   ' of them)',
                                   (' - %s'
                                    % c for c in component['hosts_types']),
                                   'ReqNotMet')

    count = 0
    for component in scfg['components']:
        auto_assign_service_comp(component, dist, cluster, check=False)
        count += 1

    return count


def auto_assign_service_comp(component, dist, cluster, check):
    """Auto-install a component on the best fitting hosts.

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
                                      cluster=cluster,
                                      ha=dist == 'ha')
                # Ignore error when adding already existing component
                except ex.CreationError as e:
                    if e.type == 'Installed':
                        pass
                    else:
                        raise e
                count -= 1
                if count == 0:
                    return 0

    return count


def auto_install_service(service, cluster, ha=False):
    """Auto-install the service clients on the fitting hosts.

    :param service: Service name
    :type service: str
    :param cluster: Cluster name
    :type cluster: str
    """

    req = 'ha' if ha else 'default'
    for s in config['services']:
        if s['name'] == service:
            for c in s['components']:
                if c['name'] in s['auto_install']:
                    auto_assign_service_comp(c, req, cluster,
                                             check=False)


def auto_install_machine(machine, cluster):
    """Auto-install the clients for all the cluster's services on a machine.

    :param machine: Machine name
    :type machine: str
    :param cluster: Cluster name
    :type cluster: str
    :return: The number of components auto-installed
    """

    count = 0
    for m in ss.svars['machines']:
        if m['name'] == machine:
            m_conf = m

    for s in config['services']:
        if s['name'] in ss.svars['services']:
            for c in s['auto_install']:
                for comp in s['components']:
                    if comp['name'] == c:
                        for t in m_conf['types']:
                            if t in comp['hosts_types']:
                                add_component(c, machine=machine,
                                              cluster=cluster)
                                count += 1

    return count
