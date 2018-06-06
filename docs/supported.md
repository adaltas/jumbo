# Supported services and components

All services supported in one version are supported in all the next ones. 

All the client components (tagged below) are always auto-installed on all hosts on service installation but can be uninstalled manually.

| Version | Service             | Components              | Client |
| ------- | ------------------- | ----------------------- | ------ |
| 0.1     | ANSIBLE             | ANSIBLE_CLIENT          |        |
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
| 0.2     | SPARK2              | SPARK2_JOBHISTORYSERVER |        |
|         |                     | SPARK2_CLIENT           | Yes    |
|         | ZEPPELIN            | ZEPPELIN_MASTER         |        |
| 0.3     | FREEIPA             | IPA_SERVER              |        |
| 0.4     | KERBEROS            | -                       |        |

You can add other HDP services through the Ambari WebUI after the cluster deployment.

## Services supporting High Availability

The following services can be installed in HA mode with Jumbo:
- HDFS
- YARN
- ZOOKEEPER

If you want to switch another service in HA, you can use the Ambari WebUI.