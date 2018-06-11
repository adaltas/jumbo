# Advanced usage

## Repositories URLs

You might want to use local repositories for your cluster to avoid unnecessary downloads. It is possible to configure the URLs used by Jumbo during the cluster provisioning with the [`setrepo`](commands/cluster.md#set-repo) command or on [cluster creation](commands/cluster.md#create) for:
- the Ambari repository (`ambari_repo`) - only Ambari 2.6.0 and higher versions are supported by Jumbo. Don't hesitate to contribute if you need support for other versions!
- the VDF file URL (`vdf`)

The VDF file was introduced in Ambari 2.6.0 ([release notes](https://docs.hortonworks.com/HDPDocuments/Ambari-2.6.0.0/bk_ambari-release-notes/content/ambari_relnotes-2.6.0.0-behavioral-changes.html)). In this file you can specify the URLs of HDP repositories and the version of HDP services. The default VDF file used is [HDP-2.6.4.0-91.xml](http://public-repo-1.hortonworks.com/HDP/centos7/2.x/updates/2.6.4.0/HDP-2.6.4.0-91.xml).

For example, to change the HDP repo URL, modify the `<baseurl>`:
```xml
<repository-version xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="version_definition.xsd">
    <release>...</release>
    <manifest>...</manifest>
    <available-services/>
    <repository-info>
        <os family="redhat7">
            <package-version>2_6_4_0_*</package-version>
            <repo>
                <baseurl>
                    http://my.url/hdp.repo/
                </baseurl>
                <repoid>HDP-2.6</repoid>
                <reponame>HDP</reponame>
                <unique>true</unique>
                </repo>
            <repo>...</repo>
            <repo>...</repo>
        </os>
    </repository-info>
</repository-version>
```

You then have to host this file on an HTTPD server and register it with `setrepo`.

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
	"name": "ANSIBLE",	 # service name
	"components": [		# list of the components of the service
		{
			"name": "ANSIBLE_CLIENT",	# component name
			"hosts_types": [           	# node types on which the component can
				"edge"                 	# 	be installed
			],
			"abbr": "ANSIBLE_C",       	# component abbreviation
			"number": {
			"default": 1,              	# number of this component needed in default mode
			"ha": 1                    	# number of this component needed in HA mode
			}
		}
	],
	"requirements": {
		"ram": 1000,					# not used yet
		"disk": 10000,					# not used yet
		"nodes": {						# number of node of each type required to install
			"default": {				# 	the service
				"edge": 1
			},
			"ha": {
				"edge": 1
			}
		},
		"services": {					# other services on which the service depends
			"default": [],
			"ha": []
		}
	},
	"auto_install": []					# clients of the service that will always be installed
}
```

A component can only be installed on nodes of `hosts_types` types. You might want to create custom types (e.g. to isolate a service). The node types are defined in the list `node_types`. To create a new type, add it to:
- the `node_types` list;
- `hosts_types` lists of the components that you want to install on nodes of the new type.


> **info**
> On auto-installation of a service, the components are added in priority to nodes of the first type of the `hosts_types` list.