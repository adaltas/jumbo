import click
from click_shell.core import Shell
import sys
import ipaddress as ipadd
from prettytable import PrettyTable
import json
import ansible
import os

from jumbo.core import clusters, nodes, services, bundles, vault
from jumbo.utils import session as ss, exceptions as ex, checks
from jumbo.cli import printlogo
from jumbo.utils.settings import OS, JUMBODIR
from jumbo.utils.prepare import init_jumbo


def print_with_color(message, color):
    if OS != 'Windows':
        click.secho(message, fg=color)
    else:
        click.echo(message)


@click.group(invoke_without_command=True)
@click.option('--cluster', '-c')
@click.pass_context
def jumbo(ctx, cluster):
    """
    Execute a Jumbo command.
    If no command is passed, start the Jumbo shell interactive mode.
    """

    init_jumbo()
    # Create the shell
    sh = Shell(prompt=click.style('jumbo > ', fg='green') if OS != 'Windows'
               else 'jumbo > ',
               intro=printlogo.jumbo_ascii() +
               '\nJumbo Shell. Enter "help" for list of supported commands.' +
               ' Type "quit" to leave the Jumbo Shell.' +
               click.style('\nJumbo v0.4.4',
                           fg='cyan'))
    # Save the shell in the click context (to modify its prompt later on)
    ctx.meta['jumbo_shell'] = sh.shell
    # Register commands that can be used in the shell
    sh.add_command(create)
    sh.add_command(exit)
    sh.add_command(delete)
    sh.add_command(use)
    sh.add_command(addnode)
    sh.add_command(rmnode)
    sh.add_command(editnode)
    sh.add_command(listclusters)
    sh.add_command(listnodes)
    sh.add_command(repair)
    sh.add_command(addservice)
    sh.add_command(addcomponent)
    sh.add_command(listcomponents)
    sh.add_command(listbundles)
    sh.add_command(rmservice)
    sh.add_command(rmcomponent)
    sh.add_command(rmbundle)
    sh.add_command(checkservice)
    sh.add_command(listservices)
    sh.add_command(start)
    sh.add_command(stop)
    sh.add_command(status)
    sh.add_command(provision)
    sh.add_command(restart)
    sh.add_command(addbundle)
    sh.add_command(addpass)
    sh.add_command(rmpass)
    sh.add_command(getpass)
    sh.add_command(savetemplate)

    # If cluster exists, call manage command (saves the shell in session
    #  variable svars and adapts the shell prompt)
    if cluster:
        if not checks.check_cluster(cluster):
            click.echo('This cluster does not exist.'
                       ' Use "create NAME" to create it.', err=True)
        else:
            ctx.invoke(use, name=cluster)

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
        click.echo('Use "quit" to quit the shell. Exit only removes context.')


@jumbo.command()
@click.argument('name')
@click.pass_context
def use(ctx, name):
    """Set a cluster to manage. Persist --cluster option.

    :param name: Cluster name
    """

    click.echo('Loading %s...' % name)

    try:
        ss.load_config(cluster=name)
        # Load services and node types according to active bundles
        services.config = services.load_services_conf(cluster=name)
        ss.dump_config(services.get_services_components_hosts(),
                       services.config)
    except ex.LoadError as e:
        print_with_color(e.message, 'red')
        if e.type == 'NoConfFile':
            click.echo('Use "repair" to regenerate `jumbo_config`.')
    except RuntimeError as e:
        print_with_color(str(e), 'red')
    else:
        click.echo('Cluster "%s" loaded.' % name)
        set_context(ctx, name)


####################
# cluster commands #
####################


def set_context(ctx, name):
    to_print = 'jumbo (%s) > ' % name
    ctx.meta['jumbo_shell'].prompt = click.style(
        to_print, fg='green') if OS != 'Windows' else to_print


def validate_cluster_name_cb(ctx, param, value):
    if not value:
        return value

    if '-' in value:
        raise click.BadParameter('"%s" is not a valid name for a cluster.\n'
                                 'Forbidden characters: "-"' % value)

    return value


