# Bundles

This section is aimed at people wanting to customize Jumbo by adding new services. It defines what the bundles are, and how to create one. Commands associated with bundles are described in the commands section of the documentation.

Jumbo comes with a set of services (Ambari, HDP services...) and a set of node types (master, sidemaster, worker, edge and ldap). Those are contained in a bundle called `jumbo-services`, installed in `~/.jumbo/bundles/jumbo-services`. This bundle is active by default for any new cluster. New bundles can be created in order to add custom services managed by Jumbo.

## Overview

```
.
└── jumbo-services
    ├── playbooks
    └── services
```

A bundle contains a set of playbooks in the `playbooks` folder, and a set of service definitions (JSON files) in the `services` folder.

## Playbooks

The entry point of a bundle is the `deploy.yml` playbook. It is the master playbook that should include all other playbooks.

Here is a simplified `jumbo-services/playbooks/` only containing PostgreSQL and Ambari:
```python
.
├── pgsql-server.yml
├── ambari.yml
├── deploy.yml  # master playbook
└── roles
    ├── ambariagents
    ├── ambaricommon
    ├── ambariserver
    └── postgres
```
If your cluster has multiple active bundles, each `deploy.yml` master playbook will be called consecutively when using the command `provision` or `start`. It  respects the order you defined in your cluster active bundles. For example, if you wish to have a bundle `foo` called first, you would add it using the command `addbundle foo --position first` (cf. bundles commands).


## Services

The services of a bundle are defined in the `services/*.json` files. These files are merged, so you can decide wether you want to split them or not. In the `jumbo-services` bundle, we have defined one service per JSON file. 

Eg. `postgresql.json`
```python
{
  "available_node_types": [],      # Additionnal node types      
  "services": [
    {
      "name": "POSTGRESQL",        # Service name
      "components": [              # List of components of the service
        {
          "name": "PSQL_SERVER",   # Component name
          "abbr": "PSQL_S",        # Component abbreviation
          "node_types": [          
            [                      # Node types on which the component
              "sidemaster"         # can be installed.
            ]
          ],
          "ansible_groups": [      # Ansible groups that should be given
            "pgsqlserver"          # to the matching nodes
          ],
          "number": {              # Number of nodes on which the component
            "default": 1,          # will be installed.
            "ha": 1                # Number of nodes for high-availibility
          }
        }
      ],
      "ansible_vars": {            # Variables that should be accessible
        "POSTGRESQL": {}           # by the Ansible playbooks. Those are
      },                           # written in `inventory/group_vars/all`
      "requirements": {
        "services": {              # Service dependencies. (eg. "AMBARI" 
          "default": [],           # would be a dependency of HDFS service)
          "ha": []                 # Dependencies for high-availability
        }
      },
      "auto_install": []           # (deprecated) Clients that will always be
                                   # installed
    }
  ]
}
```

## Create a bundle: step-by-step example

We want Java to be installed on all Ambari hosts, which correspond in the `jumbo-services` bundle to all hosts that are not of the type `ldap`. We are going to create a simple bundle, let's call it `prep-jumbo`, that we will execute before the `jumbo-services` one. It will be a preparation phase whose role is to install Java on the non-ldap machines, and set the Ansible variable `JAVA_HOME`. This optionnal variable is used in the `jumbo-services` bundle to tell ambari-setup that Java is already installed, like this (simplified):
```yml
- name: Ambari setup
  command: ambari-server setup \
    {{ '--java-home ' ~ JAVA_HOME if JAVA_HOME is defined else '' }} \
    -s
```

Once our bundle is done, we just need to do:
```sh
jumbo (mycluster) > addbundle prep-jumbo --position first
jumbo (mycluster) > addservice JAVA
```

Let's get started !

### Playbooks

This will be our overall bundle architecture:
```python
.
├── playbooks
│   ├── deploy.yml             # Master playbook
│   ├── java.yml               # Playbook to import install-java role
│   └── roles                  
│       └── install-java
│           └── tasks
│               └── main.yml    # Role to install Java 
└── services
    └── java.json               # Java service definition
```
We could make something simpler, but this is a standard architecture that would scale correctly with many services. The role is pretty straightforward:  
```yml
# playbooks/roles/install-java/tasks/main.yml
---
- name: Download open jdk 1.8
  yum:
    name: java-1.8.0-openjdk
    state: latest
```

We associate it to the hosts belonging to the `java` Ansible group:  
```yml
# playbooks/java.yml
---
- hosts: java
  become: true
  roles:
    - install-java
```

And finally we define our master playbook:  
```yml
# playbooks/deploy.yml
---
- import_playbook: java.yml
```


### Service definition

Now we need to tell Jumbo how to construct the inventory to use these playbooks. We want a `JAVA_OPENJDK_1_8_0` component to be installed on all non-ldap machines, so we need to put all non-ldap machines in the `java` Ansible group. Finally we have to export the `JAVA_HOME` variable. The JSON is pretty self-explanatory:

`services/java.json`
```python
{
  "available_node_types": [],
  "services": [
    {
      "name": "JAVA",
      "components": [
        {
          "name": "JAVA_OPENJDK_1_8_0",
          "abbr": "OPENJDK",
          "node_types": [
            [
              "!ldap"
            ]
          ],
          "ansible_groups": [
            "java"
          ],
          "number": {
            "default": -1,
            "ha": -1
          }
        }
      ],
      "ansible_vars": {
        "JAVA_HOME": "/usr/lib/jvm/jre-1.8.0-openjdk/"
      },
      "requirements": {
        "services": {}
      },
      "auto_install": []
    }
  ]
}
```
We assume that the `ldap` group already exists as this is a complementary bundle for the `jumbo-services` bundle. We could ensure that it exists like so:
```json
{
  "available_node_types": [
    "ldap"
  ],
  ...
}
```
We tell Jumbo that the component `JAVA_OPENJDK_1_8_0` should be installed on `-1` node, which means on every host matching the given `node_types`. All those hosts will be added to the `java` Ansible group. Finally we export the `JAVA_HOME` variable in `ansible_vars`.

We are done! Now let's just add it to our cluster:
```sh
jumbo (mycluster) > addbundle prep-jumbo -p first
jumbo (mycluster) > addservice JAVA
```