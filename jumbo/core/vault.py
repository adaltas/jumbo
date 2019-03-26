from ansible_vault import Vault
import string
import random
import yaml
import json
import os.path
import copy

from jumbo.utils import exceptions as ex, session as ss
from jumbo.utils.settings import JUMBODIR
from jumbo.utils.checks import valid_cluster


def create_keys(d, str_keys, value):
    """Create keys in the dictionnary d from dotted notation string in str_key.
    eg. str_keys = "AMBARI.pwd" creates d['AMBARI']['pwd'] = value 
    """

    keys = str_keys.split(".")
    for k in keys[:-1]:
        if not k in d:
            d[k] = {}
        d = d[k]
    if keys[-1] in d:
        raise ex.CreationError("vault entry", str_keys,
                               "key", str_keys, 'Exists')
    d[keys[-1]] = value


def delete_key(d, str_keys):
    """Delete key in dictionnary d from dotted notation string in str_key"""
    keys = str_keys.split(".")
    for k in keys[:-1]:
        d = d[k]
    del d[keys[-1]]


def get_key(d, str_keys):
    """Delete key in dictionnary d from dotted notation string in str_key"""
    keys = str_keys.split(".")
    for k in keys[:-1]:
        d = d[k]
    return d[keys[-1]]


@valid_cluster
def add_pass(vault_key, vault_value, length, password, *, cluster):
    """Add entry in cluster vault"""
    vault_file = JUMBODIR + 'clusters/' + cluster + '/inventory/group_vars/all/vault'
    vault = Vault(password)
    data = {}

    if os.path.isfile(vault_file):
        data = vault.load(open(vault_file).read())

    if vault_value is None:
        print('Generating random password')
        vault_value = ''.join(random.choice(
            string.ascii_letters + string.digits) for _ in range(length))

    create_keys(data, vault_key, vault_value)
    print(yaml.dump(data, default_flow_style=False))
    vault.dump(data, open(vault_file, 'wb'))


@valid_cluster
def rm_pass(vault_key, password, *, cluster):
    """Remove entry from cluster vault"""
    vault_file = JUMBODIR + 'clusters/' + cluster + '/inventory/group_vars/all/vault'

    vault = Vault(password)
    data = {}

    if os.path.isfile(vault_file):
        data = vault.load(open(vault_file).read())
        try:
            delete_key(data, vault_key)
        except KeyError:
            raise ex.LoadError('key', vault_key, 'NotExist')
    else:
        raise ex.LoadError('vault for cluster', cluster, 'NotExist')

    print(yaml.dump(data, default_flow_style=False))
    vault.dump(data, open(vault_file, 'wb'))


@valid_cluster
def get_pass(vault_key, password, *, cluster):
    """Print YAML representation of cluster vault"""
    vault_file = JUMBODIR + 'clusters/' + cluster + '/inventory/group_vars/all/vault'

    vault = Vault(password)
    data = {}

    if os.path.isfile(vault_file):
        data = vault.load(open(vault_file).read())
    else:
        raise ex.LoadError('vault for cluster', cluster, 'NotExist')

    if vault_key == '*':
        print(yaml.dump(data, default_flow_style=False))
    else:
        try:
            print(get_key(data, vault_key))
        except KeyError:
            raise ex.LoadError('key', vault_key, 'NotExist')


@valid_cluster
def change_vault_pass(password, new_password, *, cluster):
    """Change vault master password"""
    vault_file = JUMBODIR + 'clusters/' + cluster + '/inventory/group_vars/all/vault'
    vault = Vault(password)
    new_vault = Vault(new_password)
    data = {}

    if os.path.isfile(vault_file):
        data = vault.load(open(vault_file).read())

    print(yaml.dump(data, default_flow_style=False))
    new_vault.dump(data, open(vault_file, 'wb'))
