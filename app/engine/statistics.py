"""
FDIS Statistical Computation Engine
Calculates team and player performance metrics.
"""
import numpy as np
import pandas as pd
from sqlalchemy import func, case, and_
from app import db
from app.models import Team, Player, Match, MatchStats, PlayerStats


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
    if team_stats:
        avg_possession = np.mean([s.possession for s in team_stats if s.possession])
        avg_shots = np.mean([s.total_shots for s in team_stats if s.total_shots])
        avg_shots_on_target = np.mean([s.shots_on_target for s in team_stats if s.shots_on_target is not None])
        avg_passes = np.mean([s.total_passes for s in team_stats if s.total_passes])
        avg_pass_accuracy = np.mean([s.pass_accuracy for s in team_stats if s.pass_accuracy])
        avg_xg = np.mean([s.xg for s in team_stats if s.xg])
        total_yellow = sum(s.yellow_cards or 0 for s in team_stats)
        total_red = sum(s.red_cards or 0 for s in team_stats)
        avg_corners = np.mean([s.corners for s in team_stats if s.corners is not None])
        avg_tackles = np.mean([s.tackles for s in team_stats if s.tackles is not None])
        avg_interceptions = np.mean([s.interceptions for s in team_stats if s.interceptions is not None])
    else:
        avg_possession = avg_shots = avg_shots_on_target = 0
        avg_passes = avg_pass_accuracy = avg_xg = 0
        total_yellow = total_red = 0
        avg_corners = avg_tackles = avg_interceptions = 0

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
        'team': team.to_dict(),
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
        'avg_tackles': round(float(avg_tackles), 1),
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

    result = {
        'match': match.to_dict(),
        'home_stats': home_stats.to_dict() if home_stats else {},
        'away_stats': away_stats.to_dict() if away_stats else {},
    }

    # Determine dominance metrics
    if home_stats and away_stats:
        metrics = {}
        stat_fields = [
            ('possession', 'Possession', '%'),
            ('total_shots', 'Total Shots', ''),
            ('shots_on_target', 'Shots on Target', ''),
            ('total_passes', 'Passes', ''),
            ('pass_accuracy', 'Pass Accuracy', '%'),
            ('corners', 'Corners', ''),
            ('tackles', 'Tackles', ''),
            ('interceptions', 'Interceptions', ''),
            ('xg', 'Expected Goals', ''),
        ]

        home_advantages = 0
        for field, label, unit in stat_fields:
            h_val = getattr(home_stats, field, 0) or 0
            a_val = getattr(away_stats, field, 0) or 0
            dominant = 'home' if h_val > a_val else ('away' if a_val > h_val else 'equal')
            if dominant == 'home':
                home_advantages += 1
            metrics[field] = {
                'label': label,
                'home': h_val,
                'away': a_val,
                'dominant': dominant,
                'unit': unit,
            }
            
        result['metrics'] = metrics
        result['dominant_team'] = 'home' if home_advantages > len(stat_fields) / 2 else 'away'
        result['home_advantages'] = home_advantages
        result['total_metrics'] = len(stat_fields)

    return result


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
    avg_pass_accuracy = round(np.mean([s.pass_accuracy for s in stats if s.pass_accuracy]), 1)

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


def get_team_comparison(team_id_1, team_id_2):
    """
    Compare two teams across all available metrics.
    """
    stats1 = get_team_overview(team_id_1)
    stats2 = get_team_overview(team_id_2)

    if not stats1 or not stats2:
        return None

    # Head-to-head
    h2h_matches = Match.query.filter(
        ((Match.home_team_id == team_id_1) & (Match.away_team_id == team_id_2)) |
        ((Match.home_team_id == team_id_2) & (Match.away_team_id == team_id_1))
    ).order_by(Match.date.desc()).all()

    h2h = {'team1_wins': 0, 'team2_wins': 0, 'draws': 0, 'matches': []}
    for m in h2h_matches:
        if m.home_team_id == team_id_1:
            if m.home_goals > m.away_goals:
                h2h['team1_wins'] += 1
            elif m.home_goals < m.away_goals:
                h2h['team2_wins'] += 1
            else:
                h2h['draws'] += 1
        else:
            if m.away_goals > m.home_goals:
                h2h['team1_wins'] += 1
            elif m.away_goals < m.home_goals:
                h2h['team2_wins'] += 1
            else:
                h2h['draws'] += 1
        h2h['matches'].append(m.to_dict())

    return {
        'team1': stats1,
        'team2': stats2,
        'head_to_head': h2h,
    }


def get_player_comparison(player_id_1, player_id_2):
    """Compare two players across all available metrics."""
    stats1 = get_player_overview(player_id_1)
    stats2 = get_player_overview(player_id_2)

    if not stats1 or not stats2:
        return None

    return {
        'player1': stats1,
        'player2': stats2,
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
