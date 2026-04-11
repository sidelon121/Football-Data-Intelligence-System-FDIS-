"""
FDIS Natural Language Generation Engine
Generates automated analysis text from statistical data.
"""
from app.engine.statistics import (
    get_team_overview, get_match_analysis, get_player_overview,
    get_team_comparison, get_team_performance_trend
)


def generate_match_summary(match_id):
    """
    Generate a comprehensive text summary for a match.
    """
    analysis = get_match_analysis(match_id)
    if not analysis:
        return "Match data not available."

    match = analysis['match']
    home = match['home_team']
    away = match['away_team']
    hg = match['home_goals']
    ag = match['away_goals']
    hs = analysis.get('home_stats', {})
    as_ = analysis.get('away_stats', {})

    # Result description
    if hg > ag:
        result_text = f"**{home['name']}** secured a **{hg}–{ag} victory** over {away['name']}"
        winner, loser = home['name'], away['name']
        margin = hg - ag
        if margin >= 3:
            result_text += " in a commanding performance."
        elif margin == 2:
            result_text += " in a comfortable win."
        else:
            result_text += " in a tightly contested match."
    elif ag > hg:
        result_text = f"**{away['name']}** claimed a **{ag}–{hg} away victory** against {home['name']}"
        winner, loser = away['name'], home['name']
        margin = ag - hg
        if margin >= 3:
            result_text += " with a dominant display on the road."
        elif margin == 2:
            result_text += " in a convincing away performance."
        else:
            result_text += " in a closely fought encounter."
    else:
        result_text = f"**{home['name']}** and **{away['name']}** played out a **{hg}–{ag} draw**"
        winner = None
        if hg == 0:
            result_text += " in a goalless stalemate."
        else:
            result_text += " in an evenly matched contest."

    paragraphs = [result_text]

    # Possession & passing analysis
    h_poss = hs.get('possession', 0)
    a_poss = as_.get('possession', 0)
    if h_poss and a_poss:
        if abs(h_poss - a_poss) > 10:
            dominant = home['name'] if h_poss > a_poss else away['name']
            dom_poss = max(h_poss, a_poss)
            paragraphs.append(
                f"{dominant} controlled the tempo with **{dom_poss:.1f}% possession**, "
                f"dictating play throughout the match."
            )
        else:
            paragraphs.append(
                f"Possession was evenly contested — {home['name']} held {h_poss:.1f}% "
                f"while {away['name']} managed {a_poss:.1f}%."
            )

    # Shots analysis
    h_shots = hs.get('total_shots', 0)
    a_shots = as_.get('total_shots', 0)
    h_sot = hs.get('shots_on_target', 0)
    a_sot = as_.get('shots_on_target', 0)
    if h_shots or a_shots:
        paragraphs.append(
            f"{home['name']} created {h_shots} shots ({h_sot} on target), "
            f"while {away['name']} registered {a_shots} shots ({a_sot} on target)."
        )

    # xG analysis
    h_xg = hs.get('xg', 0)
    a_xg = as_.get('xg', 0)
    if h_xg or a_xg:
        xg_text = f"Expected goals: {home['name']} {h_xg:.2f} — {a_xg:.2f} {away['name']}."
        if winner:
            w_xg = h_xg if winner == home['name'] else a_xg
            w_goals = hg if winner == home['name'] else ag
            if w_goals > w_xg + 0.5:
                xg_text += f" {winner} outperformed their xG, showing clinical finishing."
            elif w_goals < w_xg - 0.5:
                xg_text += f" {winner} underperformed their xG, suggesting they could have scored more."
        paragraphs.append(xg_text)

    # Discipline
    h_yc = hs.get('yellow_cards', 0)
    a_yc = as_.get('yellow_cards', 0)
    h_rc = hs.get('red_cards', 0)
    a_rc = as_.get('red_cards', 0)
    if h_yc + a_yc + h_rc + a_rc > 0:
        cards = []
        if h_yc + a_yc > 0:
            cards.append(f"{h_yc + a_yc} yellow cards")
        if h_rc + a_rc > 0:
            cards.append(f"{h_rc + a_rc} red cards")
        discipline_text = f"The referee showed {' and '.join(cards)} across the match"
        if h_yc + a_yc > 6:
            discipline_text += " — a heated affair."
        else:
            discipline_text += "."
        paragraphs.append(discipline_text)

    return "\n\n".join(paragraphs)


