import eventlet
import time
import logging

logger = logging.getLogger('test_event')
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler('events.log')
fh.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
fh.setFormatter(formatter)
# add the handlers to logger
logger.addHandler(ch)
logger.addHandler(fh)


class RebootABC(object):
    def __init__(self, interval=1):
        self.interval = interval

    def run(self):
        i = 1
        while i <= 5:
            logger.info("Running RebootABC after %s interval" % self.interval)
            time.sleep(self.interval)
            i += 1


class GenerateReport(object):
    def __init__(self, interval=1):
        self.interval = interval

    def run(self):
        i = 1
        while i <= 5:
            logger.info("Running GenerateReport after %s interval" %
                        self.interval)
            time.sleep(self.interval)
            i += 1


class Game:
    pass


class Game():
    pass


if __name__ == '__main__':
    eventlet.monkey_patch()
    a = RebootABC()
    b = GenerateReport()
    pool = eventlet.greenpool.GreenPool()
    pool.spawn(a.run)
    pool.spawn(b.run)
    pool.waitall()

