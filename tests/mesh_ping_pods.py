import paramiko
import json
import itertools
import random
import concurrent.futures


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
    cmd = f"oc get pods -o json -n {ns_name}"
    output = run_command(ip, cmd)[1]
    pods = json.loads(output)['items']
    running_pods = list()
    for _pod in pods:
        if _pod['status']['phase'] == 'Running':
            running_pods.append(_pod)
    random.shuffle(running_pods)
    results = list()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        for c_pod, s_pod in itertools.permutations(running_pods[:3], 2):
            cmd = f"oc exec -it {c_pod['metadata']['name']} -n {ns_name} -- " \
                  f"ping -c 1 {s_pod['status']['podIP'] }"
            results.append(executor.submit(run_command, ip, cmd))
    results = [_r.result() for _r in results]
    rcs = [_r[0] for _r in results]
    print(rcs)
    import pdb; pdb.set_trace()

