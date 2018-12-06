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

// JMQT protocol version 1.0

var that = null;
var packetCounter = 1;
window.onbeforeunload = function () {
    console.log('unload');
    if (that != null) {
        if (that.websocket != null) {
            try {
                that.disconnect();
            }
            catch (e) {
                console.log(e);
            }
        }
    }
}

function increaseCounter() {
    packetCounter += 1;
    if (packetCounter == 99999) {
        packetCounter = 1;
    }
}
const JMQT = {
    statusCodes: {
        UNKNOWN: -1,
        OK: 1,
        FAILED: 0,
        MALFORMED_PACKET: 3,
        SERVER_ERROR: 5,
        INVALID_TOKEN: 6,
        NOT_ALLOWED: 7,
        CLIENT_OFFLINE: 8,
        NETWORK_ERROR: 9,
        INVALID_PACKET: 10
    }
}
class JMQTClient {
    // properties of the class
    properties() {
        this.JMQT_VERSION = '1.0';
        this.statusCodes = JMQT.statusCodes;
        this.websocket = null;
        this.timeoutMiliSeconds = 0;
        this.hbGap = 0;
        this.lastHbAck = 0;
        this.lastHbSent = 0;

        this.authJson = null;
        this.isAuthPending = false;
        this.clientId = null;
        this.authToken = null;
        this.isConnectPending = false;

        this.opened = false;
        this.connected = false;
        this._subCallbacks = {};
        this._unsubCallbacks = {};
        this._pubCallbacks = {};
        this._authCallback = null;
        this._connectCallback = null;
        this._disconnectCallback = null;
        this._dataCallback = null;
    }

    // constructor
    constructor(jmqtHost, jmqtPort, enableSsl) {
        this.properties();
        var prefix = "ws://";
        if (enableSsl) {
            prefix = "wss://";
        }
        this.websockAddress = prefix + jmqtHost + ":" + jmqtPort + "/";
        that = this;
    }

    _open() {
        if (!this.opened) {
            console.log('Opening web socket ' + this.websockAddress);
            this.websocket = new WebSocket(this.websockAddress);
            this.websocket.onmessage = this._incomingHandler;
            this.websocket.onclose = this._disconnectHandler;
            this.websocket.onopen = this._openHandler;
        }
    }

    _openHandler() {
        console.log('Web socket opened ' + that.websockAddress);
        that.opened = true;
        if (that.isAuthPending) {
            that.auth(that.authJson, that._authCallback);
        } else if (that.isConnectPending) {
            that.conn(that.clientId, that.authToken, that._connectCallback);
        }
    }

    _disconnectHandler() {
        console.log('Web socket closed ' + that.websockAddress);
        that.connected = false;
        that.opened = false;
        if (that.isAuthPending) {
            that._authCallback(that.statusCodes.NETWORK_ERROR);
        } else if (that.isConnectPending) {
            that._connectCallback(that.statusCodes.NETWORK_ERROR);
        }
        if (that._disconnectCallback != null) {
            that._disconnectCallback(that.websockAddress);
        }
    }