def generate_team_analysis(team_id):
    """
    Generate comprehensive text analysis for a team.
    """
    data = get_team_overview(team_id)
    if not data or data.get('matches_played', 0) == 0:
        return "Insufficient data to generate team analysis."

    team_name = data['team']['name']
    paragraphs = []

    # Overall record
    mp = data['matches_played']
    w, d, l = data['wins'], data['draws'], data['losses']
    pts = data['points']
    wr = data['win_rate']

    record_text = (
        f"**{team_name}** have played **{mp} matches** this season, recording "
        f"**{w} wins, {d} draws, and {l} losses** ({pts} points). "
    )
    if wr >= 70:
        record_text += f"With a {wr}% win rate, they have been exceptional."
    elif wr >= 50:
        record_text += f"A {wr}% win rate reflects a solid, competitive campaign."
    elif wr >= 30:
        record_text += f"A {wr}% win rate shows room for improvement."
    else:
        record_text += f"At just {wr}% win rate, results have been disappointing."
    paragraphs.append(record_text)

    # Goals
    gf = data['goals_for']
    ga = data['goals_against']
    gd = data['goal_difference']
    avg_gf = data['avg_goals_per_match']
    paragraphs.append(
        f"They have scored **{gf} goals** (averaging {avg_gf} per game) and conceded {ga}, "
        f"giving them a goal difference of **{'+' if gd >= 0 else ''}{gd}**. "
        f"They have kept **{data['clean_sheets']} clean sheets** ({data['clean_sheet_rate']}%)."
    )

    # Playing style
    style_parts = []
    if data['avg_possession'] > 55:
        style_parts.append(f"a possession-dominant approach ({data['avg_possession']}%)")
    elif data['avg_possession'] < 45:
        style_parts.append(f"a counter-attacking style ({data['avg_possession']}% possession)")
    else:
        style_parts.append(f"balanced possession play ({data['avg_possession']}%)")

    if data['avg_pass_accuracy'] > 87:
        style_parts.append(f"excellent passing accuracy ({data['avg_pass_accuracy']}%)")
    elif data['avg_pass_accuracy'] > 82:
        style_parts.append(f"solid passing accuracy ({data['avg_pass_accuracy']}%)")

    if data['avg_xg'] > 2:
        style_parts.append(f"a high-quality chance creation (xG: {data['avg_xg']})")

    if style_parts:
        paragraphs.append(
            f"Their playing style is characterized by {', '.join(style_parts)}."
        )

    # Form
    form = data['form']
    if form:
        form_str = ' '.join(form)
        recent_wins = form.count('W')
        paragraphs.append(
            f"**Recent form** (latest first): {form_str}. "
            f"They have won {recent_wins} of their last {len(form)} matches."
        )
        if recent_wins >= 4:
            paragraphs.append(f"{team_name} are in outstanding form and look difficult to stop.")
        elif recent_wins <= 1:
            paragraphs.append(f"{team_name} are struggling for results and need a turnaround.")

    return "\n\n".join(paragraphs)


