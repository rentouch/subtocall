# SubToCall - allows shared subscriptions in crossbar / WAMP

### Attention
This is customized to fit the needs of rentouch. Therefore it has hard-coded
uri patterns inside.


## Why does this exists
WAMP does not support shared subscriptions. The issue is that when you want to
share workload on multiple instances of backend-servers you are stuck to
registrations. But you can not always use registrations. An example: Clients
which publish their status-changes to all other peers. You may
want to store the state of the client in the backend.

Having multiple backend-server instances also allow rolling upgrades without 
any downtime.

## How it does work
![overview](https://github.com/rentouch/subtocall/raw/master/doc/overview.png)

This server will check crossbar for registrations which have a defined pattern:
**com.x.y.SUB_z**. The last part of the uri has to start with 'SUB_'.

After the event reaches the subToCall server we can decide if we want to transfer
the data to the piplanning-server's via Redis or WAMP. WAMP is default, but you
tell subToCall to use Redis by setting the env variable 'USE_REDIS_MQ' to 1.

### Pro and Cons of Redis / WAMP
#### WAMP:
- (-) As we try to use shared subscriptions to lower the load on our backend, we 
introduce a (new) bottle-neck with this 'forwarder' / server.
- (+) It uses the existing infrastructure.
- (+) We do not need to add a redis-puller on piplanning-server.

#### Redis:
- (+) Does not introduce a new bottleneck as Redis can cache the events for a
short period of time.
- (-) We do not know for sure if a event got handled by piplanning-server. The
event could be lost.
- (-) The queue could get filled up heavily if all piplanning-server's crashed.
This will result in a inconsistent state (single source of truth (piplanningserver)
is not up to date)


## Installation
**Only works with Python3.x**
* pip install -r requirements.txt


## Usage
You can pass the following environment variables:
* WAMP_URL: url to crossbar (e.g. wss://demo.crossbar.com/ws/)
* CROSSBAR_REALM: crossbar-realm, default to 'realm1'
* BACKEND_USERNAME: username for WAMP-CRA authentication
* BACKEND_SECRET: secret for WAMP-CRA authentication

For more configuration checkout utils.py.
