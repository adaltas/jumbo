# Déploiement d'un cluster avec FreeIPA et Ambari

Le but de ce projet est le déploiement d'un environnement de VMs CentOS composé de :
* un server FreeIPA avec DNS intégré ;
* des clients FreeIPA ;
* un serveur Ambari.

## Structure

Sont présentes les VMs master01, master02, master03, ldap01, edge01, worker01 et worker02 avec les éléments :
* Ansible sur edge01 ;
* IPA server sur ldap01 ;
* IPA client sur toutes les machines sauf ldap01 ;
* Ambari server sur master03.

La configuration de ces VMs est visible dans le [Vagrantfile](Vagrantfile).

## Déroulement

1. **Vagrant :**
    1. démarre les VMs et leur provisionne notre clé ssh personnelle `~/.ssh/id_rsa.pub` ; 
    1. provisionne Ansible sur la machine edge01 ;  
    1. définit la clé SSH de la machine Ansible (edge01) comme étant la clé Vagrant pour avoir accès aux autres machines ;
    1. lance le playbook [`playbooks/full-deploy.yml`](playbooks/full-deploy.yml).
1. **Ansible :**
    1. définit le nom des hosts en suivant le fichier [`hosts`](cluster-provisioning/inventory/hosts) de l'inventory Ansible;
    1. installe et démarre le serveur IPA avec DNS intégré sur ldap01 ;
    1. définit ldap01 comme serveur DNS sur les autres machines ;
    1. installe le client IPA sur ces autres machines ;
    1. configure les machines pour accueillir Ambari agent (sauf ldap01) ;
    1. installe et démarre le serveur Ambari sur master03 ;
    2. installe et démarre le serveur PostgreSQL sur master02 et crées les bases de données `hive` et `oozie` ;
    2. (optionnel, cf. Cluster HDP) installe, configure et démarre les agents Ambari sur toutes les machines (sauf ldap01) ;
    3. (optionnel, cf. Cluster HDP) lance la création d'un cluster via l'API Ambari   

## Provider

Le projet supporte **VirtualBox** et **libvirt** comme providers pour Vagrant.
Par défaut Vagrant va tenter d'utiliser libvirt, puis VirtualBox.
Le provider par défaut peut être forcé via la variable d'environnement `VAGRANT_DEFAULT_PROVIDER`.
Il est aussi possible de choisir le provider lors de l'init :
```bash
vagrant up --provider libvirt|virtualbox
```
Une fois les machines instanciées, il n'est plus nécessaire de respécifier le provider.

Si la machine hôte est Linux et si KVM est activé dans le noyau, il est fortement conseillé d'utiliser libvirt.

### Configuration de libvirt

Installer le paquet qemu, libvirt et démarrer le service libvirtd
```bash
$ systemctl start libvirtd
$ systemctl enable libvirtd
```

Installer les plugins vagrant suivant :

```bash
$ vagrant plugin install vagrant-mutate
$ vagrant plugin install vagrant-libvirt
```

Installer les paquets **ebtables**, **dnsmasq** et **virt-manager**. Dans virt-manager, configurer le qemu system en ajoutant QEMU/KVM (File > Add Connection) et ajouter un pool de disque nommé hdp-cluster (QEMU/KVM > Stockage > **+** Ajouter un pool).

Installer la box libvirt:
```bash
$ vagrant box add centos/7 --provider libvirt
```

Attention, libvirt ne peut fonctionner conjointement avec VirtualBox. Éteindre tous les process VirtualBox.

## Configuration

La configuration du cluster se fait via le fichier [`playbooks/inventory/group_vars/all`](playbooks/inventory/group_vars/all).

### Cluster HDP

Ce projet offre la possibilité de lancer automatiquement l'installation d'un cluster HDP. Pour cela, configurez la variable `use_blueprint: true` dans [`playbooks/inventory/group_vars/all`](playbooks/inventory/group_vars/all).

Les fichiers à configurer pour l'installation sont :
- `blueprint.json`, le blueprint du cluster à déployer ;
- `cluster.json`, le mapping des host groups vers les machines virtuelles ;
- `version_definitions.json`, la définition des versions des composants de la stack et des repos à utiliser (au format [VDF file](https://docs.hortonworks.com/HDPDocuments/Ambari-2.6.0.0/bk_ambari-release-notes/content/ambari_relnotes-2.6.0.0-behavioral-changes.html)).


## Lancement

Il est nécessaire de posséder une clé SSH publique dans `~/.ssh/id_rsa.pub` afin de pouvoir se connecter aux machines (la clé est provisionnée automatiquement par Vagrant).  
Après avoir cloné le git et installé vagrant : `vagrant up`.

## Ambari

Après l'installation, vous pouvez ensuite accéder à Ambari WebUI via l'adresse
```
http://10.10.10.13:8080/
```

Le cluster possède par défaut une database PostgresSQL sur master02 avec hive et oozie préconfigurés (db/user/password).

## TODO

- [x] Vagrantfile avec provisionning
- [x] Configuration du nom des hosts via Ansible
- [x] Installation de freeIPA server et clients via Ansible
- [x] Installation du serveur Ambari via Ansible.
- [x] Déploiement d'un cluster HDP avec un blueprint Ambari
- [ ] Sécurisation du cluster (Kerberos + SSL)
