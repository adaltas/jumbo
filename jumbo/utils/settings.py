import os
import platform

OS = platform.system()

JUMBODIR = os.path.expanduser('~/.jumbo/')

NOT_HADOOP_COMP = [
    'ANSIBLE_CLIENT',
    'PSQL_SERVER',
    'AMBARI_SERVER',
    'IPA_SERVER'
]
