"""
FDIS Statistical Computation Engine
Calculates team and player performance metrics.
"""
from marimo import json
from marimo import json
import numpy as np
import pandas as pd
from soupsieve import match
from sqlalchemy import func, case, and_
from app import db
from app.models import Team, Player, Match, MatchStats, PlayerStats
import json as py_json  

def get_team_overview(team_id):
    """
    Get comprehensive overview statistics for a team.
    
    Returns dict with: matches_played, wins, draws, losses, goals_for, goals_against,
    goal_difference, win_rate, avg stats, form, etc.
    """
    team = Team.query.get(team_id)
    if not team:
        return None

    # Get all matches for this team
    home_matches = Match.query.filter_by(home_team_id=team_id).all()
    away_matches = Match.query.filter_by(away_team_id=team_id).all()
    all_matches = home_matches + away_matches

    if not all_matches:
        return {
            'team': team.to_dict(),
            'matches_played': 0,
            'message': 'No match data available'
        }

    # Calculate W/D/L
    wins = draws = losses = goals_for = goals_against = 0
    clean_sheets = 0

    for m in home_matches:
        goals_for += m.home_goals or 0
        goals_against += m.away_goals or 0
        if m.home_goals > m.away_goals:
            wins += 1
        elif m.home_goals == m.away_goals:
            draws += 1
        else:
            losses += 1
        if (m.away_goals or 0) == 0:
            clean_sheets += 1

    for m in away_matches:
        goals_for += m.away_goals or 0
        goals_against += m.home_goals or 0
        if m.away_goals > m.home_goals:
            wins += 1
        elif m.away_goals == m.home_goals:
            draws += 1
        else:
            losses += 1
        if (m.home_goals or 0) == 0:
            clean_sheets += 1

    total = len(all_matches)
    points = wins * 3 + draws

    # Get aggregate match stats
    team_stats = MatchStats.query.filter_by(team_id=team_id).all()
    
    def safe_mean(values):
        return np.mean(values) if values else 0

    if team_stats:
        avg_possession = safe_mean([s.possession for s in team_stats if s.possession])
        avg_shots = safe_mean([s.total_shots for s in team_stats if s.total_shots])
        avg_shots_on_target = safe_mean([s.shots_on_target for s in team_stats if s.shots_on_target is not None])
        avg_passes = safe_mean([s.total_passes for s in team_stats if s.total_passes])
        avg_pass_accuracy = safe_mean([s.pass_accuracy for s in team_stats if s.pass_accuracy])
        avg_xg = safe_mean([s.xg for s in team_stats if s.xg])
        total_yellow = sum(s.yellow_cards or 0 for s in team_stats)
        total_red = sum(s.red_cards or 0 for s in team_stats)
        avg_corners = safe_mean([s.corners for s in team_stats if s.corners is not None])
        avg_tackles_total = safe_mean([s.tackles_total for s in team_stats if s.tackles_total is not None])
        avg_interceptions = safe_mean([s.interceptions for s in team_stats if s.interceptions is not None])
    else:
        avg_possession = avg_shots = avg_shots_on_target = 0
        avg_passes = avg_pass_accuracy = avg_xg = 0
        total_yellow = total_red = 0
        avg_corners = avg_tackles_total = avg_interceptions = 0

    # Form (last 5 matches)
    sorted_matches = sorted(all_matches, key=lambda m: m.date, reverse=True)
    form = []
    for m in sorted_matches[:5]:
        if m.home_team_id == team_id:
            if m.home_goals > m.away_goals:
                form.append('W')
            elif m.home_goals == m.away_goals:
                form.append('D')
            else:
                form.append('L')
        else:
            if m.away_goals > m.home_goals:
                form.append('W')
            elif m.away_goals == m.home_goals:
                form.append('D')
            else:
                form.append('L')

    return {
        'team': team.to_dict() if team else None,
        'matches_played': total,
        'wins': wins,
        'draws': draws,
        'losses': losses,
        'goals_for': goals_for,
        'goals_against': goals_against,
        'goal_difference': goals_for - goals_against,
        'points': points,
        'win_rate': round(wins / total * 100, 1) if total > 0 else 0,
        'avg_goals_per_match': round(goals_for / total, 2) if total > 0 else 0,
        'avg_goals_conceded': round(goals_against / total, 2) if total > 0 else 0,
        'clean_sheets': clean_sheets,
        'clean_sheet_rate': round(clean_sheets / total * 100, 1) if total > 0 else 0,
        'avg_possession': round(float(avg_possession), 1),
        'avg_shots': round(float(avg_shots), 1),
        'avg_shots_on_target': round(float(avg_shots_on_target), 1),
        'avg_passes': round(float(avg_passes), 0),
        'avg_pass_accuracy': round(float(avg_pass_accuracy), 1),
        'avg_xg': round(float(avg_xg), 2),
        'avg_corners': round(float(avg_corners), 1),
        'avg_tackles_total': round(float(avg_tackles_total), 1),
        'avg_interceptions': round(float(avg_interceptions), 1),
        'total_yellow_cards': total_yellow,
        'total_red_cards': total_red,
        'form': form,
        'form_string': ''.join(form),
    }


