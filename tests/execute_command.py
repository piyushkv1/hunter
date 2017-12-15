#!/usr/bin/env python

"""
Written by Piyush Verma
Email: piyushv@vmware.com

Helper to run command in remote
"""

import paramiko
import atexit
import requests.packages.urllib3 as urllib3
import ssl
import json
import time
from lxml import etree
from copy import deepcopy
from threading import Thread
from time import sleep

from pyVmomi import vim
from pyVim.connect import SmartConnect, Disconnect


def ipRange(start_ip, end_ip):
    start = list(map(int, start_ip.split(".")))
    end = list(map(int, end_ip.split(".")))
    temp = start
    ip_range = []

    ip_range.append(start_ip)
    while temp != end:
        start[3] += 1
        for i in (3, 2, 1):
            if temp[i] == 256:
                temp[i] = 0
                temp[i - 1] += 1
        ip_range.append(".".join(map(str, temp)))

    return ip_range


def run_command(ip, cmd):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username='root', password='ca$hc0w')
    print "Running command %s in %s" % (cmd, ip)
    return ssh.exec_command(cmd)


def get_obj(content, vimtype, name, folder=None):
    obj = None
    if not folder:
        folder = content.rootFolder
    container = content.viewManager.CreateContainerView(folder, vimtype, True)
    for item in container.view:
        if item.name == name:
            obj = item
            break
    return obj


def get_vms_name_ip():
    urllib3.disable_warnings()
    si = None
    context = None
    if hasattr(ssl, 'SSLContext'):
        context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
        context.verify_mode = ssl.CERT_NONE
    if context:
        # Python >= 2.7.9
        si = SmartConnect(host="10.112.201.213",
                          port=443,
                          user="administrator@vsphere.local",
                          pwd="Admin!23",
                          sslContext=context)
    else:
        # Python >= 2.7.7
        si = SmartConnect(host="10.112.201.213",
                          port=443,
                          user="administrator@vsphere.local",
                          pwd="Admin!23")
    atexit.register(Disconnect, si)
    print "Connected to vCenter Server"
    content = si.RetrieveContent()

    datacenter = get_obj(content, [vim.Datacenter], 'PK-Jarvis')
    cluster = get_obj(content, [vim.ClusterComputeResource], 'Cluster',
                      datacenter.hostFolder)
    host_obj = None
    for host in cluster.host:
        if host.name == "10.192.99.138":
            host_obj = host
            break
    name_ip = dict()
    for vm in host_obj.vm:
        for net in vm.guest.net:
            ipAddress = net.ipConfig.ipAddress
            for ip in ipAddress:
                if ip.ipAddress.startswith("10"):
                    name_ip[vm.name] = ip.ipAddress
                    break
    return name_ip


def get_vms_ip():
    return get_vms_name_ip().values()


def get_stopped_container(ip):
    cmd = "docker ps -aq -f status=exited"
    _, stdout, _ = run_command(ip, cmd)
    return [line.strip() for line in stdout.readlines()]


def get_stale_ports(ip):
    #c_ids = get_stopped_container(ip)
    ports = list()
    c_ids = []
    for i in range(1, 2):
        c_ids.append("container%s" % i)
    for cid in c_ids:
        cmd = "ovs-vsctl find interface external_ids:container_id=%s | grep name" % cid
        _, stdout, _ = run_command(ip, cmd)
        for line in stdout.readlines():
            port = line.split(":")[1].replace('"', '').strip()
            ports.append(port)
    return ports


def delete_stale_ports(ip):
    ports = get_stale_ports(ip)
    cmd = ""
    for port in ports:
        cmd += "ovs-vsctl del-port %s; " % port
    run_command(ip, cmd)


def delete_stopped_containers(ip):
    cmd = ""
    for cid in get_stopped_container(ip):
        cmd += "docker rm %s; " % cid
    run_command(ip, cmd)


def create_20_containers(ip, ch_index):
    for i in range(21, 111):
        cmd = "docker run -i -d --privileged --net=none --name=container%s ubuntu1604:piyushv" % i
        run_command(ip, cmd)
        cip = "192.168.%s.%s/16" % (ch_index, i)
        mac = "aa:bb:cc:dd:%s:%s" % (format(ch_index, 'x').zfill(2), format(i, 'x').zfill(2))
        cmd = "ovs-docker add-port br-int eth1 container%s --ipaddress=%s " \
              "--gateway=192.168.0.1 --macaddress=%s" % (i, cip, mac)
        run_command(ip, cmd)
        vlan = i
        cmd = "ovs-docker set-vlan br-int eth1 container%s %s" % (i, vlan)
        #run_command(deepcopy(ip), deepcopy(cmd))
        try:
            Thread(target=run_command, args=(deepcopy(ip), deepcopy(cmd))).start()
        except Exception as e:
            print "Error: unable to start process %s" % e


