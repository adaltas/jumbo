# Node commands

## Add node

**Command: `addnode <name>`**

Add a new empty node to a cluster.

**Options**

- `--types` or `-t` (required) - The node type(s) to choose between `master`, `sidemaster`, `edge`, `worker`, `ldap`. Type `-t` before each type. See [Key principles](../getting-started/key-principles.md) for type descriptions and [Avanced usage](../advanced-usage.md) for custom type creation.
- `--ip` or `-i` (prompt if not specified) - The node IP address.
- `--ram` or `-r` (prompt if not specified) - The memory allocated to the node in MB.
- `--cpus` or `-p` - The number of CPUs allocated to the node, 1 by default.
- `--cluster` or `-c` - The cluster to which the node should be added.

---
## List nodes

**Command: `listnodes`**

List the nodes of a cluster.

**Options**

- `--cluster` or `-c` - The cluster on which to list the nodes.

---
## Remove node

**Command: `rmnode <name>`**

Remove a node from a cluster.

**Options**

- `--force` or `-f` - Avoid the confirmation prompt.
- `--cluster` or `-c` - The cluster in which the node should be deleted.