def get_match_analysis(match_id):
    """
    Get detailed statistical analysis for a specific match.
    """
    match = Match.query.get(match_id)
    if not match:
        return None

    home_stats = MatchStats.query.filter_by(
        match_id=match_id, team_id=match.home_team_id
    ).first()
    away_stats = MatchStats.query.filter_by(
        match_id=match_id, team_id=match.away_team_id
    ).first()

    # ==========================================
    # 🔥 SOLUSI FINAL: INISIALISASI VARIABEL DI SINI
    # ==========================================
    metrics_final = {}
    metrics_circle = []

    # Determine dominance metrics
    if home_stats and away_stats:
        # 1. Inisialisasi list HANYA untuk metrics_bar
        metrics_bar = [
            ('xg', 'Expected Goals', ''),
            ('possession', 'Possession', '%'),
            ('total_passes', 'Total Passes', ''),
            ('total_shots', 'Total Shots', ''),
            ('hit_woodwork', 'Hit Woodwork', ''),
            ('passes_into_penalty_area', 'Passes into Box', ''),
            ("final_third_entries", 'Final Third Entries', ''),
            ('throw_ins', 'Throw-ins', ''),
            ('corners', 'Corners', ''),
            ('interceptions', 'Interceptions', ''),
            ('offsides', 'Offsides', ''),
            ('through_balls', 'Through Balls', ''),
            ('goalkeeper_saves', 'Goalkeeper Save', ''),
            ('clearances', 'Clearances', ''),
            ('fouls', 'Fouls Committed', ''),
            ('yellow_cards', 'Yellow Cards', ''),
            ('red_cards', 'Red Cards', ''),
        ]

        for item in metrics_bar:
                    metrics_final[item['label']] = {
                        'home': item['home'],
                        'away': item['away'],
                        'label': item['label'],
                        'unit': item['unit'],
                        'dominant': 'home' if item['home'] > item['away'] else 'away' if item['away'] > item['home'] else 'none'
                    }
            

# ==========================================
# 3. STATISTIK LINGKARAN (DONUT CHARTS)
# ==========================================

