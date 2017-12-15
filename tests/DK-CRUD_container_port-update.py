#!/usr/bin/env python

"""
Written by Piyush Verma
Email: piyushv@vmware.com

Container port helper
"""

import ssl
import sys
import argparse
import base64
from urllib import urlencode
import json
import httplib
from pprint import pprint


class TinyClient(object):
    # For single thread use only, no sync inside.
    DEFAULT_VERSION = 'v1'

    def __init__(self, mp_ip, mp_user='admin', mp_password='Admin\!23Admin', port=443):
        self.mp_ip = mp_ip
        self.mp_user = mp_user
        self.mp_password = mp_password
        self.port = port

        self.content_type = "application/json"
        self.accept_type = "application/json"
        self.response = None
        self.url_prefix = "/api/" + self.DEFAULT_VERSION
        self.auth = base64.urlsafe_b64encode(self.mp_user + ':' + self.mp_password).decode('ascii')
        self.headers = {'Authorization': 'Basic %s' % self.auth,
                        'content-type': self.content_type}
        self.set_url(None)
        self._connect()

    def _connect(self):
        if sys.version_info >= (2,7,9):
            ctx = ssl._create_unverified_context()
            self.connection = httplib.HTTPSConnection(self.mp_ip, self.port, context=ctx, timeout=30000)
        else:
            self.connection = httplib.HTTPSConnection(self.mp_ip, self.port, timeout=30000)

    def _close(self):
        self.connection.close()

    def _request(self, method, endpoint, payload="", url_parameters=None):
        url_params_string = ""
        if url_parameters:
            if "?" in endpoint:
                url_params_string = "&%s" % urlencode(url_parameters)
            else:
                url_params_string = "?%s" % urlencode(url_parameters)
        request = "%s%s%s" % (self.url_prefix, endpoint, url_params_string)
        print("DEBUG _request: %s %s" %(method, request))
        if payload:
            print("DEBUG _payload: %s" %payload)
        self.connection.request(method, request, payload, self.headers)
        self.response = self.connection.getresponse()
        return self.response

    def request(self, method, endpoint, payload="", params={}):
        if type(payload) is not str:
            payload = json.dumps(payload)
        response = self._request(method, endpoint, payload, url_parameters=params)
        print("DEBUG: http status code %s" %response.status)
        # object not found
        if method == 'GET' and response.status == 404:
            return None
        result_string = response.read()
        # DELETE response body is empty
        py_dict = json.loads(result_string) if result_string else {}
        if response.status < 200 or response.status >= 300 or "error_code" in py_dict:
            raise Exception(py_dict)
        else:
            return py_dict

    def create(self, py_dict, params={}):
        if not self.create_url:
            self.create_url = self.url
        return self.request('POST', self.create_url, payload= py_dict, params=params)

    def read(self, object_id=None, params={}):
        if not self.read_url:
            self.read_url = self.url
        if object_id:
            return self.request('GET', "%s/%s" %(self.read_url, object_id), params=params)
        else:
            return self.request('GET', self.read_url, params=params)

    def update(self, object_id, py_dict, params={}):
        if not self.update_url:
            self.update_url = self.url
        return self.request('PUT', "%s/%s"  %(self.update_url, object_id), py_dict, params=params)

    def delete(self, object_id, params={}):
        if not self.delete_url:
            self.delete_url = self.url
        return self.request("DELETE", "%s/%s" %(self.delete_url, object_id), params=params)
    
    def set_url(self, url, create_url = None, read_url = None, update_url = None, delete_url = None):
        self.url = url
        self.create_url = None
        self.read_url = None
        self.update_url = None
        self.delete_url = None

    def get_all(self, params={}):
        res = self.read(params=params)
        if res:
            return res['results']
        else:
            return []

    def get_one_id(self, name, params={}):
        res = None
        all = self.get_all(params=params)
        for r in all:
            if r['display_name'] == name:
                res = r['id']
                break
        return res


doable = [
          "create_cif",
          "delete_cif",
          "update_cif",
          "list_cif",
          "list_vif",
          "update_parent_vif",
          "list_ls",
          ]