@jumbo.command()
@click.argument('name', callback=validate_cluster_name_cb)
@click.option('--domain', '-d', help='Domain name of the cluster')
@click.option('--realm', '-R', help='Realm of the cluster')
@click.option('--template', '-t', help='Preconfigured cluster name')
@click.option('--template-file', '-t', type=click.Path(),
              help='Preconfigured cluster path')
@click.option('--remote', '-r', is_flag=True, help='Use existing machines')
@click.pass_context
def create(ctx, name, domain, realm, template, template_file, remote):
    """Create a new cluster.

    :param name: New cluster name
    """
    if template and template_file:
        print_with_color(
            '--template or --template-file required, not both.', 'red')
        sys.exit(1)

    click.echo('Creating "%s"...' % name)
    try:
        clusters.create_cluster(cluster=name,
                                domain=domain,
                                realm=realm,
                                template=template,
                                template_path=template_file,
                                remote=remote)
    except ex.CreationError as e:
        print_with_color(e.message, 'red')
    else:
        click.echo('Cluster "{}" created (domain name = "{}").'.format(
            name,
            domain if domain else '%s.local' % name))
        set_context(ctx, name)


@jumbo.command()
@click.argument('cluster_name', required=False)
@click.option('--cluster', '-c')
@click.option('--force', '-f', is_flag=True, help='Force deletion')
@click.pass_context
def delete(ctx, cluster_name, cluster, force):
    """Delete a cluster.

    :param name: Name of the cluster to delete
    """
    cluster = cluster_name if cluster_name else cluster
    if not cluster:
        cluster = ss.svars['cluster']

    if not force:
        if not click.confirm(
                'Are you sure you want to delete the cluster %s' % cluster):
            return

    try:
        clusters.delete_cluster(cluster=cluster)
    except ex.LoadError as e:
        print_with_color(e.message, 'red')
    else:
        click.echo('Cluster "%s" deleted.' % cluster)
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
                                     'Services'])
        cluster_table.align['Name'] = 'l'
        cluster_table.align['Domain Name'] = 'l'
        cluster_table.align['Services'] = 'l'
        for cluster in clusters.list_clusters():
            cluster_table.add_row([cluster['cluster'],
                                   cluster['domain'],
                                   len(cluster['nodes']),
                                   '\n'.join(cluster['services'])])
    except ex.LoadError as e:
        print_with_color(e.message, 'red')
        if e.type == 'NoConfFile':
            click.echo('Use "repair" to regenerate "jumbo_config".')
    else:
        cluster_table.sortby = 'Name'
        click.echo(cluster_table)


@jumbo.command()
@click.argument('name')
@click.option('--domain', '-d', help='Domain name of the cluster')
@click.option('--remote', '-r', is_flag=True, help='Use existing machines')
def repair(name, domain, remote):
    """Recreate "jumbo_config" if it doesn't exist.

    :param name: Cluster name
    """

    if clusters.repair_cluster(cluster=name,
                               domain=domain,
                               remote=remote):
        click.echo('Recreated "jumbo_config" from scratch '
                   'for cluster "{}" (domain name = "{}").'
                   .format(name, domain if domain else '%s.local' % name))
    else:
        click.echo('Nothing to repair in cluster "%s".' % name)


##################
# Nodes commands #
##################

def validate_ip_cb(ctx, param, value):
    return value
    if not value:
        return value
    try:
        ipadd.ip_address(value)
    except ValueError:
        raise click.BadParameter('"%s" is not a valid IP address.' % value)

    return value


@jumbo.command()
@click.argument('name')
@click.option('--types', '-t', multiple=True,
              required=True, help='VM host type(s)')
@click.option('--ip', '-i', callback=validate_ip_cb, prompt='IP',
              help='VM IP address')
@click.option('--ram', '-r', type=int, prompt='RAM (MB)',
              help='RAM allocated to the VM in MB')
