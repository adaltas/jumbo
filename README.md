# Jumbo - A local Hadoop cluster bootstrapper

Jumbo is a tool that allows you to deploy a **virtualized Hadoop cluster** on a local machine in minutes. This tool is especially targeted to developers with a limited knowledge of Hadoop to help them **quickly bootstrap development environments** without struggling with machines and services configurations.

![Jumbo shell](https://i.imgur.com/4wKtZUf.png)

Jumbo is written in Python and relies on other tools that it coordinates:
- [Vagrant](https://github.com/hashicorp/vagrant), to manage the virtual machines;
- [Ansible](https://github.com/ansible/ansible), to configure the cluster;
- [Apache Ambari](https://ambari.apache.org/), to provision and manage the Hadoop cluster.

The distribution used for the Hadoop cluster is [Hortonworks Data Platform](https://hortonworks.com/products/data-platforms/hdp/).

## Key principles

Jumbo manages the following types of items:
- `cluster`: a VM cluster and the mapping of the components installed;
- `vm`: a virtual machine managed by Vagrant. A `vm` belongs to a `cluster`;
- `service`: a service available for install (e.g. 'POSTGRESQL', 'HDFS'). A `service` is installed at `cluster` level;
- `component`: a component available for install (e.g. 'PSQL_SERVER', 'DATANODE'). A `component` is installed on a `vm` and belongs to a `service`.

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

A `vm` must have at least one of the following types:
- `master`: hosts master components like the NameNode of HDFS;
- `smaster`: hosts key components of services without slaves like the HiveMetastore of Hive;
- `worker`: hosts slave components like the DataNode of HDFS;
- `edge`: hosts components exposing APIs like the HiveServer2 of Hive;
- `ldap`: hosts security components like the IPA-server of FreeIPA.

A `vm` can be assigned multiple types at creation time. To deploy a functional Hadoop cluster, you will need at least:
- 1 `master`
- 1 `smaster`
- 1 `edge`
- 1 `worker`

## Installation

**Requirement:** Vagrant has to be installed on your local machine.

```shell
git clone jumbo jumbo_dir
cd jumbo_dir
pip install .
```

## Quick Start Guide

You can find all the available commands with the command `help` and more details about a specific command with `help command`.

### Configure your cluster

In this tutorial we will build a tiny **3 nodes cluster** with basic Hadoop services installed.

#### Cluster creation and Jumbo context

First, lets enter the Jumbo shell and create our cluster:

```
[user@computer:Dir]$ jumbo
Jumbo v0.1
jumbo > create mycluster
Creating mycluster...
Cluster `mycluster` created (domain name = "mycluster.local").
jumbo (mycluster) >
```

After creating a cluster, the *Jumbo context* is set to this cluster. You can see the name of the cluster loaded (`jumbo (mycluster) >`). Use `exit` to reset the context, and then `manage` to set to context to an existing cluster:

```shell
jumbo (mycluster) > exit
jumbo > manage anothercluster
Loading test...
Cluster `anothercluster` loaded.
jumbo (anothercluster) > 
```

#### Virtual machine creation

Now that we have created our cluster, lets add 3 virtual machines to it:

*Adjust the RAM of VMs to your local machine*

```shell
jumbo (mycluster) > addvm master --types master --ip 10.10.10.11 --ram 2000 --disk 10000
Machine `master` added to cluster `mycluster`.
jumbo (mycluster) > addvm smaster -t sidemaster -t edge
IP: 10.10.10.12
RAM (MB): 3000
Disk (MB): 10000
Machine `smaster` added to cluster `mycluster`.
jumbo (mycluster) > addvm worker -t worker --cpus 2
IP: 10.10.10.13
RAM (MB): 3000
Disk (MB): 10000
Machine `worker` added to cluster `mycluster`.
```

We now have all the machines needed to deploy a functional Hadoop cluster. Use `listvm` to see details about the machines of the cluster:

```shell
jumbo (mycluster) > listvm
+---------+------------------+-------------+----------+-----------+------+
|   Name  |      Types       |      IP     | RAM (MB) | Disk (MB) | CPUs |
+---------+------------------+-------------+----------+-----------+------+
|  master |      master      | 10.10.10.11 |   2000   |   10000   |  1   |
| smaster | sidemaster, edge | 10.10.10.12 |   3000   |   10000   |  1   |
|  worker |      worker      | 10.10.10.13 |   3000   |   10000   |  2   |
+---------+------------------+-------------+----------+-----------+------+
```

#### Service installation

Before installing a component, you need to install the service to which the component belongs. A service can have dependencies to other services. A service dependency is satisfied if the service is installed and if the minimum required number of each component is installed. If the requirements to install a service are not met, Jumbo will tell you what services or components you have to install:

```shell
jumbo (mycluster) > addservice AMBARI
The requirements to add the service `AMBARI` are not met!
These services are missing:
 - ANSIBLE,
 - POSTGRESQL
jumbo (mycluster) > addservice ANSIBLE
Service `ANSIBLE` and related clients added to cluster `mycluster`.
```

#### Component installation

After installing the service AMBARI, we can install the component ANSIBLE_CLIENT on the host that will be responsible of running the Ansible playbooks (we advise to install it on the cluster `sidemaster`).

```shell
jumbo (mycluster) > addcomp ANSIBLE_CLIENT -m smaster
Component `ANSIBLE_CLIENT` added to machine `mycluster/smaster`
```

#### Installation of all Hadoop services and components

We have to reproduce the same procedure of installation for the following services and components (respect this order for services):

| Service    | Components          | Machine type |
| ---------- | ------------------- | ------------ |
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

When installing some services, you will notice that some components are installed automatically (they are needed to access the service from any machine). When you add a new vm to a cluster with services installed, the clients of each service are automatically installed on the vm.

#### Launch the cluster deployment

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
        "Installation of cluster `test2localcluster` in progress.", 
        "Ambari WebUI: http://10.10.10.12:8080", 
        "User: 'admin', Password: 'admin'"
    ]
}
```

#### Remove items

Use the commands `rmvm`, `rmservice`, or `rmcomp` to remove items.


## Supported services and components

| Service            | Components          |
| ------------------ | ------------------- |
| ANSIBLE            | ANSIBLE_CLIENT      |
| POSTGRESQL         | PSQL_SERVER         |
| AMBARI             | AMBARI_SERVER       |
| HDFS               | NAMENODE            |
|                    | SECONDARY_NAMENODE  |
|                    | DATANODE            |
|                    | JOURNALNODE         |
|                    | HDFS_CLIENT         |
| YARN (+MAPREDUCE2) | RESOURCEMANAGER     |
|                    | NODEMANAGER         |
|                    | HISTORYSERVER       |
|                    | APP_TIMELINE_SERVER |
|                    | YARN_CLIENT         |
|                    | MAPREDUCE2_CLIENT   |
|                    | SLIDER              |
| ZOOKEEPER          | ZOOKEEPER_SERVER    |
|                    | ZOOKEEPER_CLIENT    |
|                    | ZKFC                |
| HIVE               | HIVE_METASTORE      |
|                    | HIVE_SERVER         |
|                    | WEBHCAT_SERVER      |
|                    | HCAT                |
|                    | HIVE_CLIENT         |




## TO DO

- [ ] Add more supported services;
- [ ] Add support for HA clusters;
- [ ] Secure the cluster with Kerberos;
- [ ] Publish a wiki;
- [ ] Complete the user assistance;
