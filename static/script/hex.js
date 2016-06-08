angular.module('hitm')
.directive('hexedit', function($compile) {
    return {
        restrict: 'E',
        scope: {
            stream: '=data'
        },
        //replace: true,
        //require: '?ngModel',
        templateUrl: 'partials/hex.html',
        link: function($scope, $element, $attributes) {
            $scope.decimalToHex = function decimalToHex(d, padding) {
                var hex = Number(d).toString(16).toUpperCase();
                padding = typeof (padding) === "undefined" || padding === null ? padding = 2 : padding;

                while (hex.length < padding) {
                    hex = "0" + hex;
                }

                return hex;
            }
            $scope.decimalToChar = function(c) {
                h = "";
                h = 63<c && 127>c?h+String.fromCharCode(c):h+".";
                return h;
            }
            $scope.diffClass = function(index) {
                if(!("data" in $scope.stream) || $scope.stream.length <= 0) {
                    return ""
                }
                if("diff" in $scope.stream) {
                    for(i = 0; i < $scope.stream.diff.length; i++) {
                        var diff = $scope.stream.diff[i];
                        // check which packet we're in...
                        if (index >= diff.offset && index < (diff.offset + diff.data.length)) {
                            if(diff.data[index - diff.offset] == $scope.stream.data[index]) {
                                return "hex-match";
                            } else {
                                return "hex-diff";
                            }
                        }
                    }
                }
                return "";
            }
        }

    };
});
