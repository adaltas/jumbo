from jumbo.utils.settings import JUMBODIR
from jumbo.utils.checks import valid_cluster
from jumbo.utils import session as ss

import subprocess
import time
import os


@valid_cluster
def cmd(cmd, *, cluster):
    """Run a command in the vagrantfile folder and print output
    """

    ss.load_config(cluster)
    ss.dump_config()
    try:
        res = subprocess.Popen(cmd,
                               cwd=os.path.join(JUMBODIR, cluster),
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT
                               )

        for line in res.stdout:
            print(line.decode('utf-8').rstrip())

        if cmd[1] == 'up':
            # Start services after a vagrant up
            start_services()

    except KeyboardInterrupt:
        res.kill()


def start_services():
    """Call Ambari API to start all services
       until Ambari server accepts the request
    """
    max_retries = 20

    ip = None
    for node in ss.svars['nodes']:
        for comp in node['components']:
            if comp == 'AMBARI_SERVER':
                ip = node['ip']
                break

    if ip:
        cmd = ('curl -u admin:admin -H "X-Requested-By: ambari" '
               '-X PUT '
               '-d \'{\"RequestInfo\": '
               '{\"context\":\"Start all services\"}, '
               '\"Body\":{\"ServiceInfo\": '
               '{\"state\":\"STARTED\"}}}\' ' +
               ip + ':8080/api/v1/clusters/' +
               ss.svars['domain'].replace('.', '') + '/services')

        retries = 0
        accepted = False
        res = subprocess.Popen(cmd,
                               shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
        for line in res.stdout:
            if "Accepted" in line.decode('utf-8').rstrip():
                accepted = True
                break

        while not accepted and retries < max_retries:
            print('Server is not up yet. Retrying to start services...')
            time.sleep(5)
            res = subprocess.Popen(cmd,
                                   shell=True,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT)
            for line in res.stdout:
                if "Accepted" in line.decode('utf-8').rstrip():
                    accepted = True
                    break
            retries += 1

        if accepted:
            print('Services are starting. View progression at '
                  'http://%s:8080 (admin/admin)' % ip)
        else:
            print('Timeout. Wait longer and start again, or '
                  'start services manually at '
                  'http://%s:8080 (admin/admin)' % ip)
