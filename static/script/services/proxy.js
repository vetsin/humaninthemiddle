angular.module('hitm')
.factory('ProxyService', function($wamp) {
    var proxies = [] 

    function convert(data) {
        data = atob(data);
        bytes = []
        for(var i = 0; i < data.length; i++) {
            bytes.push(data.charCodeAt(i));
        }
        return bytes;
    }

    var proxyService = {
        list: function(cb) {
            $wamp.call('com.hitm.list').then(
                function(res) {
                    proxies = JSON.parse(res);
                    if (cb) cb(proxies);
                }
            );
        },
        start: function(localPort, remoteHost, remotePort, cb) {
            $wamp.call('com.hitm.start',[localPort,remoteHost,remotePort]).then(
                function(res) {
                    if (cb) cb(res);
                }
            );
        },
        stop: function(localPort, cb) {
            $wamp.call('com.hitm.stop', [localPort]).then(
                function(res) {
                    if (cb) cb(res);
                }
            );
        },
        getProxy: function(localPort, cb) { 
            //console.log('getProxy')
            for(var i=0; i < proxies.length; i++) {
                var proxy = proxies[i]
                if (proxy.localPort == localPort) {
                    console.log('ret getProxy' + proxy)
                    if (cb) cb(proxy);    
                }
            }
            if (cb) cb({});    
        },
        getBuffer: function(localPort, type, cb, start=null, end=null) {
            type = type.toLowerCase()
            type = type.charAt(0).toUpperCase() + type.slice(1);
            console.log('calling')
            $wamp.call('com.hitm.' + localPort + '.getBuffer', [type, start, end]).then(
                function (res) {
                    // Expects b64 encoder due to autobahnjs not supporting msgpack yet
                    // https://github.com/crossbario/autobahn-js/issues/67
                    console.log('converting to cb...');
                    cb(convert(res));
                },
                function (error) {
                    console.log('error!' + error)
                }
            );
        },
        getLocalBuffer: function(localPort, cb, start=null, end=null) {
            this.getBuffer(localPort, "local", cb, start, end);
        },
        getRemoteBuffer: function(localPort, cb, start=null, end=null) {
            this.getBuffer(localPort, "remote", cb, start, end);
        },
        getPackets: function(localPort, type, cb, start=null, end=null, includeData=true) {
            $wamp.call('com.hitm.' + localPort + '.getPackets', [type, start, end, includeData]).then(
                function(res) {  
                    if(includeData) {
                        for(var i=0; i < res.length; i++) {
                            res[i].data = convert(res[i].data)
                        }
                    }
                    cb(res)
                }
            );
        },
        getPacket: function(localPort, type, id, cb) {
            $wamp.call('com.hitm.' + localPort + '.getPacket', [type, id]).then(
                function(packet) {
                    console.log(packet);
                    packet.data = convert(packet.data);
                    console.log(packet.hasOwnProperty('body'));
                    if(packet.hasOwnProperty('body')) {
                        packet.body = convert(packet.body);
                    }
                    cb(packet);
                }
            );
        },
        streamSubscribe: function(localPort, type, cb) {
            type = type.toLowerCase()
            type = type.charAt(0).toUpperCase() + type.slice(1);
            $wamp.subscribe("com.hitm." + localPort + ".raw" + type, 
                function(raw) {
                    for(var i = 0; i < raw.length; i++) {
                        raw[i].data = convert(raw[i].data)
                    }
                    cb(raw);
                }
            );
        },
        packetSubscribe: function(localPort, type, cb) {
            type = type.toLowerCase()
            type = type.charAt(0).toUpperCase() + type.slice(1);
            $wamp.subscribe("com.hitm." + localPort + ".packet" + type,
                function(res) {  
                    for(var i = 0; i < res.length; i++) {
                        //res[i].packet.data = convert(res[i].packet.data);
                        res[i].data = convert(res[i].data);
                        if(res[i].hasOwnProperty('body')) {
                            res[i].body = convert(res[i].body);
                        }
                    }
                    cb(res)
                }
            ); 
        },
        validatePacket: function(localPort, type, cb, start=null, end=null) {
            $wamp.call('com.hitm.' + localPort + '.validatePacket', [type, start, end]).then(
                function (data) {
                   if (cb) cb(convert(data[0]), data[1]); 
                }
            );
        },
        applyConfig: function(localPort, type, config, cb) {
            $wamp.call('com.hitm.' + localPort + '.applyConfig', [type, config]).then(
                function (res) {
                    if (cb) cb(res)
                }
            );
        },
        getConfig: function(localPort, type, cb) {
            $wamp.call('com.hitm.' + localPort + '.getConfig', [type]).then(cb);
        },
        reloadClass: function(localPort, type, cb) {
            $wamp.call('com.hitm.' + localPort + '.loadProtocols').then(cb);
        },
        reprocess: function(localPort, type, cb) {
            $wamp.call('com.hitm.' + localPort + '.reprocess', [type]).then(cb);
        }
    };
    return proxyService;
});
