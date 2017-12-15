from nsx.nsx2 import NSXManager
import argparse
from pprint import pprint
# https://docs.vmware.com/en/VMware-NSX-T/index.html


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
                        default="default")
    parser.add_argument("--lsid",
                        dest="lsid",
                        help='The logical switch id')
    parser.add_argument("--vifid",
                        dest="vifid",
                        help="The vm's vnic vif id")
    parser.add_argument("--vlan",
                        dest="vlan",
                        type=int,
                        help="VLAN id of tagged container",
                        default=0)
    parser.add_argument("--cmac",
                        dest="cmac",
                        help="Container MAC address")
    parser.add_argument("--cip",
                        dest="cip",
                        help="Container IP address",
                       )
    parser.add_argument("--appid",
                        dest="appid",
                        help="Application ID for container",
                        default="default-app")
    parser.add_argument("--cifid",
                        dest="cifid",
                        help="The cif id used in create/delete/update container port.")
    parser.add_argument("--vm",
                        dest="vm",
                        help="VM to list vif ids")
    supported_operations = ["logicalswitches"]
    parser.add_argument("operation",
                        metavar="operation",
                        choices=supported_operations,
                        help="Operation to do on NSX Manager")
    return parser.parse_args()

if __name__ == '__main__':
    args = getargs()
    nsx = NSXManager(ip=args.ip)
    if args.operation == 'logicalswitches':
        nsx.get_logicalswitches()