# SubToCall - allows shared subscriptions in crossbar / WAMP

## How does it work
![overview](https://github.com/rentouch/subtocall/raw/master/doc/overview.png)

This server will check crossbar for registrations which have a defined pattern:
**com.x.y.SUB_z**. The last part of the uri has to start with 'SUB_'.


## Why
WAMP does not support shared subscriptions. The issue is that when you want to
share workload on multiple instances of backend-servers you are stuck to
registrations. But you can not always use registrations. An example: Clients
which publish their status-changes to all other peers. You may
want to store the state of the client in the backend.

Having multiple backend-server instances also allow rolling upgrades without 
any downtime.


### Downsides
As we try to use shared subscriptions to lower the load on our backend, we 
introduce a (new) bottle-neck with this 'forwarder' / server.


## Installation
**Only works with Python3.x**
* pip install -r requirements.txt


## Usage
You can pass the following environment variables:
* WAMP_URL: url to crossbar (e.g. wss://demo.crossbar.com/ws/)
* CROSSBAR_REALM: crossbar-realm, default to 'realm1'
* BACKEND_USERNAME: username for WAMP-CRA authentication
* BACKEND_SECRET: secret for WAMP-CRA authentication

