angular.module('hitm')
.factory('ProxyService', function($wamp) {
    //var proxies = {}
    var proxyService = {
        list: function(cb) {
            $wamp.call('com.hitm.proxy.list').then(
                function(res) {
                    if (cb) cb(JSON.parse(res));
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
        }
    };
    return proxyService;
});
