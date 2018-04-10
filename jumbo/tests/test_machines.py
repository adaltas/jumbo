import unittest

from jumbo.core import clusters, machines
from jumbo.utils import session as ss


class TestMachineMethods(unittest.TestCase):
    def test_add(self):
        clusters.create_cluster('test')
        machines.add_machine(
            'toto',
            '10.10.10.11',
            1000,
            10000,
            [
                'master'
            ]
        )
        self.assertEqual(
            ss.svars['machines'][0],
            {
                'name': 'toto',
                'ip': '10.10.10.11',
                'ram': 1000,
                'disk': 10000,
                'types': ['master'],
                'cpus': 1
            })
        machines.add_machine(
            "toto",
            "10.10.10.11",
            1000,
            10000,
            [
                "master"
            ],
            2)
        self.assertEqual(
            ss.svars['machines'][0],
            {
                'name': 'toto',
                'ip': '10.10.10.11',
                'ram': 1000,
                'disk': 10000,
                'types': ['master'],
                'cpus': 2
            })


if __name__ == '__main__':
    unittest.main()