# ----------------------
# RAW VALUES
# ----------------------

        # PASSING
        h_passes = getattr(home_stats, 'total_passes', 0) or 0
        a_passes = getattr(away_stats, 'total_passes', 0) or 0

        h_pass_acc = getattr(home_stats, 'pass_accuracy', 0.0) or 0.0
        a_pass_acc = getattr(away_stats, 'pass_accuracy', 0.0) or 0.0

        h_acc_passes = int(h_passes * (h_pass_acc / 100))
        a_acc_passes = int(a_passes * (a_pass_acc / 100))


        # SHOOTING
        h_shots = getattr(home_stats, 'total_shots', 0) or 0
        a_shots = getattr(away_stats, 'total_shots', 0) or 0

        h_sot = getattr(home_stats, 'shots_on_target', 0) or 0
        a_sot = getattr(away_stats, 'shots_on_target', 0) or 0

        h_off = getattr(home_stats, 'shots_off_target', 0) or 0
        a_off = getattr(away_stats, 'shots_off_target', 0) or 0

        h_blocked = getattr(home_stats, 'blocked_shots', 0) or 0
        a_blocked = getattr(away_stats, 'blocked_shots', 0) or 0

        h_inside = getattr(home_stats, 'shots_inside_box', 0) or 0
        a_inside = getattr(away_stats, 'shots_inside_box', 0) or 0

        h_outside = getattr(home_stats, 'shots_outside_box', 0) or 0
        a_outside = getattr(away_stats, 'shots_outside_box', 0) or 0


        # DRIBBLES
        h_drib_att = getattr(home_stats, 'dribbles_attempted', 0) or 0
        a_drib_att = getattr(away_stats, 'dribbles_attempted', 0) or 0

        h_drib_suc = getattr(home_stats, 'dribbles_succeeded', 0) or 0
        a_drib_suc = getattr(away_stats, 'dribbles_succeeded', 0) or 0

        h_drib_att = max(h_drib_att, h_drib_suc)
        a_drib_att = max(a_drib_att, a_drib_suc)


        # BIG CHANCES
        h_bc_scored = getattr(home_stats, 'big_chances_scored', 0) or 0
        a_bc_scored = getattr(away_stats, 'big_chances_scored', 0) or 0

        h_bc_missed = getattr(home_stats, 'big_chances_missed', 0) or 0
        a_bc_missed = getattr(away_stats, 'big_chances_missed', 0) or 0

        h_bc_tot = h_bc_scored + h_bc_missed
        a_bc_tot = a_bc_scored + a_bc_missed
        
        # Duels
        h_duels_won = getattr(home_stats, 'duels_won', 0) or 0
        a_duels_won = getattr(away_stats, 'duels_won', 0) or 0

        h_duels_total = getattr(home_stats, 'duels_total', 0) or 0
        a_duels_total = getattr(away_stats, 'duels_total', 0) or 0
        
        #tackles
        h_tackles_success = getattr(home_stats, 'tackles_success', 0) or 0
        a_tackles_success = getattr(away_stats, 'tackles_success', 0) or 0

        h_tackles_total = getattr(home_stats, 'tackles_total', 0) or 0
        a_tackles_total = getattr(away_stats, 'tackles_total', 0) or 0

        h_final_third_success = getattr(home_stats, "passes_final_third_success", 0) or 0
        a_final_third_success = getattr(away_stats, "passes_final_third_success", 0) or 0

        h_final_third = getattr(home_stats, "passes_final_third", 0) or 0
        a_final_third = getattr(away_stats, "passes_final_third", 0) or 0
        
        h_long_success = getattr(home_stats, "long_balls_success", 0) or 0
        a_long_success = getattr(away_stats, "long_balls_success", 0) or 0

        h_long = getattr(home_stats, "long_balls", 0) or 0
        a_long = getattr(away_stats, "long_balls", 0) or 0
        
        h_cross_success = getattr(home_stats, "crosses_success", 0) or 0
        a_cross_success = getattr(away_stats, "crosses_success", 0) or 0

        h_cross = getattr(home_stats, "crosses", 0) or 0
        a_cross = getattr(away_stats, "crosses", 0) or 0
        # ----------------------
        # A. PASS ACCURACY
        # ----------------------
        if h_passes > 0 or a_passes > 0:
            metrics_circle.append({
                'label': 'Pass Accuracy',
                'labels': ['Accurate', 'Failed'],
                'home_values': [
                    h_acc_passes,
                    max(h_passes - h_acc_passes, 0)
                ],
                'away_values': [
                    a_acc_passes,
                    max(a_passes - a_acc_passes, 0)
                ],
                'home_text': f"{h_acc_passes}/{h_passes}" if h_passes > 0 else "0/0",
                'away_text': f"{a_acc_passes}/{a_passes}" if a_passes > 0 else "0/0"
            })


        # ----------------------
        # B. SHOT DISTRIBUTION
        # ----------------------
        metrics_circle.append({
            'label': 'Shot Distribution',
            'labels': ['On Target', 'Off Target', 'Blocked'],
            'home_values': [h_sot, h_off, h_blocked],
            'away_values': [a_sot, a_off, a_blocked],
            'home_text': f"{h_sot}/{h_shots}" if h_shots > 0 else "0/0",
            'away_text': f"{a_sot}/{a_shots}" if a_shots > 0 else "0/0"
        })


        # ----------------------
        # C. SHOT LOCATION
        # ----------------------
        metrics_circle.append({
            'label': 'Shot Location',
            'labels': ['Inside Box', 'Outside Box'],
            'home_values': [h_inside, h_outside],
            'away_values': [a_inside, a_outside],
            'home_text': f"{h_inside}/{h_shots}" if h_shots > 0 else "0/0",
            'away_text': f"{a_inside}/{a_shots}" if a_shots > 0 else "0/0"
        })


        # ----------------------
        # D. DRIBBLE SUCCESS
        # ----------------------
        if h_drib_att > 0 or a_drib_att > 0:
            metrics_circle.append({
                'label': 'Dribble Success',
                'labels': ['Success', 'Failed'],
                'home_values': [
                    h_drib_suc,
                    max(h_drib_att - h_drib_suc, 0)
                ],
                'away_values': [
                    a_drib_suc,
                    max(a_drib_att - a_drib_suc, 0)
                ],
                'home_text': f"{h_drib_suc}/{h_drib_att}" if h_drib_att > 0 else "0/0",
                'away_text': f"{a_drib_suc}/{a_drib_att}" if a_drib_att > 0 else "0/0"
            })


        # ----------------------
        # E. BIG CHANCES
        # ----------------------
        if h_bc_tot > 0 or a_bc_tot > 0:
            metrics_circle.append({
                'label': 'Big Chances',
                'labels': ['Scored', 'Missed'],
                'home_values': [h_bc_scored, h_bc_missed],
                'away_values': [a_bc_scored, a_bc_missed],
                'home_text': f"{h_bc_scored}/{h_bc_tot}" if h_bc_tot > 0 else "0/0",
                'away_text': f"{a_bc_scored}/{a_bc_tot}" if a_bc_tot > 0 else "0/0"
            })    
        
            metrics_circle.append({
                'label': 'Duels Won',
                'labels': ['Won', 'Lost'],
                'home_values': [
                    h_duels_won,
                    max(h_duels_total - h_duels_won, 0)
                ],
                'away_values': [
                    a_duels_won,
                    max(a_duels_total - a_duels_won, 0)
                ],
                'home_text': f"{h_duels_won}/{h_duels_total}" if h_duels_total > 0 else "0/0",
                'away_text': f"{a_duels_won}/{a_duels_total}" if a_duels_total > 0 else "0/0"
            })
            
            metrics_circle.append({
                'label': 'Tackle Success',
                'labels': ['Success', 'Failed'],
                'home_values': [
                    h_tackles_success,
                    max(h_tackles_total - h_tackles_success, 0)
                ],
                'away_values': [
                    a_tackles_success,
                    max(a_tackles_total - a_tackles_success, 0)
                ],
                'home_text': f"{h_tackles_success}/{h_tackles_total}" if h_tackles_total > 0 else "0/0",
                'away_text': f"{a_tackles_success}/{a_tackles_total}" if a_tackles_total > 0 else "0/0"
            })
                
            metrics_circle.append({
                "label": "Passes Final Third",
                "labels": ["Success", "Failed"],
                "home_values": [
                    h_final_third_success,
                    max(h_final_third - h_final_third_success, 0)
                ],
                "away_values": [
                    a_final_third_success,
                    max(a_final_third - a_final_third_success, 0)
                ],
                "home_text": f"{h_final_third_success}/{h_final_third}",
                "away_text": f"{a_final_third_success}/{a_final_third}"
            })


            metrics_circle.append({
                "label": "Long Balls",
                "labels": ["Success", "Failed"],
                "home_values": [
                    h_long_success,
                    max(h_long - h_long_success, 0)
                ],
                "away_values": [
                    a_long_success,
                    max(a_long - a_long_success, 0)
                ],
                "home_text": f"{h_long_success}/{h_long}",
                "away_text": f"{a_long_success}/{a_long}"
            })

        metrics_circle.append({
            "label": "Cross Accuracy",
            "labels": ["Success", "Failed"],
            "home_values": [
                h_cross_success,
                max(h_cross - h_cross_success, 0)
            ],
            "away_values": [
                a_cross_success,
                max(a_cross - a_cross_success, 0)
            ],
            "home_text": f"{h_cross_success}/{h_cross}" if h_cross > 0 else "0/0",
            "away_text": f"{a_cross_success}/{a_cross}" if a_cross > 0 else "0/0"
        })
        # ==========================================
        # 4. KONVERSI KE FORMAT HTML (data.metrics)
        # ==========================================
        metrics_final = {}
        for item in metrics_bar:
            metrics_final[item['label']] = {
                'home': item['home'],
                'away': item['away'],
                'label': item['label'],
                'unit': item['unit'],
                'dominant': 'home' if item['home'] > item['away'] else 'away' if item['away'] > item['home'] else 'none'
            }
    
    return {
        'match': match.to_dict(),
        'metrics': metrics_final,
        'circle_metrics': metrics_circle,
        'home_team': match.home_team.to_dict(),
        'away_team': match.away_team.to_dict()
    }
