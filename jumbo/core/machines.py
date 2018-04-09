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

    try:
        temp = ss.jinja_env.get_template('Vagrantfile.j2')
        with open(JUMBODIR + ss.svars['cluster'] + '/Vagrantfile', 'w') as vf:
            vf.write(temp.render(hosts=ss.svars['machines']))
    except IOError:
        return False

    ss.add_machine(m)
    ss.dump_config()

    return True


def list_machines(cluster):
    with open(JUMBODIR + cluster + '/jumbo_config', 'r') as clf:
        cluster_conf = json.load(clf)

    return cluster_conf['machines']
