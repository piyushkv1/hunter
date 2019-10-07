import sys; print('Python %s on %s' % (sys.version, sys.platform))
sys.path.extend(['/Users/piyushv/hunter', '/Users/piyushv/hunter/pyvmomi', '/Users/piyushv/hunter/nsx-integration-for-openshift'])

from nsx.nsx2 import NSXManager
import argparse
from prettytable import PrettyTable
# https://docs.vmware.com/en/VMware-NSX-T/index.html
import logging
import sys
logger = logging.getLogger()
logging.disable(sys.maxint)


def getargs():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip",
                        dest="ip",
                        required=True,
                        help="NSX Manager IP address")
    parser.add_argument("--user",
                        dest="user",
                        help="NSX Manager username",
                        default="admin")
    parser.add_argument("--password",
                        dest="password",
                        help="NSX Manager password",
                        default="Admin!23Admin")
    parser.add_argument("--port_id",
                        dest="port_id",
                        help='Logical switch port id')
    parser.add_argument("--ls_id",
                        dest="ls_id",
                        help='Logical switch id')
    parser.add_argument("--vif_id",
                        dest="vif_id",
                        help="VM's vnic vif id")
    parser.add_argument("--c_vlan",
                        dest="c_vlan",
                        type=int,
                        help="VLAN id of tagged container",
                        default=0)
    parser.add_argument("--c_mac",
                        dest="c_mac",
                        help="Container MAC address")
    parser.add_argument("--c_ip",
                        dest="c_ip",
                        help="Container IP address",
                       )
    parser.add_argument("--app_id",
                        dest="app_id",
                        help="Application ID for container",
                        default="default-app")
    parser.add_argument("--cif_id",
                        dest="cif_id",
                        help="The cif id used in create/delete/update"
                             "container port.")
    parser.add_argument("--vm",
                        dest="vm",
                        help="VM to list vif ids")
    supported_operations = ["logicalswitches", "logicalports", "vifs",
                            "setparent", "createcifport", "updatecifport",
                            "deletelsport", "openshiftconfiguration"]
    parser.add_argument("operation",
                        metavar="operation",
                        choices=supported_operations,
                        help="Operation to do on NSX Manager")
    return parser.parse_args()


def logicalswitches(args):
    client = NSXManager(ip=args.ip)
    results = list(client.get_logicalswitches())
    output = PrettyTable(field_names=["Logical Switch", "ID", "VNI"])
    for ls in results:
        name = ls['display_name']
        id = ls['id']
        vni = ls['vni']
        output.add_row([name, id, vni])
    print output


def logicalports(args):
    client = NSXManager(ip=args.ip)
    results = list(client.get_logicalports())
    output = PrettyTable(field_names=["Logical Port", "ID", "Logical Switch"])
    for port in results:
        name = port['display_name']
        id = port['id']
        switch = port['logical_switch_id']
        output.add_row([name, id, switch])
    print output


def vifs(args):
    client = NSXManager(ip=args.ip)
    vms = list(client.get_vms())
    vifs = [vif for vif in list(client.get_vifs())
            if vif.has_key('lport_attachment_id')]
    ports = list(client.get_logicalports())
    for port in ports:
        attachment_id = port['attachment']['id']
        for vif in vifs:
            if vif['lport_attachment_id'] == attachment_id:
                vif['ls_port_id'] = port['id']
                if port["attachment"].has_key("context") and \
                    port["attachment"]["context"]["vif_type"] == "PARENT":
                    vif['vif_type'] = "PARENT"
                else:
                    vif['vif_type'] = "Not PARENT"
    output = PrettyTable(field_names=["VM Name", "Adapter Name", "VIF ID",
                                      "Logical Port", "Parent"])
    for vm in vms:
        vm_name = vm['display_name']
        vm_id = vm['external_id']
        vm_vifs = [vif for vif in vifs if vm_id in vif['owner_vm_id']]
        for vm_vif in vm_vifs:
            vm_vif_name = vm_vif['device_name']
            vif_id = vm_vif['lport_attachment_id']
            lsp_id = vm_vif['ls_port_id']
            output.add_row([vm_name, vm_vif_name, vif_id, lsp_id,
                            vm_vif['vif_type']])
    print output


def setparent(args):
    """
    Tag vif port to parent
    :param args:
    :return:
    """
    if not args.portid:
        raise ValueError("Param: portid not defined")
    client = NSXManager(ip=args.ip)
    client.update_logicalport_parent(port_id=args.port_id)


def createcifport(args):
    if not args.cif_id:
        raise ValueError("Param: cif_id not defined")
    if not args.vif_id:
        raise ValueError("Param: vif_id not defined")
    if not args.ls_id:
        raise ValueError("Param: ls_id not defined")
    if not args.c_ip:
        raise ValueError("Param: c_ip not defined")
    if not args.c_mac:
        raise ValueError("Param: c_mac not defined")
    if not args.c_vlan:
        raise ValueError("Param: c_vlan not defined")
    client = NSXManager(ip=args.ip)
    port_id = client.create_ciflsport(ls_id=args.ls_id, vif_id=args.vif_id,
                                      cif_id=args.cif_id, c_ip=args.c_ip,
                                      c_mac=args.c_mac, c_vlan=args.c_vlan,
                                      app_id=args.app_id)
    print port_id


def updatecifport(args):
    client = NSXManager(ip=args.ip)
    client.update_ciflsport(cif_id=args.cif_id)


def deletelsport(args):
    client = NSXManager(ip=args.ip)
    client.delete_lsport(port_id=args.port_id)


def openshiftconfiguration(args):
    client = NSXManager(ip=args.ip)
    tz_name = "os-tz"
    edge_cluster = "os-edge-cluster"
    t0_router = "os-router-t0"
    pod_ip_block = "os-pod-ip-block"
    snat_ip_block = "os-snat-ip-block"
    #tz_id = client.create_tz(tz_name, "nsx")
    # edge_cluster_id = client.create_edge_cluster(edge_cluster)
    # t0_router_id = client.create_router(t0_router, edge_cluster_id, "TIER0")
    # pod_ip_block_id = client.create_ipblock(pod_ip_block, "10.15.1.0/24")
    # snat_ip_block_id = client.create_ipblock(snat_ip_block, "192.168.1.0/24")
    py_dict = {
        "tags": [
            {
                "scope": "ncp/cluster",
                "tag": "os_cluster"
            }
        ]
    }
    tz_id = "0c07493f-445b-4b47-af3b-1818206ce2f7"
    client.update_tz(tz_id, py_dict)
    # return {'tz_id': tz_id,
    #         'edge_cluster_id': edge_cluster_id,
    #         't0_router_id': t0_router_id,
    #         'pod_ip_block_id': pod_ip_block_id,
    #         'snat_ip_block_id': snat_ip_block_id}


if __name__ == '__main__':
    args = getargs()
    eval(args.operation + '(args)')