def get_player_overview(player_id):
    """
    Get comprehensive statistics for a player.
    """
    player = Player.query.get(player_id)
    if not player:
        return None

    stats = PlayerStats.query.filter_by(player_id=player_id).all()
    if not stats:
        return {
            'player': player.to_dict(),
            'matches_played': 0,
            'message': 'No performance data available'
        }

    total_matches = len(stats)
    total_minutes = sum(s.minutes_played or 0 for s in stats)
    total_goals = sum(s.goals or 0 for s in stats)
    total_assists = sum(s.assists or 0 for s in stats)
    total_shots = sum(s.shots or 0 for s in stats)
    total_shots_on_target = sum(s.shots_on_target or 0 for s in stats)
    total_passes = sum(s.passes or 0 for s in stats)
    total_key_passes = sum(s.key_passes or 0 for s in stats)
    total_tackles = sum(s.tackles or 0 for s in stats)
    total_interceptions = sum(s.interceptions or 0 for s in stats)
    total_dribbles_attempted = sum(s.dribbles_attempted or 0 for s in stats)
    total_dribbles_succeeded = sum(s.dribbles_succeeded or 0 for s in stats)
    total_yellow = sum(s.yellow_cards or 0 for s in stats)
    total_red = sum(s.red_cards or 0 for s in stats)

    ratings = [s.rating for s in stats if s.rating is not None and s.rating > 0]
    avg_rating = round(np.mean(ratings), 2) if ratings else 0
    pass_accuracies = [s.pass_accuracy for s in stats if s.pass_accuracy]
    avg_pass_accuracy = round(np.mean(pass_accuracies), 1) if pass_accuracies else 0

    # Per 90 minutes calculations
    per_90_factor = total_minutes / 90 if total_minutes > 0 else 1

    return {
        'player': player.to_dict(),
        'matches_played': total_matches,
        'total_minutes': total_minutes,
        'avg_minutes': round(total_minutes / total_matches, 0) if total_matches > 0 else 0,
        'total_goals': total_goals,
        'total_assists': total_assists,
        'goal_contributions': total_goals + total_assists,
        'goals_per_90': round(total_goals / per_90_factor, 2),
        'assists_per_90': round(total_assists / per_90_factor, 2),
        'total_shots': total_shots,
        'total_shots_on_target': total_shots_on_target,
        'shot_accuracy': round(total_shots_on_target / total_shots * 100, 1) if total_shots > 0 else 0,
        'total_passes': total_passes,
        'avg_pass_accuracy': avg_pass_accuracy,
        'total_key_passes': total_key_passes,
        'key_passes_per_90': round(total_key_passes / per_90_factor, 2),
        'total_tackles': total_tackles,
        'total_interceptions': total_interceptions,
        'tackles_per_90': round(total_tackles / per_90_factor, 2),
        'interceptions_per_90': round(total_interceptions / per_90_factor, 2),
        'total_dribbles_attempted': total_dribbles_attempted,
        'total_dribbles_succeeded': total_dribbles_succeeded,
        'dribble_success_rate': round(total_dribbles_succeeded / total_dribbles_attempted * 100, 1)
            if total_dribbles_attempted > 0 else 0,
        'avg_rating': avg_rating,
        'total_yellow_cards': total_yellow,
        'total_red_cards': total_red,
        'ratings_trend': [{'match_id': s.match_id, 'rating': s.rating} for s in stats if s.rating],
    }


