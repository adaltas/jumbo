from ansible_vault import Vault
import string
import random
import yaml
import os.path

from jumbo.utils import exceptions as ex, session as ss
from jumbo.utils.settings import JUMBODIR
from jumbo.utils.checks import valid_cluster


def create_keys(d, str_keys, value):
    keys = str_keys.split(".")
    for k in keys[:-1]:
        if not k in d:
            d[k] = {}
        d = d[k]
    if keys[-1] in d:
        raise ex.CreationError("vault entry", str_keys,
                               "key", str_keys, 'Exists')
    d[keys[-1]] = value


@valid_cluster
def add_pass(vault_key, vault_value, length, password, *, cluster):
    vault_file = JUMBODIR + 'clusters/' + cluster + '/inventory/group_vars/all/vault'
    vault = Vault(password)
    data = {}

    if os.path.isfile(vault_file):
        data = vault.load(open(vault_file).read())
        print(data)

    if vault_value is None:
        print('Generating random password')
        vault_value = ''.join(random.choice(
            string.ascii_letters + string.digits) for _ in range(length))

    create_keys(data, vault_key, vault_value)
    print(data)
    vault.dump(data, open(vault_file, 'wb'))
