import os

# URL to crossbar
WAMP_URL = os.getenv('WAMP_URL', 'ws://crossbar')

# crossbar realm
CROSSBAR_REALM = os.getenv('REALM', 'realm1')

# For WAMP-CRA authentication
BACKEND_USERNAME = os.getenv('BACKEND_USERNAME', 'backend')
BACKEND_SECRET = os.getenv('BACKEND_SECRET', '1234')

# If you want to use the redis message-queue instead of the wamp load-balancer
USE_REDIS_MQ = os.getenv('USE_REDIS_MQ', False)

# URL to redis
REDIS_HOST = os.getenv('REDIS_HOST', 'redis-queue')

# Port of redis
REDIS_PORT = os.getenv('REDIS_PORT', 6379)
REDIS_PORT = int(REDIS_PORT)