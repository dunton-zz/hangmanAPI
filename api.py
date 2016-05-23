# -*- coding: utf-8 -*-`
"""api.py - Create and configure the Game API exposing the resources.
This can also contain game logic. For more complex games it would be wise to
move game logic to another file. Ideally the API will be simple, concerned
primarily with communication to/from the API's users."""

import re
import logging
import endpoints
from protorpc import remote, messages, message_types
from google.appengine.api import memcache
from google.appengine.api import taskqueue
from google.appengine.ext import ndb

from models import User, Game, Score, Word
from models import StringMessage, NewGameForm, GameForm, MakeMoveForm, \
    ScoreForms, UserGamesForm, GameForms, HighScores, IntegerMessage
from models import UserForms 
from utils import get_by_urlsafe

NEW_GAME_REQUEST = endpoints.ResourceContainer(NewGameForm)
GET_GAME_REQUEST = endpoints.ResourceContainer(
        urlsafe_game_key=messages.StringField(1),)
MAKE_MOVE_REQUEST = endpoints.ResourceContainer(
    MakeMoveForm,
    urlsafe_game_key=messages.StringField(1),)
USER_REQUEST = endpoints.ResourceContainer(user_name=messages.StringField(1),
                                           email=messages.StringField(2))
GET_ALL_GAMES_REQUEST = endpoints.ResourceContainer(user_name=messages.StringField(1),)
HIGH_SCORES_REQUEST = endpoints.ResourceContainer(
        number_of_results=messages.IntegerField(1))
CANCEL_GAME_REQUEST = endpoints.ResourceContainer(urlsafe_game_key=messages.StringField(1),)


MEMCACHE_MOVES_REMAINING = 'MOVES_REMAINING'

