import os
import json
import mysql.connector
from datetime import datetime

# ✅ MySQL connection
conn = mysql.connector.connect(
    host="localhost",
    user="root",       # change if needed
    password="Shreya1322#",  # change if needed
    database="ipl"
)
cursor = conn.cursor()

# Path to your folder containing JSON files
data_dir = "ipl_json"

for file_name in os.listdir(data_dir):
    if not file_name.endswith(".json"):
        continue

    file_path = os.path.join(data_dir, file_name)
    with open(file_path, "r") as f:
        data = json.load(f)

    match_id = int(file_name.replace(".json", ""))

    # --- Matches table ---
    info = data["info"]
    outcome = info.get("outcome", {})
    winner = outcome.get("winner", None)
    margin_type, margin_value = None, None
    if "by" in outcome:
        margin_type, margin_value = list(outcome["by"].items())[0]

    cursor.execute("""
        INSERT IGNORE INTO matches
        (match_id, season, city, venue, match_date, toss_winner, toss_decision, 
         winner, margin_type, margin_value, player_of_match)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        match_id,
        info.get("season"),
        info.get("city"),
        info.get("venue"),
        datetime.strptime(info["dates"][0], "%Y-%m-%d"),
        info["toss"]["winner"],
        info["toss"]["decision"],
        winner,
        margin_type,
        margin_value,
        ", ".join(info.get("player_of_match", []))
    ))

    # --- Teams table ---
    for team in info["teams"]:
        cursor.execute("""
            INSERT INTO teams (match_id, team_name) VALUES (%s, %s)
        """, (match_id, team))

    # --- Players table ---
    for team, players in info["players"].items():
        for player in players:
            cursor.execute("""
                INSERT IGNORE INTO players (player_id, player_name) VALUES (%s, %s)
            """, (info["registry"]["people"][player], player))

    # --- Innings table ---
    for inning_no, inning in enumerate(data["innings"], start=1):
        team_name = inning["team"]
        for over in inning["overs"]:
            over_no = over["over"]
            for ball_no, delivery in enumerate(over["deliveries"], start=1):
                batter = delivery["batter"]
                bowler = delivery["bowler"]
                runs = delivery["runs"]

                runs_batter = runs.get("batter", 0)
                runs_extras = runs.get("extras", 0)
                runs_total = runs.get("total", 0)

                wicket_kind, player_out = None, None
                if "wickets" in delivery:
                    w = delivery["wickets"][0]
                    wicket_kind = w.get("kind")
                    player_out = w.get("player_out")

                cursor.execute("""
                    INSERT INTO innings
                    (match_id, inning_no, team_name, over_no, ball_no, batter, bowler,
                     runs_batter, runs_extras, runs_total, wicket_kind, player_out)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    match_id, inning_no, team_name, over_no, ball_no,
                    batter, bowler, runs_batter, runs_extras, runs_total,
                    wicket_kind, player_out
                ))

    conn.commit()
    print(f"Inserted {file_name}")

cursor.close()
conn.close()