@click.option('--cpus', '-p', default=1,
              help='Number of CPUs allocated to the VM')
@click.option('--cluster', '-c')
@click.pass_context
def addnode(ctx, name, types, ip, ram, cpus, cluster):
    """
    Create a new VM in the cluster being managed.
    Another cluster can be specified with "--cluster".

    :param name: New VM name
    """
    for type in types:
        if type not in services.get_available_types():
            print_with_color('Error: Invalid node type: `%s`. Available: %s' %
                             (type, services.get_available_types()), 'red')
            return

    switched = True if cluster else False
    if not cluster:
        cluster = ss.svars['cluster']

    try:
        nodes.add_node(name, ip, ram, types, cpus, cluster=cluster)
        count = services.auto_install_node(name, cluster)
    except (ex.LoadError, ex.CreationError) as e:
        print_with_color(e.message, 'red')
        if e.type == 'NoConfFile':
            click.echo('Use "repair" to regenerate `jumbo_config`.')
        switched = False
    else:
        click.echo('Machine "{}" added to cluster "{}". {}'
                   .format(name, cluster,
                           '{} clients auto installed on "{}".'
                           .format(count, name) if count else ''))
    finally:
        if switched:
            set_context(ctx, cluster)


@jumbo.command()
@click.argument('name')
@click.pass_context
@click.option('--cluster', '-c')
@click.option('--force', '-f', is_flag=True, help='Force deletion')
def rmnode(ctx, name, cluster, force):
    """Removes a VM.

    :param name: VM name
    """
    switched = True if cluster else False
    if not cluster:
        cluster = ss.svars['cluster']

    if not force:
        if not click.confirm(
                'Are you sure you want to remove the node "{}" '
                'of cluster "{}"?'.format(name, cluster)):
            return

    try:
        nodes.remove_node(cluster=cluster, node=name)
    except ex.LoadError as e:
        print_with_color(e.message, 'red')
        if e.type == 'NoConfFile':
            click.echo('Use "repair" to regenerate `jumbo_config`')
        switched = False
    else:
        click.echo('Machine "{}" removed of cluster "{}".'
                   .format(name, cluster))
    finally:
        if switched:
            set_context(ctx, cluster)


@jumbo.command()
@click.argument('name', required=True)
@click.option('--ip', '-i', callback=validate_ip_cb,
              help='VM new IP address')
@click.option('--ram', '-r', type=int,
              help='RAM allocated to the VM in MB')
@click.option('--cpus', '-p',
              help='Number of CPUs allocated to the VM')
@click.option('--newname', '-n',
              help='New name of the node')
@click.option('--cluster', '-c')
@click.pass_context
def editnode(ctx, name, ip, ram, cpus, newname, cluster):
    """
    Modifies an already existing VM in the cluster being managed.

    """

    switched = True if cluster else False
    if not cluster:
        cluster = ss.svars['cluster']

    if ip or ram or cpus or newname:
        try:
            changed = nodes.edit_node(name,
                                      ip,
                                      ram,
                                      cpus,
                                      newname,
                                      cluster=cluster)
            if changed:
                click.echo('\n"{}" configurations changed:\n - {}'.format(
                    name,
                    '\n - '.join(
                        '{}: {} -> {}'
                        .format(c[0], c[1], c[2]) for c in changed))
                )
        except (ex.LoadError, ex.CreationError) as e:
            print_with_color(e.message, 'red')
    else:
        click.echo('Nothing to do. Type "help editnode" for usage.')

    if switched:
        set_context(ctx, cluster)


@jumbo.command()
@click.option('--cluster', '-c')
def listnodes(cluster):
    """
    List VMs in the cluster being managed.
    Another cluster can be specified with "--cluster".
    """
    if not cluster:
        cluster = ss.svars['cluster']

    try:
        node_table = PrettyTable(
            ['Name', 'Types', 'IP', 'RAM (MB)', 'CPUs'])

        for m in clusters.list_nodes(cluster=cluster):
            node_table.add_row([m['name'], ', '.join(m['types']), m['ip'],
                                m['ram'], m['cpus']])
    except ex.LoadError as e:
        print_with_color(e.message, 'red')
    else:
        print_colorized_table(node_table)


