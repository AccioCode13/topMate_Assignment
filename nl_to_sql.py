# nl_to_sql.py
import re
from typing import Tuple, Any, Dict

def map_query_to_sql(text: str) -> Tuple[str, tuple, str]:
    """
    Returns (sql, params, description)
    If it can't map, returns (None,(), message)
    """
    q = text.strip().lower()

    # 1. Show me all matches
    if re.search(r"\ball matches\b|\bshow me all matches\b|\blist matches\b", q):
        sql = "SELECT match_id, season, venue, match_date, winner, margin_type, margin_value FROM matches ORDER BY match_date LIMIT 500"
        return sql, (), "All matches (up to 500)"

    # 2. Which team won the most matches?
    if re.search(r"which team won the most matches|team won the most matches|most wins", q):
        sql = "SELECT winner AS team, COUNT(*) AS wins FROM matches WHERE winner IS NOT NULL GROUP BY winner ORDER BY wins DESC LIMIT 5"
        return sql, (), "Teams by most match wins"

    # 3. Highest total score (single innings total)
    if re.search(r"highest total score|highest innings total|highest total", q):
        sql = """
        SELECT match_id, inning_no, team_name, SUM(runs_total) AS innings_total
        FROM innings
        GROUP BY match_id, inning_no, team_name
        ORDER BY innings_total DESC
        LIMIT 5
        """
        return sql, (), "Highest innings totals"

    # 4. Show matches played in <city/venue>
    m = re.search(r"show matches played in (.+)", q)
    if m:
        place = m.group(1).strip()
        sql = "SELECT match_id, season, venue, match_date, winner FROM matches WHERE city LIKE %s OR venue LIKE %s ORDER BY match_date LIMIT 200"
        param = (f"%{place}%", f"%{place}%")
        return sql, param, f"Matches in {place}"

    # 5. Who scored the most runs across all matches?
    if re.search(r"who (scored|has scored) the most runs|top run scorers|most runs", q):
        sql = "SELECT batter AS player, SUM(runs_batter) AS runs FROM innings GROUP BY batter ORDER BY runs DESC LIMIT 20"
        return sql, (), "Top run scorers"

    # 6. Which bowler took the most wickets?
    if re.search(r"who (took|has taken) the most wickets|most wickets|top wicket", q):
        # We count deliveries that have player_out and bowler not null
        sql = "SELECT bowler, COUNT(*) AS wickets FROM innings WHERE player_out IS NOT NULL GROUP BY bowler ORDER BY wickets DESC LIMIT 20"
        return sql, (), "Top wicket takers"

    # 7. Show me <player> batting stats
    m = re.search(r"show me (.+?)'s batting stats|show me (.+?) batting stats|(.+) batting stats", text, re.I)
    if m:
        name = m.group(1) if m.group(1) else m.group(2)
        name = name.strip()
        # approximate exact match - use LIKE
        sql = """
        SELECT
            %s AS player,
            SUM(runs_batter) AS total_runs,
            COUNT(*) FILTER (WHERE runs_batter>0) AS scoring_balls,
            SUM(runs_total) AS runs_including_extras,
            COUNT(*) AS balls_faced
        FROM innings
        WHERE LOWER(batter) LIKE LOWER(%s)
        """
        # MySQL doesn't support FILTER — use alternative
        sql = """
        SELECT
            %s AS player,
            COALESCE(SUM(runs_batter),0) AS total_runs,
            COALESCE(SUM(CASE WHEN runs_batter>0 THEN 1 ELSE 0 END),0) AS scoring_balls,
            COALESCE(SUM(runs_total),0) AS runs_including_extras,
            COUNT(*) AS balls_faced
        FROM innings
        WHERE LOWER(batter) LIKE LOWER(%s)
        """
        param = (name, f"%{name}%")
        return sql, param, f"Batting stats for {name}"

    # 8. Who has the best bowling figures in a single match? (max wickets in a match by bowler)
    if re.search(r"best bowling figures|best bowling in a single match|best bowling figures in a single match", q):
        sql = """
        SELECT match_id, bowler, COUNT(*) AS wickets_in_match
        FROM innings
        WHERE player_out IS NOT NULL
        GROUP BY match_id, bowler
        ORDER BY wickets_in_match DESC
        LIMIT 10
        """
        return sql, (), "Best bowling (most wickets in a match)"

    # 9. Average first innings score
    if re.search(r"average first innings|avg first innings|average of first innings", q):
        sql = """
        SELECT ROUND(AVG(total_score),2) AS avg_first_innings FROM (
            SELECT match_id, SUM(runs_total) AS total_score
            FROM innings
            WHERE inning_no = 1
            GROUP BY match_id
        ) t
        """
        return sql, (), "Average first-innings score"

    # 10. Venue with highest scoring matches (by average total)
    if re.search(r"which venue has the highest scoring matches|venue has the highest scoring matches|highest scoring venue", q):
        sql = """
        SELECT m.venue, ROUND(AVG(t.total),2) AS avg_total
        FROM (
            SELECT match_id, SUM(runs_total) AS total
            FROM innings
            GROUP BY match_id
        ) t
        JOIN matches m ON m.match_id = t.match_id
        GROUP BY m.venue
        ORDER BY avg_total DESC
        LIMIT 10
        """
        return sql, (), "Venues by average match total"

    # 11. Show me all centuries (batter scored >=100 in an innings)
    if re.search(r"all centuries|show me all centuries|centuries scored", q):
        sql = """
        SELECT match_id, inning_no, team_name, batter, SUM(runs_batter) AS runs
        FROM innings
        GROUP BY match_id, inning_no, team_name, batter
        HAVING SUM(runs_batter) >= 100
        ORDER BY runs DESC
        LIMIT 100
        """
        return sql, (), "All centuries"

    # 12. Most successful chase target (largest target successfully chased)
    if re.search(r"most successful chase|most successful chase target|successful chase target", q):
        sql = """
        -- Find matches where winner is team that batted second and reached target
        SELECT m.match_id, m.venue, m.winner, t2.total AS chase_target
        FROM (
            SELECT match_id, inning_no, SUM(runs_total) AS total
            FROM innings
            GROUP BY match_id, inning_no
        ) t1
        JOIN (
            SELECT match_id, SUM(runs_total) AS total
            FROM innings
            GROUP BY match_id
        ) t2 ON t1.match_id = t2.match_id
        JOIN matches m ON m.match_id = t1.match_id
        LIMIT 10
        """
        # NOTE: Accurate chase logic requires knowing which inning was second; this is a placeholder
        return sql, (), "Most successful chase targets (approximate)"

    # 13. Team powerplay performance (first 6 overs runs per team)
    if re.search(r"powerplay|first 6 overs|power play", q):
        sql = """
        SELECT team_name, ROUND(AVG(powerplay_runs),2) AS avg_powerplay
        FROM (
            SELECT match_id, team_name, SUM(runs_total) AS powerplay_runs
            FROM innings
            WHERE over_no < 6
            GROUP BY match_id, team_name
        ) t
        GROUP BY team_name
        ORDER BY avg_powerplay DESC
        LIMIT 20
        """
        return sql, (), "Powerplay (first 6 overs) performance per team (approx)"

    # 14. Scorecard for match between <team1> and <team2>
    m = re.search(r"scorecard for match between (.+?) and (.+)", text, re.I)
    if m:
        t1 = m.group(1).strip()
        t2 = m.group(2).strip()
        sql = """
        SELECT i.match_id, i.inning_no, i.team_name, SUM(i.runs_total) AS inning_total
        FROM innings i
        WHERE (i.team_name LIKE %s OR i.team_name LIKE %s) AND i.match_id IN (
            SELECT match_id FROM matches WHERE (teams LIKE %s OR teams LIKE %s)
            )
        GROUP BY i.match_id, i.inning_no, i.team_name
        ORDER BY i.match_id, i.inning_no
        """
        # Note: We don't have a 'teams' column concatenated; alternative is to search matches table by venue or by team in teams table.
        # We'll fallback to searching matches table by team lists present in teams table:
        # Simpler: return list of innings where team_name matches either t1 or t2
        sql = """
        SELECT match_id, inning_no, team_name, SUM(runs_total) AS inning_total
        FROM innings
        WHERE team_name LIKE %s OR team_name LIKE %s
        GROUP BY match_id, inning_no, team_name
        ORDER BY match_id, inning_no
        LIMIT 50
        """
        params = (f"%{t1}%", f"%{t2}%")
        return sql, params, f"Scorecard-ish for matches between {t1} and {t2}"

    # 15. How many sixes in final? (assuming final match can be identified by season/event)
    if re.search(r"sixes.*final|in the final.*sixes|how many sixes were hit in the final", q):
        # Placeholder—we identify final by season latest or event name "Final" is not always present.
        sql = """
        SELECT SUM(CASE WHEN runs_batter = 6 THEN 1 ELSE 0 END) AS sixes
        FROM innings
        WHERE match_id IN (
            SELECT match_id FROM matches WHERE season = (SELECT season FROM matches ORDER BY match_date DESC LIMIT 1)
        )
        """
        return sql, (), "Total sixes in latest season's matches (approx for final)"

    # fallback
    return None, (), "Sorry — I couldn't map that question automatically. Try a simpler phrasing or ask for \"list supported queries\"."
