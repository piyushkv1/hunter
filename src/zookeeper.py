from kazoo.client import KazooClient
import argparse


def getargs():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip",
                        dest="ip",
                        required=True,
                        help="ZK Server IP address")
    parser.add_argument("--port",
                        dest="port",
                        required=True,
                        help="ZK Server port number")
    return parser.parse_args()


if __name__ == '__main__':
    args = getargs()
    print args.ip
    zk = KazooClient(hosts='%s:%s' % (args.ip, args.port))
    zk.start()
    import pdb; pdb.set_trace()
    data = zk.get("/testbed/launcher/0/obj")
    new_data = data[0].replace('10.112.199.190', '127.0.0.1')
    zk.set("/testbed/launcher/0/obj", new_data)