# Advanced usage

## Versions and repositories URLs

Since v0.4.3, Jumbo supports fine grained versions and repositories management. All configurations are done through files called `versions.json`. When upgrading to v0.4.3, the default `verions.json` will be added to the `~/.jumbo` directory, and an empty `versions.json` file to any new cluster's root directory (e.g. `~/.jumbo/newcluster/versions.json`).

### How does it work?

`versions.json` work in "cascading" mode, with priority to the cluster level `versions.json`. If a version definition is not found in this files, the global version set in `~/.jumbo/versions.json` will be used.

In `versions.json` files, you will find 3 sets of items:

- `services` - Jumbo services not part of a specific Big Data platform (e.g. POSTGRESQL or AMBARI),
- `resources` - pieces of software used by platforms,
- `platforms` - Big Data platforms such as HDP or CDH.

`services` and `resources` share the same structure:

```json
{
  "name": "POSTGRESQL",
  "versions": {
    "9.6": "https://download.postgresql.org/pub/repos/yum/9.6/redhat/rhel-7-x86_64/pgdg-centos96-9.6-3.noarch.rpm",
    "10": "https://download.postgresql.org/pub/repos/yum/10/redhat/rhel-7-x86_64/pgdg-centos10-10-2.noarch.rpm"
  }
}
```

Each `service`/`resource` has several versions available and each version is associated with its repository. The default `versions.json` file uses the official repositories of each software.

`platforms` also have several versions, each of which is tied to a version of each `resource` it uses:

```json
{
  "name": "HDP",
  "versions": {
    "2.6.4.0": [
      {
        "resource": "HDP",
        "version": "2.6.4.0"
      },
      {
        "resource": "HDP_GPL",
        "version": "2.6.4.0"
      },
      {
        "resource": "HDP_UTILS",
        "version": "1.1.0.22"
      },
      {
        "resource": "POSTGRESQL_JDBC_DRIVER",
        "version": "42.2.1"
      }
    ]
  }
}
```

### How to change the versions used?

`services` and `platforms` have a `default` attribute, which is set to the latest version by default. Change this attribute to whatever version you want to use (the version has to be described in `versions`).

```json
{
  "name": "POSTGRESQL",
  "versions": {
    "9.6": "https://download.postgresql.org/pub/repos/yum/9.6/redhat/rhel-7-x86_64/pgdg-centos96-9.6-3.noarch.rpm",
    "10": "https://download.postgresql.org/pub/repos/yum/10/redhat/rhel-7-x86_64/pgdg-centos10-10-2.noarch.rpm"
  },
  "default": "9.6" // set the version to use here
}
```

### How to change the repositories used?

In `services` and `resources`, simply change the url associated with the version you are using. This can be useful to use private local repositories.

## Kerberos

> **danger**
> We don't recommend using Kerberos if you are not familiar with it.

Jumbo supports the use of Kerberos to secure the cluster. `KERBEROS` is a Jumbo service with no component that can be added like any other service:

```
**[terminal]
**[prompt jumbo (mycluster) > ]**[command addservice KERBEROS]
```

The cluster will be kerberized after the HDP installation.  
It is possible to disable it afterward within the Ambari UI.

## Custom node types

In `jumbo/core/config/services.json`, the services are defined as follow:

```python
{
	"name": "ANSIBLE",				# service name
	"components": [				   # list of the components of the service
		{
			"name": "ANSIBLE_CLIENT", # component name
			"hosts_types": [		  # node types on which the component...
				"edge"                # ...can be installed
			],
			"abbr": "ANSIBLE_C",	  # component abbreviation
			"number": {
			"default": 1,			 # number needed in default mode
			"ha": 1			       # number needed in HA mode
			}
		}
	],
	"requirements": {
		"ram": 1000,                  # not used yet
		"disk": 10000,			    # not used yet
		"nodes": {					# number of node of each type required...
			"default": {			  # ...for the service
				"edge": 1
			},
			"ha": {
				"edge": 1
			}
		},
		"services": {				 # other services on which the service depends
			"default": [],
			"ha": []
		}
	},
	"auto_install": []				# clients that will always be installed
}
```

A component can only be installed on nodes of `hosts_types` types. You might want to create custom types (e.g. to isolate a service). The node types are defined in the list `node_types`. To create a new type, add it to:

- the `node_types` list;
- `hosts_types` lists of the components that you want to install on nodes of the new type.

> **info**
> On auto-installation of a service, the components are added in priority to nodes of the first type of the `hosts_types` list.