def create_scale_cif_ports(names_ip):
    vms = sorted(names_ip.keys())
    for ch_index in range(1, 21):
        vm = vms[ch_index-1]
        ip = names_ip[vm]
        create_20_containers(ip, ch_index)


def install_node_agent_dgo(ip):
    nsxujo_build = "7362771"
    cmds = list()
    cmds.append('set interface eth1 ofport_request=1')
    cmds.append('docker rm -f nsx-node-agent || true')
    cmds.append('docker rmi nsx-node-agent-testing || true')
    cmds.append('docker images | grep "nsx-ncp" | awk \'{print $1}\' | '
                'xargs docker rmi || true')
    cmds.append('rm -f nsx-ncp*')
    # Get runtime build based on containerhost type
    ncp_config_file = None
    ncp_image = None
    os_version = "Ubuntu"
    if 'Ubuntu' in os_version:
        ncp_config_file = 'nsx-ncp-ubuntu-2.1.0.0.0.%s.tar' % nsxujo_build
        ncp_image = '2.1.0.0.0.%s/nsx-ncp-ubuntu' % nsxujo_build
    elif 'RHEL' in os_version:
        ncp_config_file = 'nsx-ncp-rhel-2.1.0.0.0.%s.tar' % nsxujo_build
        ncp_image = '2.1.0.0.0.%s/nsx-ncp-rhel' % nsxujo_build
    cmds.append(
        'wget http://build-squid.eng.vmware.com/build/mts/'
        'release/bora-%s/publish/%s' % (nsxujo_build, ncp_config_file))
    cmds.append('docker load -i %s' % ncp_config_file)
    cmds.append('docker tag registry.local/%s '
                'nsx-node-agent-testing' % ncp_image)
    cmds.append('mkdir /etc/nsx-ujo || true')
    cmds.append('touch /etc/nsx-ujo/ncp.ini || true')
    cmds.append('mkdir /var/run/nsx-ujo || true')
    cmds.append(
        'docker run --privileged --net=host '
        '--name nsx-node-agent --entrypoint="/bin/bash" '
        '-v /etc/nsx-ujo/ncp.ini:/etc/nsx-ujo/ncp.ini '
        '-v /usr/lib/libopenvswitch.so.1:/usr/lib/libopenvswitch.so.1 '
        '-v /usr/bin/ovs-vsctl:/usr/bin/ovs-vsctl '
        '-v /var/run/openvswitch:/var/run/openvswitch '
        '-v /var/run/nsx-ujo:/var/run/nsx-ujo '
        '-v /var/run/netns:/var/run/netns '
        '-v /proc:/host/proc '
        '-d nsx-node-agent-testing '
        '-c /usr/local/bin/nsx_node_agent')
    for i in range(len(cmds)):
        run_command(ip, cmds[i])
        if i == 5 or i == 6:
            time.sleep(60)
        time.sleep(5)


def install_node_agent_dk(ip):
    nsxujo_build="6500154"
    cmds = list()
    cmds.append('set interface eth1 ofport_request=1')
    cmds.append('docker rm -f nsx-node-agent || true')
    cmds.append('docker rmi nsx-node-agent-testing || true')
    cmds.append('docker images | grep "nsx-ncp" | awk \'{print $1}\' | '
                'xargs docker rmi || true')
    cmds.append('rm -f nsx-ncp-ob-*')
    cmds.append(
        'wget http://build-squid.eng.vmware.com/build/mts/'
        'release/bora-%s/publish/'
        'nsx-ncp-ob-%s.tar' % (nsxujo_build, nsxujo_build))
    cmds.append('docker load -i nsx-ncp-ob-%s.tar' % nsxujo_build)
    cmds.append('docker tag registry.local/ob-%s/nsx-ncp '
                'nsx-node-agent-testing' % nsxujo_build)
    cmds.append('mkdir /etc/nsx-ujo || true')
    cmds.append('touch /etc/nsx-ujo/ncp.ini || true')
    cmds.append('mkdir /var/run/nsx-ujo || true')
    cmds.append(
        'docker run --privileged --net=host '
        '--name nsx-node-agent --entrypoint="/bin/bash" '
        '-v /etc/nsx-ujo/ncp.ini:/etc/nsx-ujo/ncp.ini '
        '-v /usr/lib/libopenvswitch.so.1:/usr/lib/libopenvswitch.so.1 '
        '-v /usr/bin/ovs-vsctl:/usr/bin/ovs-vsctl '
        '-v /var/run/openvswitch:/var/run/openvswitch '
        '-v /var/run/nsx-ujo:/var/run/nsx-ujo '
        '-v /var/run/netns:/var/run/netns '
        '-v /proc:/host/proc '
        '-d nsx-node-agent-testing '
        '-c /usr/local/bin/nsx_node_agent')
    for i in range(len(cmds)):
        run_command(ip, cmds[i])
        if i == 5 or i == 6:
            time.sleep(60)
        time.sleep(5)


