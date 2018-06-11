# Cluster commands

## Create

**Command: `create [name]`**

Create a new empty cluster with a specified name. After the cluster creation, the context is automatically set to this cluster.

**Options**

- `--domain DOMAIN` or `-d DOMAIN` - Specify a domain name for the cluster. By default, it is generated as `<name>.local`. The domain name is used for nodes urls and for the Kerberos realm which is the domain in uppercase letters.
- `--ambari-repo REPO-URL` - Specify the url where the Ambari repository should be downloaded. By default, it is the official repository of Ambari 2.6.1.5 (http://public-repo-1.hortonworks.com/ambari/centos7/2.x/updates/2.6.1.5/ambari.repo).
- `--vdf VDF-URL` - Specify the url where the [VDF file](https://docs.hortonworks.com/HDPDocuments/Ambari-2.6.0.0/bk_ambari-release-notes/content/ambari_relnotes-2.6.0.0-behavioral-changes.html) for the HDP stack should be downloaded. By default, it is the official VDF file for HDP 2.6.4.0 (http://public-repo-1.hortonworks.com/HDP/centos7/2.x/updates/2.6.4.0/HDP-2.6.4.0-91.xml).

---
## Delete

**Command: `delete [name]`**

Delete a cluster previously created. On deletion, the Vagrant virtual machines of the cluster are also destroyed.

**Options**
- `--force` or `-f` - Avoid the confirmation message prompt.

---
## Exit

**Command: `exit`**

*Only usefull in the Jumbo shell.*

Clean the Jumbo shell context.

---
## List clusters

**Command: `listclusters`**

List all the clusters managed by Jumbo. The list contains details about the domain names, the numbers of VMs, the services installed and the repositories URLs.

---
## Provision

**Command: `provision`**

Start the virtual machines and force provisioning.

**Options**

- `--cluster` or `-c` - The cluster of the virtual machines.

---
## Repair

**Command: `repair [name]`**

Recreate a `jumbo_config` file for a cluster if it has been destroyed. If this is the case, Jumbo will let you know with an error message.

---
## Restart

**Command: `restart`**

Restart the virtual machines of a cluster.

**Options**

- `--cluster` or `-c` - The cluster of the virtual machines.

---
## Set repo

**Command: `setrepo [name]`**

Set an URL to use for repositories downloads. The repositories that can be set are `ambari_repo` and `vdf`. See the [Advanced usage](../advanced-usage.md) section for more details.

**Options**

- `--value` or `-v` - The actual url of the repository.
- `--cluster` or `-c` - The cluster on which the url should be set.

---
## Start

**Command: `start`**

Start the virtual machines of a cluster. Once started, starts the Hadoop services. **The first time**, it will start the virtual machines and install all components.

**Options**

- `--cluster` or `-c` - The cluster of the virtual machines.

---
## Status

**Command: `status`**

Give the status of the virtual machines of a cluster.

**Options**

- `--cluster` or `-c` - The cluster of the virtual machines.

---
## Stop 

**Command: `stop`**

Stop the virtual machines of a cluster.

**Options**

- `--cluster` or `-c` - The cluster of the virtual machines.

---
## Use

**Command: `use [name]`**

*Only usefull in the Jumbo shell.*

Set the context to a previously created cluster. The context allows to use Jumbo without specifying the cluster on every command. The current context is indicated next to `jumbo` in the shell:

```
**[terminal]
**[prompt jumbo > ]**[command use mycluster]
Loading mycluster...
Cluster "mycluster" loaded.
**[prompt jumbo (mycluster) > ]
```