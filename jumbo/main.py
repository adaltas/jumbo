import click
from click_shell.core import Shell
import ipaddress as ipadd
from prettytable import PrettyTable

from jumbo.core import clusters, machines as vm, services
from jumbo.utils import session as ss, exceptions as ex
from jumbo.cli import printlogo


@click.group(invoke_without_command=True)
@click.option('--cluster', '-c')
@click.pass_context
def jumbo(ctx, cluster):
    """
    Execute a Jumbo command.
    If no command is passed, start the Jumbo shell interactive mode.
    """

    # Create the shell
    sh = Shell(prompt=click.style('\njumbo > ',
                                  fg='green'),
               intro=printlogo.jumbo_ascii() + click.style('\nJumbo v0.1',
                                                           fg='cyan'))
    # Save the shell in the click context (to modify its prompt later on)
    ctx.meta['jumbo_shell'] = sh.shell
    # Register commands that can be used in the shell
    sh.add_command(create)
    sh.add_command(exit)
    sh.add_command(delete)
    sh.add_command(manage)
    sh.add_command(addvm)
    sh.add_command(rmvm)
    sh.add_command(listcl)
    sh.add_command(listvm)
    sh.add_command(repair)
    sh.add_command(addservice)
    sh.add_command(addcomp)
    sh.add_command(listcomp)
    sh.add_command(rmservice)
    sh.add_command(rmcomp)

    # If cluster exists, call manage command (saves the shell in session
    #  variable svars and adapts the shell prompt)
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
    """Reset current context.

    :param ctx: Click context
    """

    if ss.svars.get('cluster'):
        ss.svars['cluster'] = None
        ctx.meta['jumbo_shell'].prompt = click.style('jumbo > ', fg='green')
    else:
        click.echo('Use `quit` to quit the shell. Exit only removes context.')


####################
# cluster commands #
####################

def set_context(ctx, name):
    ctx.meta['jumbo_shell'].prompt = click.style(
        'jumbo (%s) > ' % name, fg='green')


@jumbo.command()
@click.argument('name')
@click.option('--domain', '-d', help='Domain name of the cluster')
@click.pass_context
def create(ctx, name, domain):
    """Create a new cluster.

    :param name: New cluster name
    """

    click.echo('Creating %s...' % name)
    try:
        clusters.create_cluster(cluster=name, domain=domain)
    except ex.CreationError as e:
        click.secho(e.message, fg='red', err=True)
    else:
        click.echo('Cluster `{}` created (domain name = "{}").'.format(
            name,
            domain if domain else '%s.local' % name))
        set_context(ctx, name)

@jumbo.command()
@click.argument('name')
@click.pass_context
def manage(ctx, name):
    """Set a cluster to manage. Persist --cluster option.

    :param name: Cluster name
    """

    click.echo('Loading %s...' % name)

    try:
        ss.load_config(cluster=name)
    except ex.LoadError as e:
        click.secho(e.message, fg='red', err=True)
        if e.type == 'NoConfFile':
            click.secho('Use "repair" to regenerate `jumbo_config`.')
    else:
        click.echo('Cluster `%s` loaded.' % name)
        set_context(ctx, name)


@jumbo.command()
@click.argument('name')
@click.option('--force', '-f', is_flag=True, help='Force deletion')
def delete(name, force):
    """Delete a cluster.

    :param name: Name of the cluster to delete
    """

    if not force:
        if not click.confirm(
                'Are you sure you want to delete the cluster %s' % name):
            return

    try:
        clusters.delete_cluster(cluster=name)
    except ex.LoadError as e:
        click.secho(e.message, fg='red', err=True)
    else:
        click.echo('Cluster `%s` deleted.' % name)
        ss.clear()


@jumbo.command()
def listcl():
    """List clusters managed by Jumbo."""
    try:
        cluster_table = PrettyTable(['Name', 'Domain Name', 'VMs',
                                     'Services'])
        for cluster in clusters.list_clusters():
            cluster_table.add_row([cluster['cluster'],
                                   cluster['domain'],
                                   len(cluster['machines']),
                                   ', '.join(cluster['services'])])
    except ex.LoadError as e:
        click.secho(e.message, fg='red', err=True)
        if e.type == 'NoConfFile':
            click.echo('Use "repair" to regenerate `jumbo_config`.')
    else:
        click.echo(cluster_table)


@jumbo.command()
@click.argument('name')
@click.option('--domain', '-d', help='Domain name of the cluster')
def repair(name, domain):
    """Recreate `jumbo_config` if it doesn't exist.

    :param name: Cluster name
    """

    if clusters.repair_cluster(cluster=name, domain=domain):
        click.echo('Recreated `jumbo_config` from scratch '
                   'for cluster `{}` (domain name = "{}").'
                   .format(name, domain if domain else '%s.local' % name))
    else:
        click.echo('Nothing to repair in cluster `%s`.' % name)


###############
# VM commands #
###############

