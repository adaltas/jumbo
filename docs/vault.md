# Vault

You can store custom passwords in a vault managed by Ansible Vault. A vault is encrypted using a master password. It will basically override the default configurations stored in the Ansible inventory variable file `inventory/group_vars/all/vars`. Bundles should document the password variables that can be changed.

Example: in the `jumbo-services` bundle, the Ambari configuration we have in `inventory/group_vars/all/vars` is:
```
AMBARI:
  pwd: admin
  ssl:
    enabled: false
    port: 8442
  user: admin
```

`AMBARI.pwd` is the default password used if the property is not present in the vault located at `inventory/group_vars/all/vault`

## Adding entries to the vault

Randomly generated password with 12 characters (default is 10):
```
jumbo (mycluster) > addpass AMBARI.pwd --length 12 -p vaultM4sterP@ssword
```

Setting Ambari admin password to `4dm1n`:
```
jumbo (mycluster) > addpass AMBARI.pwd 4dm1n -p vaultM4sterP@ssword
```

## Removing entry from the vault
Remove entry `AMBARI.pwd`:
```
jumbo (mycluster) > rmpass AMBARI.pwd -p vaultM4sterP@ssword
```

## Viewing vault content
Viewing specific key:
```
jumbo (mycluster) > getpass AMBARI.pwd -p vaultM4sterP@ssword
```
Viewing the whole vault:
```
jumbo (mycluster) > getpass -p vaultM4sterP@ssword
```

## Vault master password

Default vault password is `changeit` if you don't specify a master password for your first entry (using the command `addpass`).
To change the current vault password:
```
jumbo (mycluster) > changevaultpass previousPass newPass
```