def install_node_agent_all(vmip=dict):
    for vm in sorted(vmip.keys()):
        ip = vmip[vm]
        install_node_agent(ip)


def run_command_all_hosts(ips, cmd):
    for ip in ips:
        run_command(ip, cmd)


def kvm_running_vms(ip):
    cmd = "virsh list"
    vms = []
    _, stdout, _ = run_command(ip, cmd)
    for line in stdout.readlines()[2:-1]:
        vm = line.split()[1]
        if vm.startswith("vm"):
            vms.append(vm)
    return vms


def kvm_restart_vms(ip):
    vms = kvm_running_vms(ip)
    for vm in vms:
        cmd = "virsh destroy %s" % vm
        run_command(ip, cmd)
        cmd = "virsh start %s" % vm
        run_command(ip, cmd)


def kvm_reset_bridge(ip):
    cmd = "ovs-vsctl del-br br-int"
    run_command(ip, cmd)
    cmd = "ovs-vsctl add-br br-int;" \
          "ovs-vsctl add-port br-int eth1 -- set interface eth1 ofport=1;" \
          "ifconfig eth1 up"
    run_command(ip, cmd)


def kvm_get_vm_ip(ip):
    vms = kvm_running_vms(ip)
    vm_ip = dict()
    for vm in vms:
        cmd = "virsh domiflist %s|grep %s-00|awk '{print $NF}'" % (vm, vm)
        _, stdout, _ = run_command(ip, cmd)
        mac_addr = stdout.read().strip()
        cmd = "grep %s /var/log/arpwatch | tail -1 | grep -Pom 1 '[0-9.]{7,15}'" % mac_addr
        _, stdout, _ = run_command(ip, cmd)
        ip_addr = stdout.read().strip()
        vm_ip[vm] = ip_addr
    return vm_ip


def kvm_add_nic_vm(ip, vm):
    bridge_name = "br-int"
    dev_name = "%s-01" % vm
    eth_config = etree.Element("interface", type="bridge")
    eth_config.append(etree.Element("source", bridge="%s" % bridge_name))
    eth_config.append(etree.Element("virtualport", type="openvswitch"))
    eth_config.append(etree.Element("target", dev="%s" % dev_name))
    eth_config.append(etree.Element("model", type="virtio"))
    eth_spec = etree.tostring(eth_config, pretty_print=True)
    cmd = "echo '%s' > ethernet.xml" % eth_spec
    run_command(ip, cmd)
    cmd = "virsh attach-device %s --persistent ethernet.xml" % vm
    run_command(ip, cmd)


def kvm_add_nic_all_vms(ip):
    vms = kvm_running_vms(ip)
    for vm in vms:
        kvm_add_nic_vm(ip, vm)


def kvm_remove_nic_vm(ip, vm, mac):
    cmd = "virsh detach-interface %s bridge --mac %s --persistent" % (vm, mac)
    run_command(ip, cmd)


def kvm_vm_vif(ip):
    bridge_name = "br-int"
    vms = kvm_running_vms(ip)
    vm_vif = dict()
    for vm in vms:
        cmd = "virsh dumpxml %s|grep -A 2 %s|grep interfaceid" % (vm, bridge_name)
        _, stdout, _ = run_command(ip, cmd)
        stdout = stdout.read()
        output = stdout.lstrip().replace("<parameters interfaceid='", "")
        output = output.replace("'/>", "")
        vm_vif[vm] = output.strip()
    return vm_vif


def kvm_create_vm(ip, name):
    image = "/vms/images/k8snode-ubuntu1610-v21/k8snode-ubuntu1610-v21.img"
    cmd = "qemu-img create -f qcow2 -b %s /vms/images/%s.img" % (image, name)
    run_command(ip, cmd)
    cmd = "qemu-img info /vms/images/%s.img" % name
    run_command(ip, cmd)


def kvm_increase_run(vmip=dict):
    for vm in sorted(vmip.keys()):
        ip = vmip[vm]
        cmd = "mount -o remount,size=500M /run"
        run_command(ip, cmd)

if __name__ == "__main__":
    for ip in ["10.192.202.224"]:
        install_node_agent_dgo(ip)
