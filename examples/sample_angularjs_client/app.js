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

'use strict';

// JMQT server address and wecsocket port
// default ports - 8012 without SSL, 8013 with SSL
var jmqtHost = "localhost",
    jmqtPort = 8012,
    enableSsl = false;

// create the angular app
var myApp = angular.module('app', ['ui.router']);

// here we will configure our angular app
myApp.config(['$stateProvider',
    '$urlRouterProvider', function ($stateProvider, $urlRouterProvider) {
        // defining the rouets (angular ui router)
        var homeState = {
            name: 'home',
            url: '/home',
            templateUrl: 'templates/home.html',
            controller: 'homeCtrl',
        };
        $stateProvider.state(homeState);
        $urlRouterProvider.otherwise('home');

    }]);

// function to validate a form 
var forceValidateForm = function (form) {
    angular.forEach(form.$error, function (field) {
        angular.forEach(field, function (errorField) {
            errorField.$setTouched();
        })
    });
}

// directive to enable autoScroll in a div
myApp.directive('autoScroll', function () {
    return {
        scope: {
            autoScroll: "="
        },
        link: function (scope, element) {
            scope.$watchCollection('autoScroll', function (newValue) {
                if (newValue) {
                    $(element).scrollTop($(element)[0].scrollHeight);
                }
            });
        }
    }
})

// initialize the app
myApp.run(['$rootScope', 'jmqtService',
    function ($rootScope, jmqtService) {
        // we must initialize the jmqtService service by calling the jmqtService.setClient function
        jmqtService.setClient(jmqtHost, jmqtPort, enableSsl);
    }
]);

// enable angular tooltip
$(function () {
    $('[data-toggle="tooltip"]').tooltip()
})

