import click
from click_shell.core import Shell
import ipaddress as ipadd
from prettytable import PrettyTable

from jumbo.core import clusters, machines as vm
from jumbo.utils import session as ss


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
               intro=click.style('Jumbo shell v0.1',
                                 fg='cyan'))
    # Save the shell in the click context (to modify its prompt later on)
    ctx.meta['jumbo_shell'] = sh.shell
    # Register commands that can be used in the shell
    sh.add_command(create)
    sh.add_command(exit)
    sh.add_command(delete)
    sh.add_command(manage)
    # If cluster exists, call manage command (saves the shell in session
    #  variable svars and adapts the shell prompt)
    sh.add_command(addvm)
    sh.add_command(rmvm)
    sh.add_command(listcl)
    sh.add_command(listvm)
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


# cluster commands

@jumbo.command()
@click.argument('name')
@click.pass_context
def create(ctx, name):
    """
    Create a new cluster.

    :param name: New cluster name
    """
    click.echo('Creating %s...' % name)
    if clusters.create_cluster(name):
        click.echo('Cluster `%s` created.' % name)
        ctx.meta['jumbo_shell'].prompt = click.style(
            'jumbo (%s) > ' % name, fg='green')
    else:
        click.secho('Cluster already exists!', fg='red', err=True)


@jumbo.command()
@click.argument('name')
@click.pass_context
def manage(ctx, name):
    """
    Set a cluster to manage. Persist --cluster option.

    :param name: Cluster name
    """
    click.echo('Loading %s...' % name)
    exists, loaded = clusters.load_cluster(name)
    if loaded:
        click.echo('Cluster `%s` loaded.' % name)
        ctx.meta['jumbo_shell'].prompt = click.style(
            'jumbo (%s) > ' % name, fg='green')
    else:
        if exists:
            click.secho('Couldn\'t find the file `jumbo_config`!\n'
                        'All cluster configuration has been lost.',
                        fg='red', err=True)
            click.echo('Recreating `jumbo_config` from scratch...')
            ctx.meta['jumbo_shell'].prompt = click.style(
                'jumbo (%s) > ' % name, fg='green')
        else:
            click.secho('Cluster doesn\'t exist!', fg='red', err=True)


@jumbo.command()
@click.argument('name')
@click.option('--force', '-f', is_flag=True)
def delete(name, force):
    """
    Delete a cluster.

    :param name: Name of the cluster to delete
    """
    if clusters.check_cluster(name):
        if force:
            clusters.delete_cluster(name)
        else:
            if click.confirm(
                    'Are you sure you want to delete the cluster %s' % name):
                clusters.delete_cluster(name)
                ss.clear()
    else:
        click.secho('Cluster `%s` doesn\'t exist!' % name, fg='red', err=True)


@jumbo.command()
def listcl():
    """
    List clusters managed by Jumbo.
    """

    cluster_table = PrettyTable(['Name', 'Number of VMs'])

    for cluster in clusters.list_clusters():
        cluster_table.add_row([cluster['cluster'].split('/')[-1],
                               len(cluster['machines'])])

    click.echo(cluster_table)


# VM commands

def validate_ip(ctx, param, value):
    try:
        ipadd.ip_address(value)
    except ValueError:
        raise click.BadParameter('%s is not a valid IP address.' % value)

    return value


@jumbo.command()
@click.argument('name')
@click.option('--types', '-t', multiple=True, type=click.Choice([
    'master', 'sidemaster', 'edge', 'worker', 'ldap', 'other']),
    required=True, help='VM host type(s)')
@click.option('--ip', '-i',  callback=validate_ip, prompt='IP',
              help='VM IP address')
@click.option('--ram', '-r', type=int, prompt='RAM (MB)',
              help='RAM allocated to the VM in MB')
@click.option('--disk', '-d', type=int, prompt='Disk (MB)',
              help='Disk allocated to the VM in MB')
@click.option('--cpus', '-p', default=1,
              help='Number of CPUs allocated to the VM')
@click.option('--cluster', '-c',
              help='Cluster in which the VM will be created')
