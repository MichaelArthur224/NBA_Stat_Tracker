from flask import Flask, jsonify, request
import pandas as pd
from nba_api.stats.static import players
from nba_api.stats.endpoints import playergamelog

app = Flask(__name__)

@app.route('/')
def home():
    return """
    <h1>NBA Player Stats API</h1>
    <p>Try going to: <a href="/api/player/LeBron James">/api/player/LeBron James</a></p>
    """
@app.route('/api/player/<player_name>', methods=['GET'])
def get_player_stats(player_name):
    try:
        # Allow the user to pass a season query parameter, default to "2024-25"
        season = request.args.get('season', '2024-25')

        # 1. Find the player
        player_dict = players.find_players_by_full_name(player_name)

        if len(player_dict) == 0:
            return jsonify({"error": f"Player '{player_name}' not found"}), 404

        player_id = player_dict[0]["id"]

        # 2. Get Game Logs
        gamelog = playergamelog.PlayerGameLog(
            player_id=player_id,
            season=season
        )

        df = gamelog.get_data_frames()[0]

        # Check if the player has played any games this season
        if df.empty:
            return jsonify({
                "player": player_dict[0]['full_name'],
                "message": f"No games found for season {season}",
                "data": []
            }), 200

        # 3. Select Useful Columns
        columns_to_keep = [
            "GAME_DATE", "MATCHUP", "WL", "MIN", "PTS", "REB", "AST",
            "STL", "BLK", "FGM", "FGA", "FG_PCT", "FG3M", "FG3A", "FG3_PCT"
        ]
        stats_df = df[columns_to_keep]

        # 4. Convert DataFrame to a list of dictionaries for JSON output
        stats_data = stats_df.to_dict(orient='records')

        return jsonify({
            "player": player_dict[0]['full_name'],
            "player_id": player_id,
            "season": season,
            "games_played": len(stats_df),
            "data": stats_data
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    # Run the Flask app on port 5000
    app.run(debug=True, port=5000)
