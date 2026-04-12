"""
FDIS CSV/Excel Data Handler
Parses uploaded CSV and Excel files into the database.
"""
import json
import os
import pandas as pd
from datetime import datetime
from app import db
from app.models import Team, Player, Match, MatchStats, PlayerStats, UploadHistory


# Flexible column name mapping — maps various user header names to our internal names
MATCH_COLUMN_MAP = {
    # Date
    'date': 'date', 'match_date': 'date', 'tanggal': 'date', 'game_date': 'date',
    # Teams
    'home_team': 'home_team', 'home': 'home_team', 'tim_tuan_rumah': 'home_team',
    'away_team': 'away_team', 'away': 'away_team', 'tim_tamu': 'away_team',
    # Goals
    'home_goals': 'home_goals', 'home_score': 'home_goals', 'hg': 'home_goals', 'fthg': 'home_goals',
    'away_goals': 'away_goals', 'away_score': 'away_goals', 'ag': 'away_goals', 'ftag': 'away_goals',
    # League/Season
    'league': 'league', 'liga': 'league', 'competition': 'league',
    'season': 'season', 'musim': 'season',
    'venue': 'venue', 'stadium': 'venue', 'stadion': 'venue',
    'referee': 'referee', 'wasit': 'referee',
    # Stats
    'home_possession': 'home_possession', 'away_possession': 'away_possession',
    'home_shots': 'home_total_shots', 'home_total_shots': 'home_total_shots',
    'away_shots': 'away_total_shots', 'away_total_shots': 'away_total_shots',
    'home_shots_on_target': 'home_shots_on_target', 'away_shots_on_target': 'away_shots_on_target',
    'home_passes': 'home_total_passes', 'home_total_passes': 'home_total_passes',
    'away_passes': 'away_total_passes', 'away_total_passes': 'away_total_passes',
    'home_pass_accuracy': 'home_pass_accuracy', 'away_pass_accuracy': 'away_pass_accuracy',
    'home_corners': 'home_corners', 'away_corners': 'away_corners',
    'home_fouls': 'home_fouls', 'away_fouls': 'away_fouls',
    'home_yellow_cards': 'home_yellow_cards', 'away_yellow_cards': 'away_yellow_cards',
    'home_red_cards': 'home_red_cards', 'away_red_cards': 'away_red_cards',
    'home_xg': 'home_xg', 'away_xg': 'away_xg',
    'home_tackles': 'home_tackles', 'away_tackles': 'away_tackles',
    'home_interceptions': 'home_interceptions', 'away_interceptions': 'away_interceptions',
    'home_offsides': 'home_offsides', 'away_offsides': 'away_offsides',
    'home_goalkeeper_saves': 'home_goalkeeper_saves', 'away_goalkeeper_saves': 'away_goalkeeper_saves',
}

PLAYER_COLUMN_MAP = {
    'name': 'name', 'player_name': 'name', 'nama': 'name', 'player': 'name',
    'team': 'team', 'team_name': 'team', 'tim': 'team', 'club': 'team',
    'position': 'position', 'pos': 'position', 'posisi': 'position',
    'nationality': 'nationality', 'nation': 'nationality', 'kebangsaan': 'nationality',
    'shirt_number': 'shirt_number', 'number': 'shirt_number', 'no': 'shirt_number',
    'match_id': 'match_id',
    'minutes_played': 'minutes_played', 'minutes': 'minutes_played', 'mins': 'minutes_played',
    'rating': 'rating', 'match_rating': 'rating',
    'goals': 'goals', 'gol': 'goals',
    'assists': 'assists', 'assist': 'assists',
    'shots': 'shots', 'shots_on_target': 'shots_on_target',
    'passes': 'passes', 'pass_accuracy': 'pass_accuracy',
    'key_passes': 'key_passes',
    'crosses': 'crosses',
    'tackles': 'tackles', 'interceptions': 'interceptions',
    'blocks': 'blocks', 'clearances': 'clearances',
    'fouls_committed': 'fouls_committed', 'fouls_drawn': 'fouls_drawn',
    'yellow_cards': 'yellow_cards', 'red_cards': 'red_cards',
    'dribbles_attempted': 'dribbles_attempted', 'dribbles_succeeded': 'dribbles_succeeded',
}


