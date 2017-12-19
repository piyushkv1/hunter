import argparse
from prettytable import PrettyTable
import logging
import sys
from vsphere.vc import VCenter
logger = logging.getLogger()
logging.disable(sys.maxint)


def getargs():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip",
                        dest="ip",
                        required=True,
                        help="vCenter IP address")
    parser.add_argument("--user",
                        dest="user",
                        help="vCenter username",
                        default="administrator@vsphere.local")
    parser.add_argument("--password",
                        dest="password",
                        help="vCenter password",
                        default="Admin!23")
    parser.add_argument("--port_id",
                        dest="port_id",
                        help='Logical switch port id')
    parser.add_argument("--vm",
                        dest="vm",
                        help="VM to list vif ids")
    supported_operations = ["createlinkedclone"]
    parser.add_argument("operation",
                        metavar="operation",
                        choices=supported_operations,
                        help="Operation to do on NSX Manager")
    return parser.parse_args()


def createlinkedclone(args):
    if not args.vm:
        raise ValueError("Param: vm is not defined")
    vc = VCenter(ip=args.ip)
    vm = vc.get_vm(args.vm)
    vc.create_linkedclone(vm=vm, new_vm="test")


if __name__ == '__main__':
    args = getargs()
    eval(args.operation + '(args)')