@click.pass_context
def addvm(ctx, name, types, ip, ram, disk, cpus, cluster):
    """
    Create a new VM in the cluster being managed.
    Another cluster can be specified with "--cluster".

    :param name: New VM name
    """

    switched = False
    current = ss.svars['cluster']

    if cluster:
        if current and cluster != current:
            click.secho('You are currently managing the cluster `%s`. '
                        'Type "exit" to manage other clusters.'
                        % ss.svars['cluster'], fg='red')
            return

        if not clusters.check_cluster(cluster):
            click.secho('Cluster `%s` doesn\'t exist!' % cluster, fg='red',
                        err=True)
            return

        switched, loaded = clusters.switch_cluster(cluster)

        if not loaded:
            click.secho('Failed to load `%s`!' % cluster, fg='red')
            return

        current = cluster
    else:
        if not ss.svars['cluster']:
            click.secho('No cluster specified nor managed! Use "--cluster" '
                        'to specify a cluster.', fg='red', err=True)
            return

    if vm.check_machine(current, name):
        click.secho('A machine with the name `%s` already exists.\nUse '
                    '"modifyvm" to change its configuration.' % name,
                    fg='red')
        return

    m_ip = vm.check_ip(current, ip)
    if m_ip:
        click.secho('The address `{}` is already used by '
                    'machine `{}`.'.format(ip, m_ip), fg='red')
        return

    if vm.add_machine(name, ip, ram, disk, types, cpus):
        click.echo('Machine `{}` added to cluster `{}`.'.format(name, current))

    # TODO: Only echo if in shell mode
    if switched:
        click.echo('\nSwitched to cluster `%s`.' % current)
        ctx.meta['jumbo_shell'].prompt = click.style(
            'jumbo (%s) > ' % current, fg='green')


@jumbo.command()
@click.argument('name')
@click.pass_context
@click.option('--cluster', '-c', help='Cluster of the VM to be deleted')
def rmvm(ctx, name, cluster):
    """
    Removes a VM.

    :param name: VM name
    """

    switched = False
    current = ss.svars['cluster']

    if cluster:
        if current and cluster != current:
            click.secho('You are currently managing the cluster `%s`. '
                        'Type "exit" to manage other clusters.'
                        % ss.svars['cluster'], fg='red')
            return

        if not clusters.check_cluster(cluster):
            click.secho('Cluster `%s` doesn\'t exist!' % cluster, fg='red',
                        err=True)
            return

        switched, loaded = clusters.switch_cluster(cluster)

        if not loaded:
            click.secho('Failed to load `%s`!' % cluster, fg='red')
            return

        current = cluster
    else:
        if not ss.svars['cluster']:
            click.secho('No cluster specified nor managed! Use "--cluster" '
                        'to specify a cluster.', fg='red', err=True)
            return

    if vm.remove_machine(current, name):
        click.echo('Machine `{}` removed of cluster `{}`.'
                   .format(name, current))
    else:
        click.secho('Machine `%s` doesn\'t exist!' % name, fg='red')

    # TODO: Only echo if in shell mode
    if switched:
        click.echo('\nSwitched to cluster `%s`.' % current)
        ctx.meta['jumbo_shell'].prompt = click.style(
            'jumbo (%s) > ' % current, fg='green')


@jumbo.command()
@click.option('--cluster', '-c', help='Cluster in which to list the VMs')
def listvm(cluster):
    """
    List VMs in the cluster being managed.
    Another cluster can be specified with "--cluster".
    """

    if cluster:
        if clusters.check_cluster(cluster):
            ss.svars['cluster'] = cluster
        else:
            click.secho('Cluster `%s` does not exist' % cluster,
                        fg='red', err=True)
            return
    else:
        if not ss.svars['cluster']:
            click.secho('No cluster specified nor managed! Use "--cluster" '
                        'to specify a cluster.', fg='red', err=True)
            return
        cluster = ss.svars['cluster']

    vm_table = PrettyTable(
        ['Name', 'Types', 'IP', 'RAM (MB)', 'Disk (MB)', 'CPUs'])

    for m in vm.list_machines(cluster):
        vm_table.add_row([m['name'], ', '.join(m['types']), m['ip'],
                          m['ram'], m['disk'], m['cpus']])

    click.echo(vm_table)


if __name__ == '__main__':
    pass
