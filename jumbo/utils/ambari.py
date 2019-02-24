import os
import subprocess
import time

from jumbo.utils.settings import JUMBODIR
from jumbo.utils import session as ss
from jumbo.utils import exceptions as ex


def start_services(cluster):
    """ Call Ambari API to start all services
    """

    cmd = ["ansible-playbook", "playbooks/start-services.yml",
           "-i", "playbooks/inventory"]
    try:
        res = subprocess.Popen(cmd,
                               cwd=os.path.join(
                                   JUMBODIR+'clusters', cluster),
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)

        for line in res.stdout:
            print(line.decode('utf-8').rstrip())

    except KeyboardInterrupt:
        res.kill()
