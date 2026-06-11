from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
from nba_api.stats.static import players
from nba_api.stats.endpoints import playergamelog

app = Flask(__name__)

# Enable CORS so your standalone frontend files can query this API
CORS(app)

# Prevent Flask from squishing JSON into a single line (enables pretty-printing)
app.json.compact = False


@app.route('/')
def home():
    """Friendly welcome page for the root URL."""
    return """
    <h1>NBA Player Stats API</h1>
    <p>The server is running perfectly!</p>
    <p>Try searching for a player via your HTML page, or visit: 
    <a href="/api/player/LeBron James">/api/player/LeBron James</a></p>
    """


@app.route('/api/player/<player_name>', methods=['GET'])
def get_player_stats(player_name):
    try:
        # Allow the user to pass an optional season query parameter (defaults to 2024-25)
        season = request.args.get('season', '2024-25')

        # 1. Look up the player by name
        player_dict = players.find_players_by_full_name(player_name)

        # If no player matches the name exactly, return a 404
        if len(player_dict) == 0:
            return jsonify({
                               "error": f"Player '{player_name}' not found. Make sure to use their full official name (e.g., 'Stephen Curry' instead of 'Steph')."}), 404

        player_id = player_dict[0]["id"]

        # 2. Fetch Game Logs from the NBA API
        gamelog = playergamelog.PlayerGameLog(
            player_id=player_id,
            season=season
        )

        df = gamelog.get_data_frames()[0]

        # Handle cases where a player exists but has no records for the selected season
        if df.empty:
            return jsonify({
                "player": player_dict[0]['full_name'],
                "message": f"No games found for season {season}",
                "data": []
            }), 200

        # 3. Filter down to the essential columns
        columns_to_keep = [
            "GAME_DATE", "MATCHUP", "WL", "MIN", "PTS", "REB", "AST",
            "STL", "BLK", "FGM", "FGA", "FG_PCT", "FG3M", "FG3A", "FG3_PCT"
        ]
        stats_df = df[columns_to_keep]

        # 4. Convert the rows into an array of dictionaries for clean JSON translation
        stats_data = stats_df.to_dict(orient='records')

        # Return the structured payload
        return jsonify({
            "player": player_dict[0]['full_name'],
            "player_id": player_id,
            "season": season,
            "games_played": len(stats_df),
            "data": stats_data
        }), 200

    except Exception as e:
        # Catch network timeouts or API changes gracefully
        return jsonify({"error": f"Internal Server Error: {str(e)}"}), 500


if __name__ == '__main__':
    # Start the server on local port 5000 with debug mode enabled
    app.run(debug=True, port=5000)
