# Component commands

## Add component

**Command: `addcomponent [name]`**

Add a component to a node.
The list of the components is available in the [Supported services](../supported.md) section.

**Options**

- `--node` or `-n` (required) - The node on which the component should be added.
- `--cluster` or `-c` - The cluster of the node.

---
## List components

**Command: `listservices`**

List the components installed on a node.

**Options**

- `--node` or `-n` - The node on which the components should be listed.
- `--all` or `-a` - List the components on all nodes.
- `--cluster` or `-c` - The cluster of the node(s).

---
## Remove component

**Command: `rmcomponent [name]`**

Remove a component of a node.

**Options**

- `--node` or `-n` - The node of which the component should be removed.
- `--cluster` or `-c` - The cluster of the node(s).
- `--force` or `-f` - Avoid the confirmation prompt.

