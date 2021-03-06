# JMQT 1.0 Open Source Server and Client
This GitHub repository contains an open source implementation of the [JMQT protocol version 1.0](https://shubhadeepb14.github.io/jmqt/). There are four primary modules which are freely available to use :
1. A **python based JMQT server** (with Load Balancer support for distributed environment) developed using [python asyncio](https://docs.python.org/3/library/asyncio.html) (python 3.5 or above)
2. A **python based JMQT client** (python 2.7 or above)
3. A **python load blanacer** developed using [python PumpkinLB](https://github.com/kata198/PumpkinLB) library (python 3.5 or above)
4. A **Javascript based JMQT client** which can directly run on web browsers (Angular JS 1.6.5)

## About JMQT
JMQT is a publish-subscribe based IoT and messaging protocol. JMQT protocol is open & free, and can be used without any license agreement. No one owns JMQT.

To know more about JMQT, visit [JMQT website](https://shubhadeepb14.github.io/jmqt/)

## Directory Structure
- **pyjmqt** : Python based **JMQT server, client and load balancer** libraries
  - **server** - Libary for **JMQT server** developed using [asyncio](https://docs.python.org/3/library/asyncio.html) which supports python 3.5 or above.
  - **client** - Library for **JMQT client** which supports python 2.7 or above
 - **jsclient** : Library for **JMQT client** developed using **Javascript** which can directly run on web browsers :
    - **jmqt-client.js** - Actual Javascript library file
 - **examples** : Example projects that use **pyjmqt** and **jsclient** libraries
    - **sample_angularjs_client** - **Browser based application** developed using [AngularJS 1.6.5](https://angularjs.org/) and **'jmqt-client.js'** to demonstrate JMQT functionalities
    - **sample_server.py** - Python (3.5 or above) based **JMQT server application** developed using **'pyjmqt.server'** library
    - **sample_client.py** - Python (2.7 or above) based **JMQT client application** developed using **'pyjmqt.client'** library
    - **sample_load_balancer.py** - Python (3.5 or above) based **JMQT Load Balancer** developed using **[PumpkinLB](https://github.com/kata198/PumpkinLB)**
## Features
- **pyjmqt.server** :
    1. Developed using **Python 3 asyncio** for JMQT 1.0
    2. Supports **Socket and WebSocket**
    3. Supports **SSL** on Socket and WebSocket
    4. Integration with **MySQL** or **SQLite** for storage
    5. Supports **distributed architecture** using **Redis** pub/sub
    6. Supports **load balancing** using [python PumpkinLB](https://github.com/kata198/PumpkinLB) library
- **pyjmqt.client** :
    1. Developed using **Python 2.7** for JMQT 1.0
    2. Supports **Socket** and **SSL**
    3. Requires **no additional** python libraries
    4. Supports **Linux Single Board Computers** (tested on **RaspberryPi** and **BeagleBone Black**)
- **jsclient** :
    1. Developed using plain **Javascript** for JMQT 1.0
    2. Supports **WebSocket**
    3. Requires **no additional** Javascript libraries
    4. Supports **any browser** with [WebSocket support](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)

## Requirements
- **pyjmqt.server** :
    1. **Python 3.5** or above (recommended 3.6 or above)
    2. **MySQL** (required for distributed environment) or **SQLite** for permanent storage of packets
    3. **Redis** server (required for distributed environment)
    4. Python libraries as listed in **pip_requirements/server.txt**
- **pyjmqt.client** :
    1. **Python 2.7** or above
- **jsclient** :
    - *No special requirements*
- **load balancer** :
    1. **Python 3.5** or above (recommended 3.6 or above)
    2. Python libraries as listed in **pip_requirements/load_balancer.txt**

## Running the examples and Developer Guides
For the instructions to run the examples or to read the developer guides, please open the **[examples](https://github.com/shubhadeepb14/jmqt/tree/master/examples)** directory and have a look at **[README.md](https://github.com/shubhadeepb14/jmqt/blob/master/examples/README.md)**.

## Licensing
This repository is open source and under **[MIT license](https://opensource.org/licenses/MIT)**.
