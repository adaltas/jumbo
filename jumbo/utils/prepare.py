import os
import pathlib
from shutil import copyfile
from distutils import dir_util

from jumbo.utils.settings import JUMBODIR


def init_jumbo():
    if not os.path.isfile(JUMBODIR + 'versions.json'):
        if not os.path.isdir(JUMBODIR):
            pathlib.Path(JUMBODIR).mkdir()
        copyfile(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) +
                 '/core/config/versions.json', JUMBODIR + 'versions.json')

    if not os.path.isdir(JUMBODIR + 'clusters/'):
        pathlib.Path(JUMBODIR + 'clusters').mkdir()

    if not os.path.isfile(JUMBODIR + 'bundles/jumbo-services/'):
        if not os.path.isdir(JUMBODIR + 'bundles/'):
            pathlib.Path(JUMBODIR + 'bundles').mkdir()
        dir_util.copy_tree(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))) +
            '/core/data/jumbo-services',
            JUMBODIR + 'bundles/jumbo-services')
