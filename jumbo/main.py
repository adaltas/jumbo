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
    machines.add_machine(
        "toto",
        "10.10.10.11",
        1000,
        10000,
        [
            "master"
        ],
        2)
    machines.add_machine(
        "tata",
        "10.10.10.12",
        2000,
        10000,
        [
            "edge"
        ],
        2)


@shell(prompt=click.style('jumbo > ', fg='green'), intro=click.style('Welcome to the jumbo shell v0.1.3.3.7!', blink=True, fg='cyan'))
@click.option('--cluster')
def jumbo_shell(cluster):
    if cluster:
        if not clusters.check_cluster(cluster):
            click.echo(
                'This cluster does not exist. Use `create NAME` to create it.', err=True)
        else:
            session.svars['cluster'] = cluster


@jumbo_shell.command()
@click.argument('name')
def create(name):
    click.echo('Creating %s...' % name)
    if clusters.create_cluster(name):
        click.echo('Cluster `%s` created.' % name)


@jumbo_shell.command()
def hello():
    print('Hello')


if __name__ == '__main__':
    main()
