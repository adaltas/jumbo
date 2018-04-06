import click
from click_shell.core import Shell

from jumbo.core import machines
from jumbo.utils import clusters, session as ss


@click.group(invoke_without_command=True)
@click.option('--cluster', '-c')
@click.pass_context
def jumbo(ctx, cluster):
    """
    Execute a Jumbo command.
    If no command is passed, start the Jumbo shell interactive mode.
    """

    # Create the shell
    sh = Shell(prompt=click.style('jumbo > ', fg='green'),
               intro=click.style('Welcome to the jumbo shell v0.1.3.3.7!',
                                 blink=True, fg='cyan'))
    # Save the shell in the click context (to modify its prompt later on)
    ctx.meta['jumbo_shell'] = sh.shell
    # Register commands that can be used in the shell
    sh.add_command(create)
    sh.add_command(exit)
    sh.add_command(delete)
    sh.add_command(manage)
    # If cluster exists, save it to svars (session variable) and adapt prompt
    if cluster:
        if not clusters.check_cluster(cluster):
            click.echo('This cluster does not exist.'
                       ' Use `create NAME` to create it.', err=True)
        else:
            ctx.invoke(manage, name=cluster)

    # Run the command, or the shell if no command is passed
    sh.invoke(ctx)


@jumbo.command()
@click.pass_context
def exit(ctx):
    """
    Reset current context.
    :param ctx: Click context
    """
    if ss.svars.get('cluster'):
        ss.svars['cluster'] = None
        ctx.meta['jumbo_shell'].prompt = click.style('jumbo > ', fg='green')
    else:
        click.echo('Use `quit` to quit the shell. Exit only removes context.')


@jumbo.command()
@click.argument('name')
def create(name):
    """
    Create a new cluster.
    :param name: New cluster name
    """
    click.echo('Creating %s...' % name)
    if clusters.create_cluster(name):
        click.echo('Cluster `%s` created.' % name)
    else:
        click.echo(click.style('Cluster already exists!', fg='red'), err=True)


@jumbo.command()
@click.argument('name')
@click.pass_context
def manage(ctx, name):
    """
    Set a cluster to manage. Persist --cluster option.
    :param ctx:
    :param name:
    :return:
    """
    click.echo('Loading %s...' % name)
    exists, loaded = clusters.load_cluster(name)
    if loaded:
        click.echo('Cluster `%s` loaded.' % name)
        ctx.meta['jumbo_shell'].prompt = click.style(
            'jumbo (%s) > ' % name, fg='green')
    else:
        if exists:
            click.echo(click.style('Couldn\'t find the file `jumbo_config`!\n'
                                   'All cluster configuration has been lost.',
                                   fg='red'), err=True)
            click.echo('Recreating `jumbo_config` from scratch...')
            ctx.meta['jumbo_shell'].prompt = click.style(
                'jumbo (%s) > ' % name, fg='green')
        else:
            click.echo(click.style('Cluster doesn\'t exist!',
                                   fg='red'), err=True)


# @jumbo.command()
# @click.argument('name')
# @click.option('--ip', '-i')
#     def addvm(name, ):


@jumbo.command()
@click.argument('name')
@click.option('--force/--no-force', default=False)
def delete(name, force):
    """
    Delete a cluster.
    :param name: Name of the cluster to delete.
    """
    deleted = False
    if force:
        deleted = clusters.delete_cluster(name)
    else:
        if click.confirm(
                'Are you sure you want to delete the cluster %s' % name):
            deleted = clusters.delete_cluster(name)

    if not deleted:
        click.echo(click.style('Cluster `%s` does not exist' % name, fg='red'),
                   err=True)


if __name__ == '__main__':
    pass
