angular.module('hitm')
.factory('ConfigService', function($wamp) {
    var configs = [] 

    var proxyService = {
        list: function(cb) {
            $wamp.call('com.hitm.config.list').then(
                function(res) {
                    if (cb) cb(res);
                }
            );
        },
        getConfig: function(name, cb) { 
            $wamp.call('com.hitm.config.read', [name]).then(
                function(res) {
                    if (cb) cb(res);
                }
            );
        },
        writeConfig: function(name, content, cb) {
            $wamp.call('com.hitm.config.write', [name, content]).then(
                function(res) {
                    if (cb) cb(res);
                }
            );
        }
    };
    return proxyService;
});
