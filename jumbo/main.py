import click
from click_shell import shell

from jumbo.core import machines
from jumbo.core import session
from jumbo.utils import clusters


def main():
    machines.add_machine(
        'toto',
        '10.10.10.11',
        1000,
        10000,
        [
            'master'
        ]
    )
    print(session.svars["machines"])
    machines.add_machine(
        "toto",
        "10.10.10.11",
        1000,
        10000,
        [
            "master"
        ],
        2)
    print(session.svars["machines"])


@shell(prompt=click.style('jumbo > ', fg='green'), intro=click.style('Welcome to the jumbo shell!', blink=True, fg='cyan'))
@click.option('--cluster')
def jumbo_shell(cluster):
    pass


@jumbo_shell.command()
@click.option('--name', prompt='Cluster name: ')
def create_cluster(name):
    click.echo('Creating %s...' % name)
    clusters.create_cluster(name)


@jumbo_shell.command()
def hello():
    print('Hello')



if __name__ == '__main__':
    main()
