# Jumbo - A local Hadoop cluster bootstrapper

Jumbo is a tool that allows you to deploy a **virtualized Hadoop cluster** on a local machine in minutes. This tool is especially targeted to developers with a limited knowledge of Hadoop to help them **quickly bootstrap development environments** without struggling with machines and services configurations.

![Jumbo shell](https://i.imgur.com/BybZhBL.png)

Jumbo is written in Python and relies on other tools that it coordinates:
- [Vagrant](https://github.com/hashicorp/vagrant), to manage the virtual machines;
- [Ansible](https://github.com/ansible/ansible), to configure the cluster;
- [Apache Ambari](https://ambari.apache.org/), to provision and manage the Hadoop cluster.

The distribution used for the Hadoop cluster is [Hortonworks Data Platform](https://hortonworks.com/products/data-platforms/hdp/).

Check all the underlying tools versions used [here](#underlying-tools-versions).

## Key principles

Jumbo manages the following types of items:
- `cluster`: a cluster of VMs;
- `node`: a virtual machine managed by Vagrant. A `node` belongs to a `cluster`;
- `service`: a service available for install (e.g. 'POSTGRESQL', 'HDFS'). A `service` is installed at `cluster` level;
- `component`: a component available for install (e.g. 'PSQL_SERVER', 'DATANODE'). A `component` is installed on a `node` and belongs to a `service`.

```
├── mycluster
│   ├── machines
│   │   ├── master01
│   │   │   ├── component1
│   │   │   └── component2
│   │   └── worker01
│   │       └── component2
│   └── services
|       ├── service1
|       └── service2
└── anothercluster
```

A `node` must have at least one of the following types:
- `master`: hosts master components like the NameNode of HDFS;
- `sidemaster`: hosts key components of services without slaves like the Ambari server or the HiveMetastore of Hive;
- `worker`: hosts slave components like the DataNode of HDFS;
- `edge`: hosts components exposing APIs like the HiveServer2 of Hive;
- `ldap`: hosts security components like the IPA-server of FreeIPA.

A `node` can be assigned multiple types at creation time. To deploy a functional Hadoop cluster, you will need at least:
- 1 `master`
- 1 `sidemaster`
- 1 `edge`
- 1 `worker`

## Installation

**Requirements:**
- Vagrant has to be installed on your local machine.
- You need a valid SSH public key in `~/.ssh/id_rsa.pub` to provision the clusters.

```shell
git clone jumbo jumbo_dir
cd jumbo_dir
pip install .
```

## Quick Start Guide

You can find all the available commands with the command `help` and more details about a specific command with `help command`.

### Configure your cluster

In this tutorial we will see the main Jumbo commands available through the configuration of a tiny **3 nodes cluster** with basic Hadoop services installed.

#### Cluster creation and Jumbo context

First, lets enter the Jumbo shell and create our cluster:

```
[user@computer:Dir]$ jumbo
Jumbo v1.0
jumbo > create mycluster
Creating mycluster...
Cluster "mycluster" created (domain name = "mycluster.local").
jumbo (mycluster) >
```

After creating a cluster, the *Jumbo context* is set to this cluster. You can see the name of the cluster loaded (`jumbo (mycluster) >`). Use `exit` to reset the context, and then `use` to set the context to an existing cluster:

```shell
jumbo (mycluster) > exit
jumbo > use anothercluster
Loading anothercluster...
Cluster "anothercluster" loaded.
jumbo (anothercluster) > 
```

#### Virtual machine creation

Now that we have created our cluster, lets add 3 virtual machines to it:

*Adjust the RAM of VMs to your local machine!*

```shell
jumbo (mycluster) > addnode master --types master --ip 10.10.10.11 --ram 2048
Machine `master` added to cluster `mycluster`.
jumbo (mycluster) > addnode smaster -t sidemaster -t edge
IP: 10.10.10.12
RAM (MB): 3072
Machine `smaster` added to cluster `mycluster`.
jumbo (mycluster) > addnode worker -t worker --cpus 2
IP: 10.10.10.13
RAM (MB): 3072
Machine `worker` added to cluster `mycluster`.
```

We now have all the machines needed to deploy a functional Hadoop cluster. Use `listnodes` to see details about the machines of the cluster:

```shell
jumbo (mycluster) > listnodes
+---------+------------------+-------------+----------+------+
|   Name  |      Types       |      IP     | RAM (MB) | CPUs |
+---------+------------------+-------------+----------+------+
|  master |      master      | 10.10.10.11 |   2048   |  1   |
| smaster | sidemaster, edge | 10.10.10.12 |   3072   |  1   |
|  worker |      worker      | 10.10.10.13 |   3072   |  2   |
+---------+------------------+-------------+----------+------+
```

#### Service installation

A service can have dependencies to other services. A service dependency is satisfied if the service is installed and if the minimum required number of each component is installed. If the requirements to install a service are not met, Jumbo will tell you what services or components you have to install:

```shell
jumbo (mycluster) > addservice AMBARI
The requirements to add the service "AMBARI" are not met!
These services are missing:
 - ANSIBLE,
 - POSTGRESQL
jumbo (mycluster) > addservice ANSIBLE
Service "ANSIBLE" and related clients added to cluster "mycluster".
1 type of component auto-installed. Use "listcomponents -a" for details.
```

When installing a service, all its components are auto-installed on the best fitting hosts by default. You can avoid the auto-installation with the flag `--no-auto`. Note that the service's clients clients will always be installed on all hosts.

When you add a new node to a cluster with services already installed, the clients of each service are automatically installed on the node.

A list of all the services supported by Jumbo is available [here](#supported-services-and-components).

##### High Availability support

[Some services](#services-supporting-high-availability) support High Availability. To install a service in HA, use the tag `--ha` with the command `addservice`.

#### Component installation

If you choose to not auto-install the components with the flag `--no-auto`, you have to manually add components with `addcomponent` on the machines of your choice. Use the command `checkservice` to see what components are missing for the service to be complete:

```shell
jumbo (mycluster) > checkservice ANSIBLE
The service "ANSIBLE" misses:
 - 1 ANSIBLE_CLIENT
jumbo (mycluster) > addcomp ANSIBLE_CLIENT -m smaster
Component "ANSIBLE_CLIENT" added to machine "mycluster/smaster".
```


#### Installation of all Hadoop services and components

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

#### Remove items

Use the commands `rmnode`, `rmservice`, or `rmcomponent` to remove items.

#### See what have been installed

Jumbo has list commands to describe the cluster state:
- `listclusters` to list all the clusters and the services installed on each of them;
- `listnodes` to list the VMs and their configurations;
- `listservices` to list the status of each service installed on a cluster (complete or not);
- `listcomponents` to list the components installed on a machine.

### Launch the cluster deployment

Each cluster created with Jumbo has a dedicated folder in `~/.jumbo/`. Jumbo generates all the configuration files needed in this folder. You just have to start the Vagrant provisioning of the cluster and watch the magic in action:

```
cd ~/.jumbo/mycluster
vagrant up
```

You will see a thread of operations ran by Ansible. At the end of the thread, Jumbo gives you a link to the Ambari WebUI where you can follow the Hadoop cluster installation progress:

```shell
TASK [postblueprint : Waiting for HDP install] *********************************
ok: [smaster] => {
    "msg": [
        "Installation of cluster 'myclusterlocalcluster' in progress.", 
        "Ambari WebUI: http://10.10.10.12:8080", 
        "Username: 'admin', Password: 'admin'"
    ]
}
```

At this state you can already connect as root to any host of the cluster via ssh:

```shell
ssh root@10.10.10.11
```

**Before starting working on the cluster, be sure that it is entirely configured as you want!** (If you modify the cluster configuration with Jumbo after deployment, you will have to `vagrant destroy -f` and `vagrant up` again to apply changes)

## Supported services and components

All services supported in one version are supported in all the next ones. 

All the client components (tagged below) are always auto-installed on all hosts on service installation but can be uninstalled manually.

| Version | Service             | Components              | Client |
| ------- | ------------------- | ----------------------- | ------ |
| 1.0     | ANSIBLE             | ANSIBLE_CLIENT          |        |
|         | POSTGRESQL          | PSQL_SERVER             |        |
|         | AMBARI              | AMBARI_SERVER           |        |
|         | HDFS                | NAMENODE                |        |
|         |                     | SECONDARY_NAMENODE      |        |
|         |                     | DATANODE                |        |
|         |                     | JOURNALNODE             |        |
|         |                     | HDFS_CLIENT             | Yes    |
|         | YARN (+ MAPREDUCE2) | RESOURCEMANAGER         |        |
|         |                     | NODEMANAGER             |        |
|         |                     | HISTORYSERVER           |        |
|         |                     | APP_TIMELINE_SERVER     |        |
|         |                     | YARN_CLIENT             | Yes    |
|         |                     | MAPREDUCE2_CLIENT       | Yes    |
|         |                     | SLIDER                  | Yes    |
|         |                     | TEZ_CLIENT              | Yes    |
|         |                     | PIG                     | Yes    |
|         | ZOOKEEPER           | ZOOKEEPER_SERVER        |        |
|         |                     | ZOOKEEPER_CLIENT        | Yes    |
|         |                     | ZKFC                    |        |
|         | HIVE                | HIVE_METASTORE          |        |
|         |                     | HIVE_SERVER             |        |
|         |                     | WEBHCAT_SERVER          |        |
|         |                     | HCAT                    | Yes    |
|         |                     | HIVE_CLIENT             | Yes    |
|         | HBASE               | HBASE_MASTER            |        |
|         |                     | HBASE_REGIONSERVER      |        |
|         |                     | HBASE_CLIENT            | Yes    |
| 1.1     | SPARK2              | SPARK2_JOBHISTORYSERVER |        |
|         |                     | SPARK2_CLIENT           | Yes    |
|         | ZEPPELIN            | ZEPPELIN_MASTER         |        |
| 1.2     | FREEIPA             | IPA_SERVER              |        |

You can add other HDP services through the Ambari WebUI after the cluster deployment.

### Services supporting High Availability

The following services can be installed in HA mode with Jumbo:
- HDFS
- YARN

If you want to switch another service in HA, you can use the Ambari WebUI.

## Underlying tools versions

### Vagrant

Vagrant box: [`centos/7`](https://app.vagrantup.com/centos/boxes/7) (32 GB of disk per VM)

Vagrant providers available:
- libvirt (default)
- VirtualBox (if libvirt not available)

### Ansible

The latest stable release of Ansible is auto-provisioned by Vagrant on `vagrant up`.

### PostgreSQL

The latest stable release of PostgreSQL is installed with yum via Ansible.

### Ambari and HDP

Postgre JDBC Driver:
- Version: 42.2.1
- JAR: https://jdbc.postgresql.org/download/postgresql-42.2.1.jar

Ambari:
- Version: 2.6.1.5
- Repository: http://public-repo-1.hortonworks.com/ambari/centos7/2.x/updates/2.6.1.5/ambari.repo

HDP:
- Version: 2.6.4.0
- VDF file: http://public-repo-1.hortonworks.com/HDP/centos7/2.x/updates/2.6.4.0/HDP-2.6.4.0-91.xml


## Jumbo versions

- **1.0** - 27/04/18: **First stable release**
- **1.1** - 04/05/18: **Support for Spark2 and Zeppelin and minor improvements**
    - Support custom URLs for the Ambari repository and the VDF of HDP with command `seturl`;
    - New list `listservices` with services states (complete or not);
    - Better looking lists;
    - Standardized command names;
    - Support for new services: SPARK2, ZEPPELIN
- **1.2** - 09/05/18: **Support for HDFS and YARN in HA and Free IPA support**
    - Support for new service: FREEIPA
    - High Availability support for: HDFS, YARN
- **1.3** - 15/05/2018: **Unit tests**
    - Unit tests for: code execution, generated files (Vagrantfile, playbooks)
    - Minor fixes

## TO DO

- [ ] Add support for all Ambari services;
- [x] Add support for HA clusters;
- [ ] Add Kerberos support;
- [ ] Publish a wiki;
- [x] Complete the user assistance process;
- [ ] Group commands
- [ ] Proxifier vagrant start, halt, status, reload, destroy (via delete)
- [ ] Commandes générales (info, version, services disponibles, ...)
- [ ] addservice recursif sur les dépendances obligatoires
- [ ] Généraliser la HA
- [ ] Smart topology based on available ressources
- [ ] Website
- [ ] Partage (github, artcile)
