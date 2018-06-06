# Jumbo - A local Hadoop cluster bootstrapper

Jumbo is a tool that allows you to deploy a **virtualized Hadoop cluster** on a local machine in minutes. This tool is especially targeted to developers with a limited knowledge of Hadoop to help them **quickly bootstrap development environments** without struggling with machines and services configurations.

![Jumbo shell](https://i.imgur.com/COH3aMm.png)

Jumbo is written in Python and relies on other tools that it coordinates:
- [Vagrant](https://github.com/hashicorp/vagrant), to manage the virtual machines;
- [Ansible](https://github.com/ansible/ansible), to configure the cluster;
- [Apache Ambari](https://ambari.apache.org/), to provision and manage the Hadoop cluster.

The distribution used for the Hadoop cluster is [Hortonworks Data Platform](https://hortonworks.com/products/data-platforms/hdp/).

## Getting started

A complete documentation is available in Gitbook format in the `docs/` folder.  
Check https://github.com/GitbookIO/gitbook/blob/master/docs/setup.md for Gitbook installation.

Jumbo installation instructions are available in [`docs/getting-started/installation.md`](docs/getting-started/installation.md)

## Project roadmap

**Current version: [v0.4.1](docs/versions.md)**

- [x] Add Kerberos support
- [x] Add a `-r` option on `addservice` for automatic dependency installation
- [ ] Open source and share (Github, article)
- [ ] Add informative commands (info, version, available services...)
- [ ] Add support for all Ambari services
- [ ] Generalize HA support
- [x] "Proxify" Vagrant commands into Jumbo: `start`, `stop`, `status`, `restart`, `delete`
- [x] Start HDP services on vagrant start
- [ ] Smart cluster topology based on available ressources
- [ ] Host the documentation on a website
- [ ] Allow to dupplicate existing cluster with a different name

## Authors

Jumbo was developed by Gauthier Leonard and Xavier Hermand at [Adaltas](http://adaltas.com).

## License

Jumbo is licensed under MIT License. See [LICENSE](LICENSE) for the full license text.