#####################
# services commands #
#####################

@jumbo.command()
@click.argument('name')
@click.option('--cluster', '-c')
@click.option('--no-auto', is_flag=True, help='Avoid auto-install')
@click.option('--ha', '-h', is_flag=True, help='High Availability mode')
@click.option('--recursive', '-r', is_flag=True,
              help='Also auto-install all other services needed')
@click.option('--force', '-f', is_flag=True, help='Accept all prompts')
@click.option('--config', '-K', type=click.File('r'),
              help='Read config from a file')
@click.pass_context
def addservice(ctx, name, cluster, no_auto, ha, recursive, force, config):
    """
    Add a service to a cluster and auto-install its components
    on the best fitting hosts.
    """
    switched = True if cluster else False
    if not cluster:
        cluster = ss.svars['cluster']

    try:
        msg = ''
        auto_installed_count = 0
        if recursive:
            dep_serv = ''
            dep_comp = ''
            dependencies = services.get_service_dependencies(name=name,
                                                             ha=ha,
                                                             first=True,
                                                             cluster=cluster)
            if dependencies['components'] or dependencies['services']:
                click.echo('The service %s and its dependencies will be'
                           ' installed. Dependencies:' % name)
                if dependencies['components']:
                    dep_comp = ('Components:\n - %s\n' %
                                '\n - '.join(
                                    '{} {}'
                                    .format(v, k) for k, v in
                                    dependencies['components'].items()))
                if dependencies['services']:
                    dep_serv = ('Services:\n - %s\n' %
                                '\n - '.join(dependencies['services']))

                confirmed = True if force else click.confirm(
                    '{}{}\nDo you want to continue?'
                    .format(dep_comp, dep_serv))

                if confirmed:
                    auto_installed_count = services.install_dependencies(
                        dependencies=dependencies,
                        cluster=cluster)
                    msg += 'Auto-installed the dependencies:\n{}{}'.format(
                        dep_comp, dep_serv)
                else:
                    click.echo('Installation canceled.')
                    return

        conf = json.load(config) if config else {}
        services.add_service(name=name, ha=ha, cluster=cluster, serv_vars=conf)
        if no_auto:
            msg += ('No component has been auto-installed (except clients). '
                    'Use "addcomp" manually.')
        else:
            count = services.auto_assign(service=name, ha=ha, cluster=cluster)
            msg += ('{} type{} of component{} auto-installed. '
                    'Use "listcomponents -a" for details.'
                    .format(count + auto_installed_count,
                            's' if count > 1 else '',
                            's' if count > 1 else ''))
    except ex.LoadError as e:
        print_with_color(e.message, 'red')
        switched = False
        if e.type == 'NotExist':
            click.echo('Available services:\n - %s'
                       % '\n - '.join(services.get_available_services()))
    except ex.CreationError as e:
        print_with_color(e.message, 'red')
    else:
        click.echo('Service "{}" and related clients added to cluster "{}".\n'
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
                'Are you sure you want to remove the service "{}" and all its '
                'components of cluster "{}"?'.format(service, cluster)):
            return

    try:
        services.remove_service(service, cluster=cluster)
    except ex.LoadError as e:
        print_with_color(e.message, 'red')
    except ex.CreationError as e:
        print_with_color(e.message, 'red')
        switched = True
    else:
        click.echo('Service "{}" and its components removed from cluster "{}".'
                   .format(service, cluster))
    finally:
        if switched:
            set_context(ctx, cluster)


