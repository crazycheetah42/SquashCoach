def calculate_squash_elo(cl_rating, opponent_cl_rating, games_scores, K=70, opponent_name=None):
    total_games = len(games_scores)
    if total_games == 0:
        raise ValueError("games_scores must contain at least one game")

    games_won = sum(1 for u, o in games_scores if u > o)
    game_ratio = games_won / total_games

    user_points = sum(u for u, o in games_scores)
    opponent_points = sum(o for u, o in games_scores)

    initial_elo = 1000 + (cl_rating * 200)
    opponent_elo = 1000 + (opponent_cl_rating * 200)

    E = 1 / (1 + 10 ** ((opponent_elo - initial_elo) / 400))

    point_ratio = user_points / (user_points + opponent_points)
    adjusted_point = (point_ratio - 0.5) * 2
    overall_score = float(max(0, min(1, game_ratio + 0.2 * adjusted_point)))

    new_elo = initial_elo + K * (overall_score - E)
    new_elo_int = int(new_elo)

    return {
        "current_us_squash_rating": cl_rating,
        "initial_elo": initial_elo,
        "games_won": games_won,
        "games_lost": total_games - games_won,
        "total_games": total_games,
        "game_ratio": game_ratio,
        "user_points": user_points,
        "opponent_points": opponent_points,
        "point_ratio": point_ratio,
        "adjusted_point": adjusted_point,
        "overall_score": overall_score,
        "opponent_us_squash_rating": opponent_cl_rating,
        "opponent_name": opponent_name,
        "opponent_elo": opponent_elo,
        "expected_score": E,
        "K": K,
        "new_elo": new_elo,
        "new_elo_int": new_elo_int
    }
def elo_to_us_squash(elo):
    return round((elo - 1000) / 200, 2)