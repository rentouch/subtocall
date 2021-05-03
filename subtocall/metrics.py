import logging
from prometheus_client.twisted import MetricsResource
from twisted.web.server import Site
from twisted.web.resource import Resource
from twisted.internet.error import CannotListenError
from twisted.internet import reactor
from prometheus_client import Counter, Summary

log = logging.getLogger("subtocall")

root = Resource()
root.putChild(b'metrics', MetricsResource())

factory = Site(root)
try:
    reactor.listenTCP(8910, factory)
except CannotListenError as e:
    log.error("ERROR: metrics: %s" % e)

NAMESPACE = 'pip_subtocall'

REDIS_PUSHS = Counter(
   '%s_redis_push_total' % NAMESPACE,
   'Counter (int) of outgoing redis push (queue entry)'
)

SUB_RECV_TIME = Summary(
    f"{NAMESPACE}_sub_recv_time",
    "Time it took until an event got received by this service from (subscription)"
)
