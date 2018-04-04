from jinja2 import Environment, PackageLoader

svars = {
    'machines': []
}

jinja_env = Environment(
    loader=PackageLoader('jumbo', 'templates')
)


def add_machine(m):
    added = False
    for i, machine in enumerate(svars['machines']):
        if machine['name'] == m['name']:
            svars['machines'][i] = m
            added = True
    if not added:
        svars['machines'] += [
            m
        ]
