# HangmanAPI

This is an endpoints API designed for a user to play hangman. This API gives the user a fixed number of attempts (12) to guess a word and gives them points based on how many attempts they have remaining.

### Getting Started

This API was configured through Google App Engine, so it can be found at **ryans**-**game**.**appspot**.**com**/_**ah**/**api**/**explorer**. To play simply create a user, make moves and check out the other endpoints! This API also utilizes CRON to send a reminder every 24 hours to users who have unfinished games.

### Files
 
You should find 8 files in the HangmanAPI repository. These files are:

* **README**.**md**
* **api**.**py**
* **app**.**yaml**
* **cron**.**yaml**
* **index**.**yaml**
* **main**.**py**
* **models**.**py**
* **utils**.**py**

### Endpoints

These are all the endpoints found in the API

* **hangman.cancel_game**
  * Path: 'cancel/{urlsafe_game_key}'
  * Method: DELETE
  * Parameters: urlsafe_game_key
  * Returns: String saying your game is deleted
  * Description: Deletes specified game
* **hangman.create_user**
  * Path: 'create_user'
  * Method: POST
  * Parameters: user_name, email
  * Returns: String message confirming user creation
  * Description: Creates a new user
* **hangman.gamehistory**
  * Path: 'game/{urlsafe_game_key}'
  * Method: GET
  * Parameters: urlsafe_game_key
  * Returns: GameForm with current game state.
  * Description: Returns the current state of a game.
* **hangman.get_game**
  * Path: 'game/{urlsafe_game_key}'
  * Method: GET
  * Parameters: urlsafe_game_key
  * Returns: GameForm with current game state.
  * Description: Returns the current state of a game.
* **hangman.get_scores**
  * Path: 'get_scores'
  * Method: GET
  * Parameters: none
  * Returns: Returns all scores
  * Description: Returns the scores of all users
* **hangman.get_user_games**
  * Path: 'game/user/{user_name}'
  * Method: GET
  * Parameters: user_name
  * Returns: GameForms of all active games for user
  * Description: Returns the active game forms for a user
* **hangman.get_user_rankings**
  * Path: 'user_rankings'
  * Method: GET
  * Parameters: none
  * Returns: UserForms ordered by each user's score
  * Description: Returns a users ranked by score
* **hangman.high_score_leaderboard**
  * Path: 'scores/leaderboard'
  * Method: GET
  * Parameters: number_of_results
  * Returns: The n highest scores where n = number_of_results
  * Description: Returns leaderboards of highest scores
* **hangman.make_move**
  * Path: 'game/{urlsafe_game_key}'
  * Method: PUT
  * Parameters: urlsafe_game_key
  * Returns: GameForm with result of your guess
  * Description: A GameForm telling you if your guess was correct 
* **hangman.new_game**
  * Path: 'game'
  * Method: POST
  * Parameters: user, word
  * Returns: String telling you 'good luck' and a GameForm
  * Description: Returns GameForm for new game

### Objective and Score Keeping

The objective of hangman is to guess the word before you run out of attempts! In this case the number of attempts is fixed at 12. The score is simply the number of attempts remaining when the user wins. Users will then be ranked by their total score. Make moves until you run out of attempts or guess your word!!!