# Cluster level commands

## Create

**Command:** `create [name]`

This commands creates a new empty cluster with a specified name.

### Options

- `--domain DOMAIN` or `-d DOMAIN` - Specify a domain name for the cluster. By default, it is generated as `<name>.local`. The domain name is used for nodes urls and for the Kerberos realm which is the domain in uppercase letters.
- `--ambari-repo REPO-URL` - Specify the url where the Ambari repository should be downloaded. By default, it is the official repository of Ambari 2.6.1.5 (http://public-repo-1.hortonworks.com/ambari/centos7/2.x/updates/2.6.1.5/ambari.repo).
- `--vdf VDF-URL` - Specify the url where the [VDF file](https://docs.hortonworks.com/HDPDocuments/Ambari-2.6.0.0/bk_ambari-release-notes/content/ambari_relnotes-2.6.0.0-behavioral-changes.html) for the HDP stack should be downloaded. By default, it is the official VDF file for HDP 2.6.4.0 (http://public-repo-1.hortonworks.com/HDP/centos7/2.x/updates/2.6.4.0/HDP-2.6.4.0-91.xml).