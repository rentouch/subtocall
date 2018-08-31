import log
from autobahn.twisted.wamp import ApplicationSession
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.internet.defer import inlineCallbacks, returnValue
from autobahn.wamp.exception import ApplicationError
from autobahn.websocket.util import parse_url
from autobahn.wamp.types import SubscribeOptions
from autobahn.twisted import websocket
from autobahn.wamp import types
from twisted.internet import reactor
from autobahn.wamp import auth
from utils import WAMP_URL
from utils import BACKEND_SECRET
from utils import BACKEND_USERNAME
from utils import CROSSBAR_REALM

log = log.init_logger(use_logstash=False)

log.info("***** SubToCall started *****")


class MyComponent(ApplicationSession):

    def __init__(self, config):
        ApplicationSession.__init__(self, config)
        self.registrations = []

    def onConnect(self):
        transport_factory.resetDelay()
        self.join(self.config.realm, [u"wampcra"], BACKEND_USERNAME)

    def onChallenge(self, challenge):
        if challenge.method == u"wampcra":
            signature = auth.compute_wcs(BACKEND_SECRET,
                                         challenge.extra['challenge'])
            return signature
        else:
            raise Exception("Invalid authmethod {}".format(challenge.method))

    @inlineCallbacks
    def onJoin(self, details):
        log.info("Successfully connected and authenticated on server")
        registrations = yield self.call("wamp.registration.list")
        for reg_type in registrations:
                for reg_id in registrations[reg_type]:
                    reg = yield self.call("wamp.registration.get", reg_id)
                    if self.matches_pattern(reg['uri']):
                        self.start_track(reg_id, reg['uri'])
        yield self.subscribe(self.on_create, 'wamp.registration.on_create')
        yield self.subscribe(self.on_delete, 'wamp.registration.on_delete')
        log.debug("Subscribed to wamp procedure")

    def on_create(self, _, create_info):
        uri = create_info['uri']
        if self.matches_pattern(uri):
            self.start_track(create_info['id'], uri)

    def on_delete(self, _, reg_id):
        self.stop_track(reg_id)

    def start_track(self, reg_id, target_uri):
        reg = {'reg_id': reg_id,
               'target_uri': target_uri,
               'source_uri': target_uri.replace('SUB_', '')}
        self.registrations.append(reg)
        log.debug('start tracking %s %s' % (reg_id, reg['source_uri']))
        try:
            reg['registration'] = self.subscribe(
                self.sub_to_call,
                topic=reg['source_uri'],
                options=SubscribeOptions(match=u"wildcard", details_arg='wamp_details'))
        except Exception as e:
            log.exception(e)

    def stop_track(self, reg_id):
        for reg in self.registrations[:]:
            if reg["reg_id"] == reg_id:
                self.registrations.remove(reg)
                log.debug("stop tracking %s %s" % (reg_id, reg['source_uri']))
                try:
                    yield reg['registration'].unsubscribe()
                except Exception as e:
                    log.warning(e)
                break

    @inlineCallbacks
    def sub_to_call(self, *args, **kwargs):
        try:
            wamp_details = kwargs.pop('wamp_details')
            source_uri = wamp_details.topic
            split_pos = source_uri.find(source_uri.split('.')[-1])
            target_uri = '{0}SUB_{1}'.format(source_uri[:split_pos],
                                             source_uri[split_pos:])
            # log.debug("-> %s, %s, %s" % (target_uri, args, kwargs))
            yield self.call(target_uri, *args, **kwargs)
        except ApplicationError as e:
            log.warning(e)
        except Exception as e:
            log.exception(e)

    @staticmethod
    def matches_pattern(uri):
        return uri.split('.')[-1].startswith('SUB_')

    def onClose(self, wasClean):
        super(MyComponent, self).onClose(wasClean)
        log.info("onClose: Remove all rooms / sessions out of memory")

    def onLeave(self, details):
        log.info("Client session left: {}".format(details))
        if details.reason == "wamp.error.authentication_failed":
            reactor.callLater(5, self.onConnect)
        self.disconnect()

    def onDisconnect(self):
        log.info("Client session disconnected.")


if __name__ == "__main__":
    class MyClientFactory(websocket.WampWebSocketClientFactory,
                          ReconnectingClientFactory):
        maxDelay = 30
        last_connector = None

        def __init__(self, *args, **kwargs):
            websocket.WampWebSocketClientFactory.__init__(self, *args, **kwargs)

        def startedConnecting(self, connector):
            log.debug("Start connection attempt")
            self.last_connector = connector
            ReconnectingClientFactory.startedConnecting(self, connector)

        def clientConnectionFailed(self, connector, reason):
            self.last_connector = connector
            log.error("Client connection failed. Will try again...")
            ReconnectingClientFactory.clientConnectionFailed(
                self, connector, reason)

        def clientConnectionLost(self, connector, reason):
            self.last_connector = connector
            log.error("Client connection lost. Will try to reconnect...")
            ReconnectingClientFactory.clientConnectionLost(
                self, connector, reason)

    # create a WAMP application session factory
    component_config = types.ComponentConfig(realm=CROSSBAR_REALM)
    client = MyComponent(component_config)

    # Hack to have only one Client inst. and no client_factory
    def _get_session():
        return client

    # You can set a custom URL by setting the env. variable WAMP_URL.
    # e.g. WAMP_URL=ws://localhost:8091 python main.py
    transport_factory = MyClientFactory(_get_session, url=WAMP_URL)
    transport_factory.setProtocolOptions(autoPingInterval=2, autoPingTimeout=4)

    # Setup proper logging from Autobahn
    import txaio
    txaio.use_twisted()
    txaio.config.loop = reactor
    # txaio.start_logging(level='debug')

    # start the client from a Twisted endpoint
    isSecure, host, port, resource, path, params = parse_url(WAMP_URL)
    transport_factory.host = host
    transport_factory.port = port
    WAMP_connector = websocket.connectWS(transport_factory, timeout=5)

    reactor.run()
