import os
import json
from prettytable import PrettyTable


class ConvertError(Exception):
    def __init__(self):
        pass


with open('../services.json', 'r') as sf:
    services = json.load(sf)


def get_service(component):
    for s in services['services']:
        for c in s['components']:
            if c['name'] == component:
                return s['name']

    raise ConvertError()


def prettytable_to_mdtable(table: PrettyTable):
    lines = table.get_string().split('\n')

    lines[2] = lines[2].replace('+', '|')
    mdtable = '\n'.join(lines[1:-1])

    return mdtable


def generate_md(jumbofile, outputfile):
    with open(jumbofile, 'r') as jf:
        cluster = json.load(jf)

    total_ram = 0
    total_disk = 0

    node_table = PrettyTable(['Name', 'Types', 'IP', 'RAM', 'CPUs'])
    node_table.align = 'l'

    comp_table = PrettyTable(['Node', 'Component', 'Service'])
    comp_table.align = 'l'

    for n in cluster['nodes']:
        display_name = True
        total_ram += n['ram']
        total_disk += 40

        node_table.add_row(['`%s`' % n['name'],
                            '`%s`' % ', '.join(n['types']),
                            n['ip'],
                            n['ram'],
                            n['cpus']])

        for c in n['components']:
            comp_table.add_row([
                '`%s`' % n['name'] if display_name else '',
                c,
                get_service(c)
            ])
            display_name = False

    md = '# %s template \n\n' % cluster['cluster']

    md += ('### Recommended config.\n\n'
           '- RAM: more than {} GB\n- Disk: {}GB free space\n\n'
           .format(total_ram / 1024 + 4, total_disk / 2))

    md += ('### Usage\n'
           '```\ncreate mycluster --template %s\n```\n\n'
           % cluster['cluster'])

    md += '### Services installed\n\n'
    md += ', '.join(cluster['services'])
    md += '\n\n'

    md += '###  Nodes\n\n'
    md += prettytable_to_mdtable(node_table)

    md += '\n\n###  Components\n\n'
    md += prettytable_to_mdtable(comp_table)

    with open(outputfile, 'w+') as of:
        of.write(md)


def generate_all_md():
    for _, _, files in os.walk('.'):
        for f in files:
            if '.json' in f:
                generate_md(f, 'docs/%s' % f.split('.')[0] + '.md')


def main():
    for _, _, files in os.walk('./docs/'):
        for f in files:
            os.remove('docs/' + f)

    generate_all_md()


if __name__ == '__main__':
    main()