def allowed_file(filename, allowed_extensions):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def normalize_columns(df, column_map):
    """Normalize column names using the mapping dictionary."""
    df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]
    rename_map = {}
    for col in df.columns:
        if col in column_map:
            rename_map[col] = column_map[col]
    df = df.rename(columns=rename_map)
    return df


def read_file(filepath):
    """Read CSV or Excel file into a DataFrame."""
    ext = filepath.rsplit('.', 1)[1].lower()
    if ext == 'csv':
        return pd.read_csv(filepath)
    elif ext in ('xlsx', 'xls'):
        return pd.read_excel(filepath, engine='openpyxl')
    else:
        raise ValueError(f'Unsupported file format: .{ext}')


def detect_file_type(df):
    """Detect whether the file contains match data or player data."""
    cols = set(df.columns.str.lower().str.replace(' ', '_'))
    match_indicators = {'home_team', 'away_team', 'home_goals', 'away_goals', 'home', 'away'}
    player_indicators = {'player_name', 'name', 'position', 'goals', 'assists', 'minutes_played', 'rating'}

    match_score = len(cols & match_indicators)
    player_score = len(cols & player_indicators)

    if match_score >= 2:
        return 'matches'
    elif player_score >= 3:
        return 'players'
    else:
        return 'unknown'


def process_uploaded_file(filepath, filename, data_type='auto'):
    """Detect uploaded file type and process it into the database."""
    try:
        df = read_file(filepath)
    except Exception as e:
        result = {
            'success': False,
            'rows_processed': 0,
            'rows_failed': 0,
            'errors': [f'Failed to read file: {str(e)}'],
            'source_type': 'csv',
            'data_type': 'unknown',
        }
        _log_upload(filename, 'csv', 0, 'failed', result['errors'][0], details=result)
        return result

    detected_type = detect_file_type(df)
    if data_type != 'auto':
        detected_type = data_type

    if detected_type == 'matches':
        result = process_matches_file(filepath, filename)
    elif detected_type == 'players':
        result = process_players_file(filepath, filename)
    else:
        result = {
            'success': False,
            'rows_processed': 0,
            'rows_failed': 0,
            'errors': ['Could not determine data type. Please upload a match or player file or set data_type explicitly.'],
            'source_type': 'csv',
            'data_type': 'unknown',
        }
        _log_upload(filename, 'csv', 0, 'failed', result['errors'][0], details=result)

    result['data_type'] = detected_type
    return result


def get_or_create_team(name):
    """Get existing team or create new one."""
    if not name or pd.isna(name):
        return None
    name = str(name).strip()
    team = Team.query.filter(Team.name.ilike(name)).first()
    if not team:
        team = Team(name=name)
        db.session.add(team)
        db.session.flush()
    return team


def get_or_create_player(name, team_name=None, position=None, nationality=None, shirt_number=None):
    """Get existing player or create new one."""
    if not name or pd.isna(name):
        return None
    name = str(name).strip()

    # Try to find by name and team
    query = Player.query.filter(Player.name.ilike(name))
    if team_name:
        team = get_or_create_team(team_name)
        if team:
            query = query.filter_by(team_id=team.id)

    player = query.first()
    if not player:
        team = get_or_create_team(team_name) if team_name else None
        player = Player(
            name=name,
            team_id=team.id if team else None,
            position=str(position) if position and not pd.isna(position) else None,
            nationality=str(nationality) if nationality and not pd.isna(nationality) else None,
            shirt_number=int(shirt_number) if shirt_number and not pd.isna(shirt_number) else None,
        )
        db.session.add(player)
        db.session.flush()
    return player


def safe_int(val, default=0):
    """Safely convert value to integer."""
    try:
        if pd.isna(val):
            return default
        return int(float(val))
    except (ValueError, TypeError):
        return default


def safe_float(val, default=0.0):
    """Safely convert value to float."""
    try:
        if pd.isna(val):
            return default
        return float(val)
    except (ValueError, TypeError):
        return default


def parse_date(val):
    """Try to parse various date formats."""
    if pd.isna(val):
        return datetime.now().date()
    if isinstance(val, datetime):
        return val.date()
    if hasattr(val, 'date'):
        return val.date()
    for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y', '%Y/%m/%d']:
        try:
            return datetime.strptime(str(val).strip(), fmt).date()
        except ValueError:
            continue
    return datetime.now().date()