@jumbo.command()
@click.argument('name')
@click.option('--node', '-n', required=True)
@click.option('--cluster', '-c')
@click.pass_context
def addcomponent(ctx, name, node, cluster):
    """
    Add component to a node.
    """
    switched = True if cluster else False
    if not cluster:
        cluster = ss.svars['cluster']

    try:
        services.add_component(name, node=node, cluster=cluster)
    except ex.LoadError as e:
        print_with_color(e.message, 'red')
        switched = False
    except ex.CreationError as e:
        print_with_color(e.message, 'red')
    else:
        click.echo('Component "{}" added to node "{}/{}".'
                   .format(name, cluster, node))
    finally:
        if switched:
            set_context(ctx, cluster)


@jumbo.command()
@click.argument('name')
@click.option('--node', '-n', required=True)
@click.option('--cluster', '-c')
@click.option('--force', '-f', is_flag=True, help='Force deletion')
@click.pass_context
def rmcomponent(ctx, name, node, cluster, force):
    """
    Remove component from specified node.
    """
    switched = True if cluster else False
    if not cluster:
        cluster = ss.svars['cluster']

    if not force:
        if not click.confirm(
                'Are you sure you want to remove the component "{}" '
                'of node "{}/{}"?'.format(name, cluster, node)):
            return

    try:
        services.remove_component(name,
                                  node=node,
                                  cluster=cluster)
    except ex.LoadError as e:
        print_with_color(e.message, 'red')
        switched = False
    except ex.CreationError as e:
        print_with_color(e.message, 'red')
    else:
        click.echo('Component "{}" removed of node "{}/{}"'
                   .format(name, cluster, node))
    finally:
        if switched:
            set_context(ctx, cluster)


@jumbo.command()
@click.argument('node', required=False)
@click.option('--cluster', '-c')
@click.option('--all', '-a', is_flag=True,
              help='List components on all nodes')
@click.option('--abbr', is_flag=True, help='Display abbreviations')
def listcomponents(node, cluster, all, abbr):
    """
    List compononents on a given node.
    """
    if not cluster:
        cluster = ss.svars['cluster']

    if all:
        for m in ss.svars['nodes']:
            comp_table = PrettyTable(['Component', 'Service'])
            comp_table.align['Component'] = 'l'
            comp_table.align['Service'] = 'l'
            click.echo('\n' + m['name'] + ':')
            try:
                for c in services.list_components(node=m['name'],
                                                  cluster=cluster):
                    service = services.check_component(c)
                    comp_table.add_row([
                        c if not abbr else services.get_abbr(c, service),
                        service
                    ])
                    comp_table.sortby = 'Service'
            except ex.LoadError as e:
                print_with_color(e.message, 'red')
            else:
                print_colorized_table(comp_table)

    else:
        if node is None:
            click.secho('You need to specify a node name. Use --all to list'
                        ' all nodes', fg='red', err=True)
            return
        try:
            comp_table = PrettyTable(['Component', 'Service'])
            comp_table.align['Component'] = 'l'
            comp_table.align['Service'] = 'l'
            for c in services.list_components(node=node,
                                              cluster=cluster):
                service = services.check_component(c)
                comp_table.add_row([
                    c if not abbr else services.get_abbr(c, service),
                    service
                ])
                comp_table.sortby = 'Service'
        except ex.LoadError as e:
            print_with_color(e.message, 'red')
        else:
            print_colorized_table(comp_table)


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
        print_with_color(e.message, 'red')
    else:
        if missing_comp:
            click.echo('The service "{}" misses:\n{}'
                       .format(name, '\n'.join(missing_comp)))
        else:
            click.echo('The service "%s" is complete.' % name)


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
        print_with_color(e.message, 'red')
    else:
        click.echo(table_serv)


####################
#  Cluster state   #
####################

@jumbo.command()
@click.argument('cluster_name', required=False)
@click.option('--cluster', '-c')
@click.option('--no-provision', is_flag=True)
def start(cluster_name, cluster, no_provision):
    """Launches the VMs (vagrant up)
    """

    cluster = cluster_name if cluster_name else cluster
    if not cluster:
        cluster = ss.svars['cluster']

    try:
        clusters.start(no_provision, cluster=cluster)
    except (ex.LoadError, ex.CreationError) as e:
        print_with_color(e.message, 'red')


