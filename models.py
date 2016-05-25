"""models.py - This file contains the class definitions for the Datastore
entities used by the Game. Because these classes are also regular Python
classes they can include methods (such as 'to_form' and 'new_game')."""

import math
import random
from datetime import date
from protorpc import messages
from google.appengine.ext import ndb

import endpoints

from utils import get_by_urlsafe


class User(ndb.Model):
    """User profile"""
    name = ndb.StringProperty(required=True)
    email = ndb.StringProperty(required=True)
    score = ndb.IntegerProperty(default=0)
    games = ndb.IntegerProperty(default=0)

    def to_form(self):
        return UserForm(
            name=self.name,
            email=self.email,
            score=self.score,
            games=self.games)

    def add_score(self, attempts_remaining):
        '''Add points to user total'''
        points = attempts_remaining
        self.score += points
        self.put()
        return points

    def subtract_attempts(self, points):
        self.score - points
        self.put()

    def add_game(self):
        self.games += 1
        self.put()


class Word(ndb.Model):
    '''Word to guess'''
    word_to_guess = ndb.StringProperty(required=True)


class Game(ndb.Model):
    """Game object"""
    word_key = ndb.KeyProperty(kind='Word')
    attempts_remaining = ndb.IntegerProperty(default=12)
    game_over = ndb.BooleanProperty(default=False)
    score = ndb.IntegerProperty(default=0)
    letters_guessed = ndb.StringProperty(default='')
    word_so_far = ndb.StringProperty(default='')
    user = ndb.KeyProperty(kind='User')
    history = ndb.PickleProperty()

    @classmethod
    def new_game(cls, user, word_urlsafe_key):
        """Creates and returns a new game"""

        attempts = 12
        word = get_by_urlsafe(word_urlsafe_key, Word)
        if not user:
            raise endpoints.NotFoundException('User not found')
        if not word:
            raise endpoints.NotFoundException('Word not found')
        game = Game(word_key=word.key,
                    attempts_remaining=attempts,
                    game_over=False,
                    letters_guessed='',
                    word_so_far='',
                    user=user)

        game.history = []
        game.put()
        return game

    def to_form(self, message):
        """Returns a GameForm representation of the Game"""
        form = GameForm()
        form.urlsafe_key = self.key.urlsafe()
        form.user_name = self.user.get().name
        form.attempts_remaining = self.attempts_remaining
        form.word_so_far = self.word_so_far
        # form.letters_guessed = self.letters_guessed
        form.score = self.score
        form.game_over = self.game_over
        # form.history = self.history
        form.message = message
        return form

    def get_word(self):
        '''Get game word in string form'''
        return self.word_key.get().word_to_guess

    def add_points(self):
        points = self.user.get().add_score(self.attempts_remaining)
        self.score += points

    def end_game(self, won=False):
        """Ends the game - if won is True, the player won. - if won is False,
        the player lost."""
        self.game_over = True
        self.put()
        # Add the game to the score 'board'
        score = Score(user=self.user,
                      date=date.today(),
                      won=won,
                      attempts_remaining=self.attempts_remaining,
                      game=self.key)

        score_id = Score.allocate_ids(size=1, parent=self.key)[0]
        score.key = ndb.Key(Score, score_id, parent=self.key)

        score.put()
        self.add_points()
        self.user.get().add_game()


class Score(ndb.Model):
    """Score object"""
    user = ndb.KeyProperty(required=True, kind='User')
    date = ndb.DateProperty(required=True)
    won = ndb.BooleanProperty(required=True)
    attempts_remaining = ndb.IntegerProperty(required=True)
    game = ndb.KeyProperty(required=True, kind='Game')

    def to_form(self):
        return ScoreForm(user=self.user.get().name, won=self.won,
                         date=str(self.date),
                         attempts_remaining=self.attempts_remaining,
                         game=self.game.urlsafe())


class GameForm(messages.Message):
    """GameForm for outbound game state information"""
    urlsafe_key = messages.StringField(1)
    user_name = messages.StringField(2)
    attempts_remaining = messages.IntegerField(3)
    word_so_far = messages.StringField(4)
    game_over = messages.BooleanField(5)
    score = messages.IntegerField(6)
    message = messages.StringField(7)


class UserForm(messages.Message):
    '''User form class'''
    name = messages.StringField(1, required=True)
    email = messages.StringField(2, required=True)
    score = messages.IntegerField(3, required=True)
    games = messages.IntegerField(4, required=True)


class UserForms(messages.Message):
    '''Returns multiple User Forms'''
    items = messages.MessageField(UserForm, 1, repeated=True)


class NewGameForm(messages.Message):
    """Used to create a new game"""
    user_name = messages.StringField(1, required=True)
    word = messages.StringField(2, required=True)


class GameForms(messages.Message):
    """Return multiple ScoreForms"""
    items = messages.MessageField(GameForm, 1, repeated=True)


class MakeMoveForm(messages.Message):
    """Used to make a move in an existing game"""
    guess = messages.StringField(1, required=True)


class ScoreForm(messages.Message):
    """ScoreForm for outbound Score information"""
    user = messages.StringField(1, required=True)
    date = messages.StringField(2, required=True)
    won = messages.BooleanField(3, required=True)
    attempts_remaining = messages.IntegerField(4, required=True)
    game = messages.StringField(5, required=True)


class ScoreForms(messages.Message):
    """Return multiple ScoreForms"""
    items = messages.MessageField(ScoreForm, 1, repeated=True)


class StringMessage(messages.Message):
    """StringMessage-- outbound (single) string message"""
    message = messages.StringField(1, required=True)


class IntegerMessage(messages.Message):
    '''Returns message with an integer'''
    message = messages.IntegerField(1)


class UserGamesForm(messages.Message):
    '''Username for all user's games '''
    user_name = messages.StringField(1, required=True)


class HighScores(messages.Message):
    '''Specifies how many high scores to see'''
    number_of_results = messages.IntegerField(1, required=False)