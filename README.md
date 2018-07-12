# Jumbo - A local Hadoop cluster bootstrapper

Jumbo is a tool that allows you to deploy a **virtualized Hadoop cluster** on a local machine in minutes. It is made to help you **quickly bootstrap development environments** without struggling with nodes and services configurations.

![Jumbo shell](https://i.imgur.com/d78Cl2O.png)

Jumbo is written in Python and relies on other tools that it coordinates:
- [Vagrant](https://github.com/hashicorp/vagrant), to manage the virtual machines;
- [Ansible](https://github.com/ansible/ansible), to configure the cluster;
- [Apache Ambari](https://ambari.apache.org/), to provision and manage the Hadoop cluster.

The distribution used for the Hadoop cluster is [Hortonworks Data Platform](https://hortonworks.com/products/data-platforms/hdp/).

## Who can use Jumbo?

Originally, Jumbo is designed for developers with a limited knowledge of the Hadoop deployment process. But this doesn't mean that it cannot be helpful to others! Everything needed to create and deploy a Hadoop cluster is done by Jumbo, so if you need different environments (e.g. for different projects, testing...), be sure it will be useful to you!

## Getting started

A complete documentation is available at [Jumbo website](http://jumbo.adaltas.com).
Jumbo installation instructions are available on the [installation page](http://jumbo.adaltas.com/getting-started/installation).

If you want a local documentation, it is also available in [Gitbook](https://github.com/GitbookIO/gitbook) format in the `docs/` folder.

## Project roadmap

**Current version: [v0.4.2](http://jumbo.adaltas.com/overview/versions)**

- [x] Add Kerberos support
- [x] Add a `-r` option on `addservice` for automatic dependency installation
- [x] "Proxify" Vagrant commands into Jumbo: `start`, `stop`, `status`, `restart`, `delete`
- [x] Start HDP services on vagrant start
- [x] Host the documentation on a website ([jumbo.adaltas.com](http://jumbo.adaltas.com))
- [ ] Add informative commands (info, version, available services...)
- [ ] Allow custom configurations via JSON (services props, versions, urls...)
- [ ] Add support for all HDP services
- [ ] Generalize HA support
- [ ] Smart cluster topology based on available ressources
- [ ] Allow to dupplicate existing cluster with a different name

## Contributing

Jumbo is a very recent project. We would be happy to have feedback so don't hesitate to post issues or even to do a PR if you need extra features!

## Authors

Jumbo was developed by [Gauthier Leonard](https://github.com/Nuttymoon) and [Xavier Hermand](https://github.com/RReivax) at [Adaltas](http://adaltas.com).

## Contributors

- [Pierre Sauvage](https://github.com/Pierrotws)
- [Oscar Blazejewski](https://github.com/scascar)

## License

Jumbo is licensed under MIT License. See [LICENSE](LICENSE) for the full license text.
