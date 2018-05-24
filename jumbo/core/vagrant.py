from jumbo.utils.settings import JUMBODIR
from jumbo.utils.checks import valid_cluster

import subprocess
import os

@valid_cluster
def cmd(cmd, *, cluster):
    """Run a command in the vagrantfile folder and print output
    """

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

