import atexit
import requests.packages.urllib3 as urllib3
import ssl
from pyVmomi import vim
from pyVim.connect import SmartConnect, Disconnect
import tasks
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class VCenter(object):
    def __init__(self, ip=None, username='administrator@vsphere.local',
                 password='Admin!23', port=443):
        self.ip = ip
        self.username = username
        self.password = password
        self.port = port
        urllib3.disable_warnings()
        self.si = None
        context = None
        if hasattr(ssl, 'SSLContext'):
            context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
            context.verify_mode = ssl.CERT_NONE
        if context:
            # Python >= 2.7.9
            self.si = SmartConnect(host=self.ip, port=self.port,
                                   user=self.username, pwd=self.password,
                                   sslContext=context)
        else:
            # Python >= 2.7.7
            self.si = SmartConnect(host=self.ip,port=self.port,
                                   user=self.username, pwd=self.password)
        atexit.register(Disconnect, self.si)
        logger.info("Connected to vCenter %s" % self.ip)
        self.content = self.si.RetrieveContent()

    def get_obj(self, vimtype, name, folder=None):
        obj = None
        if not folder:
            folder = self.content.rootFolder
        container = self.content.viewManager.CreateContainerView(
            folder, vimtype, True)
        for item in container.view:
            if item.name == name:
                obj = item
                break
        return obj

    def get_datacenter(self, name):
        return self.get_obj([vim.Datacenter], name)

    def get_cluster(self, name, dcname):
        dc = self.get_datacenter(dcname)
        return self.get_obj([vim.ClusterComputeResource], name, dc.hostFolder)

    def get_host(self, name):
        return self.get_obj([vim.HostSystem], name)

    def get_vm(self, name):
        return self.get_obj([vim.VirtualMachine], name)

    def create_vm_snapshot(self, vm, name=None, memory=False,
                           quiesce=False):
        if not name:
            name = "hunter-snapshot"
        task = vm.CreateSnapshot_Task(name=name, memory=memory,
                                      quiesce=quiesce)
        tasks.wait_for_tasks(self.si, [task])
        return task.info.result

    def create_linkedclone(self, vm, new_vm=str, host=None, poweron=True):
        if not len(vm.rootSnapshot):
            self.create_vm_snapshot(vm)
        snapshot = vm.rootSnapshot[0]
        while len(snapshot.childSnapshot):
            snapshot = snapshot.childSnapshot[0]
        relospec = vim.vm.RelocateSpec()
        relospec.diskMoveType = 'createNewChildDiskBacking'
        if not host:
            host = vm.summary.runtime.host
        relospec.host = host
        relospec.pool = host.parent.resourcePool
        clone_spec = vim.vm.CloneSpec()
        clone_spec.powerOn = poweron
        clone_spec.location = relospec
        clone_spec.snapshot = snapshot
        folder = host.parent.parent.parent.vmFolder
        task = vm.CloneVM_Task(folder, new_vm, clone_spec)
        tasks.wait_for_tasks(self.si, [task])
        return task.info.result

    def create_clone(self, vm, new_vm=str, host=None, poweron=True):
        relospec = vim.vm.RelocateSpec()
        relospec.diskMoveType = 'createNewChildDiskBacking'
        if not host:
            host = vm.summary.runtime.host
        relospec.host = host
        relospec.pool = host.parent.resourcePool
        clone_spec = vim.vm.CloneSpec()
        clone_spec.powerOn = poweron
        clone_spec.location = relospec
        folder = host.parent.parent.parent.vmFolder
        task = vm.CloneVM_Task(folder, new_vm, clone_spec)
        tasks.wait_for_tasks(self.si, [task])
        return task.info.result