@jumbo.command()
@click.argument('cluster_name', required=False)
@click.option('--cluster', '-c')
def stop(cluster_name, cluster):
    cluster = cluster_name if cluster_name else cluster

    if not cluster:
        cluster = ss.svars['cluster']

    try:
        clusters.stop(cluster=cluster)
    except (ex.LoadError, ex.CreationError) as e:
        print_with_color(e.message, 'red')


@jumbo.command()
@click.argument('cluster_name', required=False)
@click.option('--cluster', '-c')
def status(cluster_name, cluster):
    cluster = cluster_name if cluster_name else cluster

    if not cluster:
        cluster = ss.svars['cluster']

    try:
        clusters.status(cluster=cluster)
    except (ex.LoadError, ex.CreationError) as e:
        print_with_color(e.message, 'red')


@jumbo.command()
@click.argument('cluster_name', required=False)
@click.option('--cluster', '-c')
def restart(cluster_name, cluster):
    cluster = cluster_name if cluster_name else cluster

    if not cluster:
        cluster = ss.svars['cluster']

    try:
        clusters.restart(cluster=cluster)
    except (ex.LoadError, ex.CreationError) as e:
        print_with_color(e.message, 'red')


@jumbo.command()
@click.argument('cluster_name', required=False)
@click.option('--cluster', '-c')
def provision(cluster_name, cluster):
    cluster = cluster_name if cluster_name else cluster

    if not cluster:
        cluster = ss.svars['cluster']

    try:
        clusters.provision(cluster=cluster)
    except (ex.LoadError, ex.CreationError) as e:
        print_with_color(e.message, 'red')


###########
# Bundles #
###########

@jumbo.command()
@click.argument('bundle_name', required=False)
@click.option('--name')
@click.option('--position', '-p', default='last')
@click.option('--cluster', '-c')
def addbundle(bundle_name, name, position, cluster):
    name = bundle_name if bundle_name else name

    if not cluster:
        cluster = ss.svars['cluster']

    try:
        bundles.add_bundle(name=name,
                           cluster=cluster,
                           position=position)
    except RuntimeError as e:
        print_with_color('Error: %s' % str(e), 'red')
    except (ex.LoadError, ex.CreationError) as e:
        print_with_color(e.message, 'red')
    except Warning as w:
        print_with_color('Warning: %s' % str(w), 'yellow')


@jumbo.command()
@click.argument('bundle_name', required=False)
@click.option('--name')
@click.option('--cluster', '-c')
def rmbundle(bundle_name, name, cluster):
    name = bundle_name if bundle_name else name
    if name is None:
        raise click.UsageError('Missing argument "BUNDLE_NAME"')

    if not cluster:
        cluster = ss.svars['cluster']

    try:
        bundles.rm_bundle(name=name, cluster=cluster)
    except RuntimeError as e:
        print_with_color('Error: %s' % str(e), 'red')
    except Warning as w:
        print_with_color('Warning: %s' % str(w), 'yellow')


@jumbo.command()
@click.option('--cluster', '-c')
def listbundles(cluster):

    if not cluster:
        cluster = ss.svars['cluster']

    try:
        (active, available) = bundles.list_bundles()
        # TODO output nice tables
        print("Active bundles: ")
        print(active)
        print("Available bundles: ")
        print(available)
    except (ex.LoadError, ex.CreationError) as e:
        print_with_color(e.message, 'red')
    except RuntimeError as e:
        print_with_color('Error: %s' % str(e), 'red')
    except Warning as w:
        print_with_color('Warning: %s' % str(w), 'yellow')


############
# Template #
############


