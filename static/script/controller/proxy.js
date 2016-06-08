angular.module('hitm')
.controller('ProxyCtrl', function($scope, $wamp, $stateParams, ProxyService) {
    $scope.proxies = []
    $scope.localStream = ""
    $scope.remoteStream = "";

    ProxyService.list(function(res) {
        $scope.proxies = res
    });

    $scope.start = function() { 
        ProxyService.start(8000,"127.0.0.1",8001, function(res) {
            $scope.list() //update 
        });
    }
    $scope.stop = function(port) { 
        ProxyService.stop(port, function(res) {
            $scope.list() //update 
        });
    } 
    $scope.list = function() { 
        ProxyService.list(function(res) {
            $scope.proxies = res
        });
    }
});
/*
.controller('RawViewCtrl', function($scope, $stateParams, $wamp, ProxyService) {
    $scope.currentProxy = $stateParams.currentProxy;

    ProxyService.getBuffer($scope.currentProxy, 'local',  function(data) {
        $scope.localStream = {
            'data': data,
            // Slicing the Buffer
            'start': null,
            'end': null,
            'diff': []
        };
    });
    ProxyService.getRemoteBuffer($scope.currentProxy, function(data) {
        $scope.remoteStream = data
    });

    ProxyService.getProxy($scope.currentProxy, function(proxy) {
        $wamp.subscribe("com.hitm." + proxy.localPort + ".rawLocal", function(args) {
            $scope.localStream = $scope.localStream + args
        });
        $wamp.subscribe("com.hitm." + proxy.localPort + ".rawRemote", function(args) {
            $scope.remoteStream = $scope.remoteStream + args
        });
    });
});
*/
