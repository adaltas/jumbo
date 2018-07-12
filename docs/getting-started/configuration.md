# Cluster configuration

Now we are ready to create and configure our first cluster with Jumbo!

## Cluster creation and Jumbo context

First, lets enter the Jumbo shell and create our cluster:

```shell
**[terminal]
[**[prompt user@computer]**[path :~]]**[delimiter $ ]**[command jumbo]
Jumbo v0.4.1
**[prompt jumbo > ]**[command create mycluster]
Creating mycluster...
Cluster "mycluster" created (domain name = "mycluster.local").
**[prompt jumbo (mycluster) > ]
```

After creating a cluster, the *Jumbo context* is set to this cluster. You can see the name of the cluster loaded (`jumbo (mycluster) >`). Use `exit` to reset the context, and then `use` to set the context to an existing cluster:

```shell
**[terminal]
**[prompt jumbo (mycluster) > ]**[command exit]
**[prompt jumbo > ]**[command use anothercluster]
Loading anothercluster...
Cluster "anothercluster" loaded.
**[prompt jumbo (anothercluster) > ]
```

### If you are in a hurry, use templates

When creating a cluster, you can reference a template. The cluster will then be configured in one second:

```
**[terminal]
**[prompt jumbo > ]**[command create mycluster --template small-full]
Creating mycluster...
Cluster "mycluster" created (domain name = "mycluster.local").
**[prompt jumbo (mycluster) > ]**[command listnodes]
+----------+--------------------+-------------+----------+------+
|   Name   |       Types        |      IP     | RAM (MB) | CPUs |
+----------+--------------------+-------------+----------+------+
|  edge01  |        edge        | 10.10.10.10 |   1024   |  1   |
| master01 | master, sidemaster | 10.10.10.11 |   3072   |  1   |
| worker01 |       worker       | 10.10.10.21 |   4096   |  2   |
+----------+--------------------+-------------+----------+------+
```

If this is your first time using Jumbo, we still recommend following this tutorial to learn everything you need to know!  
See the list of available templates on the Github repo ([jumbo/core/config/templates/docs](https://github.com/adaltas/jumbo/tree/master/jumbo/core/config/templates/docs))

## Virtual machine creation

Now that we have created our cluster, lets add 3 virtual machines to it:

> **danger**
> Adjust the RAM of VMs to your local machine!

```shell
**[terminal]
**[prompt jumbo (mycluster) > ]**[command addnode master --types master --ip 10.10.10.11 --ram 2048]
Machine `master` added to cluster `mycluster`. 
**[prompt jumbo (mycluster) > ]**[command addnode smaster -t sidemaster -t edge]
IP: 10.10.10.12
RAM (MB): 3072
Machine `smaster` added to cluster `mycluster`.
**[prompt jumbo (mycluster) > ]**[command addnode worker -t worker --cpus 2]
jumbo (mycluster) > IP: 10.10.10.13
RAM (MB): 3072
Machine `worker` added to cluster `mycluster`.
```

We now have all the nodes needed to deploy a functional Hadoop cluster. Use `listnodes` to see details about the nodes of the cluster:

```shell
**[terminal]
**[prompt jumbo (mycluster) > ]**[command  listnodes]
+---------+------------------+-------------+----------+------+
|   Name  |      Types       |      IP     | RAM (MB) | CPUs |
+---------+------------------+-------------+----------+------+
|  master |      master      | 10.10.10.11 |   2048   |  1   |
| smaster | sidemaster, edge | 10.10.10.12 |   3072   |  1   |
|  worker |      worker      | 10.10.10.13 |   3072   |  2   |
+---------+------------------+-------------+----------+------+
```

## Service installation

A service can have dependencies to other services. A dependency is satisfied if the required service is installed and if the minimum required number for each component is installed. If the requirements to install a service are not met, Jumbo will tell you what services or components you have to install:

```shell
**[terminal]
**[prompt jumbo (mycluster) > ]**[command addservice AMBARI]
The requirements to add the service "AMBARI" are not met!
These services are missing:
 - ANSIBLE,
 - POSTGRESQL
**[prompt jumbo (mycluster) > ]**[command addservice ANSIBLE]
Service "ANSIBLE" and related clients added to cluster "mycluster".
1 type of component auto-installed. Use "listcomponents -a" for details.
```

You can let Jumbo install all the dependencies with the tag `--recursive`:

```shell
**[terminal]
**[prompt jumbo (mycluster) > ]**[command addservice AMBARI --recursive]
The service AMBARI and its dependencies will be installed. Dependencies:
Services:
 - POSTGRESQL

Do you want to continue? [y/N]: y
Service "AMBARI" and related clients added to cluster "mycluster".
Auto-installed the dependencies:
Services:
 - POSTGRESQL
2 type of component auto-installed. Use "listcomponents -a" for details.
```

When installing a service, all its components are auto-installed on the best fitting hosts by default. You can avoid the auto-installation with the flag `--no-auto`.

Note that the service's clients will always be installed on all hosts (even with `--no-auto`) and on nodes created after the service installation. However you can use `rmcomponent` to delete them individually afterward.

A list of all the services supported by Jumbo is available [here](#supported-services-and-components).


> **info**
> **High Availability support**  
> Some services support High Availability ([list](../supported.md#services-supporting-high-availability)).  
> To install a service in HA, use the tag `--ha` with the command `addservice`.

#### Component installation

If you choose to not auto-install the components with the flag `--no-auto`, you have to manually add components with `addcomponent` on the machines of your choice. Use the command `checkservice` to see what components are missing for the service to be complete:

```shell
**[terminal]
**[prompt jumbo (mycluster) > ]**[command checkservice ANSIBLE]
The service "ANSIBLE" misses:
 - 1 ANSIBLE_CLIENT
**[prompt jumbo (mycluster) > ]**[command ANSIBLE_CLIENT -m smaster]
Component "ANSIBLE_CLIENT" added to machine "mycluster/smaster".
```


## Installation of all Hadoop services and components

We have to reproduce the same procedure of installation for the following services and components:

| Service    | Components          | Machine type |
| ---------- | ------------------- | ------------ |
| ANSIBLE    | ANSIBLE_CLIENT      | `sidemaster` |
| POSTGRESQL | PSQL_SERVER         | `sidemaster` |
| AMBARI     | AMBARI_SERVER       | `sidemaster` |
| HDFS       | NAMENODE            | `master`     |
|            | SECONDARY_NAMENODE  | `sidemaster` |
|            | DATANODE            | `worker`     |
| ZOOKEEPER  | ZOOKEEPER_SERVER    | `master`     |
| YARN       | RESOURCEMANAGER     | `master`     |
|            | APP_TIMELINE_SERVER | `edge`       |
|            | HISTORYSERVER       | `edge`       |
|            | NODEMANAGER         | `worker`     |
| HIVE       | HIVE_METASTORE      | `sidemaster` |
|            | HIVE_SERVER         | `edge`       |
| HBASE      | HBASE_MASTER        | `master`     |
|            | HBASE_REGIONSERVER  | `worker`     |

## Remove items

Use the commands `rmnode`, `rmservice`, or `rmcomponent` to remove items.

## See what have been installed

Jumbo has list commands to describe the cluster state:
- `listclusters` to list all the clusters and the services installed on each of them;
- `listnodes` to list the VMs and their configurations;
- `listservices` to list the status of each service installed on a cluster (complete or not);
- `listcomponents` to list the components installed on a machine.