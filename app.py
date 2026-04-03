from flask import Flask, render_template, request, jsonify
from logic import calculate_squash_elo
from fb_code import db
from datetime import datetime

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/matches")
def matches():
    return render_template("matches.html")

@app.route("/stats")
def stats():
    return render_template("stats.html")

@app.route("/submit_match", methods=["POST"])
def submit_match():
    data = request.json
    user_rating = float(data["user_rating"])
    opponent_rating = float(data["opponent_rating"])
    games_scores = data["games_scores"]  # [[user, opponent], ...]
    
    result = calculate_squash_elo(user_rating, opponent_rating, games_scores)
    result["date"] = datetime.now().isoformat()
    
    db.collection("matches").add(result)
    
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)