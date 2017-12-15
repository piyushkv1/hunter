from kazoo.client import KazooClient

zk = KazooClient(hosts='192.168.73.142:2259')
zk.start()
test=zk.get("/testbed/launcher/0/obj")
import pdb; pdb.set_trace()