def get_league_table(league=None, season=None):
    """
    Calculate league standings from match results.
    """
    query = Match.query
    if league:
        query = query.filter(Match.league.ilike(f'%{league}%'))
    if season:
        query = query.filter(Match.season.ilike(f'%{season}%'))

    matches = query.all()
    if not matches:
        return []

    standings = {}

    for m in matches:
        # Initialize teams
        for tid in [m.home_team_id, m.away_team_id]:
            if tid not in standings:
                team = Team.query.get(tid)
                standings[tid] = {
                    'team_id': tid,
                    'team_name': team.name if team else 'Unknown',
                    'played': 0, 'wins': 0, 'draws': 0, 'losses': 0,
                    'goals_for': 0, 'goals_against': 0,
                    'goal_difference': 0, 'points': 0,
                }

        h = standings[m.home_team_id]
        a = standings[m.away_team_id]

        h['played'] += 1
        a['played'] += 1
        h['goals_for'] += m.home_goals or 0
        h['goals_against'] += m.away_goals or 0
        a['goals_for'] += m.away_goals or 0
        a['goals_against'] += m.home_goals or 0

        if (m.home_goals or 0) > (m.away_goals or 0):
            h['wins'] += 1
            h['points'] += 3
            a['losses'] += 1
        elif (m.home_goals or 0) == (m.away_goals or 0):
            h['draws'] += 1
            a['draws'] += 1
            h['points'] += 1
            a['points'] += 1
        else:
            a['wins'] += 1
            a['points'] += 3
            h['losses'] += 1

        h['goal_difference'] = h['goals_for'] - h['goals_against']
        a['goal_difference'] = a['goals_for'] - a['goals_against']

    # Sort by points, then goal difference, then goals scored
    table = sorted(
        standings.values(),
        key=lambda x: (x['points'], x['goal_difference'], x['goals_for']),
        reverse=True
    )

    # Add position
    for i, entry in enumerate(table):
        entry['position'] = i + 1

    return table


def get_all_league_standings():
    """
    Get standings for all leagues present in the database.
    Returns a dictionary: { league_name: [standings_table] }
    """
    leagues = db.session.query(Match.league).distinct().all()
    leagues = [l[0] for l in leagues if l[0]]
    
    if not leagues:
        # Fallback if no leagues defined in matches
        return {"General": get_league_table()}
        
    all_standings = {}
    for league in leagues:
        table = get_league_table(league=league)
        if table:
            all_standings[league] = table
            
    return all_standings

