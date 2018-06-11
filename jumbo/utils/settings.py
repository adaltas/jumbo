import os
import platform

OS = platform.system()

JUMBODIR = os.path.expanduser('~/.jumbo/')

DEFAULT_URLS = {
    'ambari_repo': ('http://public-repo-1.hortonworks.com/ambari/'
                    'centos7/2.x/updates/2.6.1.5/ambari.repo'),
    'vdf': ('http://public-repo-1.hortonworks.com/HDP/centos7/'
            '2.x/updates/2.6.4.0/HDP-2.6.4.0-91.xml')
}

NOT_HADOOP_COMP = [
    'ANSIBLE_CLIENT',
    'PSQL_SERVER',
    'AMBARI_SERVER',
    'IPA_SERVER'
]
