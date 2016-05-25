# -*- coding: utf-8 -*-`
"""api.py - Create and configure the Rock, Paper, Scissors
API exposing the resources.
This file includes all of the game’s logic."""

import logging
import endpoints
from protorpc import remote, messages
from google.appengine.api import memcache
from google.appengine.api import taskqueue
from google.appengine.ext import ndb

from models import User, Game
from models import weapons
from models import StringMessage, NewGameForm, GameForm, GameForms, WeaponForm
from utils import get_by_urlsafe

# Request containers
NEW_GAME_REQUEST = endpoints.ResourceContainer(NewGameForm)
SELECT_WEAPON_REQUEST = endpoints.ResourceContainer(WeaponForm)
GET_GAME_REQUEST = endpoints.ResourceContainer(
    urlsafe_game_key=messages.StringField(1), )
CANCEL_GAME_REQUEST = endpoints.ResourceContainer(
    urlsafe_game_key=messages.StringField(1), )
GET_ALL_GAMES_REQUEST = endpoints.ResourceContainer()
GET_GAMES_BY_USER_REQUEST = endpoints.ResourceContainer(
    user_name=messages.StringField(1), )
USER_REQUEST = endpoints.ResourceContainer(user_name=messages.StringField(1),
                                           email=messages.StringField(2))
USER_RANK_REQUEST = endpoints.ResourceContainer(user_name = messages.StringField(1),)

MEMCACHE_USER_STATS = 'USER_STATS'

