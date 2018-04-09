from jumbo.utils import session as ss
from jumbo.utils.settings import JUMBODIR

import json


def add_machine(name, ip, ram, disk, types, cpus=1):
    m = {
        'name': name,
        'ip': ip,
        'ram': ram,
        'disk': disk,
        'types': types,
        'cpus': cpus
    }

    ss.add_machine(m)

    try:
        temp = ss.jinja_env.get_template('Vagrantfile.j2')
        with open(JUMBODIR + ss.svars['cluster'] + '/Vagrantfile', 'w+') as vf:
            vf.write(temp.render(hosts=ss.svars['machines']))
    except IOError:
        return False

    ss.dump_config()

    return True


def list_machines(cluster):
    if cluster != ss.svars['cluster']:
        with open(JUMBODIR + cluster + '/jumbo_config', 'r') as clf:
            cluster_conf = json.load(clf)
    else:
        cluster_conf = ss.svars

    return cluster_conf['machines']


def check_machine(cluster, name):
    if cluster != ss.svars['cluster']:
        with open(JUMBODIR + cluster + '/jumbo_config', 'r') as clf:
            cluster_conf = json.load(clf)
    else:
        cluster_conf = ss.svars

    for m in cluster_conf['machines']:
        if m['name'] == name:
            return True

    return False


def check_ip(cluster, ip):
    if cluster != ss.svars['cluster']:
        with open(JUMBODIR + cluster + '/jumbo_config', 'r') as clf:
            cluster_conf = json.load(clf)
    else:
        cluster_conf = ss.svars

    for m in cluster_conf['machines']:
        if m['ip'] == ip:
            return m['name']

    return False
