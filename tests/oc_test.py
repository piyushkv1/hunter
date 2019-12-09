import paramiko
import concurrent.futures

INPUT_YAML = "http://w3-dbc302.eng.vmware.com/piyushv/inputyaml"
NS = "myns"


def run_command(ip, cmd):
    with paramiko.SSHClient() as ssh:
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username='root', password='ca$hc0w')
        print(f"Running command {cmd} in {ip}")
        stdin, stdout, stderr = ssh.exec_command(cmd)
        stdin.flush()
        stdin.channel.shutdown_write()
        stdout.channel.settimeout(1)
        stderr.channel.settimeout(1)
        exit_code = stdout.channel.recv_exit_status()
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        if exit_code:
            raise Exception("Command:%s failed on %s: %s" % (cmd, ip, error))
        return output


def print_values(a, b):
    print(f"{a} {b}")


def create_ns_setup(ns_index):
    i = ns_index
    # ips = ['10.144.137.96', '10.144.137.193']
    ips = ["10.144.138.195"]
    with concurrent.futures.ProcessPoolExecutor() as executor:
        cmd = f"oc new-project {NS}-{i}; sleep 2;" \
              f"oc adm policy add-scc-to-user anyuid -z default -n {NS}-{i}"
        tuple(executor.map(run_command, ips, [cmd] * len(ips)))
    with concurrent.futures.ProcessPoolExecutor() as executor:
        cmd = f"oc apply -f {INPUT_YAML}/service/tcp-svc-lb.yml -n {NS}-{i}"
        tuple(executor.map(run_command, ips, [cmd] * len(ips)))
    with concurrent.futures.ProcessPoolExecutor() as executor:
        cmd = f"oc apply -f " \
              f"{INPUT_YAML}/oc/one-route-path-no-hostname.yml -n {NS}-{i}"
        tuple(executor.map(run_command, ips, [cmd] * len(ips)))
    with concurrent.futures.ProcessPoolExecutor() as executor:
        cmd = f"oc apply -f " \
              f"{INPUT_YAML}/oc/sec-one-route-path-no-hostname.yml -n {NS}-{i}"
        tuple(executor.map(run_command, ips, [cmd] * len(ips)))
    with concurrent.futures.ProcessPoolExecutor() as executor:
        cmd = f"oc apply -f " \
              f"{INPUT_YAML}/service/tcp-svc-np.yml -n {NS}-{i}"
        tuple(executor.map(run_command, ips, [cmd] * len(ips)))
    with concurrent.futures.ProcessPoolExecutor() as executor:
        cmd = f"oc scale rc tcp-rc --replicas=10 -n {NS}-{i}"
        tuple(executor.map(run_command, ips, [cmd] * len(ips)))


def delete_ns(ns_index):
    i = ns_index
    # ips = ['10.144.137.96', '10.144.137.193']
    ips = ["10.144.138.195"]
    with concurrent.futures.ProcessPoolExecutor() as executor:
        cmd = f"oc delete ns {NS}-{i}"
        tuple(executor.map(run_command, ips, [cmd] * len(ips)))


if __name__ == "__main__":
    with concurrent.futures.ProcessPoolExecutor() as executor:
        tuple(executor.map(create_ns_setup, range(11, 12)))