def get_player_comparison(player1_id, player2_id):
    """
    Compare two players comprehensively with full aliasing to prevent Jinja2 UndefinedError.
    """
    # 1. Ambil data overview lengkap untuk masing-masing pemain
    p1_data = get_player_overview(player1_id)
    p2_data = get_player_overview(player2_id)

    if not p1_data or not p2_data:
        return None

    # Siapkan variabel grafik agar kode terlihat rapi
    p1_rating = p1_data.get('avg_rating', 0)
    p2_rating = p2_data.get('avg_rating', 0)
    p1_g90 = round(p1_data.get('goals_per_90', 0) * 10, 1)
    p2_g90 = round(p2_data.get('goals_per_90', 0) * 10, 1)
    p1_a90 = round(p1_data.get('assists_per_90', 0) * 10, 1)
    p2_a90 = round(p2_data.get('assists_per_90', 0) * 10, 1)
    p1_pass = p1_data.get('avg_pass_accuracy', 0)
    p2_pass = p2_data.get('avg_pass_accuracy', 0)
    p1_dribble = p1_data.get('dribble_success_rate', 0)
    p2_dribble = p2_data.get('dribble_success_rate', 0)

    # 2. Susun mentah data metrik tabel
    raw_metrics = [
        ("Matches Played", p1_data.get('matches_played', 0), p2_data.get('matches_played', 0), ""),
        ("Total Minutes Played", p1_data.get('total_minutes', 0), p2_data.get('total_minutes', 0), " mins"),
        ("Avg Minutes Per Match", p1_data.get('avg_minutes', 0), p2_data.get('avg_minutes', 0), " mins"),
        ("Avg Rating", p1_data.get('avg_rating', 0), p2_data.get('avg_rating', 0), ""),
        ("Total Goals", p1_data.get('total_goals', 0), p2_data.get('total_goals', 0), ""),
        ("Total Assists", p1_data.get('total_assists', 0), p2_data.get('total_assists', 0), ""),
        ("Goal Contributions", p1_data.get('goal_contributions', 0), p2_data.get('goal_contributions', 0), ""),
        ("Goals Per 90", p1_data.get('goals_per_90', 0), p2_data.get('goals_per_90', 0), ""),
        ("Assists Per 90", p1_data.get('assists_per_90', 0), p2_data.get('assists_per_90', 0), ""),
        ("Total Shots", p1_data.get('total_shots', 0), p2_data.get('total_shots', 0), ""),
        ("Total Shots on Target", p1_data.get('total_shots_on_target', 0), p2_data.get('total_shots_on_target', 0), ""),
        ("Shot Accuracy", p1_data.get('shot_accuracy', 0), p2_data.get('shot_accuracy', 0), "%"),
        ("Total Passes", p1_data.get('total_passes', 0), p2_data.get('total_passes', 0), ""),
        ("Avg Pass Accuracy", p1_data.get('avg_pass_accuracy', 0), p2_data.get('avg_pass_accuracy', 0), "%"),
        ("Total Key Passes", p1_data.get('total_key_passes', 0), p2_data.get('total_key_passes', 0), ""),
        ("Key Passes Per 90", p1_data.get('key_passes_per_90', 0), p2_data.get('key_passes_per_90', 0), ""),
        ("Total Tackles", p1_data.get('total_tackles', 0), p2_data.get('total_tackles', 0), ""),
        ("Tackles Per 90", p1_data.get('tackles_per_90', 0), p2_data.get('tackles_per_90', 0), ""),
        ("Total Interceptions", p1_data.get('total_interceptions', 0), p2_data.get('total_interceptions', 0), ""),
        ("Interceptions Per 90", p1_data.get('interceptions_per_90', 0), p2_data.get('interceptions_per_90', 0), ""),
        ("Total Dribbles Attempted", p1_data.get('total_dribbles_attempted', 0), p2_data.get('total_dribbles_attempted', 0), ""),
        ("Total Dribbles Succeeded", p1_data.get('total_dribbles_succeeded', 0), p2_data.get('total_dribbles_succeeded', 0), ""),
        ("Dribble Success Rate", p1_data.get('dribble_success_rate', 0), p2_data.get('dribble_success_rate', 0), "%"),
        ("Total Yellow Cards", p1_data.get('total_yellow_cards', 0), p2_data.get('total_yellow_cards', 0), ""),
        ("Total Red Cards", p1_data.get('total_red_cards', 0), p2_data.get('total_red_cards', 0), "")
    ]

    metrics = []
    for label, v1, v2, unit in raw_metrics:
        metrics.append({
            "label": label,
            "unit": unit,
            "dominant": 'team1' if v1 > v2 else 'team2' if v2 > v1 else 'none',
            # 👇 ALIASING TINGKAT TABEL: Apapun yang dipanggil HTML (t1/p1/team1) akan sukses terisi 👇
            "t1": v1, "t2": v2,
            "p1": v1, "p2": v2,
            "team1": v1, "team2": v2
        })

    return {
        # 👇 ALIASING TINGKAT ROOT (HEADER PROFIL): Mencegah error objek profil pemain 👇
        "t1": p1_data['player'],
        "t2": p2_data['player'],
        "team1": p1_data['player'],
        "team2": p2_data['player'],
        "player1": p1_data['player'],
        "player2": p2_data['player'],
        
        "metrics": metrics,
        "player1_overview": p1_data,
        "player2_overview": p2_data,
        
        # 👇 ALIASING TINGKAT GRAFIK (CHART.JS): Menyuplai data koordinat radar chart 👇
        "chart_data": {
            "labels": ["Rating", "Goals/90 * 10", "Assists/90 * 10", "Pass Acc (%)", "Dribble Success (%)"],
            "t1": [p1_rating, p1_g90, p1_a90, p1_pass, p1_dribble],
            "t2": [p2_rating, p2_g90, p2_a90, p2_pass, p2_dribble],
            "team1": [p1_rating, p1_g90, p1_a90, p1_pass, p1_dribble],
            "team2": [p2_rating, p2_g90, p2_a90, p2_pass, p2_dribble],
            "player1": [p1_rating, p1_g90, p1_a90, p1_pass, p1_dribble],
            "player2": [p2_rating, p2_g90, p2_a90, p2_pass, p2_dribble],
        }
    }


