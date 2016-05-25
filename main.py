#!/usr/bin/env python
# coding=utf-8

"""main.py - This file contains handlers that are called by taskqueue and/or
cronjobs."""
import logging

from google.appengine.ext import ndb
import webapp2
from google.appengine.api import mail, app_identity
from api import RockPaperScissorsApi

from models import User, Game

class SendReminderEmail(webapp2.RequestHandler):
    def get(self):
        """Send a reminder email to each User with unifinished games with an email about games.
        Called every hour using a cron job"""
        app_id = app_identity.get_application_id()
        users = User.query(User.email != None)
        send_email = False
        for user in users:
            games = Game.query(ndb.AND(Game.game_over == False, ndb.OR(Game.user_one == user.key, Game.user_two == user.key)))
            # Check if the user has any unfinished turns
            for game in games:
                if game.user_one == user.key:
                    if len(game.player_one_weapons) < game.total_rounds:
                        send_email = True
                        break
                else:
                    if len(game.player_two_weapons) < game.total_rounds:
                        send_email = True
                        break
            if send_email:
                subject = 'This is a reminder!'
                body = 'Hello {}, your opponents are waiting for your turn in the wonderful game of Rock Paper and Scissors !'.format(user.name)
                # This will send test emails, the arguments to send_mail are:
                # from, to, subject, body
                mail.send_mail('noreply@{}.appspotmail.com'.format(app_id),
                           user.email,
                           subject,
                           body)


class UpdateUserStats(webapp2.RequestHandler):
    def post(self):
        """Update user stats in memcache."""
        RockPaperScissorsApi._cache_user_stats()
        self.response.set_status(204)

app = webapp2.WSGIApplication([
    ('/crons/send_reminder', SendReminderEmail),
    ('/tasks/cache_user_stats', UpdateUserStats),
], debug=True)
