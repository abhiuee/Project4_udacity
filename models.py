"""models.py - This file contains the class definitions for the Datastore
entities used by the Rock, Paper, Scissors game."""

import random
from datetime import date
from protorpc import messages
from google.appengine.ext import ndb

weapons = ['rock','paper','scissors']

class User(ndb.Model):
    """User profile"""
    name = ndb.StringProperty(required=True)
    email =ndb.StringProperty()
    wins = ndb.IntegerProperty(default = 0)
    losses = ndb.IntegerProperty(default = 0)


class Game(ndb.Model):
    """Game object"""
    player_one_weapons = ndb.StringProperty(repeated = True)
    player_two_weapons = ndb.StringProperty(repeated = True)
    total_rounds = ndb.IntegerProperty(required = True)
    game_result = ndb.StringProperty(required=True, default = 'unknown')
    game_over = ndb.BooleanProperty(required=True, default = False)
    user_one = ndb.KeyProperty(required=True, kind='User')
    user_two = ndb.KeyProperty(required = True, kind='User')
    game_cancelled = ndb.BooleanProperty(required = True, default = False)

    @classmethod
    def new_game(cls, user_one, user_two, total_rounds = 1):
        """Creates and returns a new game"""
        game = Game(user_one=user_one,
                    user_two = user_two,
                    total_rounds = total_rounds
                    )
        game.put()
        return game

    def end_game_if_finished(self):
        """Once the player has selected a weapon, check if the game is ready
        to be evaluated. If yes, then update the wins and losses for the player
        and game result"""
        list_player_two_weapons = self.player_two_weapons
        list_player_one_weapons = self.player_one_weapons
        #Game can have result only if both players have finished their rounds 
        if len(list_player_one_weapons) == len(list_player_two_weapons):
            if len(list_player_two_weapons) == self.total_rounds:
                u1 = self.user_one.get()
                u2 = self.user_two.get()
                num_wins_player_1 = 0
                num_wins_player_2 = 0
                #For every round, find the winner, if result unknown don't update 
                #the winner
                for i in range(0, self.total_rounds):
                    w1 = list_player_one_weapons[i]
                    w2 = list_player_two_weapons[i]
                    if w1 != w2:
                        if w1 == 'rock':
                            if w2 == 'scissors': 
                                num_wins_player_1 = num_wins_player_1 + 1
                            elif w2 == 'paper':
                                num_wins_player_2 = num_wins_player_2 + 1

                        if w1 == 'paper':
                            if w2 == 'rock':
                                num_wins_player_1 = num_wins_player_1 + 1
                            elif w2 == 'scissors': 
                                num_wins_player_2 = num_wins_player_2 + 1

                        if w1 == 'scissors':
                            if w2 == 'paper':
                                num_wins_player_1 = num_wins_player_1 + 1
                            elif w2 == 'rock': 
                                num_wins_player_2 = num_wins_player_2 + 1
                self.game_over = True
                if num_wins_player_2 > num_wins_player_1:
                    self.game_result = "{} won {} by {}" \
                                        .format(u2.name,num_wins_player_2,num_wins_player_1)
                    u2.wins = u2.wins + 1
                    u1.losses  = u1.losses + 1
                    u1.put()
                    u2.put()
                elif num_wins_player_1 > num_wins_player_2:
                    self.game_result = "{} won {} by {}". \
                                        format(u1.name,num_wins_player_1,num_wins_player_2)
                    u1.wins = u1.wins + 1
                    u2.losses  = u2.losses + 1
                    u1.put()
                    u2.put()
                else:
                    self.game_result = "Draw"
            else:
                self.game_over = False
        else:
            self.game_over = False


    def to_form(self, message):
        """Returns a GameForm representation of the Game"""
        form = GameForm()
        form.urlsafe_key = self.key.urlsafe()
        #Cache the user names for message creation purposes
        user_one_name = self.user_one.get().name
        user_two_name = self.user_two.get().name
        #Fill user names 
        form.user_one_name = user_one_name
        form.user_two_name = user_two_name

        #Edit message field based on whether the game is over or not
        if self.game_cancelled:
            form_message = "{} Status: Game cancelled".format(message)
        else:
            if not self.game_over:
                form_message = "{} Status: Game not completed".format(message)
            else:
                form_message = "{} Status: Game completed: {}".format(message, self.game_result)
        
        form.message = form_message
        return form

class NewGameForm(messages.Message):
    """Used to create a new game"""
    user_one = messages.StringField(1, required=True)
    user_two = messages.StringField(2, required=True)
    total_rounds = messages.IntegerField(3)


class GameForm(messages.Message):
    """GameForm for outbound game state information"""
    urlsafe_key = messages.StringField(1, required=True)
    user_one_name = messages.StringField(2, required=True)
    user_two_name = messages.StringField(3, required=True)
    message = messages.StringField(4, required=True)

class GameForms(messages.Message):
    """Return multiple GameForms"""
    items = messages.MessageField(GameForm, 1, repeated=True)

class StringMessage(messages.Message):
    """StringMessage-- outbound (single) string message"""
    message = messages.StringField(1, required=True)

class WeaponForm(messages.Message):
    """Form to select weapon"""
    urlsafe_key = messages.StringField(1, required = True)
    user_name = messages.StringField(2, required = True)
    weapon = messages.StringField(3, required = True)
