# Supported services and components

All the client components (tagged in the table) are always auto-installed on all hosts on service installation but can be uninstalled manually.  
A component can only be installed on a limited number of node's types (see table). The types order has an importance because a component will be installed first on the node of the first type on auto-installation.

| Version | Service             | Components              | Types                  | Client |
| ------- | ------------------- | ----------------------- | ---------------------- | ------ |
| 0.1     | ANSIBLE             | ANSIBLE_CLIENT          | `edge`                 |        |
|         | POSTGRESQL          | PSQL_SERVER             | `sidemaster`           |        |
|         | AMBARI              | AMBARI_SERVER           | `sidemaster`           |        |
|         | HDFS                | NAMENODE                | `master`               |        |
|         |                     | SECONDARY_NAMENODE      | `sidemaster`           |        |
|         |                     | DATANODE                | `worker`               |        |
|         |                     | JOURNALNODE             | `master`, `sidemaster` |        |
|         |                     | HDFS_CLIENT             | all but `ldap`         | Yes    |
|         |                     | ZFC                     | `master`               |        |
|         | YARN (+ MAPREDUCE2) | RESOURCEMANAGER         | `master`               |        |
|         |                     | NODEMANAGER             | `worker`               |        |
|         |                     | HISTORYSERVER           | `edge`                 |        |
|         |                     | APP_TIMELINE_SERVER     | `edge`                 |        |
|         |                     | YARN_CLIENT             | all but `ldap`         | Yes    |
|         |                     | MAPREDUCE2_CLIENT       | all but `ldap`         | Yes    |
|         |                     | SLIDER                  | all but `ldap`         | Yes    |
|         |                     | TEZ_CLIENT              | all but `ldap`         | Yes    |
|         |                     | PIG                     | all but `ldap`         | Yes    |
|         | ZOOKEEPER           | ZOOKEEPER_SERVER        | `master`, `sidemaster` |        |
|         |                     | ZOOKEEPER_CLIENT        | all but `ldap`         | Yes    |
|         | HIVE                | HIVE_METASTORE          | `sidemaster`, `master` |        |
|         |                     | HIVE_SERVER             | `edge`, `sidemaster`   |        |
|         |                     | WEBHCAT_SERVER          | `edge`                 |        |
|         |                     | HCAT                    | all but `ldap`         | Yes    |
|         |                     | HIVE_CLIENT             | all but `ldap`         | Yes    |
|         | HBASE               | HBASE_MASTER            | `master`               |        |
|         |                     | HBASE_REGIONSERVER      | `worker`               |        |
|         |                     | HBASE_CLIENT            | all but `ldap`         | Yes    |
| 0.2     | SPARK2              | SPARK2_JOBHISTORYSERVER | `edge`                 |        |
|         |                     | SPARK2_CLIENT           | all but `ldap`         | Yes    |
|         | ZEPPELIN            | ZEPPELIN_MASTER         | `edge`                 |        |
| 0.3     | FREEIPA             | IPA_SERVER              | `ldap`                 |        |
| 0.4     | KERBEROS            | -                       |                        |        |

You can add other HDP services through the Ambari WebUI after the cluster provisioning.  
Of course, all services supported in one version are supported in all the next ones. 

## Services supporting High Availability

The following services can be installed in HA mode with Jumbo:
- HDFS
- YARN
- ZOOKEEPER

If you want to switch another service in HA, you can use the Ambari WebUI.