def getargs():
    parser = argparse.ArgumentParser()


    parser.add_argument('--mp',
                        dest="mp_ip",
                        default="",
                        help='The MP IP',
                       )
    parser.add_argument('--mp_user',
                        dest="mp_user",
                        default="admin",
                        help='The MP User',
                       )
    parser.add_argument('--mp_password',
                        dest="mp_password",
                        default="default",
                        help='The MP Password',
                       )
    parser.add_argument('--container_ls_id',
                        dest="ls_id",
                        default="",
                        help='The logical switch id for container port. If it is provided, you can ignore container_ls',
                       )
    parser.add_argument('--host_vif',
                        dest="host_vif",
                        default="",
                        help='The vnic host vif id. If use --do list_vif to get it',
                       )
    parser.add_argument('--vlan',
                        dest="vlan",
                        type=int,
                        default=0,
                        help='The vlan id that is tagging container packet.',
                       )
    parser.add_argument('--mac',
                        dest="mac",
                        default="",
                        help='The mac address that container holds',
                       )
    parser.add_argument('--ip',
                        dest="ip",
                        default="",
                        help='The ip address that container holds',
                       )
    parser.add_argument('--app_id',
                        dest="app_id",
                        default="",
                        help='The app id that container holds',
                       )
    parser.add_argument('--cif_id',
                        dest="cif_id",
                        default="",
                        help='The cif id used in create/delete/update container port.',
                       )
    parser.add_argument('--vm',
                        dest="vm",
                        default='',
                        help='Optional. On which VM to list VIF',
                       )
    parser.add_argument('--do',
                        dest="do",
                        default='',
                        metavar='<actions>',
                        help='Choose only one of doable actions: '+ ','.join(doable),
                       )

    g_args = parser.parse_args()
    if g_args.do not in doable:
        raise(Exception("Invalid doable action %s" %g_args.do))
    return g_args
mp_client = None


def _handle_mp(g_args):
    mp_ip = g_args.mp_ip
    mp_user = g_args.mp_user
    mp_password = g_args.mp_password
    global mp_client
    mp_client = TinyClient(mp_ip, mp_user, mp_password)


def list_ls(g_args):
    ret = {}
    url = "/logical-switches"
    mp_client.set_url(url)
    ls_infos = mp_client.get_all()
    for ls in ls_infos:
        ret[ls["display_name"]] = ls["id"]
    pprint("ls_name: ls_id")
    pprint(ret)


def create_cif(g_args):
    url = "/logical-ports"
    mp_client.set_url(url)
    py_dict = { "resource_type":"LogicalPort",
                "attachment":{
                    "attachment_type":"VIF",
                    "id":g_args.cif_id,
                    "context":{
                        "vif_type":"CHILD",
                        "parent_vif_id":g_args.host_vif,
                        "traffic_tag":g_args.vlan,
                        "app_id":g_args.app_id or g_args.cif_id,
                        "resource_type":"VifAttachmentContext"}
                },
                "admin_state":"UP",
                "logical_switch_id":g_args.ls_id,
                "address_bindings":[{"ip_address":g_args.ip,"mac_address":g_args.mac}]}
    port_id = mp_client.create(py_dict)['id']
    print(port_id)


def kvm_create_vif(g_args):
    url = "/logical-ports"
    mp_client.set_url(url)
    vm_vif = {}
    for vm, vif in vm_vif.iteritems():
        py_dict = { "resource_type": "LogicalPort",
                    "display_name": vm,
                    "attachment": {
                        "attachment_type": "VIF",
                        "id": vif,
                    },
                    "admin_state":"UP",
                    "logical_switch_id":g_args.ls_id}
        port_id = mp_client.create(py_dict)['id']
        print(port_id)


