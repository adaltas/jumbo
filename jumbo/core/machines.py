from jumbo.core import session

# jumbo machine add --name --ip --reload


def add_machine(name, ip, ram, disk, types, cpus=1):
    session.add_machine(
        {
            "name": name,
            "ip": ip,
            "ram": ram,
            "disk": disk,
            "types": types,
            "cpus": cpus
        }
    )
    
