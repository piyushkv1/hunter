import paramiko
import json
import itertools
import concurrent.futures

TESTS = "http://w3-dbc302.eng.vmware.com/piyushv/inputyaml"
CLUSTER_NAME = "occl-one"
NCP_NAMESPACE = "nsx-system"
NAMESPACES = [f"ns-{i}" for i in range(1)]
CLIENT_POD = 'net-test-pod'
CLIENT_POD_NS = 'net-ns'
TMP_SVC_FILE = '/tmp/tcp-svc.yml'
INGRESS_IP = '172.30.123.123'


def run_command(ip, cmd):
    with paramiko.SSHClient() as ssh:
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username='root', password='ca$hc0w')
        stdin, stdout, stderr = ssh.exec_command(cmd)
        stdin.flush()
        stdin.channel.shutdown_write()
        stdout.channel.settimeout(1)
        stderr.channel.settimeout(1)
        exit_code = stdout.channel.recv_exit_status()
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        return exit_code, output, error


if __name__ == '__main__':
    ns_name = "test"
    ip = "10.116.248.199"
    cmd = f"oc create ns {ns_name};" \
          f"oc adm policy add-scc-to-user anyuid -z default -n test"
    run_command(ip, cmd)
    cmd = f"wget -O {TMP_SVC_FILE} {TESTS}/service/tcp-svc-lb.yml"
    run_command(ip, cmd)
    results = list()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        for _i in range(1, 31):
            cmd = f"sed -E 's/tcp-svc-lb.*$/tcp-svc-lb-{_i}/' {TMP_SVC_FILE} " \
                f"| oc apply -n {ns_name} -f -"
            results.append(executor.submit(run_command, ip, cmd))
    cmd = f"oc apply -f {TESTS}/oc/sec-one-route-hostname.yml -n {ns_name}"
    run_command(ip, cmd)
    import pdb; pdb.set_trace()