    // handles all incoming socket data
    _incomingHandler(event) {
        var packet = JSON.parse(event.data);
        if (packet.hasOwnProperty('authAck')) {
            var data = packet['authAck'];
            console.log('JMQT authAck, status ' + data.st);
            var token = '',
                client = '',
                msg = '';
            that.isAuthPending = false;
            if (data.st == that.statusCodes.OK) {
                token = data.at;
                client = data.cl;
            } else {
                msg = data.mg;
            }
            // call auth callback
            that._authCallback(data.st, token, client, msg);
        }
        else if (packet.hasOwnProperty('connAck')) {
            var data = packet['connAck'];
            console.log('JMQT connAck, status ' + data.st);
            if (data.st == that.statusCodes.OK) {
                that.timeoutMiliSeconds = data.ts * 1000;
                that.hbGap = (data.ts - 2) * 1000;
                that.lastHbAck = 0;
                that.lastHbSent = 0;
                that.connected = true;
                that.isConnectPending = false;
                that.heartbeat();
            }
            // call conn callback
            that._connectCallback(data.st);
        }
        if (packet.hasOwnProperty('hbAck')) {
            that.lastHbAck = new Date().getTime();
            console.log('JMQT hbAck');
        }
        else if (packet.hasOwnProperty('subAck')) {
            var data = packet['subAck'];
            // call sub callback
            if (that._subCallbacks.hasOwnProperty(data.cn)) {
                console.log('JMQT subAck for "' + data.cn + '", status ' + data.st);
                that._subCallbacks[data.cn](data.st, data.cn);
            } else {
                console.log('JMQT subAck for unknown channel "' + data.cn + '", status ' + data.st);
            }
        }
        else if (packet.hasOwnProperty('unsubAck')) {
            var data = packet['unsubAck'];
            // call sub callback
            if (that._unsubCallbacks.hasOwnProperty(data.cn)) {
                console.log('JMQT unsubAck for "' + data.cn + '", status ' + data.st);
                that._unsubCallbacks[data.cn](data.st, data.cn);
            } else {
                console.log('JMQT unsubAck for unknown channel "' + data.cn + '", status ' + data.st);
            }
        }
        else if (packet.hasOwnProperty('pubAck')) {
            var data = packet['pubAck'];
            // call sub callback
            if (that._pubCallbacks.hasOwnProperty(data.id)) {
                console.log('JMQT pubAck for "' + data.id + '", status ' + data.st);
                var pubAckData = null;
                if (data.hasOwnProperty('dt')) {
                    pubAckData = data.dt;
                }
                that._pubCallbacks[data.id](data.st, data.id, pubAckData);
            } else {
                console.log('JMQT pubAck for unknown packet "' + data.id + '", status ' + data.st);
            }
        }
        else if (packet.hasOwnProperty('push')) {
            var data = packet['push'];
            var channel = data.cn,
                client = data.cl,
                pushData = data.dt;
            var qos = 0,
                retainFlag = 0,
                packetId = '';
            if (data.hasOwnProperty('q')) {
                qos = data.q;
            }
            if (data.hasOwnProperty('rt')) {
                retainFlag = data.rt;
            }
            if (qos == 1 && !retainFlag) {
                packetId = data.id;
                that.pushAck(packetId);
            }
            that._dataCallback(channel, client, pushData, qos, retainFlag);
        }
    }

    _createAuthRequest(authJson) {
        return JSON.stringify({ auth: { dt: authJson } });
    }

    _createConnRequest(authToken, clientId) {
        return JSON.stringify({ conn: { at: authToken, cl: clientId } })
    }

    _createDisconnRequest() {
        return JSON.stringify({ disconn: {} })
    }

    _createSubRequest(channelName, persistentFlag) {
        persistentFlag = persistentFlag ? 1 : 0;
        return JSON.stringify({ sub: { cn: channelName, pr: persistentFlag } });
    }

    _createUnsubRequest(channelName) {
        return JSON.stringify({ unsub: { cn: channelName } });
    }

    _createPubRequest(channelName, jsonData, retainFlag, qos, packetId) {
        var data = {
            cn: channelName, dt: jsonData
        }

        if (channelName.toString().startsWith('$')) {
            data['id'] = packetId;
        } else if (qos > 0) {
            data['q'] = qos;
            data['id'] = packetId;
        }

        if (retainFlag) {
            data['rt'] = 1;
        }
        return JSON.stringify({ pub: data });
    }

    _createPushResponse(packetId) {
        return JSON.stringify({ pushAck: { id: packetId } });
    }

    _createHeartbeatRequest() {
        return JSON.stringify({ hb: {} });
    }

    //jmqt heartbeat
    heartbeat() {
        var proceed = false;
        var diff = 0;
        if (that.lastHbSent == 0) {
            proceed = true;
            that.lastHbAck = new Date().getTime();
        } else {
            diff = Math.abs(that.lastHbSent - that.lastHbAck);
            if (diff <= that.timeoutMiliSeconds) {
                proceed = true;
            }
        }
        console.log('JMQT heartbeat scheduled, diff ' + diff);
        if (proceed) {
            setTimeout(function () {
                if (that.connected) {
                    console.log('JMQT heartbeat..');
                    that.lastHbSent = new Date().getTime();
                    that.websocket.send(that._createHeartbeatRequest());
                    that.heartbeat();
                } else {
                    console.log('JMQT heartbeat skipped!');
                }
            }, that.hbGap);
        }
        else {
            console.log('JMQT hb ack timeout!!');
            that.disconnect();
        }
    }