def generate_player_analysis(player_id):
    """
    Generate text analysis for a player.
    """
    data = get_player_overview(player_id)
    if not data or data.get('matches_played', 0) == 0:
        return "Insufficient data to generate player analysis."

    name = data['player']['name']
    position = data['player'].get('position', 'Player')
    team = data['player'].get('team_name', '')
    paragraphs = []

    # Intro
    intro = f"**{name}**"
    if team:
        intro += f" ({team})"
    intro += f" has featured in **{data['matches_played']} matches**, "
    intro += f"accumulating {data['total_minutes']} minutes on the pitch."
    paragraphs.append(intro)

    # Goals & Assists
    gc = data['goal_contributions']
    if gc > 0:
        paragraphs.append(
            f"He has contributed **{data['total_goals']} goals and {data['total_assists']} assists** "
            f"({gc} total goal contributions), averaging {data['goals_per_90']} goals "
            f"and {data['assists_per_90']} assists per 90 minutes."
        )

    # Shooting
    if data['total_shots'] > 0:
        paragraphs.append(
            f"From {data['total_shots']} shots attempted, {data['total_shots_on_target']} were on target "
            f"— a shot accuracy of **{data['shot_accuracy']}%**."
        )

    # Passing
    if data['total_passes'] > 0:
        paragraphs.append(
            f"In the passing department, he maintains a **{data['avg_pass_accuracy']}% accuracy** "
            f"with {data['total_key_passes']} key passes ({data['key_passes_per_90']}/90min)."
        )

    # Defensive contribution
    if data['total_tackles'] + data['total_interceptions'] > 0:
        paragraphs.append(
            f"Defensively, he averages {data['tackles_per_90']} tackles and "
            f"{data['interceptions_per_90']} interceptions per 90 minutes."
        )

    # Dribbling
    if data['total_dribbles_attempted'] > 0:
        paragraphs.append(
            f"His dribbling success rate stands at **{data['dribble_success_rate']}%** "
            f"({data['total_dribbles_succeeded']}/{data['total_dribbles_attempted']})."
        )

    # Rating
    if data['avg_rating'] > 0:
        rating = data['avg_rating']
        rating_desc = "outstanding" if rating >= 8 else ("good" if rating >= 7 else ("average" if rating >= 6 else "below par"))
        paragraphs.append(
            f"His average match rating of **{rating}** suggests {rating_desc} overall performances."
        )

    return "\n\n".join(paragraphs)


def generate_comparison_narrative(team_id_1, team_id_2):
    """
    Generate comparison text between two teams.
    """
    comp = get_team_comparison(team_id_1, team_id_2)
    if not comp:
        return "Comparison data not available."

    t1 = comp['team1']
    t2 = comp['team2']
    h2h = comp['head_to_head']
    name1 = t1['team']['name']
    name2 = t2['team']['name']

    paragraphs = []

    # Overall comparison intro
    paragraphs.append(
        f"**{name1}** vs **{name2}** — a statistical comparison based on all available match data."
    )

    # Records
    paragraphs.append(
        f"{name1}: {t1['wins']}W {t1['draws']}D {t1['losses']}L "
        f"({t1['win_rate']}% win rate, {t1['points']} pts) | "
        f"{name2}: {t2['wins']}W {t2['draws']}D {t2['losses']}L "
        f"({t2['win_rate']}% win rate, {t2['points']} pts)."
    )

    # Key metric comparison
    advantages = []
    if t1['avg_possession'] > t2['avg_possession']:
        advantages.append(f"{name1} dominate possession ({t1['avg_possession']}% vs {t2['avg_possession']}%)")
    elif t2['avg_possession'] > t1['avg_possession']:
        advantages.append(f"{name2} hold more of the ball ({t2['avg_possession']}% vs {t1['avg_possession']}%)")

    if t1['avg_xg'] > t2['avg_xg']:
        advantages.append(f"{name1} create better chances (xG: {t1['avg_xg']} vs {t2['avg_xg']})")
    elif t2['avg_xg'] > t1['avg_xg']:
        advantages.append(f"{name2} create better chances (xG: {t2['avg_xg']} vs {t1['avg_xg']})")

    if advantages:
        paragraphs.append(". ".join(advantages) + ".")

    # Head-to-head
    if h2h['team1_wins'] + h2h['team2_wins'] + h2h['draws'] > 0:
        total_h2h = h2h['team1_wins'] + h2h['team2_wins'] + h2h['draws']
        paragraphs.append(
            f"**Head-to-head** ({total_h2h} meetings): "
            f"{name1} {h2h['team1_wins']}W — {h2h['draws']}D — {h2h['team2_wins']}W {name2}."
        )

    return "\n\n".join(paragraphs)
