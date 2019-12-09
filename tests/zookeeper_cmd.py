from kazoo.client import KazooClient

zk = KazooClient(hosts='192.168.73.154:28976')
zk.start()
import pdb; pdb.set_trace()
test=zk.get("/testbed/launcher/0/obj")
test=zk.get("/testbed/vm/1/obj")
