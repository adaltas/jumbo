import click
from click_shell.core import Shell

from jumbo.utils import clusters, session


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

    # If cluster exists, save it to svars (session variable) and adapt prompt
    if cluster:
        if not clusters.check_cluster(cluster):
            click.echo('This cluster does not exist.'
                       ' Use `create NAME` to create it.', err=True)
        else:
            session.svars['cluster'] = cluster
            ctx.meta['jumbo_shell'].prompt = click.style(
                'jumbo (%s) > ' % cluster, fg='green')

    # Run the command, or the shell if no command is passed
    sh.invoke(ctx)


@jumbo.command()
@click.pass_context
def exit(ctx):
    """
    Reset current context.
    :param ctx: Click context
    """
    if session.svars.get('cluster'):
        session.svars['cluster'] = None
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


if __name__ == '__main__':
    pass
