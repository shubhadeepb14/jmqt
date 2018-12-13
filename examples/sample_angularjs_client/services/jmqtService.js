// The MIT License (MIT)
// Copyright (c) 2018 Shubhadeep Banerjee
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in all
// copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
// EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
// MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
// IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
// DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
// OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
// OR OTHER DEALINGS IN THE SOFTWARE.

myApp.service('jmqtService', function ($q, $rootScope) {
    var _jmqtClient = null;

    // sets the jmqt client, must be called on initilization from rootScope
    var setClient = function (jmqtHost, jmqtPort, enableSsl) {
        // create jmqt client
        _jmqtClient = new JMQTClient(jmqtHost, jmqtPort, enableSsl);

        // register push and disconnect callbacks
        // we will broadcast the data on $rootScope which will received by the $scope
        _jmqtClient.on('push', function (channel, client, data, qos, retainFlag) {
            $rootScope.$broadcast('jmqt:push', {
                channel: channel,
                client: client,
                data: data,
                qos: qos,
                retainFlag: retainFlag
            });
        });

        _jmqtClient.on('disconnect', function (websockAddress) {
            $rootScope.$broadcast('jmqt:disconnect', {
                websockAddress: websockAddress
            });
        });
    }

    // authenticates the client
    var auth = function (authData) {
        var deferred = $q.defer();
        // call jmqt auth
        _jmqtClient.auth(authData, function (status, token, clientId, msg) {
            // this the auth callback function
            var result = {
                status: status,
                token: token,
                clientId: clientId,
                msg: msg
            }
            deferred.resolve(result);
        });

        return deferred.promise;
    }

    // create new session
    var connect = function (clientId, token) {
        var deferred = $q.defer();
        // call jmqt connect
        _jmqtClient.conn(clientId, token, function (status) {
            // this the connect callback function
            var result = {
                status: status
            }
            deferred.resolve(result);
        });

        return deferred.promise;
    }

    // disconnects the server
    var disconnect = function (sendDisconn = false) {
        _jmqtClient.disconnect(sendDisconn); //sendDisconn flag sends the disconnection packet to the server
    }

    // publishes jmqt message
    var pub = function (channelName, jsonData = {}, retainFlag = 0, qos = 0) {
        var deferred = $q.defer();
        // call jmqt publish
        _jmqtClient.pub(channelName, jsonData, retainFlag, qos, function (status, packetId, respData) {
            // this the publish callback function
            var result = {
                status: status,
                packetId: packetId,
                respData: respData
            }
            deferred.resolve(result);
        });

        return deferred.promise;
    }

    // subscribes to a jmqt channel
    var sub = function (channelName, persistentFlag = 0) {
        var deferred = $q.defer();
        // call jmqt subscribe
        _jmqtClient.sub(channelName, persistentFlag, function (status, channelName) {
            // this the subscribe callback function
            var result = {
                status: status,
                channelName: channelName
            }
            deferred.resolve(result);
        });

        return deferred.promise;
    }

    // unsubscribes from a jmqt channel
    var unsub = function (channelName) {
        var deferred = $q.defer();
        // call jmqt unsubscribe
        _jmqtClient.unsub(channelName, function (status, channelName) {
            // this the unsubscribe callback function
            var result = {
                status: status,
                channelName: channelName
            }
            deferred.resolve(result);
        });

        return deferred.promise;
    }



    return {
        setClient: setClient,
        auth: auth,
        connect: connect,
        disconnect: disconnect,
        pub: pub,
        sub: sub,
        unsub: unsub
    }
});