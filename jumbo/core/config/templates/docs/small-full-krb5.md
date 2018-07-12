# small-full-krb5 template 

### Recommended config.

- RAM: more than 13.0 GB
- Disk: 80.0GB free space

### Usage
```
create mycluster --template small-full-krb5
```

### Services installed

ANSIBLE, POSTGRESQL, AMBARI, HDFS, YARN, HIVE, FREEIPA, KERBEROS

###  Nodes

| Name       | Types                | IP          | RAM  | CPUs |
|------------|----------------------|-------------|------|------|
| `ldap01`   | `ldap`               | 10.10.10.2  | 1024 | 1    |
| `edge01`   | `edge`               | 10.10.10.10 | 1024 | 1    |
| `master01` | `master, sidemaster` | 10.10.10.11 | 3072 | 1    |
| `worker01` | `worker`             | 10.10.10.21 | 4096 | 2    |

###  Components

| Node       | Component           | Service    |
|------------|---------------------|------------|
| `ldap01`   | IPA_SERVER          | FREEIPA    |
| `edge01`   | ANSIBLE_CLIENT      | ANSIBLE    |
|            | HDFS_CLIENT         | HDFS       |
|            | YARN_CLIENT         | YARN       |
|            | MAPREDUCE2_CLIENT   | YARN       |
|            | SLIDER              | YARN       |
|            | PIG                 | YARN       |
|            | TEZ_CLIENT          | YARN       |
|            | HISTORYSERVER       | YARN       |
|            | APP_TIMELINE_SERVER | YARN       |
|            | HCAT                | HIVE       |
|            | HIVE_CLIENT         | HIVE       |
|            | HIVE_SERVER         | HIVE       |
|            | WEBHCAT_SERVER      | HIVE       |
| `master01` | PSQL_SERVER         | POSTGRESQL |
|            | AMBARI_SERVER       | AMBARI     |
|            | HDFS_CLIENT         | HDFS       |
|            | NAMENODE            | HDFS       |
|            | SECONDARY_NAMENODE  | HDFS       |
|            | YARN_CLIENT         | YARN       |
|            | MAPREDUCE2_CLIENT   | YARN       |
|            | SLIDER              | YARN       |
|            | PIG                 | YARN       |
|            | TEZ_CLIENT          | YARN       |
|            | RESOURCEMANAGER     | YARN       |
|            | HCAT                | HIVE       |
|            | HIVE_CLIENT         | HIVE       |
|            | HIVE_METASTORE      | HIVE       |
| `worker01` | HDFS_CLIENT         | HDFS       |
|            | DATANODE            | HDFS       |
|            | YARN_CLIENT         | YARN       |
|            | MAPREDUCE2_CLIENT   | YARN       |
|            | SLIDER              | YARN       |
|            | PIG                 | YARN       |
|            | TEZ_CLIENT          | YARN       |
|            | NODEMANAGER         | YARN       |
|            | HCAT                | HIVE       |
|            | HIVE_CLIENT         | HIVE       |