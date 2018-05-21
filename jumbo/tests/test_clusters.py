import unittest
import os
import random
import string

from jumbo.core import clusters
from jumbo.utils import session as ss, checks, exceptions as ex
from jumbo.utils.settings import JUMBODIR


class TestClusters(unittest.TestCase):
    def setUp(self):
        self.c_name = 'unittest' + ''.join(random.choices(
            string.ascii_letters + string.digits,
            k=5))
        self.m_name = 'test01'
        clusters.create_cluster(domain=None,
                                ambari_repo=None,
                                vdf=None,
                                cluster=self.c_name)
        print('\n\nCluster "%s" created' % self.c_name)

    def tearDown(self):
        if checks.check_cluster(self.c_name):
            clusters.delete_cluster(cluster=self.c_name)
            print('Cluster deleted\n')

    def test_create_load_cluster(self):
        print('Test "create_load_cluster"')
        cluster = ss.svars
        ss.clear()
        ss.load_config(cluster['cluster'])
        self.assertEqual(cluster, ss.svars)

    def test_create_cluster_same_name(self):
        print('Test "create_cluster_same_name"')
        self.assertRaises(ex.CreationError, self.create_same_name)

    def create_same_name(self):
        clusters.create_cluster(domain=None,
                                ambari_repo=None,
                                vdf=None,
                                cluster=self.c_name)

    def test_delete_cluster(self):
        print('Test "delete_cluster"')
        clusters.delete_cluster(cluster=self.c_name)
        self.assertFalse(checks.check_cluster(self.c_name))

    def test_repair_cluster(self):
        print('Test "repair_cluster"')
        os.remove(JUMBODIR + self.c_name + '/jumbo_config')
        print('Repairing cluster...')
        clusters.repair_cluster(domain=None,
                                ambari_repo=None,
                                vdf=None,
                                cluster=self.c_name)
        self.assertTrue(clusters.check_config(self.c_name))

    def test_list_clusters(self):
        print('Test "list_clusters"')
        self.assertIn(ss.svars, clusters.list_clusters())

    def test_set_url(self):
        print('Test "set_url"')
        clusters.set_url(url='ambari_repo',
                         value='http://test.url',
                         cluster=self.c_name)
        c = [cl for cl in clusters.list_clusters()
             if cl['cluster'] == self.c_name][0]
        self.assertEqual('http://test.url', c['urls']['ambari_repo'])


if __name__ == '__main__':
    unittest.main()
