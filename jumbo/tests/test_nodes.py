import unittest
import random
import string

from jumbo.core import clusters, nodes
from jumbo.utils import session as ss, exceptions as ex


class TestMachines(unittest.TestCase):
    def setUp(self):
        self.c_name = 'unittest' + ''.join(random.choices(
            string.ascii_letters + string.digits,
            k=5))
        self.m_name = 'test01'
        clusters.create_cluster(domain=None,
                                cluster=self.c_name)
        print('\n\nCluster "%s" created' % self.c_name)

    def tearDown(self):
        clusters.delete_cluster(cluster=self.c_name)
        print('Cluster deleted')

    def test_add_node(self):
        print('Test "add_node"')
        print('Creating node...')
        nodes.add_node(name=self.m_name,
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
            'components': []
        }
        all_nodes = ss.svars['nodes']
        node = [m for m in all_nodes if m['name'] == self.m_name][0]

        self.assertEqual(node, test01)

    def test_add_remove_node(self):
        print('Test add_remove_node')
        nodes.add_node(name=self.m_name,
                       ip='10.10.10.11',
                       ram=2048,
                       types=['master'],
                       cpus=1,
                       cluster=self.c_name)
        print('Machine created')

        print('Deleting node...')
        nodes.remove_node(cluster=self.c_name,
                          node=self.m_name)

        self.assertFalse(nodes.check_node(cluster=self.c_name,
                                          node=self.m_name))

    def test_add_node_same_name(self):
        print('Test add_node_same_ip')
        nodes.add_node(name=self.m_name,
                       ip='10.10.10.11',
                       ram=2048,
                       types=['master'],
                       cpus=1,
                       cluster=self.c_name)
        print('Machine 1 created')
        self.assertRaises(ex.CreationError, self.add_with_same_name)

    def add_with_same_name(self):
        print('Trying to create node 2...')
        nodes.add_node(name=self.m_name,
                       ip='10.10.10.12',
                       ram=2048,
                       types=['master'],
                       cpus=1,
                       cluster=self.c_name)

    def test_add_node_same_ip(self):
        print('Test add_node_same_ip')
        nodes.add_node(name=self.m_name,
                       ip='10.10.10.11',
                       ram=2048,
                       types=['master'],
                       cpus=1,
                       cluster=self.c_name)
        print('Machine 1 created')
        self.assertRaises(ex.CreationError, self.add_with_same_ip)

    def add_with_same_ip(self):
        print('Trying to create node 2...')
        nodes.add_node(name=self.m_name + '-2',
                       ip='10.10.10.11',
                       ram=2048,
                       types=['master'],
                       cpus=1,
                       cluster=self.c_name)


if __name__ == '__main__':
    unittest.main()