def validate_ip_cb(ctx, param, value):
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
@click.option('--ip', '-i',  callback=validate_ip_cb, prompt='IP',
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
    switched = True if cluster else False
    if not cluster:
        cluster = ss.svars['cluster']

    try:
        vm.add_machine(name, ip, ram, disk, types, cpus, cluster=cluster)
    except (ex.LoadError, ex.CreationError) as e:
        click.secho(e.message, fg='red', err=True)
        if e.type == 'NoConfFile':
            click.secho('Use "repair" to regenerate `jumbo_config`.')
        switched = False
    else:
        click.echo('Machine `{}` added to cluster `{}`.'.format(name, cluster))
    finally:
        if switched:
            set_context(ctx, cluster)


@jumbo.command()
@click.argument('name')
@click.pass_context
@click.option('--cluster', '-c', help='Cluster of the VM to be deleted')
@click.option('--force', '-f', is_flag=True, help='Force deletion')
def rmvm(ctx, name, cluster, force):
    """Removes a VM.

    :param name: VM name
    """
    switched = True if cluster else False
    if not cluster:
        cluster = ss.svars['cluster']

    if not force:
        if not click.confirm(
                'Are you sure you want to remove the machine `{}` '
                'of cluster `{}`?'.format(name, cluster)):
            return

    try:
        vm.remove_machine(cluster=cluster, machine=name)
    except ex.LoadError as e:
        click.secho(e.message, fg='red', err=True)
        if e.type == 'NoConfFile':
            click.secho('Use "repair" to regenerate `jumbo_config`')
        switched = False
    else:
        click.echo('Machine `{}` removed of cluster `{}`.'
                   .format(name, cluster))
    finally:
        if switched:
            set_context(ctx, cluster)


@jumbo.command()
@click.option('--cluster', '-c', help='Cluster in which to list the VMs')
def listvm(cluster):
    """
    List VMs in the cluster being managed.
    Another cluster can be specified with "--cluster".
    """
    if not cluster:
        cluster = ss.svars['cluster']

    try:
        vm_table = PrettyTable(
            ['Name', 'Types', 'IP', 'RAM (MB)', 'Disk (MB)', 'CPUs'])

        for m in clusters.list_machines(cluster=cluster):
            vm_table.add_row([m['name'], ', '.join(m['types']), m['ip'],
                              m['ram'], m['disk'], m['cpus']])
    except ex.LoadError as e:
        click.secho(e.message, fg='red', err=True)
    else:
        click.echo(vm_table)



#####################
# services commands #
#####################

@jumbo.command()
@click.argument('name')
@click.option('--cluster', '-c',
              help='The cluster in which to add the service')
@click.pass_context
def addservice(ctx, name, cluster):
    """
    Add service to a cluster.
    """
    switched = True if cluster else False
    if not cluster:
        cluster = ss.svars['cluster']

    try:
        services.add_service(name, cluster=cluster)
    except ex.LoadError as e:
        click.secho(e.message, fg='red', err=True)
        switched = False
    except ex.CreationError as e:
        click.secho(e.message, fg='red', err=True)
    else:
        click.echo('Service `{}` added to cluster `{}`'
                   .format(name, cluster))
    finally:
        if switched:
            set_context(ctx, cluster)


@jumbo.command()
@click.argument('service')
@click.option('--cluster', '-c',
              help='The cluster in which to delete the service')
@click.option('--force', '-f', is_flag=True, help='Force deletion')
@click.pass_context
def rmservice(ctx, service, cluster, force):
    """
    Removes service from cluster.
    """
    switched = True if cluster else False
    if not cluster:
        cluster = ss.svars['cluster']

    if not force:
        if not click.confirm(
                'Are you sure you want to remove the service `{}` and all its '
                'components of cluster `{}`?'.format(service, cluster)):
            return


    try:
        switched = services.remove_service(service, cluster=cluster)
    except ex.LoadError as e:
        click.secho(e.message, fg='red', err=True)
    except ex.CreationError as e:
        click.secho(e.message, fg='red', err=True)
        switched = True
    else:
        click.echo('Service `{}` and its components removed from cluster `{}`.'
                   .format(service, cluster))
    finally:
        if switched:
            set_context(ctx, cluster)


@jumbo.command()
@click.argument('name')
@click.option('--machine', '-m', required=True)
@click.option('--cluster', '-c')
@click.pass_context
def addcomp(ctx, name, machine, cluster):
    """
    Add component to a machine.
    """
    switched = True if cluster else False
    if not cluster:
        cluster = ss.svars['cluster']

    try:
        services.add_component(name, machine=machine, cluster=cluster)
    except ex.LoadError as e:
        click.secho(e.message, fg='red', err=True)
        switched = False
    except ex.CreationError as e:
        click.secho(e.message, fg='red', err=True)
    else:
        click.echo('Component `{}` added to machine `{}/{}`'
                   .format(name, cluster, machine))
    finally:
        if switched:
            set_context(ctx, cluster)


@jumbo.command()
@click.argument('name')
@click.option('--machine', '-m', required=True)
@click.option('--cluster', '-c')
@click.option('--force', '-f', is_flag=True, help='Force deletion')
@click.pass_context
def rmcomp(ctx, name, machine, cluster, force):
    """
    Remove component from specified machine.
    """
    switched = True if cluster else False
    if not cluster:
        cluster = ss.svars['cluster']

    if not force:
        if not click.confirm(
                'Are you sure you want to remove the component `{}` '
                'of machine `{}/{}`?'.format(name, cluster, machine)):
            return

    try:
        services.remove_component(name,
                                  machine=machine,
                                  cluster=cluster)
    except ex.LoadError as e:
        click.secho(e.message, fg='red', err=True)
        switched = False
    except ex.CreationError as e:
        click.secho(e.message, fg='red', err=True)
    else:
        click.echo('Component `{}` removed of machine `{}/{}`'
                   .format(name, cluster, machine))
    finally:
        if switched:
            set_context(ctx, cluster)


@jumbo.command()
@click.argument('machine')
@click.option('--cluster', '-c')
def listcomp(machine, cluster):
    """
    List compononents on the given machine.
    """
    if not cluster:
        cluster = ss.svars['cluster']

    try:
        comp_table = PrettyTable(
            ['Component', 'Service'])

        for c in services.list_components(machine=machine, cluster=cluster):
            comp_table.add_row([c, services.check_component(c)])
    except ex.LoadError as e:
        click.secho(e.message, fg='red', err=True)
    else:
        click.echo(comp_table)
