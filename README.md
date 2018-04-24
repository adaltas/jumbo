# Jumbo - A local Hadoop cluster bootstrapper

Jumbo is a tool that allows you to deploy a virtualized Hadoop cluster on a local machine in minutes. This tool is especially targeted to developers with a limited knowledge of Hadoop to help them bootstrap a development environment without struggling with machines and services configurations.

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

## Installation

**Requirement:** Vagrant has to be installed on your local machine.

```shell
git clone jumbo jumbo_dir
cd jumbo_dir
pip install .
```

## Quick Start Guide

### Configure your cluster

### Launch the installation

Each cluster created with Jumbo has a dedicated folder in `~/.jumbo/`. Jumbo generates all the configuration files needed in this folder. You just have to start the Vagrant provisioning of the cluster and watch the magic in action:
```
cd ~/.jumbo/mycluster
vagrant up
```


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




## TO DO

- [ ] Secure the cluster with Kerberos;
- [ ] Add more supported services;
- [ ] Publish a wiki;
- [ ] Complete the user assistance;
