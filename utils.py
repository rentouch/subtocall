import os

# URL to crossbar
WAMP_URL = os.getenv('WAMP_URL', 'ws://crossbar')

# crossbar realm
CROSSBAR_REALM = os.getenv('REALM', 'realm1')

# For WAMP-CRA authentication
BACKEND_USERNAME = os.getenv('BACKEND_USERNAME', 'backend')
BACKEND_SECRET = os.getenv('BACKEND_SECRET', '1234')
