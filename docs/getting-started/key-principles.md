# Key principles

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

A `node` can be assigned multiple types at creation time, except for the type `ldap` than needs to be alone.  
To deploy a functional Hadoop cluster, you will need at least:
- 1 `master`
- 1 `sidemaster`
- 1 `edge`
- 1 `worker`