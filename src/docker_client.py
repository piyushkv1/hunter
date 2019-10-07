import argparse
import logging
import sys
from docker import APIClient
logger = logging.getLogger()
logging.disable(sys.maxint)


def getargs():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip",
                        dest="ip",
                        required=True,
                        help="Containerhost IP address")
    parser.add_argument("--user",
                        dest="user",
                        help="username",
                        default="root")
    parser.add_argument("--password",
                        dest="password",
                        help="password",
                        default="Admin!23")
    supported_operations = ["test"]
    parser.add_argument("operation",
                        metavar="operation",
                        choices=supported_operations,
                        help="Operation to do on NSX Manager")
    return parser.parse_args()


def test():
    pass

if __name__ == '__main__':
    args = getargs()
    import pdb;pdb.set_trace()
    apiclient = APIClient(base_url="%s:1234" % args.ip)
    print apiclient