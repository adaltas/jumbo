# Cluster provisioning

Each cluster created with Jumbo has a dedicated folder in `~/.jumbo/`. Jumbo generates all the configuration files needed in this folder (Vagrantfile, Ansible playbooks). You just have to start the provisioning of the cluster and watch the magic in action. Once you are ready, simply use the `start` command. The first time you start your cluster, it will launch the installation of all the services. 

You will see a thread of operations ran by Ansible. At the end of the thread, Jumbo gives you a link to the Ambari WebUI where you can follow the Hadoop cluster installation progress:

```shell
**[terminal]
TASK [postblueprint : Waiting for HDP install] *********************************
ok: [smaster] => {
    "msg": [
        "Installation of cluster 'myclusterlocalcluster' in progress.", 
        "Ambari WebUI: http://10.10.10.12:8080", 
        "Username: 'admin', Password: 'admin'"
    ]
}
```

> **info**
> **What to do in case of failure during provision?** This can happen for random reasons (like a very slow internet connexion hitting timeouts, etc...), you should just try to provision the cluster again by using the `provision` command.

At this state you can already connect as root to any host of the cluster via ssh (be sure to have a set of key in your .ssh folder, your public key will automatically be added to the `authorized_keys` of the nodes):

```shell
**[terminal]
ssh root@10.10.10.11
```

> **danger**
> **Before starting working on the cluster, be sure that it is entirely configured as you want!** (If you modify the cluster configuration with Jumbo after provisioning, you will have to `vagrant destroy -f` and `vagrant up` again in your project folder in `/~.jumbo/CLUSTER_NAME/` to apply changes)  

The state of the machines can be controlled with the following commands:
- `start` to boot machines (equivalent to `vagrant up` in your project folder)
- `stop` to halt machines (equivalent to `vagrant halt`)
- `restart` to reload machines (equivalent to `vagrant reload`)
- `status` to view machines status (equivalent to `vagrant status`)
