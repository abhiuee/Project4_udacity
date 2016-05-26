#Full Stack Nanodegree Project 4

## Set-Up Instructions:
1.  Update the value of application in app.yaml to the app ID you have registered
 in the App Engine admin console and would like to use to host your instance of this sample.
1.  Run the app with the devserver using dev_appserver.py DIR, and ensure it's
 running by visiting the API Explorer - by default localhost:8080/_ah/api/explorer.
1.  (Optional) Generate your client library(ies) with the endpoints tool.
 Deploy your application.
 
 
##Game Description:
The game is called Rock Paper Scissors. This game is to be played between two players. To create a
game, you need to provide two registered user names and optionally provide the total number of rounds
you intend to play (by default only 1 round is played). The logic is simple, each player selects the 
weapons he/she wants to use in each round. Once both the players select weapons for every round, the 
winner is declared. The logic is a player who decides to play rock will beat another player who has 
chosen scissors ("rock crushes scissors") but will lose to one who has played paper ("paper covers rock"); 
a play of paper will lose to a play of scissors ("scissors cut paper")

##Score Keeping:
Each game is played between two users. When the game starts the status of the game is incomplete and unknown. Once both the users, play all the rounds, winner is selected based on the logic of the game.
Wins and losses properties for each user are updated once the winner is selected. Winner of game gets 
wins+1 while loser of the game gets losses+1. Also the ranking is based on the win ratio that is number
of wins/ (number of wins + number of losses). If two users have the same win ratio, the user with lesser
number of losses is given priority.

##Files Included:
 - api.py: Contains endpoints and game playing logic.
 - app.yaml: App configuration.
 - cron.yaml: Cronjob configuration.
 - main.py: Handler for taskqueue handler and reminder email
 - models.py: Entity and message definitions including helper methods.
 - utils.py: Helper function for retrieving ndb.Models by urlsafe Key string.

##Endpoints Included:
 - **create_user**
    - Path: 'user'
    - Method: POST
    - Parameters: user_name, email (optional)
    - Returns: Message confirming creation of the User.
    - Description: Creates a new User. user_name provided must be unique. Will 
    raise a ConflictException if a User with that user_name already exists.
    
 - **new_game**
    - Path: 'game'
    - Method: POST
    - Parameters: user_one, user_two, total_rounds (optional)
    - Returns: GameForm with initial game state.
    - Description: Creates a new Game. user_one and user_two must be registered users
      NotFoundException is raised if either users are not present in the database.
      Also adds a task to a task queue to update the user_stats.

- **get_user_ranking**
    - Path: 'user/ranking'
    - Method: GET
    - Parameters: user_name
    - Returns: StringMessage which contains the user name, ranking and win ratio.
    - Description: Returns the ranking of the user based on the win ratio and the losses.
      NotFoundException is raised if the user is not registered.

 - **get_user_rankings**
    - Path: 'user/rankings'
    - Method: GET
    - Parameters: None
    - Returns: StringMessage which contains list of user name, ranking and win ratio.
    - Description: Returns the list of users sorted by the ranking based on the win_ratio
      and losses. It uses the class method order_by_ranking which returns a list of users
      ordered by the win_ratio and number of losses
    
 - **get_all_games**
    - Path: 'game/get_all'
    - Method: GET
    - Parameters: none
    - Returns: GameForms with game states.
    - Description: Returns all the games that were created in the application
    
 - **get_game_history**
    - Path: 'game/{urlsafe_game_key}/history'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: StringMessage
    - Description: If the game is completed, returns the moves made by each player 
      and the result of the game. If game is not found, NotFoundException is raised.
      If the game is cancelled or not completed, equivalent messages are generated.
      Player moves are not returned for incomplete games. 
    
 - **get_user_games**
    - Path: 'game/get_by_user/{user_name}'
    - Method: GET
    - Parameters: user_name
    - Returns: GameForms 
    - Description: Returns all the games that are currently being played by the user.
      NotFoundException is raised if the user is not registered.
    
 - **cancel_game**
    - Path: 'game/{urlsafe_game_key}/cancel'
    - Method: PUT
    - Parameters: urlsafe_game_key
    - Returns: GameForm
    - Description: Cancels the selected game. NotFoundException is raised if game not found.
      BadRequestException is raised if the user tries to cancel a game that is already completed.

- **get_user_stats**
    - Path: 'user_stats'
    - Method: GET
    - Parameters: none
    - Returns: StringMessage
    - Description: Returns the cached wins, losses and win ratio for every user in a string message.

- **select_weapon**
    - Path: 'game/select_weapon'
    - Method: PUT
    - Parameters: urlsafe_key, user_name and weapon
    - Returns: GameForm
    - Description: Allows user to select the weapon for the particular game. 
      NotFoundException is raised if game or user not found.
      BadRequestException is raised if the user tries to play a game that is already completed.
      If the total rounds for the user are over, correct error handling is performed. If the 
      weapon selected is not one of Rock Paper Scissors, the user is provided with the information
      If all the weapons for each round are selected, game results are updated and provided in the
      GameForm

##Models Included:
 - **User**
    - Stores unique user_name and (optional) email address, wins, losses and win_ratio.
    
 - **Game**
    - Stores unique game states. Associated with User model via KeyProperty.
    
##Forms Included:
 - **GameForm**
    - Representation of a Game's state (urlsafe_key, attempts_remaining,
    game_over flag, message, user_name).
 - **NewGameForm**
    - Used to create a new game (user_name, min, max, attempts)
 - **WeaponForm**
    - Inbound select weapon form (game_id, user_name and weapon)
 - **GameForms**
    - Multiple GameForm container.
 - **StringMessage**
    - General purpose String container.

##Endpoints Not Implemented:
 - **get_high_scores**
    - The game is a two player game and the project description states that
       there is no need to implement this endpoint in a two player game

##Reminder Email Enhancements:
 - Reminder email is not sent to every user. Only users who have active
   games and need to complete their moves are sent reminder emails.