    // jmqt auth
    auth(authJson, callback) {
        try {
            this._authCallback = callback;
            this.authJson = authJson;
            if (this.opened) {
                console.log('JMQT auth..');
                this.websocket.send(this._createAuthRequest(authJson));
            } else {
                this.isAuthPending = true;
                this._open();
            }
        }
        catch (e) {
            console.log('Error in auth: ' + e);
            callback(this.statusCodes.NETWORK_ERROR);
        }
    }

    // registers the disconnection callback
    _registerDisconnectionCallback(disconnectCallback) {
        this._disconnectCallback = disconnectCallback;
    }

    // registers the disconnection callback
    _registerDataCallback(dataCallback) {
        this._dataCallback = dataCallback;
    }

    // used to register disconnect and data callbacks
    on(key, callback) {
        if (key == 'push') {
            this._registerDataCallback(callback);
        } else if (key == 'disconnect') {
            this._registerDisconnectionCallback(callback);
        }
    }

    // jmqt connect
    conn(clientId, authToken, callback) {
        if (this.connected) {
            console.log('JMQT already connected..');
            callback(this.statusCodes.OK);
            return;
        }
        try {
            this._connectCallback = callback;
            this.clientId = clientId;
            this.authToken = authToken;
            if (this.opened) {
                console.log('JMQT conn..');
                this.websocket.send(this._createConnRequest(authToken, clientId));
            } else {
                this.isConnectPending = true;
                this._open();
            }
        }
        catch (e) {
            console.log('Error in conn: ' + e);
            callback(this.statusCodes.NETWORK_ERROR);
        }
    }

    // jmqt subscribe
    sub(channelName, persistentFlag, callback) {
        try {
            if (!this.connected) {
                throw new Error('JMQT client not connected')
            }
            this._subCallbacks[channelName] = callback;
            console.log('JMQT sub "' + channelName + '", persistent ' + persistentFlag + "..");
            this.websocket.send(this._createSubRequest(channelName, persistentFlag));
        }
        catch (e) {
            console.log('Error in sub: ' + e);
            callback(this.statusCodes.NETWORK_ERROR, channelName);
        }
    }

    // jmqt unsubscribe
    unsub(channelName, callback) {
        try {
            if (!this.connected) {
                throw new Error('JMQT client not connected')
            }
            this._unsubCallbacks[channelName] = callback;
            console.log('JMQT unsub "' + channelName + '"..');
            this.websocket.send(this._createUnsubRequest(channelName));
        }
        catch (e) {
            console.log('Error in unsub: ' + e);
            callback(this.statusCodes.NETWORK_ERROR, channelName);
        }
    }

    // jmqt publish
    pub(channelName, jsonData, retainFlag, qos, callback) {
        var packetId = packetCounter.toString();
        increaseCounter();
        try {
            if (!this.connected) {
                throw new Error('JMQT client not connected')
            }
            this._pubCallbacks[packetId] = callback;
            console.log('JMQT pub "' + channelName + '", packet id ' + packetId + '..');
            this.websocket.send(this._createPubRequest(channelName, jsonData, retainFlag, qos, packetId));
        }
        catch (e) {
            console.log('Error in pub: ' + e);
            callback(this.statusCodes.NETWORK_ERROR, packetId);
        }
        return packetId;
    }

    // jmqt push ack
    pushAck(packetId) {
        try {
            console.log('JMQT pushAck packet id ' + packetId + '..');
            this.websocket.send(this._createPushResponse(packetId));
        }
        catch (e) {
            console.log('Error in pushAck: ' + e);
        }
    }

    disconnect(sendDisconn = false) {
        if (this.websocket != null) {
            if (sendDisconn) {
                console.log('Sending disconn..')
                this.websocket.send(this._createDisconnRequest())
            }
            console.log('Closing web socket ' + this.websockAddress);
            this.websocket.close();
        }
    }
}