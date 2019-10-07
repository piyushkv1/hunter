import paramiko
import concurrent.futures

# CMD = "sudo dpkg --configure -a"
# CMD = "sudo apt autoremove -y"
# CMD = "apt-get install --reinstall docker-ee docker-ee-cli containerd.io"

# CMD = "sudo apt-get remove -y docker docker-engine docker-ce docker-ce-cli docker.io -f"
# CMD = "sudo apt-get update -y"
# CMD = "apt-get install -y apt-transport-https ca-certificates curl software-properties-common"
# CMD = '''
# DOCKER_EE_URL="https://storebits.docker.com/ee/trial/sub-f927bffd-d197-4c0d-aa86-0f981b553025";
# DOCKER_EE_VERSION=19.03;
# curl -fsSL "${DOCKER_EE_URL}/ubuntu/gpg" | sudo apt-key add -;
# sudo apt-key fingerprint 6D085F96;
# sudo add-apt-repository \
#    "deb [arch=$(dpkg --print-architecture)] $DOCKER_EE_URL/ubuntu \
#    $(lsb_release -cs) \
#    stable-$DOCKER_EE_VERSION";
# '''
# CMD = "sudo apt-get update -y"
# CMD = "sudo apt-get install -y docker-ee docker-ee-cli containerd.io"
# CMD = "docker version | grep Version| head -1"
CMD = "docker swarm join --token SWMTKN-1-589z1opkspov0bzmw7mphtj3y4fsacis3eh01mkisln0gzodxa-4hnoj2a4cps4vgzye3rqccl9s 10.112.203.150:2377"


def run_command(ip):
    cmd = CMD
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
        if exit_code:
            raise Exception("Command:%s failed on %s: %s" % (cmd, ip, error))
        return output


if __name__ == "__main__":
    ips = ['10.112.202.104', '10.112.203.94', '10.112.202.194']
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = tuple(executor.map(run_command, ips))
    import pdb; pdb.set_trace()