@jumbo.command()
@click.option('--name', help='Save by name in Jumbo default location.')
@click.option('--path', help='Custom location for template JSON file.')
@click.option('--cluster', '-c')
@click.option('--force', '-f', is_flag=True)
def savetemplate(name, path, cluster, force):
    if not cluster:
        cluster = ss.svars['cluster']

    if not name and not path:
        print_with_color('--name or --path required.', 'red')
        sys.exit(1)
    if name and path:
        print_with_color('--name or --path required, not both.', 'red')
        sys.exit(1)

    template_path = path if path else JUMBODIR + 'templates/' + name + '.json'
    if os.path.isfile(template_path):
        if not force:
            if not click.confirm(
                    'Are you sure you want to delete the cluster %s' % cluster):
                return

    try:
        ss.load_config(cluster=cluster)
        # Load services and node types according to active bundles
        services.config = services.load_services_conf(cluster=cluster)
        ss.dump_template(template_path, services.get_services_components_hosts(),
                         services.config)
    except ex.LoadError as e:
        print_with_color(e.message, 'red')
    else:
        print_with_color('Template `%s` saved.' %
                         template_path.split('/')[-1].split('.')[0], 'green')


#########
# Vault #
#########


@jumbo.command()
@click.argument('vault_key')
@click.argument('vault_value', required=False)
@click.option('--cluster', '-c')
@click.option('--length', '-l', type=int, default=10)
@click.option('--password', '-p', default='changeit')
def addpass(vault_key, vault_value, cluster, length, password):
    if not cluster:
        cluster = ss.svars['cluster']

    try:
        vault.add_pass(vault_key, vault_value, length,
                       password, cluster=cluster)
    except (ex.LoadError, ex.CreationError) as e:
        print_with_color(e.message, 'red')
    except (ansible.parsing.vault.AnsibleVaultError) as e:
        print_with_color(e.message + '. Wrong vault password ?', 'red')


@jumbo.command()
@click.argument('vault_key')
@click.option('--cluster', '-c')
@click.option('--password', '-p', default='changeit')
def rmpass(vault_key, cluster, password):
    if not cluster:
        cluster = ss.svars['cluster']

    try:
        vault.rm_pass(vault_key, password, cluster=cluster)
    except (ex.LoadError, ex.CreationError) as e:
        print_with_color(e.message, 'red')
    except (ansible.parsing.vault.AnsibleVaultError) as e:
        print_with_color(e.message + '. Wrong vault password ?', 'red')


@jumbo.command()
@click.argument('vault_key', required=False, default='*')
@click.option('--cluster', '-c')
@click.option('--password', '-p', default='changeit')
def getpass(vault_key, cluster, password):
    if not cluster:
        cluster = ss.svars['cluster']

    try:
        vault.get_pass(vault_key, password, cluster=cluster)
    except (ex.LoadError, ex.CreationError) as e:
        print_with_color(e.message, 'red')
    except (ansible.parsing.vault.AnsibleVaultError) as e:
        print_with_color(e.message + '. Wrong vault password ?', 'red')


@jumbo.command()
@click.argument('vault_pass')
@click.argument('new_vault_pass')
@click.option('--cluster', '-c')
def changevaultpass(vault_pass, new_vault_pass, cluster):
    if not cluster:
        cluster = ss.svars['cluster']

    try:
        vault.change_vault_pass(vault_pass, new_vault_pass, cluster=cluster)
    except (ex.LoadError, ex.CreationError) as e:
        print_with_color(e.message, 'red')
    except (ansible.parsing.vault.AnsibleVaultError) as e:
        print_with_color(e.message + '. Wrong vault password ?', 'red')


#########
# Bonus #
#########


@jumbo.command()
def logo():
    """Print a random ASCII logo.
    """

    click.echo(printlogo.jumbo_ascii())


def print_colorized_table(table):
    to_print = []

    if OS != 'Windows':
        color = False
        lines = table.get_string().split('\n')
        for i, l in enumerate(lines):
            if i > 2 and lines[i] != lines[-1]:
                to_print.append(click.style(
                    l, fg='blue' if color else 'white'))
                color = not color
            else:
                to_print.append(l)
    else:
        to_print = table

    for l in to_print:
        click.echo(l)
