import logging
import txredisapi as redis
from twisted.internet.defer import inlineCallbacks, returnValue
from utils import REDIS_HOST
from utils import REDIS_PORT
log = logging.getLogger("subtocall")


class RedisQueue(object):
    """Simple Queue with Redis Backend"""
    def __init__(self, namespace='queue'):
        self.namespace = namespace
        self.rc = None
        rc = redis.ConnectionPool(host=REDIS_HOST, port=REDIS_PORT)

        def con_established(result):
            self.rc = result
            log.info("Connection established to Redis")

        def conn_failed(f):
            log.error("Was not able to connect to Redis")
            print(f.getTraceback())

        rc.addCallback(con_established)
        rc.addErrback(conn_failed)

    @inlineCallbacks
    def put(self, key, item):
        """Put item into the queue."""
        key = '%s:%s' % (self.namespace, key)
        yield self.rc.rpush(key, item)


queue = RedisQueue()
