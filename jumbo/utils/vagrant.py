from jumbo.utils.settings import JUMBODIR
from jumbo.utils.checks import valid_cluster
from jumbo.utils import session as ss

import subprocess
import time
import os


@valid_cluster
def start(*, cluster):
    cmd = ['vagrant', 'up', '--color']
    handle_cmd(cmd, cluster=cluster)


@valid_cluster
def stop(*, cluster):
    cmd = ['vagrant', 'halt', '--color']
    handle_cmd(cmd, cluster=cluster)


@valid_cluster
def status(*, cluster):
    cmd = ['vagrant', 'status', '--color']
    handle_cmd(cmd, cluster=cluster)


@valid_cluster
def restart(*, cluster):
    handle_cmd(['vagrant', 'halt', '--color'], cluster=cluster)
    handle_cmd(['vagrant', 'up', '--color'], cluster=cluster)


@valid_cluster
def delete(*, cluster):
    cmd = ['vagrant', 'destroy', '-f']
    handle_cmd(cmd, cluster=cluster)


@valid_cluster
def handle_cmd(cmd, *, cluster):
    try:
        res = subprocess.Popen(cmd,
                               cwd=os.path.join(JUMBODIR, cluster),
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT
                               )

        for line in res.stdout:
            print(line.decode('utf-8').rstrip())

    except KeyboardInterrupt:
        res.kill()
