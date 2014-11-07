var app = angular.module('myApp', ['ngRoute', 'ui.bootstrap', 'angulartics', 'angulartics.google.analytics', 'directive.g+signin']);

app.service('RegionService', function ($http, PlayerService, TournamentService, RankingsService) {
    var service = {
        regions: [],
        region: '',
        setRegion: function (newRegion) {
            if (newRegion != this.region) {
                this.region = newRegion;
                PlayerService.playerList = null;
                TournamentService.tournamentList = null;
                RankingsService.rankingsList = null;

                $http.get('http://api.garpr.com/' + this.region + '/players').
                    success(function(data) {
                        PlayerService.playerList = data;
                    });

                $http.get('http://api.garpr.com/' + this.region + '/tournaments').
                    success(function(data) {
                        TournamentService.tournamentList = data.tournaments.reverse();
                    });

                $http.get('http://api.garpr.com/' + this.region + '/rankings').
                    success(function(data) {
                        RankingsService.rankingsList = data;
                    });
            }
        }
    };

    $http.get('http://api.garpr.com/regions').
        success(function(data) {
            service.regions = data.regions;
        });

    return service;
});

app.service('PlayerService', function () {
    var service = {
        playerList: null,
        getPlayerIdFromName: function (name) {
            for (i = 0; i < this.playerList.players.length; i++) {
                p = this.playerList.players[i]
                if (p.name == name) {
                    return p.id;
                }
            }
            return null;
        }
    };
    return service;
});

app.service('TournamentService', function () {
    var service = {
        tournamentList: null
    };
    return service;
});

app.service('RankingsService', function () {
    var service = {
        rankingsList: null
    };
    return service;
});

app.service('UserService', function () {
    var service = {
        loggedIn: false,
        authResult: null,
        idToken: null,
        email: null,
        updateWithAuthResult: function (authResult) {
            console.log('updateWithAuthResult');
            this.loggedIn = true;
            this.authResult = authResult;
            this.idToken = authResult.id_token;
            this.email = 'test@test.com'; // TODO change
        },
        logOut: function () {
            this.loggedIn = false;
            this.authResult = null;
            this.idToken = null;
            this.email = null;
        }
    };

    return service;
});

app.config(['$routeProvider', function($routeProvider) {
    $routeProvider.when('/:region/rankings', {
        templateUrl: 'rankings.html',
        controller: 'RankingsController',
        activeTab: 'rankings'
    }).
    when('/:region/players', {
        templateUrl: 'players.html',
        controller: 'PlayersController',
        activeTab: 'players'
    }).
    when('/:region/players/:playerId', {
        templateUrl: 'player_detail.html',
        controller: 'PlayerDetailController',
        activeTab: 'players'
    }).
    when('/:region/tournaments', {
        templateUrl: 'tournaments.html',
        controller: 'TournamentsController',
        activeTab: 'tournaments'
    }).
    when('/:region/headtohead', {
        templateUrl: 'headtohead.html',
        controller: 'HeadToHeadController',
        activeTab: 'headtohead'
    }).
    when('/about', {
        templateUrl: 'about.html',
        activeTab: 'about'
    }).
    otherwise({
        redirectTo: '/norcal/rankings'
    });
}]);

app.controller("NavbarController", function($scope, $route, RegionService) {
    $scope.regionService = RegionService;
    $scope.$route = $route;
});

app.controller("UserController", function($scope, $route, UserService) {
    $scope.userService = UserService;
    
    $scope.logOut = function () {
        console.log('before sign out');
        gapi.auth.signOut();
        $scope.userService.logOut();
        console.log('after sign out');
    };

    $scope.$on('event:google-plus-signin-success', function (event, authResult) {
        UserService.updateWithAuthResult(authResult);
        $scope.$apply();
        console.log(authResult);
        console.log(UserService.idToken);
        // Send login to server or save into cookie
    });
    $scope.$on('event:google-plus-signin-failure', function (event, authResult) {
        // Auth failure or signout detected
    });
});

app.controller("RankingsController", function($scope, $http, $routeParams, RegionService, RankingsService) {
    RegionService.setRegion($routeParams.region);
    $scope.regionService = RegionService;
    $scope.rankingsService = RankingsService
});

app.controller("TournamentsController", function($scope, $http, $routeParams, RegionService, TournamentService) {
    RegionService.setRegion($routeParams.region);
    $scope.regionService = RegionService;
    $scope.tournamentService = TournamentService;
});

app.controller("PlayersController", function($scope, $http, $routeParams, RegionService, PlayerService) {
    RegionService.setRegion($routeParams.region);
    $scope.regionService = RegionService;
    $scope.playerService = PlayerService;
});

app.controller("PlayerDetailController", function($scope, $http, $routeParams, RegionService) {
    RegionService.setRegion($routeParams.region);
    $scope.regionService = RegionService;
    $scope.playerId = $routeParams.playerId;

    $http.get('http://api.garpr.com/' + $routeParams.region + '/players/' + $routeParams.playerId).
        success(function(data) {
            $scope.playerData = data;
        });

    $http.get('http://api.garpr.com/' + $routeParams.region + '/matches/' + $routeParams.playerId).
        success(function(data) {
            $scope.matches = data.matches.reverse();
        });

});

app.controller("HeadToHeadController", function($scope, $http, $routeParams, RegionService, PlayerService) {
    RegionService.setRegion($routeParams.region);
    $scope.regionService = RegionService;
    $scope.playerService = PlayerService;
    $scope.player1 = null;
    $scope.player2 = null;
    $scope.wins = 0;
    $scope.losses = 0;

    $scope.onChange = function() {
        if ($scope.player1 != null && $scope.player2 != null) {
            $http.get('http://api.garpr.com/' + $routeParams.region + 
                '/matches/' + $scope.player1.id + '?opponent=' + $scope.player2.id).
                success(function(data) {
                    $scope.playerName = $scope.player1.name;
                    $scope.opponentName = $scope.player2.name;
                    $scope.matches = data.matches.reverse();
                    $scope.wins = data.wins;
                    $scope.losses = data.losses;
                });
        }
    };

    $scope.typeaheadFilter = function(playerName, viewValue) {
        var lowerPlayerName = playerName.toLowerCase();
        var lowerViewValue = viewValue.toLowerCase();

        // try matching the full name first
        if (lowerPlayerName.indexOf(lowerViewValue) == 0) {
            return true;
        }

        // if viewValue is >= 3 chars, allow substring matching
        // this is to allow players with very short names to appear for small search terms
        if (lowerViewValue.length >= 3 && lowerPlayerName.indexOf(lowerViewValue) != -1) {
            return true;
        }

        var tokens = playerName.split(new RegExp('[-_|. ]', 'g')).filter(function (str) { return str; });
        for (i = 0; i < tokens.length; i++) {
            if (tokens[i].toLowerCase().indexOf(viewValue.toLowerCase()) == 0) {
                return true;
            }
        }

        return false;
    };
});