def process_matches_file(filepath, filename):
    """Process a matches CSV/Excel file and insert into database."""
    result = {
        'success': True,
        'rows_processed': 0,
        'rows_failed': 0,
        'errors': [],
        'matches_created': 0,
    }

    try:
        df = read_file(filepath)
        df = normalize_columns(df, MATCH_COLUMN_MAP)
    except Exception as e:
        result['success'] = False
        result['errors'].append(f'Failed to read file: {str(e)}')
        _log_upload(filename, 'csv', 0, 'failed', str(e))
        return result

    required = ['home_team', 'away_team']
    missing = [col for col in required if col not in df.columns]
    if missing:
        result['success'] = False
        result['errors'].append(f'Missing required columns: {", ".join(missing)}')
        _log_upload(filename, 'csv', 0, 'failed', f'Missing columns: {", ".join(missing)}')
        return result

    for idx, row in df.iterrows():
        try:
            home_team = get_or_create_team(row.get('home_team'))
            away_team = get_or_create_team(row.get('away_team'))

            if not home_team or not away_team:
                result['rows_failed'] += 1
                result['errors'].append(f'Row {idx + 1}: Missing team name')
                continue

            match_date = parse_date(row.get('date', None))

            # Check for duplicate match
            existing = Match.query.filter_by(
                home_team_id=home_team.id,
                away_team_id=away_team.id,
                date=match_date
            ).first()

            if existing:
                match = existing
            else:
                match = Match(
                    home_team_id=home_team.id,
                    away_team_id=away_team.id,
                    date=match_date,
                    home_goals=safe_int(row.get('home_goals', 0)),
                    away_goals=safe_int(row.get('away_goals', 0)),
                    league=str(row.get('league', '')) if not pd.isna(row.get('league', '')) else None,
                    season=str(row.get('season', '')) if not pd.isna(row.get('season', '')) else None,
                    venue=str(row.get('venue', '')) if not pd.isna(row.get('venue', '')) else None,
                    referee=str(row.get('referee', '')) if not pd.isna(row.get('referee', '')) else None,
                )
                db.session.add(match)
                db.session.flush()
                result['matches_created'] += 1

            # Create match stats for home team
            _create_match_stats(match.id, home_team.id, row, 'home')
            # Create match stats for away team
            _create_match_stats(match.id, away_team.id, row, 'away')

            result['rows_processed'] += 1

        except Exception as e:
            result['rows_failed'] += 1
            result['errors'].append(f'Row {idx + 1}: {str(e)}')
            continue

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        result['success'] = False
        result['errors'].append(f'Database commit failed: {str(e)}')

    status = 'success' if result['success'] else 'partial'
    _log_upload(filename, 'csv', result['rows_processed'], status,
                '; '.join(result['errors'][:5]) if result['errors'] else None)

    return result


def _create_match_stats(match_id, team_id, row, side):
    """Create or update MatchStats for a team in a match."""
    existing = MatchStats.query.filter_by(match_id=match_id, team_id=team_id).first()
    if existing:
        stats = existing
    else:
        stats = MatchStats(match_id=match_id, team_id=team_id)

    prefix = f'{side}_'
    stats.goals = safe_int(row.get(f'{prefix}goals', row.get('home_goals' if side == 'home' else 'away_goals', 0)))
    stats.possession = safe_float(row.get(f'{prefix}possession', 0))
    stats.total_shots = safe_int(row.get(f'{prefix}total_shots', 0))
    stats.shots_on_target = safe_int(row.get(f'{prefix}shots_on_target', 0))
    stats.total_passes = safe_int(row.get(f'{prefix}total_passes', 0))
    stats.pass_accuracy = safe_float(row.get(f'{prefix}pass_accuracy', 0))
    stats.corners = safe_int(row.get(f'{prefix}corners', 0))
    stats.fouls = safe_int(row.get(f'{prefix}fouls', 0))
    stats.yellow_cards = safe_int(row.get(f'{prefix}yellow_cards', 0))
    stats.red_cards = safe_int(row.get(f'{prefix}red_cards', 0))
    stats.xg = safe_float(row.get(f'{prefix}xg', 0))
    stats.tackles = safe_int(row.get(f'{prefix}tackles', 0))
    stats.interceptions = safe_int(row.get(f'{prefix}interceptions', 0))
    stats.offsides = safe_int(row.get(f'{prefix}offsides', 0))
    stats.goalkeeper_saves = safe_int(row.get(f'{prefix}goalkeeper_saves', 0))

    if not existing:
        db.session.add(stats)


