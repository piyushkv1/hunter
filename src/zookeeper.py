from kazoo.client import KazooClient


class Zookeeper:
    def __int__(self, ip, port):
        self.ip = ip
        self.port = port
        self.client = KazooClient(hosts=ip)

    def replace_value(self, ):
        pass