import os
from groq import Groq

# ========================
# INIT CLIENT (GLOBAL)
# ========================
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("❌ GROQ_API_KEY tidak ditemukan di environment variables")

client = Groq(api_key=api_key)

# Gunakan model LLaMA 3.1 yang sangat cepat dari Groq
MODEL_ID = "openai/gpt-oss-120b"


# ========================
# HELPER FORMAT METRICS
# ========================
def format_metrics(metrics):
    if not metrics:
        return "No statistical metrics available."

    lines = []
    for m in metrics.values():
        label = m.get('label', '')
        home = m.get('home', 0)
        away = m.get('away', 0)
        lines.append(f"- {label}: {home} vs {away}")

    return "\n".join(lines)


# ========================
# MATCH AI
# ========================
def generate_ai_match_analysis(data):
    try:
        if not data:
            return None

        match = data['match']
        metrics = format_metrics(data.get('metrics', {}))

        home = match['home_team']['name']
        away = match['away_team']['name']

        prompt = f"""
You are the Lead Tactical Analyst for a professional Football Data Intelligence System.
Your task is to provide a purely data-driven post-match analysis.

CRITICAL RULES:
1. STRICTLY base your analysis ONLY on the data provided below.
2. DO NOT invent, hallucinate, or guess any events, names, goals, or statistics not present in the data.
3. Maintain an objective, professional, and highly analytical tone.

--- MATCH DATA ---
Fixture: {home} (Home) vs {away} (Away)
Final Score: {match['home_goals']} - {match['away_goals']}
Goalscorers: Home [{match['home_goalscorers']}] | Away [{match['away_goalscorers']}]
Venue: {match['venue']} | League: {match['league']}
Date: {match['date']}
Key Statistics (Home vs Away):
{metrics}
------------------

Based exclusively on the data above, provide a 3-paragraph tactical breakdown:
-Match overview and the final result justification.
-Deep dive into the statistics. Compare key metrics.
-Tactical conclusion and the most decisive factor of the match.
"""

        res = client.chat.completions.create(
            model=MODEL_ID,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3 # Temperature rendah agar fokus pada data murni
        )

        return res.choices[0].message.content.strip()

    except Exception as e:
        print("❌ AI MATCH ERROR:", e)
        return None


# ========================
# PLAYER AI
# ========================
def generate_ai_player_analysis(data):
    try:
        if not data:
            return None

        player = data.get('player', {})

        prompt = f"""
You are an elite Football Scout and Data Analyst.
Provide a strictly statistical performance evaluation of the player based ONLY on the provided metrics.

CRITICAL RULES:
1. DO NOT invent or hallucinate any statistics, match events, or traits outside of what the numbers suggest.
2. Be highly objective and professional.

--- PLAYER DATA ---
Name: {player.get('name')}
Team: {player.get('team_name')}
Matches Played: {data.get('matches_played', 0)}
Total Goals: {data.get('total_goals', 0)}
Total Assists: {data.get('total_assists', 0)}
Average Match Rating: {data.get('avg_rating', 0.0)}/10
-------------------

Write a precise 2-paragraph scouting report:
-Summary of their output (goals, assists) relative to matches played.
-Data-driven conclusions on their current form and value to the team.
"""

        res = client.chat.completions.create(
            model=MODEL_ID,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        return res.choices[0].message.content.strip()

    except Exception as e:
        print("❌ AI PLAYER ERROR:", e)
        return None


# ========================
# TEAM AI
# ========================
def generate_ai_team_analysis(data):
    try:
        if not data:
            return None

        team = data.get('team', {})
        metrics_text = format_metrics(data.get('metrics', {}))

        prompt = f"""
You are the Head of Data Analytics for a professional football club.
Provide a tactical team assessment based strictly on the provided performance metrics.

CRITICAL RULES:
1. DO NOT hallucinate match results, player names, or stats not present below.
2. If metrics are missing or zero, state that there is insufficient data.

--- TEAM DATA ---
Team: {team.get('name')}
League: {team.get('league')}
Matches Played: {data.get('matches_played', 0)}
Form: {data.get('wins', 0)} Wins, {data.get('losses', 0)} Losses
Win Rate: {data.get('win_rate', 0.0)}%

Aggregated Statistics:
{metrics_text}
-----------------

Provide a 3-paragraph tactical analysis:
-Overall team performance based on win rate.
-Tactical profile based on aggregated statistics.
-Strengths and areas for improvement.
"""

        res = client.chat.completions.create(
            model=MODEL_ID,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        return res.choices[0].message.content.strip()

    except Exception as e:
        print("❌ AI TEAM ERROR:", e)
        return None


# ========================
# COMPARISON AI
# ========================
def generate_ai_comparison_analysis(data, compare_type="team"):
    try:
        if not data:
            return None

        meta = data.get('meta', {}) if isinstance(data, dict) else {}
        name1 = meta.get('name1', 'Entity A')
        name2 = meta.get('name2', 'Entity B')

        metrics_text = ""
        for m in data.get('metrics', []):
            metrics_text += f"- {m.get('label','')}: {name1} ({m.get('t1',0)}) vs {name2} ({m.get('t2',0)})\n"

        entity_label = "Teams" if compare_type == "team" else "Players"

        prompt = f"""
You are a Senior Football Data Analyst.
Conduct a head-to-head statistical comparison between these two {entity_label}.

CRITICAL RULES:
1. Base your comparison ENTIRELY on the provided metrics. DO NOT hallucinate.
2. Be objective, highlighting statistical advantages and disadvantages.

--- HEAD-TO-HEAD DATA ---
{name1} vs {name2}

Metrics Compared:
{metrics_text}
-------------------------

Write a 3-paragraph comparative analysis:
-High-level summary of who holds the overall statistical advantage.
-Detailed metric breakdown. Contrast their styles.
-Final tactical conclusion.
"""

        res = client.chat.completions.create(
            model=MODEL_ID,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        return res.choices[0].message.content.strip()

    except Exception as e:
        print("❌ AI COMPARE ERROR:", e)
        return None