# Developer Guides
This developer guide is intended to describe the use the following libraries
- Python JMQT Server using **pyjmqt.server**
- Python JMQT client using **pyjmqt.client**
- Web browser client using **jsclient**
- Load balancer using **[PumpkinLB](https://github.com/kata198/PumpkinLB)**

## Default Ports
Below is the list of the TCP port numbers used by the example applications (as specified in the JMQT 1.0 Specifications)
-  8010 : Plain Socket
-  8011 : Plain WebSocket
-  8012 : SSL Socket
-  8013 : SSL WebSocket

## Run the examples
To run the examples, make sure that the requirements as mentioned in the [README.md](https://github.com/shubhadeepb14/jmqt/blob/master/README.md) are installed and configured. By default, we do not need Redis or MySQL to run the examples, as the example server uses SQLite Database by default. We also do not need any SSL certificates as the SSL is by default disabled in example server and clients. The clients (python client and browser application) are configured to the default ports in 'localhost' with SSL disabled.

Before executing the following commands, please make sure you are in the 'examples' directory.

### Run the Server
To run the server, execute the following command in a terminal :
```
python3 sample_server.py
```
The output will look something like the following :
```
12-15 10:30:08 [JMQTServer] INF : Loading config "server.conf"
12-15 10:30:08 [JMQTServer:ConnectionHandler] INF : MySQL/MariaDb is disabled. Switching to SQLite..
12-15 10:30:09 [JMQTServer:SQLiteService] INF : Connecting SQLite Db jmqt.db
12-15 10:30:09 [JMQTServer:CacheService] INF : Redis is disabled. Skip connection..
12-15 10:30:09 [JMQTServer:MyJMQTApp] INF : Server Start
12-15 10:30:09 [JMQTServer:MyJMQTApp] INF : Server start
12-15 10:30:09 [JMQTServer:SOCKET] INF : Listening on tcp 8010
12-15 10:30:09 [JMQTServer:WEB_SOCKET] INF : Listening on tcp 8012
```
If the output looks like the above, it means that the server has been started properly.

### Run the Python Client
To run the python client, execute the following command in a terminal :
```
python3 sample_client.py
```
The output will look something like the following :
```
12-15 10:33:48 [JMQTClient] INF : Loading config "client.conf"
12-15 10:33:48 [JMQTClient] INF : [MAIN] Start initiated..
12-15 10:33:49 [JMQTClient] INF : [MAIN] Retry auth..
12-15 10:33:49 [JMQTClient] INF : [MAIN] Requesting auth with client name 'pyclient1'
12-15 10:33:49 [JMQTClient] INF : Opening socket localhost:8010
12-15 10:33:49 [JMQTClient] INF : Read started
12-15 10:33:49 [JMQTClient] INF : Socket opened localhost:8010
12-15 10:33:49 [JMQTClient] INF : auth..
12-15 10:33:49 [JMQTClient] INF : authAck, status 1
12-15 10:33:49 [JMQTClient] INF : [MAIN] Auth status OK
12-15 10:33:49 [JMQTClient] INF : [MAIN] Requesting conn with client id 'pyclient1'
12-15 10:33:49 [JMQTClient] INF : conn..
12-15 10:33:49 [JMQTClient] INF : connAck, status 1
12-15 10:33:49 [JMQTClient] INF : HB started
12-15 10:33:49 [JMQTClient] INF : [Main] Data on 'update' from  : {'online': 'pyclient1'} (QOS 0, RETAIN 0)
12-15 10:33:49 [JMQTClient] INF : [MAIN] Conn status 1
12-15 10:33:49 [JMQTClient] INF : [MAIN] Requesting sub to channel 'mychannel'
12-15 10:33:49 [JMQTClient] INF : sub 'mychannel' persistent 1
12-15 10:33:49 [JMQTClient] INF : [Main] Data on 'ch' from pyclient1 : 2018-12-06 12:33:36.414643 (QOS 0, RETAIN 1)
12-15 10:33:49 [JMQTClient] INF : [MAIN] Sub to channel 'mychannel' status 1
12-15 10:33:59 [JMQTClient] INF : [MAIN] Pub dummy data on 'mychannel'
```
If the output looks like the above, it means that the client has been started properly. This client will have a client id as 'pyclient1' by default and will send a dummy data to channel 'mychannel' in every 10 seconds.

### Run the Web Client
To run the web client, first 'cd' to the 'sample_angularjs_client' directory
```
cd sample_angularjs_client
```
We need to put this folder in a web server in order to run the browser client. The simplest way is to use python3 'http.server'. For production, we may use nginx or apache for hosting the web client.
```
python3 -m http.server 8000
```
The output must be
```
Serving HTTP on 0.0.0.0 port 8000 (http://0.0.0.0:8000/) ...
```
If the output looks like the above, it means that the web client has been started properly. You can visit this client opening the URL 'http://localhost:8000' in a browser. The screen will look like below :

![webclient_default](https://github.com/shubhadeepb14/jmqt/raw/master/examples/screenshots/webclient_default.png)

## Testing all together
The JMQT python client will have a client id as 'pyclient1' by default and will send a dummy data to channel 'mychannel' in every 10 seconds.

```
12-15 11:28:36 [JMQTClient] INF : [Main] Data on 'mychannel' from webclient : Test Message (QOS 1, RETAIN 0)
```

```
12-15 11:37:32 [JMQTClient] INF : [Main] Data on '#pyclient1' from webclient : p2p Message (QOS 1, RETAIN 0)
```

## Directory Structure
This directory contains the sample projects which use the above libraries. 
1. **sample_server.py** : Python 3.6 code which uses the **pyjmqt.server** library to implement a JMQT server. A .conf file is required which contains the server configuraion:
   - **server.conf** : Configuration file for the **pyjmqt.server** library.
2. **sample_client.py** : Python 2.7 code which uses the **pyjmqt.client** library (uses Socket connection) to implement a JMQT client. A .conf file is required which contains the client configuraion:
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
The first parameter of the log functions is the message to log and the second paramters is optional and can be used to identify the source of the of the message. Please note, the path of the log file and log mode is controlled by the 'server.conf' file.
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

To enable Redis, "ENABLE_REDIS" field in 'server.conf' must be set to 1 and the "REDIS" related fields must be uncommented : 
```
ENABLE_REDIS = 1
# uncomment following settings if REDIS is enabled
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB_INDEX = 0
REDIS_PASSWORD = ""
```

To enable MySql, "ENABLE_MYSQL" field 'server.conf' must be set to 1 and the "MYSQL" related fields must be uncommented : 
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
To enable SSL, first we need the server side SSL key and certificate files. These files can be self prepared using OpenSSL or can be assigned by a certificate authority. To prepare own certificates, follow the instructions given in **[certificates.md](https://github.com/shubhadeepb14/jmqt/blob/master/examples/certificates.md)**. Please note, to enable SSL on WebSocket using WSS (WebSocket Secure) and release the application for global use, the certificates must be retrived from a Certificate Authotiry, otherwise the browsers won't be able to use the WSS protocol.

To enable the SSL, "ENABLE_SSL" 'server.conf' field must be set to 1 and "SSL" related fields must be uncommented :
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
## 2. sample_client.py
### 2.a. import the Client class
To start with, first we include the pyjmqt.server API into our code (line 30 - 32)
```
from pyjmqt.client.api import Client
```
### 2.b. Define the application class
We have defined a **class** which contains all the functions and properties are needed to implement the pyjmqt.client library (line 34) :
```
class Main():
```
The **initiate_program** function of this class takes the client name as an arguement (line 46):
```
def initiate_program(self, client_name):
```
### 2.c. Create the client (Object of the Client class)
Inside the 'initiate_program' function, we pass the path of the **config file** (client.conf file) to create an object of the **Client** (line 44):
```
self.__client = Client(self.__configFile)
```
### 2.d. Callbacks and API calls
There are two callbacks which the client code must register (line 54 - 55).
```
self.__client.registerPushcallback(self.push_callback)
self.__client.registerDisconnectcallback(self.disconnect_callback)
```
And for every call to the client API (e.g. auth, connect etc.), a callback must be passed along with the required paramters 
```
self.__client.auth(authData, self.auth_callback) # line 94
self.__client.conn(self.__client_id, self.__auth_token, self.connect_callback) # line 114
self.__client.sub(self.__test_channel, persistent, self.sub_callback) # line 125
self.__client.pub(self.__test_channel, str(datetime.datetime.now()), retain, qos, self.pub_callback) # line 71
```
The corresponding callback functions do not have any return types. For the list of the parameters, please refer to the definition of the callback functions.

### 2.e. Use the logger
The client API contains a logger which can be accessed by the user code. The following snippet is used to access the logger
```
self.logger = self.__client.get_logger()
```
To log a message using the logger, we can use
```
self.logger.log_debug('This is a debug message', 'JMQT client')
self.logger.log_info('This is an info', 'JMQT client')
self.logger.log_warning('Sample Warning!', 'JMQT client')
self.logger.log_error('Fatal Error', 'JMQT client')
```
The first parameter of the log functions is the message to log and the second paramters is optional and can be used to identify the source of the of the message. Please note, the path of the log file and log mode is controlled by the ‘client.conf’ file.
### 2.f. Configuration file (client.conf)
The **client.conf** file contains the configuration paramters to run the client. We must pass the path of this file while creating the object of the 'Client' class in step C. If no configuratin file is passed, the server will use the default configuration. The default configuration is same as the configuration provided in **client.conf**.
### 2.g. Get Configuration Values
It is possible to fetch any configuration paramter from the user code. To do that, we first use the following snippet to get the configuration paramters as a dictionary
```
self.clientConfig = self.server.get_client_config()
```
Then we can access any parameter as shown below 
```
remotePort = self.clientConfig['REMOTE_PORT']
```
### 2.h. Running the client
The client code needs a loop to hold the control of the function. The refer to the **run** function in the **Main** class.

This function also publishes a data to a test channel (defined as a class variable) in every 10 seconds.
```
__test_channel = 'ch' # line 44 
pck_id = self.__client.pub(self.__test_channel, str(datetime.datetime.now()), retain, qos, self.pub_callback) # line 71
```
To run the client, simply execute the following command in a terminal 
```
python sampler_client.py
```
or
```
python3 sampler_client.py
```
### 2.i. Enabling SSL
To enable SSL, first we need the client side SSL key and certificate files. To prepare own certificates, follow the instructions given in **certificates.md**. 

To enable the SSL, "ENABLE_SSL" field in 'client.conf' must be set to 1 and "SSL" related fields must be uncommented :
```
ENABLE_SSL = 1
# path of the ssl certificate file, uncomment if SSL is enabled
SSL_CERT_PATH = 'client.crt'
# path of the ssl key file, uncomment if SSL is enabled
SSL_KEY_PATH = 'client.key'
```
And the "REMOTE_PORT" field must be set to the SSL Socket Port of the server (8011 by default)
```
REMOTE_PORT = 8011
```
## 3. sample_angularjs_client
This directory contains a web client which implements all the basic operations of **JMQT** protocol using **WebSocket**. This aplications has been developed using **AngularJS 1.6.5** and **[jmqt-client.js](https://github.com/shubhadeepb14/jmqt/tree/master/jsclient)**. This demo application contains a single page (we named it 'home') and uses [Angular UI Router](https://github.com/angular-ui/ui-router) to render the page.

To understand the basic structure of the code, first take a look at the following files :
-  **index.html** - The root html file of the Angular App. All the JS and CSS dependencies are imported here.
-  **static/js/jmqt-client.js** - JMQT Javascript client library.
-  **services/jmqtService.js** - An Angular JS service wrapper for the JMQT client library. This service directly accesses the JMQT client library and the Angular controller use this service for all the JMQT client calls.
-  **app.js** - The JS file which creates the Angular App. This file contains the basic JMQT configurations (e.g. host, port etc.) at line 26 - 28. And after that, it contains the Angular App definition and configuration. At line 77 in this file, we initiate the JMQT client using the jmqtService.
-  **controllers/homeCtrl.js** - The Angular controller which performs all the UI actions on the home page.
-  **templates/home.html** - HTML template for the home page.

The JMQT client library can be imported into the code by importing the **[jmqt-client.js](https://github.com/shubhadeepb14/jmqt/tree/master/jsclient)** file. As mentioned above, all access to this library is wrapped up in the **services/jmqtService.js** file. To understand how the library works, we need to take a look at this file.

#### 3.a. Inititating the client 
The following is used to initiate the JMQT client (line 28) :
```
_jmqtClient = new JMQTClient(jmqtHost, jmqtPort, enableSsl);
```
#### 3.b. Registering callbacks
Just like the Python client, we need to register the callbacks for 'push' and 'disconnect'. See line 32 - 46
```
_jmqtClient.on('push', function (channel, client, data, qos, retainFlag) {
    //your code here
});

_jmqtClient.on('disconnect', function (websockAddress) {
    //your code here
});
```
#### 3.c. JMQT operations
All JMQT operations (e.g auth, connect, pub, sub etc.) can be done using the '_jmqtClient' object. For example, to do the 'auth' operations, we need :
```
_jmqtClient.auth(authData, function (status, token, clientId, msg) {
    //your code here 
});
```
Take a look at the following function definitions of **services/jmqtService.js** file to have a better understanding of the operations :
-  **auth** : var auth = function (authData)
```
_jmqtClient.auth(authData, function (status, token, clientId, msg) {
    //your code here
});
```
-  **connect** : var connect = function (clientId, token)
```
_jmqtClient.conn(clientId, token, function (status) {
    //your code here
});
```
-  **disconnect** : var disconnect = function (sendDisconn = false)
```
_jmqtClient.disconnect(sendDisconn); 
```
-  **sub** : var sub = function (channelName, persistentFlag = 0)
```
_jmqtClient.sub(channelName, persistentFlag, function (status, channelName) {
    //your code here
});
```
-  **unsub** : var unsub = function (channelName)
```
_jmqtClient.unsub(channelName, function (status, channelName) {
    //your code here
});
```
-  **pub** : var pub = function (channelName, jsonData = {}, retainFlag = 0, qos = 0)
```
_jmqtClient.pub(channelName, jsonData, retainFlag, qos, function (status, packetId, respData) {
    //your code here
});
```
Please note, in non-angular applications, the 'jmqtService' file is not required and the above operations can directly be accessed by the DOM controllers.
#### 3.d. Accessing the service
The controller **controllers/homeCtrl.js** injects the dependency on the **jmqtService** using the following code 
```
myApp.controller("homeCtrl", function ($scope, jmqtService) {
```
Now the controller can access the functions defined in **jmqtService**. For an example, the 'auth' function can be accessed as
```
var promise = jmqtService.auth({ client_name: $scope.clientData.clientName });
    promise.then(function (result) {
        if (result.status == JMQT.statusCodes.OK) {
            $scope.log("JMQT client authentication OK. Sending connect request..");
        } else {
            $scope.log("JMQT client authentication FAILED. Status " + result.status + ", Message " + result.msg);
        }
    });
```
The service broadcasts the 'push' and 'disconnect' data and the controller receives the same as follows
```
    //when a new data arrives, this functions receives the data
    $scope.$on('jmqt:push', function (event, packet) {
        
    });

    //disconnection trigger is received here
    $scope.$on('jmqt:disconnect', function (event, websockAddress) {
        
    })
```
## 4. sample_load_balancer.py
To load balance the pyjmqt.server, first we need to run the 'sample_server.py' in at least two different nodes. Let's assume that one of the nodes has the IP 192.168.1.10 and the other has the IP 192.168.1.11.

Now, take a look at the **load_balancer.conf** file. For the given scenario, the configuration must go as follows
```
[options]
buffer_size=4096

[mappings]
8010=192.168.1.10:8010,192.168.1.11:8010
8011=192.168.1.10:8011,192.168.1.11:8011
8012=192.168.1.10:8012,192.168.1.11:8012
8013=192.168.1.10:8013,192.168.1.11:8013
```
Here, 'buffer_size' is the size of the buffer to be read from the Socket/Web Socket connection and the 'mappings' values contain the mapping of the local ports (for default ports, see the 'Default Ports' section of this document) to the remote IP:Port combination.

Once the configuration is set, just run the load balancer using python 3 (3.6 or above):
```
python3 sample_load_balancer.py
```

Please note, to run the server with load balancers, the 'ENABLE_MYSQL' and 'ENABLE_REDIS' fields must be enabled in the server config file ('server.conf').