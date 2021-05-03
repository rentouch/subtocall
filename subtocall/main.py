import json
import time
from autobahn.twisted.wamp import ApplicationSession
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.internet.defer import inlineCallbacks
from autobahn.wamp.exception import ApplicationError
from autobahn.websocket.util import parse_url
from autobahn.wamp.types import SubscribeOptions
from autobahn.twisted import websocket
from autobahn.wamp import types
from twisted.internet import reactor
from autobahn.wamp import auth
from subtocall.utils import WAMP_URL
from subtocall.utils import BACKEND_SECRET
from subtocall.utils import BACKEND_USERNAME
from subtocall.utils import CROSSBAR_REALM
from subtocall.utils import USE_REDIS_MQ
from subtocall.rqueue import queue
from subtocall import log
log = log.init_logger()
from subtocall.metrics import REDIS_PUSHS, SUB_RECV_TIME

log.info("***** SubToCall started *****")


class MyComponent(ApplicationSession):

    def __init__(self, config):
        ApplicationSession.__init__(self, config)
        self.subscriptions = []

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
                try:
                    reg = yield self.call("wamp.registration.get", reg_id)
                except Exception as e:
                    log.exception(e)
                    self.leave()
                if self.matches_pattern(reg['uri']):
                    self.start_track(reg_id, reg['uri'])
        try:
            yield self.subscribe(self.on_create, 'wamp.registration.on_create')
            yield self.subscribe(self.on_delete, 'wamp.registration.on_delete')
        except Exception as e:
            log.exception(e)
            self.leave()

        # Subscribe to all events
        yield self.subscribe(
            self.sub_to_call,
            topic='ch.rentouch.piplanning',
            options=SubscribeOptions(match=u"prefix",
                                     details_arg='wamp_details'))
        number_of_procedures = len(self.subscriptions)
        log.debug(f"Subscribed to {number_of_procedures} wamp procedures")
        if number_of_procedures < 2:
            log.erro("Was not able to track at least 2 WAMP procedures -> exit!")
            reactor.stop()


    @inlineCallbacks
    def on_create(self, _, create_info):
        uri = create_info['uri']
        if self.matches_pattern(uri):
            self.start_track(create_info['id'], uri)

    @inlineCallbacks
    def on_delete(self, _, reg_id):
        self.stop_track(reg_id)

    def start_track(self, reg_id, target_uri):
        reg = {'reg_id': reg_id,
               'target_uri': target_uri,
               'main_topic': target_uri.split('.')[-2],
               'procedure': target_uri.split('.')[-1].replace('SUB_', '')}
        self.subscriptions.append(reg)
        log.debug('start tracking %s %s %s %s' % (reg_id, reg['target_uri'], reg['main_topic'], reg['procedure']))

    def stop_track(self, reg_id):
        for reg in self.subscriptions[:]:
            if reg["reg_id"] == reg_id:
                self.subscriptions.remove(reg)
                log.debug("stop tracking %s %s" % (reg_id, reg['target_uri']))
                break

    @inlineCallbacks
    def sub_to_call(self, *args, **kwargs):
        try:
            wamp_details = kwargs.pop('wamp_details')
            source_uri = wamp_details.topic
            authid = wamp_details.publisher_authid
            if source_uri == 'ch.rentouch.piplanning.heartbeat':
                return False

            topic_parts = source_uri.split('.')
            company = topic_parts[5]
            procedure = topic_parts[-1]
            api_version = topic_parts[3]

            if len(topic_parts) == 9:
                main_topic = 'board'
            elif len(topic_parts) == 8:
                main_topic = 'session'
            elif len(topic_parts) == 7:
                main_topic = 'monit'
            else:
                return False

            part_id = topic_parts[-2]
            for sub in self.subscriptions:
                if sub['main_topic'] == main_topic and \
                        sub['procedure'] == procedure:
                    # Make sure that we pass the origin of the request
                    from_backend = (wamp_details.publisher_authrole == 'backend')

                    # Construct target uri
                    target_uri = sub['target_uri']
                    split_pos = target_uri.find('..') + 1
                    target_uri = '{0}{1}{2}'.format(
                        target_uri[:split_pos], company,
                        target_uri[split_pos:])

                    if USE_REDIS_MQ:
                        data = {'procedure': procedure,
                                'target_uri': target_uri,
                                'main_topic': main_topic,
                                'args': args,
                                'from_backend': from_backend,
                                'authid': authid,
                                'kwargs': kwargs}
                        if main_topic == 'board':
                            data['kwargs']['board_id'] = part_id
                        else:
                            data['kwargs']['session_id'] = part_id
                        r_key = '%s_%s' % (api_version, 'piserver')
                        # Use different key for monitoring
                        if main_topic == 'monit':
                            r_key = 'monit'
                            SUB_RECV_TIME.observe(time.time()-args[0])
                            REDIS_PUSHS.inc()
                        else:
                            REDIS_PUSHS.inc()
                        yield queue.put(r_key, json.dumps(data))

                    else:
                        # Call target uri with arguments
                        # log.debug("-> %s, %s %s, %s, backend=%s" %
                        #           (target_uri, part_id, args, kwargs, from_backend))
                        if main_topic == 'board':
                            yield self.call(
                                target_uri, *args, board_id=part_id,
                                from_backend=from_backend, **kwargs)
                        else:
                            yield self.call(
                                target_uri, *args, session_id=part_id,
                                from_backend=from_backend, **kwargs)
                    break
        except ApplicationError as e:
            log.debug("-> %s, %s %s, %s" %
                      (target_uri, part_id, args, kwargs))
            log.warning(e)
        except Exception as e:
            log.exception(e)

    @staticmethod
    def matches_pattern(uri):
        return uri.split('.')[-1].startswith('SUB_')

    def onClose(self, wasClean):
        super(MyComponent, self).onClose(wasClean)
        log.info(f"onClose: wasClean: {wasClean}")

    def onLeave(self, details):
        log.info("Client session left: {}".format(details))
        try:
            log.debug(f'wasClean: {self.wasClean}')
            log.debug(f'wasNotCleanReason: {self.wasNotCleanReason}')
            log.debug(f'droppedByMe: {self.droppedByMe}')
        except Exception as e:
            log.exception(e)
        if details.reason == "wamp.error.authentication_failed":
            reactor.callLater(5, self.onConnect)
        self.disconnect()

    def onDisconnect(self):
        log.info("Client session disconnected.")


