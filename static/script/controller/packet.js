angular.module('hitm')
.controller('PacketCtrl', function($scope, $wamp, $stateParams, ProxyService) {
//    $scope.currentProxy = $stateParams.currentProxy;
    $scope.receivers = [];
    
    ProxyService.list(function(res) {
        $scope.proxies = res
        for(var i = 0; i < res.length; i++) {
            var l = angular.copy(res[i]);
            l.type = "Local";
            var r = angular.copy(res[i]);
            r.type = "Remote";
            $scope.receivers = $scope.receivers.concat(l)
            $scope.receivers = $scope.receivers.concat(r)
        }
    });


})
.controller('DefineCtrl', function($scope, $wamp, $stateParams, ProxyService, ConfigService) {
    $scope.currentProxy = $stateParams.currentProxy;
    $scope.start = 0;
    $scope.end = 2048;
    $scope.type = $stateParams.type;
    $scope.freeze = false;
    $scope.stream = {
        'data': "",
        // Slicing the Buffer
        'start': null,
        'end': null,
        'diff': []
    };

    $scope.getBuffer = function(start=null, end=null) {
        ProxyService.getBuffer($scope.currentProxy, $scope.type, function(data) {
           $scope.stream.data = data 
        }, $scope.start, $scope.end);
    }

    $scope.load = function() {
        ConfigService.getConfig($scope.configs.selectedOption, function(config) {
            $scope.currentConfig = JSON.stringify(config, null, "\t")
        });
    }

    $scope.save = function() {
        ConfigService.writeConfig($scope.configs.selectedOption, JSON.parse($scope.currentConfig), function(res) {
            console.log(res);
        });
    }

    $scope.apply = function() {
        ProxyService.applyConfig($scope.currentProxy, $scope.type, JSON.parse($scope.currentConfig), function(res) {
            $scope.currentConfig = JSON.stringify(res, null, "\t")
        });
    }

    $scope.validatePacket = function() {
        var start = 0;
        var callback = function(data, size) {
            $scope.stream.diff.push({'data':data, 'size':size, 'offset':start})
            if(size == 0) {
                return;
            }
            start += size;
            console.log($scope.stream.diff);
            if(start < $scope.stream.data.length) {
                validate();
            }
        }
        var validate = function() {
            ProxyService.validatePacket($scope.currentProxy, $scope.type, callback, start);
        }
        $scope.stream.diff = [];
        validate();
    }

    $scope.getConfig = function() {
        ProxyService.getConfig($scope.currentProxy, $scope.type, function(config) {
            console.log(config);
            $scope.currentConfig = JSON.stringify(config, null, "\t")
        });
    }

    $scope.reloadClass = function() {
        ProxyService.reloadClass($scope.currentProxy, $scope.type, function() {
            console.log('classes reloaded');
        });
    }
    
    // Init Stuff
    $scope.getBuffer();
    $scope.getConfig();

    ConfigService.list(function(configs) {
        $scope.configs = { 
            selectedOption: null,
            files: configs
        }
    });
    
    // Subscribe to live updates
    ProxyService.streamSubscribe($scope.currentProxy, $scope.type, function(raw) {
        for(var i = 0; i < raw.length; i++) {
            var r = raw[i];
            if(r.offset > $scope.start && r.offset < $scope.end) {
                $scope.stream.data = $scope.stream.data.concat(r.data);
            }
        }
    });
});