@endpoints.api(name='rock_paper_scissors', version='v1')
class RockPaperScissorsApi(remote.Service):
    """Rock, Paper, Scissors Game API"""

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=StringMessage,
                      path='user',
                      name='create_user',
                      http_method='POST')
    def create_user(self, request):
        """Create a User. Requires a unique username"""
        if User.query(User.name == request.user_name).get():
            raise endpoints.ConflictException(
                'A User with the name {} already exists!'.format(request.user_name))
        user = User(name=request.user_name, email=request.email)
        user.put()
        return StringMessage(message='User {} created!'.format(
            request.user_name))

    @endpoints.method(request_message= USER_RANK_REQUEST,
                      response_message= StringMessage,
                      path='user/ranking',
                      name = 'user_ranking',
                      http_method = 'GET')
    def get_user_rankings(self, request):
        """Inefficient way to find ranking, for the user request
        find the user and then compare win ratio with other users
        if win ratio is equal, compare the number of losses"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                'A User with the name {} does not exist!'.format(request.user_name))
        users = User.query(User.name != request.user_name)
        losses = user.losses
        wins = user.wins
        if (losses + wins) == 0:
            win_percent = 0.0
        else:
            win_percent = float(wins)/(losses + wins)
        ranking = 0
        total_users = 1
        for other_user in users:
            total_users = total_users + 1
            if (other_user.losses + other_user.wins) == 0:
                other_user_win_percent = 0.0
            else:
                other_user_win_percent = float(other_user.wins)/(other_user.wins+other_user.losses)
            if other_user_win_percent < win_percent:
                ranking = ranking - 1
            elif other_user_win_percent == win_percent:
                if other_user.losses >= losses:
                    ranking = ranking - 1
        ranking = total_users + ranking
        #Create a ranking message
        msg = "User {} Ranking {} Win Ratio {}".format(user.name, ranking, win_percent)
        return StringMessage(message = msg)

    @endpoints.method(request_message=NEW_GAME_REQUEST,
                      response_message=GameForm,
                      path='game',
                      name='new_game',
                      http_method='POST')
    def new_game(self, request):
        """Creates new rock, paper, scissors game.
        The creator passes information about two users who are 
        to play the game. Total number of rounds is optional"""
        user_one = User.query(User.name == request.user_one).get()
        if not user_one:
            raise endpoints.NotFoundException(
                'A User with the name {} does not exist!'.format(request.user_one))
        user_two = User.query(User.name == request.user_two).get()
        if not user_two:
            raise endpoints.NotFoundException(
                'A User with the name {} does not exist!'.format(request.user_two))
        if not request.total_rounds:
          game = Game.new_game(user_one.key, user_two.key)
        else:
          game = Game.new_game(user_one.key, user_two.key, request.total_rounds)
        # Use a task queue to update the user wins.
        # This is just a demonstration of memcache
        taskqueue.add(url='/tasks/cache_user_stats')
        return game.to_form("Game Successfully Created!")

    @endpoints.method(request_message=GET_ALL_GAMES_REQUEST,
                      response_message=GameForms,
                      path='game/get_all',
                      name='get_all_games',
                      http_method='GET')
    def get_all_games(self, request):
        """Return all games."""
        return GameForms(items=[game.to_form('') for game in Game.query()])

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=StringMessage,
                      path='game/{urlsafe_game_key}/history',
                      name='get_game_history',
                      http_method='GET')
    def get_game_history(self, request):
        """Return the history of the game
        History is returned only if the game is finished
        The message contains the weapons selected by both users
        and the game result"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)

        if not game:
            raise endpoints.NotFoundException('Game not found!')

        if game.game_over:
          msg = "User {} selected {}. User {} selected {}. Result {}" \
                  .format(game.user_one.get().name, game.player_one_weapons, 
                  game.user_two.get().name, game.player_two_weapons,
                  game.game_result)
        elif game.game_cancelled:
          msg = "Game cancelled"
        else:
          msg = "Game not yet completed"
        return StringMessage(message = msg)

    @endpoints.method(request_message=GET_GAMES_BY_USER_REQUEST,
                      response_message=GameForms,
                      path='game/get_by_user/{user_name}',
                      name='get_user_games',
                      http_method='GET')
    def get_user_games(self, request):
        """Return all games that the user is currently playing."""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                'A User with the name {} does not exist!'.format(request.user_name))

        games = Game.query(ndb.AND(Game.game_over == False, \
                ndb.OR(Game.user_one == user.key, Game.user_two == user.key)))
        return GameForms(items=[game.to_form(msg) for game in games])

    @endpoints.method(request_message=CANCEL_GAME_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}/cancel',
                      name='cancel_game',
                      http_method='POST')
    def cancel_game(self, request):
        """Cancel the game requested by user.
        Completed games will not be cancelled"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)

        if not game:
            raise endpoints.NotFoundException('Game not found!')

        if game.game_over:
            raise endpoints.BadRequestException('Completed game can not be cancelled!')
        
        game.game_cancelled = True            
        game.game_over = True
        game.game_result = 'unknown'
        game.put()
        return game.to_form("Game Successfully Cancelled!")
    
    @endpoints.method(request_message=SELECT_WEAPON_REQUEST,
                      response_message = GameForm,
                      path = 'game/{urlsafe_game_key}/select_weapon',
                      name = 'select_weapon',
                      http_method = 'POST')
    def select_weapon(self, request):
        """User selects the weapon and the game is updated"""
        game = get_by_urlsafe(request.urlsafe_key, Game)

        if not game:
            raise endpoints.NotFoundException('Game not found!')

        if game.game_over:
            raise endpoints.BadRequestException('Can not select weapon for completed/cancelled game')

        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                'A User with the name {} does not exist!'.format(request.user_name))
        # Find the weapon array for the user
        update_weapon = 0
        if game.user_one == user.key:
            update_weapon = 1
        else:
            if game.user_two == user.key:
                update_weapon = 2
            else:
                raise endpoints.NotFoundException('User {} is not a participant in this game!'.format(request.user_name))
        weapon = request.weapon.lower()
        # Default message if weapon not found in allowed weapons
        # Add weapon only if the user has not played the full 
        # quota of rounds
        msg = "Wrong Weapon Selected"
        if weapon in weapons:
            if update_weapon == 1:
                if len(game.player_one_weapons) < game.total_rounds:
                  game.player_one_weapons.append(weapon)
                  msg = "Weapon Successfully Updated"
                else:
                  msg = "You have played all your rounds"
            if update_weapon == 2:
                if len(game.player_two_weapons) < game.total_rounds:
                  game.player_two_weapons.append(weapon)
                  msg = "Weapon Successfully Updated"
                else:
                  msg = "You have played all your rounds"
            # Update winner and loser if the game is finished
            game.end_game_if_finished()
            game.put()
        return game.to_form(msg)

    @endpoints.method(response_message=StringMessage,
                      path='user_stats',
                      name='get_user_stats',
                      http_method='GET')
    def get_user_stats(self, request):
        """Get the cached user stats"""
        return StringMessage(message=memcache.get(MEMCACHE_USER_STATS) or 'No Stats Found')

    @staticmethod
    def _cache_user_stats():
        """Populates memcache with each NEW GAME. This is used to see the win 
        percentage of every user
        """
        users = User.query()
        msg = ''
        # Build memcache string that details stats for each player.
        for user in users:
            wins = user.wins
            losses = user.losses
            if wins + losses == 0:
                win_percent = 0.0
            else:
                win_percent = float(wins)/(wins+losses)
            one_player = "{} {} {} {} {} Win Ratio {} " \
                .format(user.name,
                        wins,
                        "win" if wins < 1 else "wins",
                        losses,
                        "loss" if losses < 1 else "losses",
                        win_percent
                        )

            msg += one_player

        memcache.set(MEMCACHE_USER_STATS, msg)

api = endpoints.api_server([RockPaperScissorsApi])