@endpoints.api(name='hangman', version='v1')
class HangmanApi(remote.Service):
    """Game API"""
    @endpoints.method(request_message=USER_REQUEST,
                      response_message=StringMessage,
                      path='user',
                      name='create_user',
                      http_method='POST')
    def create_user(self, request):
        """Create a User. Requires a unique username"""
        if User.query(User.name == request.user_name).get():
            raise endpoints.ConflictException(
                    'A User with that name already exists!')
        user = User(name=request.user_name, email=request.email)
        #user.key = ndb.Key(User, user.name)
        user.put()
        return StringMessage(message='User {} created!'.format(
                request.user_name))

    @endpoints.method(request_message=NEW_GAME_REQUEST,
                      response_message=GameForm,
                      path='game',
                      name='new_game',
                      http_method='POST')
    def new_game(self, request):
        """Creates new game"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        word = Word.query(Word.word_to_guess == request.word).get()
        if not word:
            word = Word(word_to_guess=request.word)
            word.put()
        try:
            game = Game.new_game(user.key,
                                 word.key.urlsafe()
                                 #attempts = 12
                                 )
            return game.to_form('Good luck playing Hangman!')
        except:
            raise
        

        # Use a task queue to update the average attempts remaining.
        # This operation is not needed to complete the creation of a new game
        # so it is performed out of sequence.
        # taskqueue.add(url='/tasks/cache_average_attempts')
        # return game.to_form('Good luck playing Hangman!')

    

    @endpoints.method(request_message=MAKE_MOVE_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='make_move',
                      http_method='PUT')
    def make_move(self, request):
        """Makes a move. Returns a game state with message"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if not game:
          raise endpoints.NotFoundException("We could not find your game!")

        if game.game_over:
          return game.to_form('That game is over, sorry')
        
        if request.guess in game.letters_guessed:
          respond_to_user = 'You already guessed that letter'
          respond_to_user = respond_to_user.format(request.guess)
          return game.to_form(respond_to_user)

        game_word = game.get_word()
        game.history.append(request.guess)

        if request.guess not in game_word:
          game.letters_guessed += request.guess
          game.attempts_remaining -= 1

          if game.attempts_remaining == 0:
            game.end_game(won=False)
            respond_to_user = 'You lose, the word was {}'
            respond_to_user = respond_to_user.format(game_word)
          else:
            respond_to_user = 'The letter {} is not in the word'
            respond_to_user = respond_to_user.format(request.guess)

          game.put()
          return game.to_form(respond_to_user)

        else:

          game.letters_guessed += request.guess

          for (index, letter) in enumerate(game_word):
            if letter == request.guess:
              game.word_so_far = game.word_so_far[0:index] + request.guess + game.word_so_far[index + 1:]
          
          if game.word_so_far == game_word:
            game.end_game(won=True)
            respond_to_user = 'Great job! You won!!! You guessed {}'
            respond_to_user = respond_to_user.format(game_word)
          else:
            respond_to_user = 'Good guess! {} is in the word!'
            respond_to_user = respond_to_user.format(request.guess)

          game.put()
          return game.to_form(respond_to_user)

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='get_game',
                      http_method='GET')
    def get_game(self, request):
        """Return the current game state."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            return game.to_form('Go and make a move!')
        else:
            raise endpoints.NotFoundException('Could not find your game!')


    #### Part of Udacity required endpoint ###
    @endpoints.method(request_message=GET_ALL_GAMES_REQUEST,
                      response_message=GameForms,
                      path='game/user/{user_name}',
                      name='get_user_games',
                      http_method='GET')
    def get_user_games(self, request):
        '''Get all active games a user is playing'''
        user = User.query(User.name == request.user_name).get()
        if not user:
            #raise endpoints.NotFoundException('A user with that name does not exist')
        
        # attempt to match user and user key
        #games = Game.query()
        #games = Game.query(Game.user == user.key)
                #game_forms = []
        #for game in games:
        #  hide = True
         # if game.game_over != True:
          #  hide = False
          #singleGameForm = game.to_form()
          #game_forms.append(singleGameForm)
        return GameForms(items=[game.to_form() for game in Game.query()])
        #return StringMessage(message= str(user_key))

    #### End it ########
  
    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=StringMessage,
                      path='game/{urlsafe_game_key}/history',
                      name='gamehistory',
                      http_method='GET')
    def get_game_history(self, request):
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if not game:
          raise endpoints.NotFoundException('Game not found!')
        return StringMessage(message=str(game.history))
    ##This is correct for ScoreForms iteration
    
    @endpoints.method(response_message=ScoreForms,
                      path='scores',
                      name='get_scores',
                      http_method='GET')
    def get_scores(self, request):
        """Return all scores"""
        return ScoreForms(items=[score.to_form() for score in Score.query()])
    

    @endpoints.method(request_message=CANCEL_GAME_REQUEST,
                      response_message=StringMessage,
                      path='cancel/{urlsafe_game_key}',
                      name='cancel_game',
                      http_method='PUT')
    def cancel_game(self,request):
        '''Cancel an active game'''
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if not game:
          raise endpoints.NotFoundException("We could not find your game!")

        if game.game_over == False:

          game.key.delete()
          return StringMessage(message="Game cancelled!")
        else: 
          return StringMessage(message="You can't delete a completed game!")

        

    #@endpoints.method(request_message=USER_REQUEST,
                  #    response_message=ScoreForms,
                  #    path='scores/user/{user_name}',
                  #    name='get_user_scores',
                  #    http_method='GET')
    #def get_user_scores(self, request):
    #  """Returns all of an individual User's scores"""
    #  user = User.query(User.name == request.user_name).get()
     # if not user:
      #    raise endpoints.NotFoundException(
      #            'A User with that name does not exist!')
     # scores = Score.query(Score.user == user.key)
     # return ScoreForms(items=[score.to_form() for score in scores])

     #A ranking of users by taking wins/total games tie breaker
     #being spot on the leaderboard

    @endpoints.method(
                      response_message=UserForms,
                      path='user_rankings',
                      name='get_user_rankings',
                      http_method='GET')
    def get_user_rankings(self, request):
      # count number of times user appears in Score database
      users = User.query(User.score >= 0).fetch()
      #users = users.order(users, key=lambda x: x.score, reverse=True)
      return UserForms(items=[user.to_form() for user in users])
      
      


    @endpoints.method(request_message=HIGH_SCORES_REQUEST,
                      response_message=ScoreForms,
                      path='scores/leaderboard',
                      name='high_score_leaderboard',
                      http_method='GET')
    def get_high_scores(self, request):
      '''Order scores by attempts remaining for high score list'''
      scores = Score.query()
      scores = scores.order(-Score.attempts_remaining)
      
      if request.number_of_results :
        number = int(request.number_of_results)
        scores = scores.fetch(number)
        return ScoreForms(items=[score.to_form() for score in scores])
      else:
        return ScoreForms(items=[score.to_form() for score in scores])
     
    @endpoints.method(response_message=StringMessage,
                      path='games/average_attempts',
                      name='get_average_attempts_remaining',
                      http_method='GET')
    def get_average_attempts(self, request):
      """Get the cached average moves remaining"""
      return StringMessage(message=memcache.get(MEMCACHE_MOVES_REMAINING) or '')

    @staticmethod
    def _cache_average_attempts():
        """Populates memcache with the average moves remaining of Games"""
        games = Game.query(Game.game_over == False).fetch()
        if games:
            count = len(games)
            total_attempts_remaining = sum([game.attempts_remaining
                                        for game in games])
            average = float(total_attempts_remaining)/count
            memcache.set(MEMCACHE_MOVES_REMAINING,
                         'The average moves remaining is {:.2f}'.format(average))


api = endpoints.api_server([HangmanApi])

    
