"""
FDIS Manual Data Entry Handler
Processes form-submitted match and player data.
"""
from datetime import datetime
from app import db
from app.models import Match, MatchStats, Player, PlayerStats
from app.ingestion.csv_handler import get_or_create_team, get_or_create_player, safe_int, safe_float


def process_manual_match(data):
    """
    Process a manually entered match from form data.
    
    Args:
        data: Dictionary with match data from the form.
    
    Returns:
        Dictionary with result status and match info.
    """
    result = {'success': True, 'errors': [], 'match_id': None}

    try:
        # Get or create teams
        home_team = get_or_create_team(data.get('home_team'))
        away_team = get_or_create_team(data.get('away_team'))

        if not home_team or not away_team:
            result['success'] = False
            result['errors'].append('Both home and away team names are required.')
            return result

        # Parse date
        try:
            match_date = datetime.strptime(data.get('date', ''), '%Y-%m-%d').date()
        except (ValueError, TypeError):
            match_date = datetime.now().date()

        # Create match
        match = Match(
            home_team_id=home_team.id,
            away_team_id=away_team.id,
            date=match_date,
            home_goals=safe_int(data.get('home_goals', 0)),
            away_goals=safe_int(data.get('away_goals', 0)),
            league=data.get('league') or None,
            season=data.get('season') or None,
            venue=data.get('venue') or None,
            referee=data.get('referee') or None,
        )
        db.session.add(match)
        db.session.flush()

        # Create home team stats
        home_stats = MatchStats(
            match_id=match.id,
            team_id=home_team.id,
            goals=safe_int(data.get('home_goals', 0)),
            possession=safe_float(data.get('home_possession', 0)),
            total_shots=safe_int(data.get('home_shots', 0)),
            shots_on_target=safe_int(data.get('home_shots_on_target', 0)),
            total_passes=safe_int(data.get('home_passes', 0)),
            pass_accuracy=safe_float(data.get('home_pass_accuracy', 0)),
            corners=safe_int(data.get('home_corners', 0)),
            fouls=safe_int(data.get('home_fouls', 0)),
            yellow_cards=safe_int(data.get('home_yellow_cards', 0)),
            red_cards=safe_int(data.get('home_red_cards', 0)),
            xg=safe_float(data.get('home_xg', 0)),
            tackles=safe_int(data.get('home_tackles', 0)),
            interceptions=safe_int(data.get('home_interceptions', 0)),
        )
        db.session.add(home_stats)

        # Create away team stats
        away_stats = MatchStats(
            match_id=match.id,
            team_id=away_team.id,
            goals=safe_int(data.get('away_goals', 0)),
            possession=safe_float(data.get('away_possession', 0)),
            total_shots=safe_int(data.get('away_shots', 0)),
            shots_on_target=safe_int(data.get('away_shots_on_target', 0)),
            total_passes=safe_int(data.get('away_passes', 0)),
            pass_accuracy=safe_float(data.get('away_pass_accuracy', 0)),
            corners=safe_int(data.get('away_corners', 0)),
            fouls=safe_int(data.get('away_fouls', 0)),
            yellow_cards=safe_int(data.get('away_yellow_cards', 0)),
            red_cards=safe_int(data.get('away_red_cards', 0)),
            xg=safe_float(data.get('away_xg', 0)),
            tackles=safe_int(data.get('away_tackles', 0)),
            interceptions=safe_int(data.get('away_interceptions', 0)),
        )
        db.session.add(away_stats)

        db.session.commit()
        result['match_id'] = match.id

    except Exception as e:
        db.session.rollback()
        result['success'] = False
        result['errors'].append(f'Failed to save match: {str(e)}')

    return result


def process_manual_player_stats(data):
    """
    Process manually entered player statistics.
    
    Args:
        data: Dictionary with player stats from form.
    
    Returns:
        Dictionary with result status.
    """
    result = {'success': True, 'errors': [], 'player_id': None}

    try:
        player = get_or_create_player(
            name=data.get('player_name'),
            team_name=data.get('team'),
            position=data.get('position'),
            nationality=data.get('nationality'),
            shirt_number=data.get('shirt_number'),
        )
        if not player:
            result['success'] = False
            result['errors'].append('Player name is required.')
            return result

        match_id = safe_int(data.get('match_id', 0))
        if match_id > 0:
            ps = PlayerStats(
                match_id=match_id,
                player_id=player.id,
                minutes_played=safe_int(data.get('minutes_played', 0)),
                rating=safe_float(data.get('rating')),
                goals=safe_int(data.get('goals', 0)),
                assists=safe_int(data.get('assists', 0)),
                shots=safe_int(data.get('shots', 0)),
                shots_on_target=safe_int(data.get('shots_on_target', 0)),
                passes=safe_int(data.get('passes', 0)),
                pass_accuracy=safe_float(data.get('pass_accuracy', 0)),
                tackles=safe_int(data.get('tackles', 0)),
                interceptions=safe_int(data.get('interceptions', 0)),
                yellow_cards=safe_int(data.get('yellow_cards', 0)),
                red_cards=safe_int(data.get('red_cards', 0)),
            )
            db.session.add(ps)

        db.session.commit()
        result['player_id'] = player.id

    except Exception as e:
        db.session.rollback()
        result['success'] = False
        result['errors'].append(f'Failed to save player stats: {str(e)}')

    return result