def get_team_comparison(team1_id, team2_id):
    """
    Compare two teams comprehensively with full aliasing for solid consistency.
    """
    t1_data = get_team_overview(team1_id)
    t2_data = get_team_overview(team2_id)

    if not t1_data or not t2_data:
        return None

    t1_wr = t1_data.get('win_rate', 0)
    t2_wr = t2_data.get('win_rate', 0)
    t1_pos = t1_data.get('avg_possession', 0)
    t2_pos = t2_data.get('avg_possession', 0)
    t1_pa = t1_data.get('avg_pass_accuracy', 0)
    t2_pa = t2_data.get('avg_pass_accuracy', 0)
    t1_cs = t1_data.get('clean_sheet_rate', 0)
    t2_cs = t2_data.get('clean_sheet_rate', 0)
    t1_xg = round(t1_data.get('avg_xg', 0) * 10, 1)
    t2_xg = round(t2_data.get('avg_xg', 0) * 10, 1)

    raw_metrics = [
        ("Matches Played", t1_data.get('matches_played', 0), t2_data.get('matches_played', 0), ""),
        ("Wins", t1_data.get('wins', 0), t2_data.get('wins', 0), ""),
        ("Draws", t1_data.get('draws', 0), t2_data.get('draws', 0), ""),
        ("Losses", t1_data.get('losses', 0), t2_data.get('losses', 0), ""),
        ("Points", t1_data.get('points', 0), t2_data.get('points', 0), ""),
        ("Win Rate", t1_data.get('win_rate', 0), t2_data.get('win_rate', 0), "%"),
        ("Goals For", t1_data.get('goals_for', 0), t2_data.get('goals_for', 0), ""),
        ("Goals Against", t1_data.get('goals_against', 0), t2_data.get('goals_against', 0), ""),
        ("Goal Difference", t1_data.get('goal_difference', 0), t2_data.get('goal_difference', 0), ""),
        ("Avg Goals Per Match", t1_data.get('avg_goals_per_match', 0), t2_data.get('avg_goals_per_match', 0), ""),
        ("Avg Goals Conceded", t1_data.get('avg_goals_conceded', 0), t2_data.get('avg_goals_conceded', 0), ""),
        ("Clean Sheets", t1_data.get('clean_sheets', 0), t2_data.get('clean_sheets', 0), ""),
        ("Clean Sheet Rate", t1_data.get('clean_sheet_rate', 0), t2_data.get('clean_sheet_rate', 0), "%"),
        ("Avg Possession", t1_data.get('avg_possession', 0), t2_data.get('avg_possession', 0), "%"),
        ("Avg Expected Goals (xG)", t1_data.get('avg_xg', 0), t2_data.get('avg_xg', 0), ""),
        ("Avg Shots", t1_data.get('avg_shots', 0), t2_data.get('avg_shots', 0), ""),
        ("Avg Shots on Target", t1_data.get('avg_shots_on_target', 0), t2_data.get('avg_shots_on_target', 0), ""),
        ("Avg Passes", t1_data.get('avg_passes', 0), t2_data.get('avg_passes', 0), ""),
        ("Avg Pass Accuracy", t1_data.get('avg_pass_accuracy', 0), t2_data.get('avg_pass_accuracy', 0), "%"),
        ("Avg Corners", t1_data.get('avg_corners', 0), t2_data.get('avg_corners', 0), ""),
        ("Avg Tackles", t1_data.get('avg_tackles_total', 0), t2_data.get('avg_tackles_total', 0), ""),
        ("Avg Interceptions", t1_data.get('avg_interceptions', 0), t2_data.get('avg_interceptions', 0), ""),
        ("Total Yellow Cards", t1_data.get('total_yellow_cards', 0), t2_data.get('total_yellow_cards', 0), ""),
        ("Total Red Cards", t1_data.get('total_red_cards', 0), t2_data.get('total_red_cards', 0), "")
    ]

    metrics = []
    for label, v1, v2, unit in raw_metrics:
        metrics.append({
            "label": label,
            "unit": unit,
            "dominant": 'team1' if v1 > v2 else 'team2' if v2 > v1 else 'none',
            "t1": v1, "t2": v2,
            "team1": v1, "team2": v2
        })

    return {
        "t1": t1_data['team'],
        "t2": t2_data['team'],
        "team1": t1_data['team'],
        "team2": t2_data['team'],
        "metrics": metrics,
        "team1_overview": t1_data,
        "team2_overview": t2_data,
        "chart_data": {
            "labels": ["Win Rate (%)", "Possession (%)", "Pass Accuracy (%)", "Clean Sheet (%)", "Avg xG * 10"],
            "t1": [t1_wr, t1_pos, t1_pa, t1_cs, t1_xg],
            "t2": [t2_wr, t2_pos, t2_pa, t2_cs, t2_xg],
            "team1": [t1_wr, t1_pos, t1_pa, t1_cs, t1_xg],
            "team2": [t2_wr, t2_pos, t2_pa, t2_cs, t2_xg]
        }
    }

