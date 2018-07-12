# Service commands

## Add service

**Command: `addservice <name>`**

Add a service to a cluster and install the service's clients on all nodes. By default, also auto-install the service's components on the best fitting hosts.  
The list of the services is available in the [Supported services](../supported.md) section.

**Options**

- `--cluster` or `-c` - The cluster to which the service should be added.
- `--no-auto` - Avoid the auto-installation of the components. Only the clients will be installed. See [`addcomponent`](component.md#add-component) for manual component installation.
- `--ha` or `-h` - Install the service in High Availability mode. Not available for all services (list [here](../supported.md#services-supporting-high-availability)).
- `--recursive` or `-r` - Also install all the service's dependencies (components and services).

---
## Check service

**Command: `checkservice <name>`**

Check if a service is complete (if all the components needed for it to be functional are installed) on a cluster. If not, a list of the missing components is given.

**Options**

- `--cluster` or `-c` - The cluster on which to check the service.

---
## List services

**Command: `listservices`**

List all the services installed on a cluster and their status. The services' names are colored:
- green = service complete
- orange = service missing a few components
- red = service missing a lot of components
If a service misses components, they are listed.

**Options**

- `--cluster` or `-c` - The cluster in which the service should be deleted.

---
## Remove service

**Command: `rmservice <name>`**

Remove a service and all its components of a cluster. A service cannot be deleted if other services depend on it.

**Options**

- `--cluster` or `-c` - The cluster in which the service should be deleted.
- `--force` or `-f` - Avoid the confirmation prompt.
