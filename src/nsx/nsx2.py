from nsxclient import TinyClient
from pprint import pprint


class NSXManager(object):
    def __init__(self, ip=None, username='admin', password='Admin\!23Admin',
                 port=443):
        self.ip = ip
        self.username = username
        self.password = password
        self.port = port
        self.client = TinyClient(ip, username, password, port)

    def get_logicalswitches(self):
        url = "/logical-switches"
        self.client.set_url(url)
        ls_infos = self.client.get_all()
        print ls_infos

    def get_logicalports(self):
        pass

    def list_ls(self):
        ret = {}
        url = "/logical-switches"
        self.client.set_url(url)
        ls_infos = self.client.get_all()
        for ls in ls_infos:
            ret[ls["display_name"]] = ls["id"]
        pprint("ls_name: ls_id")
        pprint(ret)

    def create_cif(self):
        url = "/logical-ports"
        self.client.set_url(url)
        py_dict = {"resource_type":"LogicalPort",
                    "attachment":{
                        "attachment_type":"VIF",
                        "id":self.cif_id,
                        "context":{
                            "vif_type":"CHILD",
                            "parent_vif_id":self.host_vif,
                            "traffic_tag":self.vlan,
                            "app_id":self.app_id or self.cif_id,
                            "resource_type":"VifAttachmentContext"}
                    },
                    "admin_state":"UP",
                    "logical_switch_id":self.ls_id,
                    "address_bindings":[{"ip_address":self.ip,"mac_address":self.mac}]}
        port_id = self.client.create(py_dict)['id']
        print(port_id)


    def kvm_create_vif(self):
        url = "/logical-ports"
        self.client.set_url(url)
        vm_vif = {}
        for vm, vif in vm_vif.iteritems():
            py_dict = { "resource_type": "LogicalPort",
                        "display_name": vm,
                        "attachment": {
                            "attachment_type": "VIF",
                            "id": vif,
                        },
                        "admin_state":"UP",
                        "logical_switch_id":self.ls_id}
            port_id = self.client.create(py_dict)['id']
            print(port_id)


    def update_cif(self):
        url = "/logical-ports"
        self.client.set_url(url)
        params = {"attachment_id": self.cif_id}
        res = self.client.read(params = params)
        if res["result_count"] <1:
            raise(Exception("No such CIF %s" %self.cif_id))
        py_dict = res["results"][0]
        port_id = py_dict["id"]
        if self.ip:
            py_dict["address_bindings"][0]["ip_address"] = self.ip
        if self.mac:
            py_dict["address_bindings"][0]["mac_address"] = self.mac
        if self.host_vif:
            py_dict["attachment"]["context"]["parent_vif_id"] = self.host_vif
        if self.vlan:
            py_dict["attachment"]["context"]["traffic_tag"] = self.vlan
        if self.app_id:
            py_dict["attachment"]["context"]["app_id"] = self.app_id
        if self.ls_id:
            py_dict["logical_switch_id"] = self.ls_id
        self.client.update(port_id, py_dict)


    def delete_cif(self):
        url = "/logical-ports"
        self.client.set_url(url)
        params = {"attachment_id": self.cif_id}
        res = self.client.read(params = params)
        if res["result_count"] <1:
            raise(Exception("No such CIF %s" %self.cif_id))
        port_id = res["results"][0]["id"]
        self.client.delete(port_id, params={"detach":"true"})


    def list_cif(self):
        url = "/logical-ports"
        ret = {}
        vif_cif_info = {}
        self.client.set_url(url)
        res = self.client.read()
        for r in res['results']:
            if r.has_key("attachment") and r["attachment"].has_key("context") and r["attachment"]["context"]["vif_type"]=="CHILD":
                vif = r["attachment"]["context"]["parent_vif_id"]
                cif = r["attachment"]["id"]
                lpid = r["id"]
                info_tuple = (cif,r["attachment"], r["logical_switch_id"], r["address_bindings"])
                if vif_cif_info.has_key(vif):
                    vif_cif_info[vif].append(info_tuple)
                else:
                    vif_cif_info[vif] = [info_tuple]
                ret[cif] = lpid
        print("VIF: CIF + attachment + logical_switch_id + address")
        pprint(vif_cif_info)
        return ret


    def list_vif(self):
        url = "/fabric/virtual-machines"
        self.client.set_url(url)
        if self.vm:
            params = {"display_name": self.vm}
        else:
            params = {}
        res = self.client.read(params=params)
        vm_map = {}
        if res["result_count"] >0:
            for r in res['results']:
                vm_map[r['display_name']] = r["external_id"]
        else:
            raise(Exception("No VM %s" %self.vm))
        url = "/fabric/vifs"
        self.client.set_url(url)
        if self.vm:
            vm_id = vm_map[self.vm]
            params = {"owner_vm_id":vm_id}
        else:
            params = {}
        res = self.client.read(params=params)
        vmid_vif_map = {}
        if res["result_count"] >0:
            for r in res['results']:
                if r.has_key("lport_attachment_id"):
                    url = "/logical-ports"
                    self.client.set_url(url)
                    lsp_info = self.client.read(params={"attachment_id":r["lport_attachment_id"]})
                    if lsp_info["result_count"] == 0:
                        continue
                    p = lsp_info["results"][0]
                    if p["attachment"].has_key("context") and p["attachment"]["context"]["vif_type"]=="PARENT":
                        parent = "PARENT"
                    else:
                        parent = "Not PARENT"
                    if vmid_vif_map.has_key(r["owner_vm_id"]):
                        vmid_vif_map[r["owner_vm_id"]].append((r["device_name"],r["lport_attachment_id"],parent))
                    else:
                        vmid_vif_map[r["owner_vm_id"]] = [(r["device_name"],r["lport_attachment_id"],parent)]
        ret = {}
        for k,v in vm_map.items():
            if vmid_vif_map.has_key(v):
                ret[k] = vmid_vif_map[v]
        print("VM: vnic + vif + parent")
        pprint(ret)
        return ret


    def update_parent_vif(self):
        url = "/logical-ports"
        self.client.set_url(url)
        params = {"attachment_id": self.host_vif}
        res = self.client.read(params = params)
        if res["result_count"] <1:
            raise(Exception("No such VIF %s" %self.host_vif))
        py_dict = res["results"][0]
        port_id = py_dict["id"]
        py_dict["attachment"]["context"]={"resource_type": "VifAttachmentContext",
                                          "vif_type": "PARENT"}
        self.client.update(port_id, py_dict)


    def update_all_vif_parent(self):
        vifs = list_vif(self)
        for vif in vifs.values():
            if vif[0][2] == 'PARENT':
                print("Ignoring: %s" % vif[0][1])
                continue
            self.host_vif = vif[0][1]
            update_parent_vif(self)

    def create_20_containers(self, ip, vif_id, vm_name, ch_index):
        if not len(self.ls_id):
            raise Exception("container_ls_id args not defined")
        for i in range(1, 21):
            cmd = "docker run -i -d --privileged --net=none --name=container%s ubuntu1604:piyushv" % i
            #run_command(ip, cmd)
            cip = "192.168.%s.%s/16" % (ch_index, i)
            mac = "aa:bb:cc:dd:%s:%s" % (format(ch_index, 'x').zfill(2), format(i, 'x').zfill(2))
            cmd = "ovs-docker add-port br-int eth1 container%s --ipaddress=%s " \
                  "--gateway=192.168.0.1 --macaddress=%s" % (i, cip, mac)
            #run_command(ip, cmd)
            vlan = i
            cmd = "ovs-docker set-vlan br-int eth1 container%s %s" % (i, vlan)
            #run_command(ip, cmd)
            self.host_vif = vif_id
            self.vlan = vlan
            self.ip = cip
            self.mac = mac
            self.cif_id = vm_name + "_" + "container%s" % i
            create_cif(self)


    def create_scale_cif_ports(self):
        if not len(self.ls_id):
            raise Exception("container_ls_id args not defined")
        names_ip = dict()
        vifs = list_vif(self)
        vms = sorted(names_ip.keys())
        for ch_index in range(1, 21):
            vm = vms[ch_index-1]
            vif_id = vifs[vm][0][1]
            ip = names_ip[vm]
            create_20_containers(self, ip, vif_id, vm, ch_index)
