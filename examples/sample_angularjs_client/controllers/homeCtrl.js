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

myApp.controller("homeCtrl", function ($scope, $timeout, jmqtService) {
    $scope.clientData = { clientName: "webclient" }
    $scope.pubData = { message: "", channelName: "" }
    $scope.subData = { channelName: "", persistent: false }

    $scope.showSubForm = false;
    $scope.logMessages = [];
    $scope.connected = false;

    $scope.resetClientValues = function () {
        $scope.myChannels = [];
        channelPacketID = null;
    }

    //connects our sample JMQT server 
    $scope.connect = function (form) {
        if ($scope.connected) {
            //disconnect if already connected
            jmqtService.disconnect(sendDisconn = true);
        }
        else {
            //validate the client name
            forceValidateForm(form);
            if (form.$valid) {
                //set the authentication request
                $scope.log("Authenticating JMQT client..");
                $scope.setConnectionStatus(false);
                //the response of the auth request will be received by the $scope.authCallback function
                var promise = jmqtService.auth({ client_name: $scope.clientData.clientName });
                promise.then(function (result) {
                    if (result.status == JMQT.statusCodes.OK) {
                        $scope.log("JMQT client authentication OK. Sending connect request..");
                        //store client id and auth token here for future usage
                        $scope.clientId = result.clientId;
                        //if authentication is valid, then connect the client
                        //the response of the connection request will be received by the $scope.connectCallback function
                        var promise = jmqtService.connect(result.clientId, result.token);
                        promise.then($scope.connectCallback);
                    } else {
                        $scope.log("JMQT client authentication FAILED. Status " + result.status + ", Message " + result.msg);
                    }
                });
            }
        }
    }

    //response of the conn request is received here
    $scope.connectCallback = function (result) {
        if (result.status == JMQT.statusCodes.OK) {
            $scope.setConnectionStatus(true);
            $scope.log("JMQT client connect OK.");
            $scope.getMyChannels();
        } else {
            $scope.log("JMQT client connect FAILED. Status " + result.status);
        }
    }

    //when a new data arrives, this functions receives the data
    $scope.$on('jmqt:data', function (event, packet) {
        $scope.$apply(function () {
            var strData = '';
            if (packet.data.constructor === {}.constructor) {
                strData = JSON.stringify(packet.data);
            } else {
                strData = packet.data.toString();
            }
            var sender = packet.client;
            if (sender == ''){
                sender = 'server';
            }
            $scope.log("Message on channel '" + packet.channel + "' from '" + sender + "' : <" + strData + "> (QOS " + packet.qos + ", RETAIN " + packet.retainFlag + ")");
        });
    });

    //disconnection trigger is received here
    $scope.$on('jmqt:disconnect', function (event, websockAddress) {
        $scope.$apply(function () {
            $scope.resetClientValues();
            $scope.setConnectionStatus(false);
            $scope.log("JMQT client disconnected.");
        });
    })


    //$mySubscriptions is a control channel available in the test server, 
    //which returns a list temporary and persistent channels that the client has subscribed to
    $scope.getMyChannels = function () {
        //we store the global packet id for the published data so that we can check it later in $scope.pubCallback
        var promise = jmqtService.pub('$mySubscriptions');
        promise.then(function (result) {
            if (result.status == JMQT.statusCodes.OK) {
                $scope.log("Received my subscriptions.");
                $scope.myChannels = result.respData.channels
            } else {
                $scope.log("Receiving my subscriptions FAILED. Status " + result.status);
            }
        });
        $scope.myChannels = [];
        $scope.log("Getting my subscriptions..");
    }

    //this function publishes some data
    $scope.send = function (form) {
        forceValidateForm(form);
        if (form.$valid) {
            //if the form is valid, send the pub request
            var promise = jmqtService.pub($scope.pubData.channelName, jsonData = $scope.pubData.message, retainFlag = 1, qos = 0);
            promise.then(function (result) {
                //check the status of the response
                if (result.status == JMQT.statusCodes.OK) {
                    if (result.respData == null) {
                        $scope.log("Publish packet id " + result.packetId + " OK.");
                    } else {
                        // check if the response data is a JSON objects
                        if (result.respData.constructor === {}.constructor) {
                            result.respData = JSON.stringify(result.respData);
                        } else {
                            result.respData = result.respData.toString();
                        }
                        $scope.log("Publish packet id " + result.packetId + " OK. Data : " + result.respData);
                    }
                }
                else {
                    $scope.log("Publish packet id " + result.packetId + " FAILED. Status " + result.status);
                }
            });
            $scope.log("Publishing to \"" + $scope.pubData.channelName);
        }
    }

    //this function subscribes to a channel
    $scope.sub = function (form) {
        forceValidateForm(form);
        if (form.$valid) {
            //if the form is valid, send the sub request
            $scope.log("Subscribing to \"" + $scope.subData.channelName + "\", persistent " + $scope.subData.persistent + "..");
            var promise = jmqtService.sub($scope.subData.channelName, persistentFlag = $scope.subData.persistent);
            promise.then(function (result) {
                //receives the response of the sub request
                if (result.status == JMQT.statusCodes.OK) {
                    $scope.log("Subscribe to \"" + result.channelName + "\" OK.");
                } else {
                    $scope.log("Subscribe to \"" + result.channelName + "\" FAILED. Status " + result.status);
                }
                $scope.getMyChannels();
            });
            $scope.subData.channelName = "";
            $scope.showSubForm = false;
        }
    }

    //this function unsubscribes to a channel
    $scope.unsub = function (channel) {
        $scope.log("Unubscribing to \"" + channel + "\"..");
        //if the form is valid, send the unsub request
        var promise = jmqtService.unsub(channel);
        promise.then(function (result) {
            //receives the response of the unsub request
            if (result.status == JMQT.statusCodes.OK) {
                $scope.log("Unsubscribe to \"" + result.channelName + "\" OK.");
            } else {
                $scope.log("Unsubscribe to \"" + result.channelName + "\" FAILED. Status " + result.status);
            }
            $scope.getMyChannels();
        });
    }

    //logs a message
    //as this function is called from non-angular JS callback (directly from the jmqt-client library),
    //we need to call $timeout to apply the changes on the $scope
    $scope.log = function (msg) {
        $scope.logMessages.push(msg);
    }

    $scope.clearLog = function () {
        $scope.logMessages = [];
    }

    //sets the current connection status
    //as this function is called from non-angular JS callback (directly from the jmqt-client library),
    //we need to call $timeout to apply the changes on the $scope
    $scope.setConnectionStatus = function (isConnected) {
        $scope.connected = isConnected;
    }

    $scope.resetClientValues();
});