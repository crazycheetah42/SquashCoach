# Imports

# Creating variables
cl_rating = float(input("What is your current US Squash rating?\n"))
initial_elo = 1000 + (cl_rating * 200)
games_won = int(input("How many games did you win?\n"))
games_lost = int(input("How many games did you lose? \n"))
total_games = games_won + games_lost
game_ratio = games_won / total_games
user_points = 0
opponent_points = 0
opponent_cl_rating = float(input("What is the rating of your opponent?\n"))
opponent_elo = 1000 + (opponent_cl_rating * 200)
point_ratio = None
adjusted_point = None
E = 1 / (1 + 10 ** ((opponent_elo - initial_elo) / 400))

for i in range(1, total_games+1):
    u = int(input(f"Your points in game {i}: "))
    o = int(input(f"Opponent points in game {i}: "))
    user_points += u
    opponent_points += o

print(f"Your game ratio is {game_ratio}")
point_ratio = user_points / (user_points + opponent_points)
print(f"Your point ratio is {point_ratio}")

adjusted_point = (point_ratio - 0.5) * 2
overall_score = game_ratio + 0.2 * adjusted_point
overall_score = float(max(0, min(1, overall_score)))

K = 70  # how much each match affects rating

user_elo = initial_elo + K * (overall_score - E)
user_elo_int = int(user_elo)

print(f"Your ELO rating for this game is {overall_score}")
print(f"Your new elo is {user_elo_int}")