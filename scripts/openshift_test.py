import os
import time
import subprocess
import yaml
from configparser import ConfigParser, RawConfigParser
from collections import defaultdict

import pdb


# Install Openshift CLI from https://access.redhat.com/downloads/content/290
# Login command
# oc login https://sc-rdops-vm17-dhcp-16-4.eng.vmware.com:8443 --token=lUW-wINJF9jFsWjwF--qRwoEP6VI7gNlF9GU407YPc8
# Logout command
# oc logout

def run_cmd(cmd=None):
    print("Running command: %s" % cmd)
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, shell=True)
    o, e = proc.communicate()
    result = dict()
    result['stdout'] = o.decode('ascii')
    result['srderr'] = e.decode('ascii')
    result['rc'] = str(proc.returncode)
    return result


def create_delete_many_pods_stress(replicas=50):
    for _ in range(100):
        cmd = "oc scale --replicas=%s rc tcp-rc -n test" % replicas
        run_cmd(cmd)
        time.sleep(10)
        cmd = "oc scale --replicas=1 rc tcp-rc -n test"
        run_cmd(cmd)
        time.sleep(10)


if __name__ == '__main__':
    create_delete_many_pods_stress()