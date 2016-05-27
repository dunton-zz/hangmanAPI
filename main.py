#!/usr/bin/env python

"""main.py - This file contains handlers that are called by taskqueue and/or
cronjobs."""
import logging

import webapp2
from google.appengine.api import mail, app_identity

from models import Game, User


class SendReminderEmail(webapp2.RequestHandler):
    def get(self):
        """Send a reminder email to each User with an email about games.
        Once a day if they have unfinished games"""
        app_id = app_identity.get_application_id()
        users = User.query()  # NOQA
    
        for user in users:
            subject = "You have unfinished games!"
            body = '''Hey {}, you have unfinished games!'''.format(user.name)

            qry1 = Game.query(Game.user == user.key)
            games = qry1.filter(Game.game_over == False)

            if games.count() > 0:
                games_active = ''' You have {} game(s) in progress. The keys for those games are: {}'''.\
                                format(games.count(), ''', 
                                    '''.
                                       join(game.key.urlsafe() for game in games))

                body += games_active

            logging.debug(body)

            # This will send test emails, the arguments to send_mail are:
            # from, to, subject, body
            mail.send_mail('noreply@{}.appspotmail.com'.format(app_id),
                           user.email,
                           subject,
                           body)




app = webapp2.WSGIApplication([
    ('/crons/send_reminder', SendReminderEmail),
], debug=True)
