from jumbo.utils import session as ss
from jumbo.utils.settings import JUMBODIR


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
    ss.dump_config()

    temp = ss.jinja_env.get_template('Vagrantfile.j2')
    with open(JUMBODIR + ss.svars['cluster'] + '/Vagrantfile', 'w') as vf:
        vf.write(temp.render(hosts=ss.svars['machines']))
