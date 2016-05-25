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
* **hangman.create_user**
* **hangman.gamehistory**
* **hangman.get_game**
* **hangman.get_scores**
* **hangman.get_user_games**
* **hangman.get_user_rankings**
* **hangman.high_score_leaderboard**
* **hangman.make_move**
* **hangman.new_game**

### Objective and Score Keeping

The objective of hangman is to guess the word before you run out of attempts! In this case the number of attempts is fixed at 12. The score is simply the number of attempts remaining when the user wins. Users will then be ranked by their total score. Make moves until you run out of attempts or guess your word!!!