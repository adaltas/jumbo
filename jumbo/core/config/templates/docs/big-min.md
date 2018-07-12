# big-min template 

### Recommended config.

- RAM: more than 19.0 GB
- Disk: 120.0GB free space

### Usage
```
create mycluster --template big-min
```

### Services installed

ANSIBLE, POSTGRESQL, AMBARI, ZOOKEEPER, HDFS, YARN

###  Nodes

| Name       | Types        | IP          | RAM  | CPUs |
|------------|--------------|-------------|------|------|
| `edge01`   | `edge`       | 10.10.10.10 | 1024 | 1    |
| `master01` | `master`     | 10.10.10.11 | 2048 | 1    |
| `master02` | `master`     | 10.10.10.12 | 2048 | 1    |
| `master03` | `sidemaster` | 10.10.10.13 | 2048 | 1    |
| `worker01` | `worker`     | 10.10.10.21 | 4096 | 2    |
| `worker02` | `worker`     | 10.10.10.22 | 4096 | 2    |

###  Components

| Node       | Component         | Service    |
|------------|-------------------|------------|
| `edge01`   | ANSIBLE_CLIENT    | ANSIBLE    |
|            | ZOOKEEPER_CLIENT  | ZOOKEEPER  |
|            | HDFS_CLIENT       | HDFS       |
|            | YARN_CLIENT       | YARN       |
|            | MAPREDUCE2_CLIENT | YARN       |
|            | SLIDER            | YARN       |
|            | PIG               | YARN       |
| `master01` | ZOOKEEPER_CLIENT  | ZOOKEEPER  |
|            | ZOOKEEPER_SERVER  | ZOOKEEPER  |
|            | HDFS_CLIENT       | HDFS       |
|            | NAMENODE          | HDFS       |
|            | JOURNALNODE       | HDFS       |
|            | ZKFC              | HDFS       |
|            | YARN_CLIENT       | YARN       |
|            | MAPREDUCE2_CLIENT | YARN       |
|            | SLIDER            | YARN       |
|            | PIG               | YARN       |
| `master02` | ZOOKEEPER_CLIENT  | ZOOKEEPER  |
|            | ZOOKEEPER_SERVER  | ZOOKEEPER  |
|            | HDFS_CLIENT       | HDFS       |
|            | NAMENODE          | HDFS       |
|            | JOURNALNODE       | HDFS       |
|            | ZKFC              | HDFS       |
|            | YARN_CLIENT       | YARN       |
|            | MAPREDUCE2_CLIENT | YARN       |
|            | SLIDER            | YARN       |
|            | PIG               | YARN       |
| `master03` | PSQL_SERVER       | POSTGRESQL |
|            | AMBARI_SERVER     | AMBARI     |
|            | ZOOKEEPER_CLIENT  | ZOOKEEPER  |
|            | ZOOKEEPER_SERVER  | ZOOKEEPER  |
|            | HDFS_CLIENT       | HDFS       |
|            | JOURNALNODE       | HDFS       |
|            | YARN_CLIENT       | YARN       |
|            | MAPREDUCE2_CLIENT | YARN       |
|            | SLIDER            | YARN       |
|            | PIG               | YARN       |
| `worker01` | ZOOKEEPER_CLIENT  | ZOOKEEPER  |
|            | HDFS_CLIENT       | HDFS       |
|            | DATANODE          | HDFS       |
|            | YARN_CLIENT       | YARN       |
|            | MAPREDUCE2_CLIENT | YARN       |
|            | SLIDER            | YARN       |
|            | PIG               | YARN       |
|            | TEZ_CLIENT        | YARN       |
|            | NODEMANAGER       | YARN       |
| `worker02` | ZOOKEEPER_CLIENT  | ZOOKEEPER  |
|            | HDFS_CLIENT       | HDFS       |
|            | DATANODE          | HDFS       |
|            | YARN_CLIENT       | YARN       |
|            | MAPREDUCE2_CLIENT | YARN       |
|            | SLIDER            | YARN       |
|            | PIG               | YARN       |
|            | TEZ_CLIENT        | YARN       |
|            | NODEMANAGER       | YARN       |