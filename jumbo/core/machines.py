from jumbo.utils import session as ss


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
    temp = ss.jinja_env.get_template('Vagrantfile.j2')
    print(temp.render(hosts=ss.svars['machines']))