if __name__ == "__main__":
    class MyClientFactory(websocket.WampWebSocketClientFactory,
                          ReconnectingClientFactory):
        maxDelay = 30
        # Exit application if we fail to connect more than n-times in a row.
        # We expect the orchestrator to restart this app properly.
        failed_max = 4
        failed_counter = 0

        def __init__(self, *args, **kwargs):
            websocket.WampWebSocketClientFactory.__init__(self, *args, **kwargs)

        def startedConnecting(self, connector):
            log.debug("Start connection attempt")
            ReconnectingClientFactory.startedConnecting(self, connector)

        def clientConnectionFailed(self, connector, reason):
            if self.failed_counter >= self.failed_max:
                log.info(
                    f'failed too many times '
                    f'{self.failed_counter}/{self.failed_max}: '
                    f'Stop reactor and exit')
                reactor.stop()
                return
            self.failed_counter += 1
            log.error(f"failed {self.failed_counter} / {self.failed_max}")
            log.error("Client connection failed. Will try again...")
            ReconnectingClientFactory.clientConnectionFailed(
                self, connector, reason)

        def clientConnectionLost(self, connector, reason):
            log.error("Client connection lost. Will try to reconnect...")
            ReconnectingClientFactory.clientConnectionLost(
                self, connector, reason)

        def resetDelay(self):
            ReconnectingClientFactory.resetDelay(self)
            self.failed_counter = 0

    # create a WAMP application session factory
    component_config = types.ComponentConfig(realm=CROSSBAR_REALM)
    client = MyComponent(component_config)

    # Hack to have only one Client inst. and no client_factory
    def _get_session():
        return client

    # You can set a custom URL by setting the env. variable WAMP_URL.
    # e.g. WAMP_URL=ws://localhost:8091 python main.py
    transport_factory = MyClientFactory(_get_session, url=WAMP_URL)
    transport_factory.setProtocolOptions(autoPingInterval=10, autoPingTimeout=60)

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
