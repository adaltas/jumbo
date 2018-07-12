# Versions

## Jumbo versions

- **v0.4.2** - 12/07/2018: **Templates for clusters**
    - New option for `create` command: `--template`
- **v0.4.1** - 05/06/2018: **Vagrant commands integration and `-r` tag for `addservice`**
    - New commands: `start`, `stop`, `restart`, `status` to interact with the cluster directly within Jumbo
    - New tag `--recursive` for `addservice` to add a service and all its dependencies
- **v0.4** - 17/05/2018: **Kerberos support and unit tests**
    - Unit tests for: code execution, generated files (Vagrantfile, playbooks)
    - Minor fixes
    - Support for new services: KERBEROS
    - v0.4.0.1: Change version tags (1.* -> 0.*)
- **v0.3** - 09/05/18: **Support for HDFS and YARN in HA and Free IPA support**
    - Support for new service: FREEIPA
    - High Availability support for: HDFS, YARN
    - v0.3.1: Hotfix FreeIPA install
- **v0.2** - 04/05/18: **Support for Spark2 and Zeppelin and minor improvements**
    - Support custom URLs for the Ambari repository and the VDF of HDP with command `seturl`
    - New list `listservices` with services states (complete or not)
    - Better looking lists
    - Standardized command names
    - Support for new services: SPARK2, ZEPPELIN
- **v0.1** - 27/04/18: **First stable release**

## Underlying tools versions

By default, Jumbo uses these versions for the tools that it coordinates.  
Some versions can be easily changed as detailed in the [Advanced usage](advanced-usage.md) section.

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