def process_players_file(filepath, filename):
    """Process a player stats CSV/Excel file and insert into database."""
    result = {
        'success': True,
        'rows_processed': 0,
        'rows_failed': 0,
        'errors': [],
        'players_created': 0,
    }

    try:
        df = read_file(filepath)
        df = normalize_columns(df, PLAYER_COLUMN_MAP)
    except Exception as e:
        result['success'] = False
        result['errors'].append(f'Failed to read file: {str(e)}')
        _log_upload(filename, 'csv', 0, 'failed', str(e))
        return result

    if 'name' not in df.columns:
        result['success'] = False
        result['errors'].append('Missing required column: name (player name)')
        _log_upload(filename, 'csv', 0, 'failed', 'Missing column: name')
        return result

    for idx, row in df.iterrows():
        try:
            player = get_or_create_player(
                name=row.get('name'),
                team_name=row.get('team'),
                position=row.get('position'),
                nationality=row.get('nationality'),
                shirt_number=row.get('shirt_number'),
            )
            if not player:
                result['rows_failed'] += 1
                result['errors'].append(f'Row {idx + 1}: Missing player name')
                continue

            # If match_id is provided, create player stats
            match_id = safe_int(row.get('match_id', 0))
            if match_id > 0:
                match = Match.query.get(match_id)
                if match:
                    existing = PlayerStats.query.filter_by(
                        match_id=match_id, player_id=player.id
                    ).first()
                    if not existing:
                        ps = PlayerStats(
                            match_id=match_id,
                            player_id=player.id,
                            minutes_played=safe_int(row.get('minutes_played', 0)),
                            rating=safe_float(row.get('rating')),
                            goals=safe_int(row.get('goals', 0)),
                            assists=safe_int(row.get('assists', 0)),
                            shots=safe_int(row.get('shots', 0)),
                            shots_on_target=safe_int(row.get('shots_on_target', 0)),
                            passes=safe_int(row.get('passes', 0)),
                            pass_accuracy=safe_float(row.get('pass_accuracy', 0)),
                            key_passes=safe_int(row.get('key_passes', 0)),
                            crosses=safe_int(row.get('crosses', 0)),
                            tackles=safe_int(row.get('tackles', 0)),
                            interceptions=safe_int(row.get('interceptions', 0)),
                            blocks=safe_int(row.get('blocks', 0)),
                            clearances=safe_int(row.get('clearances', 0)),
                            fouls_committed=safe_int(row.get('fouls_committed', 0)),
                            fouls_drawn=safe_int(row.get('fouls_drawn', 0)),
                            yellow_cards=safe_int(row.get('yellow_cards', 0)),
                            red_cards=safe_int(row.get('red_cards', 0)),
                            dribbles_attempted=safe_int(row.get('dribbles_attempted', 0)),
                            dribbles_succeeded=safe_int(row.get('dribbles_succeeded', 0)),
                        )
                        db.session.add(ps)

            result['rows_processed'] += 1

        except Exception as e:
            result['rows_failed'] += 1
            result['errors'].append(f'Row {idx + 1}: {str(e)}')
            continue

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        result['success'] = False
        result['errors'].append(f'Database commit failed: {str(e)}')

    status = 'success' if result['success'] else 'partial'
    _log_upload(filename, 'csv', result['rows_processed'], status,
                '; '.join(result['errors'][:5]) if result['errors'] else None)

    return result


def _log_upload(filename, source_type, row_count, status, error_message=None, details=None):
    """Log upload to history table."""
    upload = UploadHistory(
        filename=filename,
        source_type=source_type,
        row_count=row_count,
        status=status,
        error_message=error_message,
        details=json.dumps(details) if details is not None else None,
    )
    db.session.add(upload)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
