import json
import os
import pathlib

from shutil import copyfile

from jumbo.utils.settings import JUMBODIR
from jumbo.utils import exceptions as ex


if not os.path.isfile(JUMBODIR + 'versions.json'):
    if not os.path.isdir(JUMBODIR):
        pathlib.Path(JUMBODIR).mkdir()
    copyfile(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) +
             '/core/config/versions.json', JUMBODIR + 'versions.json')


def get_yaml_config(cluster=None):
    """Get the versions to use for each service/platform/ressource

    :raises ex.LoadError: If the file versions.json doesn't exist
    :return: The versions to use
    :rtype: dict
    """

    yaml_versions = {
        'services': {},
        'platform': {},
        'repositories': {}
    }

    if not os.path.isfile(JUMBODIR + 'versions.json'):
        raise ex.LoadError('file', JUMBODIR + 'versions.json', 'NotExist')

    # Global versions settings
    with open(JUMBODIR + 'versions.json', 'r') as vs:
        jumbo_versions = json.load(vs)

    yaml_versions = update_yaml_versions(yaml_versions, jumbo_versions)

    if not cluster:
        return yaml_versions

    # Cluster versions settings
    if os.path.isfile(JUMBODIR + cluster + '/versions.json'):
        with open(
                JUMBODIR + cluster + '/versions.json', 'r') as vs:
            cluster_versions = json.load(vs)

        yaml_versions = update_yaml_versions(yaml_versions, cluster_versions)

    return yaml_versions


def update_yaml_versions(yaml_versions, json_versions):
    """
    Update the versions dictionnary to be printed in YAML with values from 
    the JSON versions dictionnary found in versions.json.

    :param yaml_versions: versions dict to be printed in YAML format
    :type yaml_versions: dict
    :param json_versions: versions dict in JSON format
    :type json_versions: dict
    :return: versions dict to be printed in YAML format
    :rtype: dict
    """

    if json_versions.get('repositories', False):
        for repo in json_versions['repositories']:
            yaml_versions['repositories'].update({
                repo['name']: {
                    'source': repo['source'],
                    'dest': repo['dest']
                }
            })
    if json_versions.get('services', False):
        for service in json_versions['services']:
            version, url = [(v, u) for (v, u) in service['versions'].items()
                            if v == service['default']][0]
            yaml_versions['services'].update({
                service['name']: {
                    "version": version,
                    "url": url
                }
            })

    if json_versions.get('platforms', False):
        for platform in json_versions['platforms']:
            version, resources = [(v, r) for (v, r)
                                  in platform['versions'].items()
                                  if v == platform['default']][0]
            platform_resources = {}

            for item in resources:
                url = [r for r in json_versions['resources']
                       if r['name'] == item['resource']][0]['versions'][
                           item['version']]
                platform_resources.update({
                    item['resource']: {
                        'version': item['version'],
                        'url': url
                    }
                })

            yaml_versions['platform'].update({
                platform['name']: {
                    'version': version,
                    'resources': platform_resources
                }
            })

    return yaml_versions


def update_versions_file():
    """
    Update the versions.json file found in ~/.jumbo/ with the newest 
    available versions

    """

    config_dir = os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))) + '/core/config/'

    with open(config_dir + 'versions.json', 'r') as u_vs:
        up_to_date_versions = json.load(u_vs)

    with open(JUMBODIR + 'versions.json', 'r') as c_vs:
        current_versions = json.load(c_vs)

    # Merge current services config
    for service in up_to_date_versions['services']:
        current_service = [s for s in current_versions['services']
                           if s['name'] == service['name']]
        if current_service:
            for vers, _ in service['versions'].items():
                current_url = current_service[0]['versions'].get(vers, False)
                if current_url:
                    service['versions'][vers] = current_url
            service['default'] = current_service[0]['default']

    # Merge current platforms config
    for platform in up_to_date_versions['platforms']:
        current_platform = [p for p in current_versions['platforms']
                            if p['name'] == platform['name']]
        if current_platform:
            platform['default'] = current_platform[0]['default']

    # Merge current resources config
    for resource in up_to_date_versions['resources']:
        current_resource = [r for r in current_versions['resources']
                            if r['name'] == resource['name']]
        if current_resource:
            for vers, _ in resource['versions'].items():
                current_url = current_resource[0]['versions'].get(vers, False)
                if current_url:
                    resource['versions'][vers] = current_url

    up_to_date_versions['repositories'] = current_versions['repositories']

    with open(JUMBODIR + 'versions.json', 'w') as c_vs:
        json.dump(up_to_date_versions, c_vs, indent=2)
