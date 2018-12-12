# Developer Guides
This developer guide is intended to describe the use the following libraries
- Python JMQT Server using **pyjmqt.server**
- Python JMQT client using **pyjmqt.client**
- Web browser client using **jsclient**
- Load balancer using **[PumpkinLB](https://github.com/kata198/PumpkinLB)**

## Directory Structure
This directory contains the sample projects which use the above libraries. 
1. **sample_server.py** : Python 3.6 code which uses the **pyjmqt.server** library to implement a JMQT server. A .conf file is required which contains the server configuraion:
   - **server.conf** : Configuration file for the **pyjmqt.server** library.
2. **sample_client.py** : Python 2.7 code which uses the **pyjmqt.client** library to implement a JMQT client. A .conf file is required which contains the client configuraion:
   - **client.conf** : Configuration file for the **pyjmqt.client** library.
3. **sample_angularjs_client** : Web Application written in Angular JS 1.6.5 which uses the **jsclient** library.
4. **sample_load_balancer.py** : Python 3.6 code which uses the **PumpkinLB** library to implement a JMQT load balancer. A .conf file is required which contains the load balancer configuraion:
   - **load_balancer.conf** : Configuration file for the **pyjmqt.client** library.

## 1. sample_server.py
### 1.a. import the Server class
To start with, first we include the pyjmqt.server API into our code (line 30 - 32)
```
from pyjmqt.server.api import Server
```
### 1.b. Define the application class
We have defined a **class** which contains all the functions and properties are needed to implement the pyjmqt.server library (line 35) :
```
class MyJMQTApp():
```
The **constructor** of this class takes the asyncio event loop as an arguement (line 37):
```
def __init__(self, loop):
```
### 1.c. Create the server (Object of the Server class)
Inside the constructor, we pass the path of the **config file** (server.conf file) and the **asyncio event loop** to create an object of the **Server** (line 44). This event loop is passed by the 'main' snippet of the code (see section '1.h. Start and Stop the server'):
```
self.server = Server(self.loop, self.configFile)
```
### 1.d. Callbacks
Next, we must register the **callbacks** which will be used by the 'Server' for any future events (line 48 - 57). There are total **8** callbacks, and all are **mandatory**.
```
self.server.set_authentication_validator(self.validate_auth)
self.server.set_connection_validator(self.validate_conn)
self.server.set_subscription_validator(self.validate_sub)
self.server.set_publish_validator(self.validate_pub)
self.server.set_control_channel_handler(self.control_packet_handler)
self.server.set_unsubscription_validator(self.validate_unsub)
self.server.set_disconnection_notifier(self.disconnection_notifier)
self.server.set_conn_close_notifier(self.conn_close_notifier)
```
These callbacks functions must be **async** functions. These functions are defined in the **MyJMQTApp** class. The **input parameres and return types are well defined** in the function body. For example, if we see the body of the **validate_auth** function, the following snippet (line 72 - 83) contains the definition of the parameters and return types.
```
async def validate_auth(self, auth_data, remote_host, protocol):
    """
    Validates authentication request.

    Called when a client sends auth request. This function must authenticate the client and return
    authentication status with client id and optional message (reason why authenctication is not OK)

    :param auth_data: Authentication data sent by the client (any, usually dictionary)
    :param remote_host: <IP>:<Port> the client is connecting from (string)
    :param protocol: Protocol which the client is connecting from (string)
    :return: returns a tuple with status code (boolean), client id (string), auth token(string) and messagse (string)
            message can be blank, it must contain the reason if the authentication failes
    """
```
All other callback function works in the same way. To have a detailed understanding of the callbacks, please check the function description for each of the registered callback functions.
### 1.e. Use the logger
The server API contains a logger which can be accessed by the user code. The following snippet is used to access the logger
```
self.logger = self.server.get_logger()
```
To log a message using the logger, we can use 
```
self.logger.log_debug('This is a debug message', 'MyJMQTApp')
self.logger.log_info('This is an info', 'MyJMQTApp')
self.logger.log_warning('Sample Warning!', 'MyJMQTApp')
self.logger.log_error('Fatal Error', 'MyJMQTApp')
```
The first parameter of the log functions is the message to log and the second paramters is a tag to identify the source of the of the message. Please note, the path of the log file and log mode is controlled by the 'server.conf' file.
### 1.f. Configuration file (server.conf)
The **server.conf** file contains the configuration paramters to run the server. We must pass the path of this file while creating the object of the 'Server' class in step C. If no configuratin file is passed, the server will use the default configuration. The default configuration is same as the configuration provided in **server.conf**.

### 1.g. Get Configuration Values
It is possible to fetch any configuration paramter from the user code. To do that, we first use the following snippet to get the configuration paramters as a dictionary
```
self.serverConfig = self.server.get_server_config()
```
Then we can access any parameter as shown below 
```
socketPort = self.serverConfig['SOCKET_PORT']
```
### 1.h. Start and Stop the server
There are two functions defined in 'MyJMQTApp' class (line 225 -237) which handles the start and stop operations. 
```
    def start(self):
        self.logger.log_info('Server start', 'MyJMQTApp')
        self.server.start()
    
    def stop(self):
        self.logger.log_info('Server stop', 'MyJMQTApp')
        self.server.stop()
```
From the **main** snippet of the code, we create an object of MyJMQTApp passing the **event loop** to the constructor. Then we call the start function, run the event loop, wait for a keyboard interrupt (ctrl + C) and call the stop function when an interrupt is received (line 239 - 252)
```
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    myApp = MyJMQTApp(loop)
    myApp.start()
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    myApp.stop()
```
To run the server, simply execute the following command in a terminal 
```
python3 sampler_server.py
```
### 1.i. Distributed Environment
To run the server in a **distributed** environment using load balancer, the **Redis** and **MySQL** must be enabled in the server.conf file. 

To enable Redis, "ENABLE_REDIS" field must be set to 1 and the "REDIS" related fields must be uncommented : 
```
ENABLE_REDIS = 1
# uncomment following settings if REDIS is enabled
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB_INDEX = 0
REDIS_PASSWORD = ""
```

To enable MySql, "ENABLE_MYSQL" field must be set to 1 and the "MYSQL" related fields must be uncommented : 
```
ENABLE_MYSQL = 1
# uncomment following settings if MYSQL is enabled
MYSQL_DB = "jmqt_core"
MYSQL_HOST = "localhost"
MYSQL_PORT = 3306
MYSQL_PSWD = ""
MYSQL_USER = "root"
```
Distriuted environment needs a load balancer. For the guide to implement a load balancer, see section '4. load_balancer.py' of this document.

### 1.j. Enabling SSL
To enable SSL, first we need the server side SSL key and certificate files. These files can be self prepared using OpenSSL or can be assigned by a certificate authority. To prepare own certificates, follow the instructions given in **certificates.md**. Please note, to enable SSL on WebSocket using WSS (WebSocket Secure) and release the application for global use, the certificates must be retrived from a Certificate Authotiry, otherwise the browsers won't be able to use the WSS protocol.

To enable the SSL, "ENABLE_SSL" field must be set to 1 and "SSL" related fields must be uncommented :
```
ENABLE_SSL = 1
# uncomment following settings if SSL is enabled
# path of the ssl certificate and key files
SSL_CERT_PATH = "server.crt"
SSL_KEY_PATH = "server.key"
# port numbers for SSL connections on SOCKET and WEBSOCKET
SSL_SOCKET_PORT = 8011
SSL_WEBSOCKET_PORT = 8013
```