def get_dashboard_summary():
    """
    Get summary statistics for the main dashboard.
    """
    total_matches = Match.query.count()
    total_teams = Team.query.count()
    total_players = Player.query.count()

    # Recent matches
    recent_matches = Match.query.order_by(Match.date.desc()).limit(5).all()

    # Top scorers (from player stats)
    top_scorers_query = db.session.query(
        Player.id, Player.name,
        func.sum(PlayerStats.goals).label('total_goals')
    ).join(PlayerStats).group_by(Player.id, Player.name).order_by(
        func.sum(PlayerStats.goals).desc()
    ).limit(5).all()

    top_scorers = [
        {'player_id': r[0], 'name': r[1], 'goals': int(r[2])}
        for r in top_scorers_query
    ]

    # Top rated players
    top_rated_query = db.session.query(
        Player.id, Player.name,
        func.avg(PlayerStats.rating).label('avg_rating'),
        func.count(PlayerStats.id).label('matches')
    ).join(PlayerStats).group_by(Player.id, Player.name).having(
        func.count(PlayerStats.id) >= 2
    ).order_by(func.avg(PlayerStats.rating).desc()).limit(5).all()

    top_rated = [
        {'player_id': r[0], 'name': r[1], 'avg_rating': round(float(r[2]), 2), 'matches': int(r[3])}
        for r in top_rated_query
    ]

    # League table
    league_table = get_league_table()

    return {
        'total_matches': total_matches,
        'total_teams': total_teams,
        'total_players': total_players,
        'recent_matches': [m.to_dict() for m in recent_matches],
        'top_scorers': top_scorers,
        'top_rated': top_rated,
        'league_table': league_table[:5],  # Top 5
    }


def get_team_performance_trend(team_id, last_n=10):
    """
    Get performance trend data over the last N matches for a team.
    Returns data suitable for line chart visualization.
    """
    team = Team.query.get(team_id)
    if not team:
        return None

    matches = Match.query.filter(
        (Match.home_team_id == team_id) | (Match.away_team_id == team_id)
    ).order_by(Match.date.asc()).all()

    if not matches:
        return None

    matches = matches[-last_n:]  # Get last N

    trend_data = []
    cumulative_points = 0

    for m in matches:
        is_home = m.home_team_id == team_id
        goals_for = m.home_goals if is_home else m.away_goals
        goals_against = m.away_goals if is_home else m.home_goals
        opponent = m.away_team if is_home else m.home_team

        if goals_for > goals_against:
            result = 'W'
            pts = 3
        elif goals_for == goals_against:
            result = 'D'
            pts = 1
        else:
            result = 'L'
            pts = 0

        cumulative_points += pts

        # Get match stats
        stats = MatchStats.query.filter_by(match_id=m.id, team_id=team_id).first()

        trend_data.append({
            'match_id': m.id,
            'date': m.date.isoformat(),
            'opponent': opponent.name if opponent else 'Unknown',
            'goals_for': goals_for,
            'goals_against': goals_against,
            'result': result,
            'cumulative_points': cumulative_points,
            'possession': stats.possession if stats else 0,
            'xg': stats.xg if stats else 0,
            'shots': stats.total_shots if stats else 0,
            'pass_accuracy': stats.pass_accuracy if stats else 0,
        })

    return {
        'team': team.to_dict(),
        'trend': trend_data,
    }
