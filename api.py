# -*- coding: utf-8 -*-`
'''
Hangman Game API 
By: Ryan Dunton
Date: May 26, 2016'''

import re
import logging
import endpoints
from protorpc import remote, messages, message_types
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
GET_ALL_GAMES_REQUEST = endpoints.ResourceContainer(user_name=messages.StringField(1),)  # NOQA
HIGH_SCORES_REQUEST = endpoints.ResourceContainer(
        number_of_results=messages.IntegerField(1))

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
                                 word.key.urlsafe())
            return game.to_form('Good luck playing Hangman!')
        except:
            raise


    @endpoints.method(request_message=MAKE_MOVE_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='make_move',
                      http_method='PUT')
    def make_move(self, request):
        """Makes a move. Returns a game state with message"""

        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        
        # Verify Game
        if not game:
            raise endpoints.NotFoundException("We could not find your game!")
        
        # Verify game is active
        if game.game_over:
            return game.to_form('That game is over, sorry')

        # Verify guess is a letter    
        if (request.guess.isalpha()):

            game_word = game.get_word()
            game.history.append("(User's guess was " + request.guess + ")")
            # Allow user to guess the whole world
            if len(request.guess) == len(game_word):
                if request.guess == game_word:
                    game.word_so_far = request.guess
                    respond_to_user = 'You guessed the word! You won!'  
                    game.end_game(won=True)
                    return game.to_form(respond_to_user)
            
            # If user guesses too long let them know and take away attempt
            if len(request.guess) > len(game_word):
                game.attempts_remaining -= 1
                respond_to_user = 'Your guess is too long!'
                return game.to_form(respond_to_user)
            
            # Verify guess is just one letter
            if len(request.guess) == 1:

                if request.guess in game.letters_guessed:
                    respond_to_user = 'You already guessed that letter'
                    respond_to_user = respond_to_user.format(request.guess)
                    return game.to_form(respond_to_user)

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
            
            # This occurs when user guesses more than one letter and length of guess is
            # less than the word
            else:

                game.attempts_remaining -= 1
                respond_to_user = 'That is not the word. Try to guess the whole word again or guess one letter at a time'
                return game.to_form(respond_to_user)
        
        else:
            #game.history.append("User guessed " + request.guess + ', not a valid guess!')    
            raise endpoints.BadRequestException('Guess is not a letter!')

        
            
        


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

    @endpoints.method(request_message=GET_ALL_GAMES_REQUEST,
                      response_message=GameForms,
                      path='game/user/{user_name}',
                      name='get_user_games',
                      http_method='GET')
    def get_user_games(self, request):
        '''Get all active games a user is playing'''
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException('''A user with that name does not exist''')

        # attempt to match user and user key
        qry1 = Game.query(Game.user == user.key)
        games = qry1.filter(Game.game_over == False)
        return GameForms(items=[game.to_form("Active Game!") for game
                                in games])

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=StringMessage,
                      path='game/{urlsafe_game_key}/history',
                      name='gamehistory',
                      http_method='GET')
    def get_game_history(self, request):
        '''Returns all moves made in game'''
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if not game:
            raise endpoints.NotFoundException('Game not found!')
        return StringMessage(message=str(game.history))

    @endpoints.method(response_message=ScoreForms,
                      path='scores',
                      name='get_scores',
                      http_method='GET')
    def get_scores(self, request):
        """Return all scores"""
        return ScoreForms(items=[score.to_form() for score in Score.query()])

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=StringMessage,
                      path='cancel/{urlsafe_game_key}',
                      name='cancel_game',
                      http_method='DELETE')
    def cancel_game(self, request):
        '''Cancel an active game'''
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if not game:
            raise endpoints.NotFoundException("We could not find your game!")

        if game.game_over == False:  # NOQA

            game.key.delete()
            return StringMessage(message="Game cancelled!")
        else:
            return StringMessage(message="You can't delete a completed game!")

    @endpoints.method(
                      response_message=UserForms,
                      path='user_rankings',
                      name='get_user_rankings',
                      http_method='GET')
    def get_user_rankings(self, request):
        '''Rank users by scores'''
        qry1 = User.query(User.score >= 0)
        users = qry1.order(-User.score)
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

        if request.number_of_results:
            number = int(request.number_of_results)
            scores = scores.fetch(number)
            return ScoreForms(items=[score.to_form() for score in scores])
        else:
            return ScoreForms(items=[score.to_form() for score in scores])

api = endpoints.api_server([HangmanApi])
    
