angular.module('hitm')
.controller('HistoryCtrl', function($scope, $stateParams, ProxyService) {
    ProxyService.list(function(res) {
        $scope.proxies = res
    });
})
.controller('HistoryViewCtrl', function($scope, $stateParams, ProxyService) {
    $scope.currentProxy = $stateParams.currentProxy;
    $scope.type = $stateParams.type;
    $scope.freeze = false;
    $scope.stream = {
        'data': "",
        // Slicing the Buffer
        'start': null,
        'end': null,
        'diff': []
    };

    $scope.getPackets = function(start=null, end=null, includeData=false) {
        ProxyService.getPackets($scope.currentProxy, $scope.type, function(packets) {
            console.log(packets)
            $scope.packets = packets
        }, start, end, includeData);
    }

    $scope.setSelected = function(id) {
        console.log('ss')
        ProxyService.getPacket($scope.currentProxy, $scope.type, id, function(packet) {
            $scope.selected = packet
            console.log($scope.selected)
        });
    }

    $scope.reprocess = function() {
        ProxyService.reprocess($scope.currentProxy, $scope.type, function(res) {
            // Update packet list
            $scope.getPackets();
        });
    }

    $scope.reloadClass = function() {
        ProxyService.reloadClass($scope.currentProxy, $scope.type, function() {
            console.log('classes reloaded');
        });
    }

    
    // Init Stuff
    $scope.getPackets();
    
    // Subscribe to live updates
    ProxyService.packetSubscribe($scope.currentProxy, $scope.type, function(res) {
        console.log(res);
        for(var i = 0; i < res.length; i++) {
            $scope.packets = $scope.packets.concat(res[i]);
        }
    });
});
