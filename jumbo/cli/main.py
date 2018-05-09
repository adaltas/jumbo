import click
from click_shell.core import Shell
import ipaddress as ipadd
from prettytable import PrettyTable

from jumbo.core import clusters, machines as vm, services
from jumbo.utils import session as ss, exceptions as ex, checks
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
    sh = Shell(prompt=click.style('jumbo > ', fg='green'),
               intro=printlogo.jumbo_ascii() +
               '\nJumbo Shell. Enter "help" for list of supported commands.' +
               ' Type "quit" to leave the Jumbo Shell.' +
               click.style('\nJumbo v1.0',
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
    sh.add_command(listclusters)
    sh.add_command(listvms)
    sh.add_command(repair)
    sh.add_command(addservice)
    sh.add_command(addcomponent)
    sh.add_command(listcomponents)
    sh.add_command(rmservice)
    sh.add_command(rmcomponent)
    sh.add_command(checkservice)
    sh.add_command(seturl)
    sh.add_command(listservices)

    # If cluster exists, call manage command (saves the shell in session
    #  variable svars and adapts the shell prompt)
    if cluster:
        if not checks.check_cluster(cluster):
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
@click.option('--ambari-repo',
              help='URL to the Ambari repository used for the installation')
@click.option('--vdf',
              help='URL to the VDF file used for HDP install')
@click.pass_context
def create(ctx, name, domain, ambari_repo, vdf):
    """Create a new cluster.

    :param name: New cluster name
    """

    click.echo('Creating %s...' % name)
    try:
        clusters.create_cluster(cluster=name,
                                domain=domain,
                                ambari_repo=ambari_repo,
                                vdf=vdf)
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
@click.pass_context
def delete(ctx, name, force):
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
        ctx.meta['jumbo_shell'].prompt = click.style('jumbo > ', fg='green')


@jumbo.command()
@click.option('--full', is_flag=True, help='Force full display')
def listclusters(full):
    """List clusters managed by Jumbo."""
    try:
        limit = 40
        if full:
            limit = 1000
        cluster_table = PrettyTable(['Name', 'Domain Name', 'VMs',
                                     'Services', 'URLs'])
        cluster_table.align['Name'] = 'l'
        cluster_table.align['Domain Name'] = 'l'
        cluster_table.align['Services'] = 'l'
        cluster_table.align['URLs'] = 'l'
        for cluster in clusters.list_clusters():
            urls = []
            for k, v in cluster['urls'].items():
                urls.append((k + '=' + v)[:limit] + ('' if full else '...'))
            cluster_table.add_row([cluster['cluster'],
                                   cluster['domain'],
                                   len(cluster['machines']),
                                   '\n'.join(cluster['services']),
                                   '\n'.join(urls)])
    except ex.LoadError as e:
        click.secho(e.message, fg='red', err=True)
        if e.type == 'NoConfFile':
            click.echo('Use "repair" to regenerate `jumbo_config`.')
    else:
        cluster_table.sortby = 'Name'
        click.echo(cluster_table)


@jumbo.command()
@click.argument('name')
@click.option('--domain', '-d', help='Domain name of the cluster')
@click.option('--ambari-repo',
              help='URL to the Ambari repository used for the installation')
@click.option('--vdf',
              help='URL to the VDF file used for HDP install')
def repair(name, domain, ambari_repo, vdf):
    """Recreate `jumbo_config` if it doesn't exist.

    :param name: Cluster name
    """

    if clusters.repair_cluster(cluster=name,
                               domain=domain,
                               ambari_repo=ambari_repo,
                               vdf=vdf):
        click.echo('Recreated `jumbo_config` from scratch '
                   'for cluster `{}` (domain name = "{}").'
                   .format(name, domain if domain else '%s.local' % name))
    else:
        click.echo('Nothing to repair in cluster `%s`.' % name)


@jumbo.command()
@click.argument('name')
@click.option('--value', '-v', prompt='URL', required=True, help='URL string')
@click.option('--cluster', '-c')
@click.pass_context
def seturl(ctx, name, value, cluster):
    """Set an URL to use for downloads.

    :param name: URL name (`ambari_repo` or `vdf`)
    """

    switched = True if cluster else False
    if not cluster:
        cluster = ss.svars['cluster']

    try:
        clusters.set_url(url=name,
                         value=value,
                         cluster=cluster)
    except (ex.CreationError, ex.LoadError) as e:
        click.secho(e.message, fg='red', err=True)
        switched = False
    else:
        click.echo('`{}` of cluster `{}` set to {}'
                   .format(name, cluster, value))
    finally:
        if switched:
            set_context(ctx, cluster)


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
@click.option('--ip', '-i', callback=validate_ip_cb, prompt='IP',
              help='VM IP address')
@click.option('--ram', '-r', type=int, prompt='RAM (MB)',
              help='RAM allocated to the VM in MB')
@click.option('--cpus', '-p', default=1,
              help='Number of CPUs allocated to the VM')
@click.option('--cluster', '-c')
@click.pass_context
def addvm(ctx, name, types, ip, ram, cpus, cluster):
    """
    Create a new VM in the cluster being managed.
    Another cluster can be specified with "--cluster".

    :param name: New VM name
    """
    switched = True if cluster else False
    if not cluster:
        cluster = ss.svars['cluster']

    try:
        vm.add_machine(name, ip, ram, types, cpus, cluster=cluster)
        count = services.auto_install_machine(name, cluster)
    except (ex.LoadError, ex.CreationError) as e:
        click.secho(e.message, fg='red', err=True)
        if e.type == 'NoConfFile':
            click.secho('Use "repair" to regenerate `jumbo_config`.')
        switched = False
    else:
        click.echo('Machine `{}` added to cluster `{}`. {}'
                   .format(name, cluster,
                           '{} clients auto installed on `{}`.'
                           .format(count, name) if count else ''))
    finally:
        if switched:
            set_context(ctx, cluster)


@jumbo.command()
@click.argument('name')
@click.pass_context
@click.option('--cluster', '-c')
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
@click.option('--cluster', '-c')
def listvms(cluster):
    """
    List VMs in the cluster being managed.
    Another cluster can be specified with "--cluster".
    """
    if not cluster:
        cluster = ss.svars['cluster']

    try:
        vm_table = PrettyTable(
            ['Name', 'Types', 'IP', 'RAM (MB)', 'CPUs'])

        for m in clusters.list_machines(cluster=cluster):
            vm_table.add_row([m['name'], ', '.join(m['types']), m['ip'],
                              m['ram'], m['cpus']])
    except ex.LoadError as e:
        click.secho(e.message, fg='red', err=True)
    else:
        print_with_colors(vm_table)


#####################
# services commands #
#####################

@jumbo.command()
@click.argument('name')
@click.option('--cluster', '-c')
@click.option('--no-auto', is_flag=True, help='Avoid auto-install')
@click.option('--ha', '-h', is_flag=True, help='High Availability mode')
@click.pass_context
def addservice(ctx, name, cluster, no_auto, ha):
    """
    Add a service to a cluster and auto-install its components
    on the best fitting hosts.
    """
    switched = True if cluster else False
    if not cluster:
        cluster = ss.svars['cluster']

    try:
        services.add_service(name=name, ha=ha, cluster=cluster)
        if no_auto:
            msg = ('No component has been auto-installed (except clients). '
                   'Use "addcomp" manually.')
        else:
            count = services.auto_assign(service=name, ha=ha, cluster=cluster)
            msg = ('{} type{} of component{} auto-installed. '
                   'Use "listcomponents -a" for details.'
                   .format(count,
                           's' if count > 1 else '',
                           's' if count > 1 else ''))
    except ex.LoadError as e:
        click.secho(e.message, fg='red', err=True)
        switched = False
        if e.type == 'NotExist':
            click.echo('Available services:\n - %s'
                       % '\n - '.join(services.get_available_services()))
    except ex.CreationError as e:
        click.secho(e.message, fg='red', err=True)
    else:
        click.echo('Service `{}` and related clients added to cluster `{}`.\n'
                   .format(name, cluster) + msg)
    finally:
        if switched:
            set_context(ctx, cluster)


@jumbo.command()
@click.argument('service')
@click.option('--cluster', '-c')
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
        services.remove_service(service, cluster=cluster)
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
def addcomponent(ctx, name, machine, cluster):
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
        click.echo('Component `{}` added to machine `{}/{}`.'
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
def rmcomponent(ctx, name, machine, cluster, force):
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
@click.argument('machine', required=False)
@click.option('--cluster', '-c')
@click.option('--all', '-a', is_flag=True,
              help='List components on all machines')
@click.option('--abbr', is_flag=True, help='Display abbreviations')
def listcomponents(machine, cluster, all, abbr):
    """
    List compononents on a given machine.
    """
    if not cluster:
        cluster = ss.svars['cluster']

    if all:
        for m in ss.svars['machines']:
            comp_table = PrettyTable(['Component', 'Service'])
            comp_table.align['Component'] = 'l'
            comp_table.align['Service'] = 'l'
            click.echo('\n' + m['name'] + ':')
            try:
                for c in services.list_components(machine=m['name'],
                                                  cluster=cluster):
                    service = services.check_component(c)
                    comp_table.add_row([
                        c if not abbr else services.get_abbr(c, service),
                        service
                    ])
                    comp_table.sortby = 'Service'
            except ex.LoadError as e:
                click.secho(e.message, fg='red', err=True)
            else:
                print_with_colors(comp_table)

    else:
        if machine is None:
            click.secho('You need to specify a machine name. Use --all to list'
                        ' all machines', fg='red', err=True)
            return
        try:
            comp_table = PrettyTable(['Component', 'Service'])
            comp_table.align['Component'] = 'l'
            comp_table.align['Service'] = 'l'
            for c in services.list_components(machine=machine,
                                              cluster=cluster):
                service = services.check_component(c)
                comp_table.add_row([
                    c if not abbr else services.get_abbr(c, service),
                    service
                ])
                comp_table.sortby = 'Service'
        except ex.LoadError as e:
            click.secho(e.message, fg='red', err=True)
        else:
            print_with_colors(comp_table)


@jumbo.command()
@click.argument('name')
@click.option('--cluster', '-c')
def checkservice(name, cluster):
    """Check if a service is complete (if all needed components are installed).

    :param name: Service name
    """

    if not cluster:
        cluster = ss.svars['cluster']

    try:
        missing_comp = services.check_service_complete(name=name,
                                                       cluster=cluster)
    except (ex.LoadError, ex.CreationError) as e:
        click.secho(e.message, fg='red', err=True)
    else:
        if missing_comp:
            click.echo('The service `{}` misses:\n{}'
                       .format(name, '\n'.join(missing_comp)))
        else:
            click.echo('The service `%s` is complete.' % name)


@jumbo.command()
@click.option('--cluster', '-c')
def listservices(cluster):
    """Check the state of all services installed.

    :param cluster: Cluster name
    :type cluster: str
    """

    if not cluster:
        cluster = ss.svars['cluster']

    try:
        table_serv = PrettyTable(['Service', 'HA', 'Missing components'])
        table_serv.align = 'l'
        for s in ss.svars['services']:
            color = 'green'
            missing_comp = services.check_service_complete(name=s,
                                                           cluster=cluster)
            if missing_comp:
                print_missing = '\n'.join(missing_comp)
                color = 'yellow' if len(missing_comp) < 5 else 'red'
            else:
                print_missing = '-'
            table_serv.add_row([click.style(s, fg=color),
                                'X' if services.check_ha(s) else ' ',
                                print_missing])
        table_serv.sortby = 'Service'
    except (ex.LoadError, ex.CreationError) as e:
        click.secho(e.message, fg='red', err=True)
    else:
        click.echo(table_serv)


@jumbo.command()
def logo():
    """Print a random ASCII logo.
    """

    click.echo(printlogo.jumbo_ascii())


def print_with_colors(table):
    to_print = []
    color = False
    lines = table.get_string().split('\n')
    for i, l in enumerate(lines):
        if i > 2 and lines[i] != lines[-1]:
            to_print.append(click.style(l, fg='blue' if color else 'white'))
            color = not color
        else:
            to_print.append(l)
    for l in to_print:
        click.echo(l)