def update_cif(g_args):
    url = "/logical-ports"
    mp_client.set_url(url)
    params = {"attachment_id": g_args.cif_id}
    res = mp_client.read(params = params)
    if res["result_count"] <1:
        raise(Exception("No such CIF %s" %g_args.cif_id))
    py_dict = res["results"][0]
    port_id = py_dict["id"]
    if g_args.ip:
        py_dict["address_bindings"][0]["ip_address"] = g_args.ip
    if g_args.mac:
        py_dict["address_bindings"][0]["mac_address"] = g_args.mac
    if g_args.host_vif:
        py_dict["attachment"]["context"]["parent_vif_id"] = g_args.host_vif
    if g_args.vlan:
        py_dict["attachment"]["context"]["traffic_tag"] = g_args.vlan
    if g_args.app_id:
        py_dict["attachment"]["context"]["app_id"] = g_args.app_id
    if g_args.ls_id:
        py_dict["logical_switch_id"] = g_args.ls_id
    mp_client.update(port_id, py_dict)


def delete_cif(g_args):
    url = "/logical-ports"
    mp_client.set_url(url)
    params = {"attachment_id": g_args.cif_id}
    res = mp_client.read(params = params)
    if res["result_count"] <1:
        raise(Exception("No such CIF %s" %g_args.cif_id))
    port_id = res["results"][0]["id"]
    mp_client.delete(port_id, params={"detach":"true"})


def list_cif(g_args):
    url = "/logical-ports"
    ret = {}
    vif_cif_info = {}
    mp_client.set_url(url)
    res = mp_client.read()
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


def list_vif(g_args):
    url = "/fabric/virtual-machines"
    mp_client.set_url(url)
    if g_args.vm:
        params = {"display_name": g_args.vm}
    else:
        params = {}
    res = mp_client.read(params=params)
    vm_map = {}
    if res["result_count"] >0:
        for r in res['results']:
            vm_map[r['display_name']] = r["external_id"]
    else:
        raise(Exception("No VM %s" %g_args.vm))
    url = "/fabric/vifs"
    mp_client.set_url(url)
    if g_args.vm:
        vm_id = vm_map[g_args.vm]
        params = {"owner_vm_id":vm_id}
    else:
        params = {}
    res = mp_client.read(params=params)
    vmid_vif_map = {}
    if res["result_count"] >0:
        for r in res['results']:
            if r.has_key("lport_attachment_id"):
                url = "/logical-ports"
                mp_client.set_url(url)
                lsp_info = mp_client.read(params={"attachment_id":r["lport_attachment_id"]})
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


def update_parent_vif(g_args):
    url = "/logical-ports"
    mp_client.set_url(url)
    params = {"attachment_id": g_args.host_vif}
    res = mp_client.read(params = params)
    if res["result_count"] <1:
        raise(Exception("No such VIF %s" %g_args.host_vif))
    py_dict = res["results"][0]
    port_id = py_dict["id"]
    py_dict["attachment"]["context"]={"resource_type": "VifAttachmentContext",
                                      "vif_type": "PARENT"}
    mp_client.update(port_id, py_dict)


def update_all_vif_parent(g_args):
    vifs = list_vif(g_args)
    for vif in vifs.values():
        if vif[0][2] == 'PARENT':
            print("Ignoring: %s" % vif[0][1])
            continue
        g_args.host_vif = vif[0][1]
        update_parent_vif(g_args)


def create_20_containers(g_args, ip, vif_id, vm_name, ch_index):
    if not len(g_args.ls_id):
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
        g_args.host_vif = vif_id
        g_args.vlan = vlan
        g_args.ip = cip
        g_args.mac = mac
        g_args.cif_id = vm_name + "_" + "container%s" % i
        create_cif(g_args)


def create_scale_cif_ports(g_args):
    if not len(g_args.ls_id):
        raise Exception("container_ls_id args not defined")
    names_ip = dict()
    vifs = list_vif(g_args)
    vms = sorted(names_ip.keys())
    for ch_index in range(1, 21):
        vm = vms[ch_index-1]
        vif_id = vifs[vm][0][1]
        ip = names_ip[vm]
        create_20_containers(g_args, ip, vif_id, vm, ch_index)


if __name__ == '__main__':
    g_args = getargs()
    _handle_mp(g_args)
    c = g_args.do + "(g_args)"
    eval(c) 

    print("done")
