from pprint import pprint
from nsx_config import TinyClient
import argparse


class NSXManager(object):
    def __init__(self, ip=None, username='admin', password='Admin!23Admin',
                 cert_file=None):
        self.ip = ip
        self.username = username
        self.password = password
        self.cert_file = cert_file
        args = argparse.Namespace()
        args.mp_ip = self.ip
        args.mp_user = self.username
        args.mp_password = self.password
        args.mp_cert_file = self.cert_file
        self.client = TinyClient(args)

    def get_logicalswitches(self):
        url = "/logical-switches"
        return self.client.read(url)['results']

    def get_logicalports(self):
        url = "/logical-ports"
        return self.client.read(url)['results']

    def get_logicalport(self, params=None):
        url = "/logical-ports"
        return self.client.read(url, params=params)['results']

    def update_logicalport_parent(self, port_id=str):
        url = "/logical-ports"
        context = {"resource_type": "VifAttachmentContext",
                   "vif_type": "PARENT"}
        result = self.client.read(url + "/" + port_id)
        result["attachment"]["context"] = context
        return self.client.update("/logical-ports", port_id, result)

    def get_vms(self):
        url = "/fabric/virtual-machines"
        return self.client.read(url)['results']

    def get_vifs(self):
        url = "/fabric/vifs"
        return self.client.read(url)['results']

    def create_ciflsport(self, ls_id=str, vif_id=str, cif_id=str, c_ip=str,
                         c_mac=str, c_vlan=int, app_id=None, name=None):
        url = "/logical-ports"
        py_dict = {
            "resource_type": "LogicalPort",
            "display_name": name,
            "attachment": {
                "attachment_type": "VIF",
                "id": cif_id,
                "context": {
                    "vif_type": "CHILD",
                    "parent_vif_id": vif_id,
                    "traffic_tag": c_vlan,
                    "app_id": app_id or cif_id,
                    "resource_type": "VifAttachmentContext"
                }
            },
            "admin_state":"UP",
            "logical_switch_id": ls_id,
            "address_bindings": [{"ip_address": c_ip, "mac_address": c_mac}]
        }
        return self.client.create(url, py_dict)['id']

    def create_lsport(self, ls_id=str, vif_id=str, name=None):
        url = "/logical-ports"
        py_dict = {
            "resource_type": "LogicalPort",
            "display_name": name,
            "attachment": {
                "attachment_type": "VIF",
                "id": vif_id,
            },
            "admin_state": "UP",
            "logical_switch_id": ls_id
        }
        return self.client.create(url, py_dict)['id']

    def update_ciflsport(self, cif_id=str, ls_id=str, vif_id=str, c_ip=str,
                         c_mac=str, c_vlan=int, app_id=None):
        params = {"attachment_id": cif_id}
        py_dict = self.get_logicalport(params=params)[0]
        if not py_dict:
            raise Exception("No such CIF %s" % self.cif_id)
        port_id = py_dict["id"]
        if ls_id:
            py_dict["logical_switch_id"] = ls_id
        if vif_id:
            py_dict["attachment"]["context"]["parent_vif_id"] = vif_id
        if c_ip:
            py_dict["address_bindings"][0]["ip_address"] = c_ip
        if c_mac:
            py_dict["address_bindings"][0]["mac_address"] = c_mac
        if c_vlan:
            py_dict["attachment"]["context"]["traffic_tag"] = c_vlan
        if app_id:
            py_dict["attachment"]["context"]["app_id"] = app_id
        url = "/logical-ports"
        self.client.update(url, port_id, py_dict)

    def delete_lsport(self, port_id=str):
        url = "/logical-ports"
        self.client.delete(url, port_id, params={"detach":"true"})

    def create_tz(self, name=str, switch_name=str):
        url = "/transport-zones"
        py_dict = {
            "display_name": name,
            "host_switch_name": switch_name,
            "transport_type": "OVERLAY"
        }
        return self.client.create(url, py_dict)['id']

    def update_tz(self, tz_id=str, my_dict=dict):
        url = "/transport-zones"
        py_dict = self.client.read(url, tz_id)
        for k, v in my_dict.iteritems():
            py_dict[k] = v
        return self.client.update(url, tz_id, py_dict)

    def delete_tz(self, tz_id=str):
        url = "/transport-zones"
        self.client.delete(url, tz_id)

    def create_edge_cluster(self, name=str, tn_ids=None):
        url = "/edge-clusters"
        py_dict = {
            "display_name": name,
            "resource_type": "EdgeCluster",
            "members": []
        }
        if tn_ids and type(tn_ids) is list:
            for tn_id in tn_ids:
                member = {"transport_node_id": tn_id}
                py_dict["members"].append(member)
        return self.client.create(url, py_dict)['id']

    def delete_edge_cluster(self, edge_cluster_id=str):
        url = "/edge-clusters"
        self.client.delete(url, edge_cluster_id)

    def create_router(self, name=str, edge_cluster_id=str, type="TIER1"):
        url = "/logical-routers"
        py_dict = {
            "resource_type": "LogicalRouter",
            "display_name": name,
            "edge_cluster_id": edge_cluster_id,
            "router_type": type,
            "high_availability_mode": "ACTIVE_STANDBY"
        }
        return self.client.create(url, py_dict)['id']

    def delete_router(self, router_id):
        url = "/logical-routers"
        self.client.delete(url, router_id)

    def create_ls(self, name=str, tz_id=str):
        url = "/logical-switches"
        py_dict = {
            "transport_zone_id": tz_id,
            "replication_mode": "MTEP",
            "admin_state": "UP",
            "display_name": name
        }
        return self.client.create(url, py_dict)['id']

    def delete_ls(self, ls_id=str):
        url = "/logical-switches"
        self.client.delete(url, ls_id)

    def create_ipblock(self, name=str, cidr=str):
        url = "/pools/ip-blocks"
        py_dict = {
            "display_name": name,
            "cidr": cidr
        }
        return self.client.create(url, py_dict)['id']

    def delete_ipblock(self, ipblock_id=str):
        url = "/pools/ip-blocks"
        self.client.delete(url, ipblock_id)
