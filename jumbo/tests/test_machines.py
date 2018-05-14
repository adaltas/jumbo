import unittest
import random
import string

from jumbo.core import clusters, machines as vm
from jumbo.utils import session as ss, exceptions as ex


class TestMachines(unittest.TestCase):
    def setUp(self):
        self.c_name = 'unittest_' + ''.join(random.choices(
            string.ascii_letters + string.digits,
            k=5))
        self.m_name = 'test01'
        clusters.create_cluster(domain=None,
                                ambari_repo=None,
                                vdf=None,
                                cluster=self.c_name)
        print('\nCluster "%s" created' % self.c_name)

    def tearDown(self):
        clusters.delete_cluster(cluster=self.c_name)
        print('OK\nCluster deleted')

    def test_add_machine(self):
        print('Test "add_machine"')
        print('Creating machine...')
        vm.add_machine(name=self.m_name,
                       ip='10.10.10.11',
                       ram=2048,
                       types=['master'],
                       cpus=1,
                       cluster=self.c_name)
        test01 = {
            'name': self.m_name,
            'ip': '10.10.10.11',
            'ram': 2048,
            'types': [
                'master'
            ],
            'cpus': 1,
            'components': [],
            'groups': []
        }
        machines = ss.svars['machines']
        machine = [m for m in machines if m['name'] == self.m_name][0]

        self.assertEqual(machine, test01)

    def test_add_remove_machine(self):
        print('Test add_remove_machine')
        vm.add_machine(name=self.m_name,
                       ip='10.10.10.11',
                       ram=2048,
                       types=['master'],
                       cpus=1,
                       cluster=self.c_name)
        print('Machine created')

        print('Deleting machine...')
        vm.remove_machine(cluster=self.c_name,
                          machine=self.m_name)

        self.assertFalse(vm.check_machine(cluster=self.c_name,
                                          machine=self.m_name))

    def test_add_machine_same_name(self):
        print('Test add_machine_same_ip')
        vm.add_machine(name=self.m_name,
                       ip='10.10.10.11',
                       ram=2048,
                       types=['master'],
                       cpus=1,
                       cluster=self.c_name)
        print('Machine 1 created')
        self.assertRaises(ex.CreationError, self.add_with_same_name)

    def add_with_same_name(self):
        print('Trying to create machine 2...')
        vm.add_machine(name=self.m_name,
                       ip='10.10.10.12',
                       ram=2048,
                       types=['master'],
                       cpus=1,
                       cluster=self.c_name)

    def test_add_machine_same_ip(self):
        print('Test add_machine_same_ip')
        vm.add_machine(name=self.m_name,
                       ip='10.10.10.11',
                       ram=2048,
                       types=['master'],
                       cpus=1,
                       cluster=self.c_name)
        print('Machine 1 created')
        self.assertRaises(ex.CreationError, self.add_with_same_ip)

    def add_with_same_ip(self):
        print('Trying to create machine 2...')
        vm.add_machine(name=self.m_name + '-2',
                       ip='10.10.10.11',
                       ram=2048,
                       types=['master'],
                       cpus=1,
                       cluster=self.c_name)


if __name__ == '__main__':
    unittest.main()
