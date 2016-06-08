angular.module('hitm', [
    'ui.router',
    'vxWamp',
    'oc.lazyLoad',
    'ui.bootstrap',
]).
config(function($stateProvider, $urlRouterProvider, $wampProvider, $ocLazyLoadProvider) {
    $ocLazyLoadProvider.config({
        debug:false,
        events:true,
    });

    $wampProvider.init({
        url: 'ws://127.0.0.1:8080/ws',
        realm: 'realm1'
    });

    $urlRouterProvider.otherwise("/proxy");

    $stateProvider
        /*
        .state('main', {
            url: "/main",
            controller: 'MainCtrl',
            templateUrl: "partials/main.html",
            resolve: {
                loadMyFiles: function($ocLazyLoad) {
                    return $ocLazyLoad.load({
                        name:'hitm', 
                        files:[
                            'script/controller/main.js',
                        ]
                    })
                }
            }
        })
        */
        .state('proxy', {
            url: "/proxy",
            controller: 'ProxyCtrl',
            templateUrl: "partials/proxy.html",
            resolve: {
                loadMyFiles: function($ocLazyLoad) {
                    return $ocLazyLoad.load({
                        name:'hitm.proxy',
                        files:[
                            'script/controller/proxy.js',
                            'script/services/proxy.js',
                        ]
                    })
                }
            }
        })
        .state('packets', {
            url: "/packets",
            controller: "PacketCtrl",
            templateUrl: "partials/packets.html",
            resolve: {
                loadMyFiles: function($ocLazyLoad) {
                    return $ocLazyLoad.load({
                        name:'hitm.packets',
                        files:[
                            'script/controller/packet.js',
                            'script/services/proxy.js',
                            'script/services/config.js',
                        ]
                    })
                }
            }
        })
        .state('packets.define', {
            url: "/:currentProxy/:type",
            controller: "DefineCtrl",
            templateUrl: "partials/packets.define.html",
            resolve: {
                loadMyFiles: function($ocLazyLoad) {
                    return $ocLazyLoad.load({
                        name:'hitm.hex',
                        files:[
                            'script/hex.js',
                            'css/hex.css',
                        ]
                    })
                }
            }
        })
        .state('history', {
            url: "/history",
            controller: "HistoryCtrl",
            templateUrl: "partials/history.html",
            resolve: {
                loadMyFiles: function($ocLazyLoad) {
                    return $ocLazyLoad.load({
                        name:'hitm.history',
                        files:[
                            'script/controller/history.js',
                            'script/services/proxy.js',
                        ]
                    })
                }
            }
        })
        .state('history.view', {
            url: "/:currentProxy/:type",
            controller: "HistoryViewCtrl",
            templateUrl: "partials/history.view.html",
            resolve: {
                loadMyFiles: function($ocLazyLoad) {
                    return $ocLazyLoad.load({
                        name:'history.view',
                        files:[
                            'script/hex.js',
                            'css/hex.css',
                        ]
                    })
                }
            }
        });

})
.run(function($wamp){
    $wamp.open();
});
