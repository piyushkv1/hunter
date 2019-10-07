import json
import yaml
import paramiko
import re

TIMEOUT=60


class SSHConnection(object):
    def __init__(self, ip, username, password):
        self.ip = ip
        self.username = username
        self.password = password
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(ip, username=self.username,
                         password=self.password, timeout=TIMEOUT)
        self.ssh.get_transport().open_session()

    def __del__(self):
        self.ssh.close()


class Kubeadm(SSHConnection):
    """
    Create k8s config
    root@sc-rdops-vm16-dhcp-244-109:/var/lib/kubelet# kubeadm config view
    api:
      advertiseAddress: 10.161.244.109
      bindPort: 6443
    authorizationModes:
    - Node
    - RBAC
    certificatesDir: /etc/kubernetes/pki
    cloudProvider: ""
    etcd:
      caFile: ""
      certFile: ""
      dataDir: /var/lib/etcd
      endpoints: null
      image: ""
      keyFile: ""
    imageRepository: gcr.io/google_containers
    kubernetesVersion: v1.8.6
    networking:
      dnsDomain: cluster.local
      podSubnet: ""
      serviceSubnet: 10.96.0.0/12
    """
    def __init__(self, ip="localhost", username="root", password="ca$hc0w"):
        super(Kubeadm, self).__init__(ip=ip, username=username,
                                      password=password)

    def init(self):
        cmd = "kubeadm init"
        options = " --apiserver-advertise-address 0.0.0.0"
        options += " --apiserver-bind-port 6443"
        options += " --pod-network-cidr 192.168.0.0/24"
        options += " --service-cidr 172.16.0.0/24"
        options += " --service-dns-domain piyush.local"
        cmd += options
        _, stdout, _ = self.ssh.exec_command(cmd)
        output = stdout.readlines()
        result = dict()
        for line in output:
            print line.strip()
            if re.match(" +kubeadm join", line):
                words = line.split()
                result['token'] = words[3]
                result['cert'] = words[-1]
        return result

    def config(self):
        cmd = "kubeadm config view"
        _, stdout, _ = self.ssh.exec_command(cmd)
        a = stdout.read()
        yaml.load(a)

    def reset(self):
        cmd = "kubeadm reset"
        self.ssh.exec_command(cmd)

    def join(self, master_ip=str, token=str, ca_cert_hash=str):
        cmd = "kubeadm join --token %s %s:6443 " % (master_ip, token)
        cmd += "--discovery-token-ca-cert-hash %s" % ca_cert_hash
        _, stdout, _ = self.ssh.exec_command(cmd)
        output = stdout.readlines()
        for line in output:
            print line.strip()
        return True

    def configure_client(self):
        cmd = "mkdir -p $HOME/.kube;" \
              "sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config;" \
              "sudo chown $(id -u):$(id -g) $HOME/.kube/config"
        _, stdout, _ = self.ssh.exec_command(cmd)
        stdout.read()


class Kubectl(SSHConnection):
    def __init__(self, ip="localhost", username="root", password="ca$hc0w"):
        super(Kubeadm, self).__init__(ip=ip, username=username,
                                      password=password)



if __name__ == '__main__':
    master = "10.161.244.109"
    minions = ["10.161.253.79"]
    kadm = Kubeadm(ip=master)
    master_config = kadm.init()
    token = master_config['token']
    cert = master_config['cert']
    import pdb; pdb.set_trace()
    for minion in minions:
        kadm = Kubeadm(ip=minion)
        kadm.join(master, token=token, ca_cert_hash=cert)
