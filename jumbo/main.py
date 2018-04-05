import click
from click_shell import shell

from jumbo.core import machines
from jumbo.utils import session
from jumbo.utils import clusters


def main():
    pass


@shell(prompt=click.style('jumbo > ', fg='green'), intro=click.style('Jumbo shell v0.1', fg='cyan'))
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
    else:
        click.echo(click.style('Cluster already exists!', fg='red'), err=True)


@jumbo_shell.command()
@click.argument('name')
def manage(name):
    click.echo('Loading %s...' % name)
    loaded, exists = clusters.load_cluster(name)
    if loaded:
        click.echo('Cluster `%s` loaded.' % name)
    else:
        if exists:
            click.echo(click.style('Couldn\'t find the file `jumbo_config`!\n'
                                   'All cluster configuration has been lost.',
                                   fg='red'), err=True)
            click.echo('Recreating `jumbo_config` from scratch...')
        else:
            click.echo(click.style('Cluster doesn\'t exist!',
                                   fg='red'), err=True)

# @jumbo_shell.command()
# @click.argument('name')
# @click.option('--ip', '-i', )
#     def addvm(''):


if __name__ == '__main__':
    main()
