# Jumbo CLI

In this section you will find all the commands available in the Jumbo CLI to manipulate:
- [clusters](cluster.md)
- [nodes](node.md)
- [services](service.md)
- [components](component.md)

There are two ways of using the CLI:
- By typing each command individually with `jumbo [command]` in your terminal;
- By entering the Jumbo shell.

We recommand using the shell, because it makes commands lighter and optimizes data loading. However it is sometimes not possible to enter a shell (e.g. in bash scripts). 

## Using the Jumbo shell

You can enter the jumbo shell with the command `jumbo`. The principal advantage of the shell is that it allows to set the **Jumbo context** to a sepcific cluster.  
Once the context is set to a cluster, all the commands will be applied to that cluster without having to specify it with the `--cluster` tag.

## Not using the Jumbo shell

In this case, it is not possible to set a context. For every node or service command, it is necessary to specify the cluster with the tag `--cluster`.