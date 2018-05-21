import unittest
import random
import string
import os
import subprocess

from jumbo.core import clusters, nodes, services
from jumbo.utils import session as ss, exceptions as ex
from jumbo.utils.settings import JUMBODIR


class TestServices(unittest.TestCase):
    def setUp(self):
        self.c_name = 'unittest_' + ''.join(random.choices(
            string.ascii_letters + string.digits,
            k=5))
        self.m_names = ['master', 'master',
                        'sidemaster_edge', 'worker', 'ldap']
        clusters.create_cluster(domain=None,
                                ambari_repo=None,
                                vdf=None,
                                cluster=self.c_name)
        print('\n\nCluster "%s" created' % self.c_name)

        for i, n in enumerate(self.m_names):
            nodes.add_machine(name=n + str(i),
                              ip='10.10.10.1%d' % (i + 1),
                              ram=2048,
                              types=n.split('_'),
                              cpus=1,
                              cluster=self.c_name)
        print('%d machines created' % i)

        for s in services.config['services']:
            self.recursive_add(s['name'], False)
        print('All services added')

    def tearDown(self):
        clusters.delete_cluster(cluster=self.c_name)
        print('Cluster deleted')

    def test_playbook_syntax(self):
        print('Test "playbook_syntax"')
        for _, _, filenames in os.walk(
                JUMBODIR + self.c_name + '/playbooks'):
            for filename in filenames:
                if '.yml' in filename:
                    ret = subprocess.call(
                        ['ansible-playbook',
                         os.path.join(JUMBODIR,
                                      self.c_name,
                                      'playbooks/%s' % filename),
                         '-i',
                         os.path.join(JUMBODIR,
                                      self.c_name,
                                      'playbooks/inventory'),
                         '--syntax-check',
                         '--list-tasks'])
                self.assertEqual(ret, 0)
            break

    def test_vagrantfile_syntax(self):
        print('Test "vagrantfile_syntax"')
        prev_dir = os.getcwd()
        os.chdir(os.path.join(JUMBODIR,
                              self.c_name,))
        ret = subprocess.call(['vagrant', 'validate'])
        os.chdir(prev_dir)
        self.assertEqual(ret, 0)

    def recursive_add(self, service, ha):
        if not services.check_service_cluster(service):
            m_serv, _ = services.check_service_req_service(service, ha)
            for serv in m_serv:
                self.recursive_add(serv, ha)

            print('Adding "%s"' % service)
            services.add_service(name=service,
                                 ha=ha,
                                 cluster=self.c_name)
            services.auto_assign(service=service,
                                 ha=ha,
                                 cluster=self.c_name)


if __name__ == '__main__':
    unittest.main()
