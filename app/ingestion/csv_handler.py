"""
FDIS CSV/Excel Data Handler
Parses uploaded CSV and Excel files into the database.
"""
import json
import os
from unittest import result
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
    # scorers
    'home_goalscorers': 'home_goalscorers', 'pencetak_gol_kandang': 'home_goalscorers', 'home_scorers': 'home_goalscorers',
    'away_goalscorers': 'away_goalscorers', 'pencetak_gol_tamu': 'away_goalscorers', 'away_scorers': 'away_goalscorers',
    # League/Season
    'league': 'league', 'liga': 'league', 'competition': 'league',
    'season': 'season', 'musim': 'season',
    'venue': 'venue', 'stadium': 'venue', 'stadion': 'venue',
    'referee': 'referee', 'wasit': 'referee',
    # Stats Utama
    'home_possession': 'home_possession', 'away_possession': 'away_possession',
    'home_shots': 'home_total_shots', 'home_total_shots': 'home_total_shots',
    'away_shots': 'away_total_shots', 'away_total_shots': 'away_total_shots',
    'home_shots_on_target': 'home_shots_on_target', 'away_shots_on_target': 'away_shots_on_target',
    'home_shots_off_target': 'home_shots_off_target', 'away_shots_off_target': 'away_shots_off_target',
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
    
    # Advanced Passing & Movement
    'home_long_balls': 'home_long_balls', 'away_long_balls': 'away_long_balls',
    'home_long_balls_success': 'home_long_balls_success', 'away_long_balls_success': 'away_long_balls_success',
    'home_passes_final_third_succes': 'home_passes_final_third_succes', 'away_passes_final_third_succes': 'away_passes_final_third_succes',
    'home_passes_final_third': 'home_passes_final_third', 'away_passes_final_third': 'away_passes_final_third',
    'home_passes_into_penalty_area': 'home_passes_into_penalty_area', 'away_passes_into_penalty_area': 'away_passes_into_penalty_area',
    'home_throw_ins': 'home_throw_ins', 'away_throw_ins': 'away_throw_ins', 
    'home_through_balls': 'home_through_balls', 'away_through_balls': 'away_through_balls',
    'home_final_third_entries': 'home_final_third_entries', 'away_final_third_entries': 'away_final_third_entries',
    'home_crosses': 'home_crosses', 'away_crosses': 'away_crosses',
    'home_crosses_success': 'home_crosses_success', 'away_crosses_success': 'away_crosses_success',
    
    # Dribbling & Box Activity
    'home_dribbles_attempted': 'home_dribbles_attempted', 'away_dribbles_attempted': 'away_dribbles_attempted',
    'home_dribbles_succeeded': 'home_dribbles_succeeded', 'away_dribbles_succeeded': 'away_dribbles_succeeded',
    'home_blocks': 'home_blocks', 'away_blocks': 'away_blocks',
    'home_shots_inside_box': 'home_shots_inside_box', 'away_shots_inside_box': 'away_shots_inside_box',
    'home_shots_outside_box': 'home_shots_outside_box', 'away_shots_outside_box': 'away_shots_outside_box',
    'home_big_chances_scored': 'home_big_chances_scored', 'away_big_chances_scored': 'away_big_chances_scored',
    'home_big_chances_missed': 'home_big_chances_missed', 'away_big_chances_missed': 'away_big_chances_missed',
    'home_hit_woodwork': 'home_hit_woodwork', 'away_hit_woodwork': 'away_hit_woodwork', 
    'home_tackles_success': 'home_tackles_success', 'away_tackles_success': 'away_tackles_success',
    'home_tackles_total': 'home_tackles_total', 'away_tackles_total': 'away_tackles_total',
    'home_clearances': 'home_clearances', 'away_clearances': 'away_clearances',
    'home_duels_won': 'home_duels_won', 'away_duels_won': 'away_duels_won',
    'home_duels_total': 'home_duels_total', 'away_duels_total': 'away_duels_total',
    'home_takles': 'home_takles', 'away_takles': 'away_takles',
    
        # Extra Time (BARU)
    'home_goals_et': 'home_goals_et', 'home_goals_extratime': 'home_goals_et',
    'away_goals_et': 'away_goals_et', 'away_goals_extratime': 'away_goals_et',
    # Penalty Shootout (BARU)
    'has_penalties': 'has_penalties', 'went_to_penalties': 'has_penalties',
    'home_penalties_scored': 'home_penalties_scored', 'home_penalty_goals': 'home_penalties_scored',
    'away_penalties_scored': 'away_penalties_scored', 'away_penalty_goals': 'away_penalties_scored',
    'home_penalties_attempted': 'home_penalties_attempted', 'home_penalty_attempts': 'home_penalties_attempted',
    'away_penalties_attempted': 'away_penalties_attempted', 'away_penalty_attempts': 'away_penalties_attempted',
    'penalty_details': 'penalty_details', 'penalty_takers': 'penalty_details',
    'home_penalty_takers': 'home_penalty_takers',
    'away_penalty_takers': 'away_penalty_takers',
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

def parse_penalty_takers(penalty_string):
    """
    Parse penalty taker string menjadi list of dicts.
    Format yang diterima:
    - "Messi (g), Suarez (g), Pique (x), Busquets (g)"
    - JSON: '[{"player": "Messi", "scored": true}, ...]'
    
    Returns: list of {"player": "name", "scored": bool, "team": "home"/"away"}
    """
    if not penalty_string or pd.isna(penalty_string):
        return []
    
    penalty_string = str(penalty_string).strip()
    
    # Jika format JSON
    if penalty_string.startswith('['):
        try:
            return json.loads(penalty_string)
        except:
            pass
    
    # Parse format: "Name (g/x), Name (g/x)"
    penalties = []
    for item in penalty_string.split(','):
        item = item.strip()
        if '(' in item and ')' in item:
            name = item[:item.rfind('(')].strip()
            result = item[item.rfind('(')+1:item.rfind(')')].strip().lower()
            scored = result in ['g', 'goal', 'yes', 'berhasil']
            penalties.append({
                'player': name,
                'scored': scored
            })
    
    return penalties


def build_penalty_details(home_penalties, away_penalties):
    """
    Combine home dan away penalty lists dengan team info.
    
    Args:
        home_penalties: list of {"player": "name", "scored": bool}
        away_penalties: list of {"player": "name", "scored": bool}
    
    Returns:
        list of {"player": "name", "scored": bool, "team": "home"/"away"}
    """
    details = []
    
    for p in (home_penalties or []):
        details.append({
            'player': p.get('player', 'Unknown'),
            'scored': p.get('scored', False),
            'team': 'home'
        })
    
    for p in (away_penalties or []):
        details.append({
            'player': p.get('player', 'Unknown'),
            'scored': p.get('scored', False),
            'team': 'away'
        })
    
    return details if details else None


def calculate_penalty_stats(penalty_details):
    """
    Calculate total penalties scored dan attempted dari penalty_details.
    
    Returns: (home_scored, home_attempted, away_scored, away_attempted)
    """
    home_scored = away_scored = 0
    home_attempted = away_attempted = 0
    
    for p in (penalty_details or []):
        if p.get('team') == 'home':
            home_attempted += 1
            if p.get('scored'):
                home_scored += 1
        elif p.get('team') == 'away':
            away_attempted += 1
            if p.get('scored'):
                away_scored += 1
    
    return home_scored, home_attempted, away_scored, away_attempted

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
    """
    Process matches CSV/Excel file dengan support penalty shootout.
    """
    result = {
        'success': True,
        'rows_processed': 0,
        'rows_failed': 0,
        'errors': [],
        'matches_created': 0,
        'penalty_matches': 0,  # BARU: track penalty matches
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
                # Update goalscorers
                if not pd.isna(row.get('home_goalscorers')):
                    match.home_goalscorers = str(row.get('home_goalscorers'))
                if not pd.isna(row.get('away_goalscorers')):
                    match.away_goalscorers = str(row.get('away_goalscorers'))
            else:
                # ==========================================
                # PENALTY DATA PROCESSING (BARU)
                # ==========================================
                has_penalties = False
                penalty_details = None
                home_penalties_scored = 0
                away_penalties_scored = 0
                home_penalties_attempted = 0
                away_penalties_attempted = 0
                
                # Check if match went to penalties
                penalty_flag = row.get('has_penalties', False)
                if penalty_flag and str(penalty_flag).lower() in ['true', 'yes', '1', 'y']:
                    has_penalties = True
                
                # Parse penalty takers dari CSV
                if has_penalties or not pd.isna(row.get('home_penalty_takers')):
                    home_pens = parse_penalty_takers(row.get('home_penalty_takers'))
                    away_pens = parse_penalty_takers(row.get('away_penalty_takers'))
                    
                    penalty_details = build_penalty_details(home_pens, away_pens)
                    has_penalties = bool(penalty_details)
                    
                    if penalty_details:
                        h_scored, h_attempted, a_scored, a_attempted = calculate_penalty_stats(penalty_details)
                        home_penalties_scored = h_scored
                        home_penalties_attempted = h_attempted
                        away_penalties_scored = a_scored
                        away_penalties_attempted = a_attempted
                
                # Jika tidak ada penalty takers tapi ada penalty scores
                elif not pd.isna(row.get('home_penalties_scored')) or not pd.isna(row.get('away_penalties_scored')):
                    has_penalties = True
                    home_penalties_scored = safe_int(row.get('home_penalties_scored', 0))
                    away_penalties_scored = safe_int(row.get('away_penalties_scored', 0))
                    home_penalties_attempted = safe_int(row.get('home_penalties_attempted', home_penalties_scored + 1))
                    away_penalties_attempted = safe_int(row.get('away_penalties_attempted', away_penalties_scored + 1))
                
                # ==========================================
                # CREATE MATCH OBJECT
                # ==========================================
                match = Match(
                    home_team_id=home_team.id,
                    away_team_id=away_team.id,
                    date=match_date,
                    home_goals=safe_int(row.get('home_goals', 0)),
                    away_goals=safe_int(row.get('away_goals', 0)),
                    home_goals_et=safe_int(row.get('home_goals_et', 0)),
                    away_goals_et=safe_int(row.get('away_goals_et', 0)),
                    league=str(row.get('league', '')) if not pd.isna(row.get('league', '')) else None,
                    season=str(row.get('season', '')) if not pd.isna(row.get('season', '')) else None,
                    venue=str(row.get('venue', '')) if not pd.isna(row.get('venue', '')) else None,
                    referee=str(row.get('referee', '')) if not pd.isna(row.get('referee', '')) else None,
                    home_goalscorers=str(row.get('home_goalscorers', '')) if not pd.isna(row.get('home_goalscorers')) else None,
                    away_goalscorers=str(row.get('away_goalscorers', '')) if not pd.isna(row.get('away_goalscorers')) else None,
                    # PENALTY INFO (BARU)
                    has_penalties=has_penalties,
                    penalty_details=penalty_details,
                    home_penalties_scored=home_penalties_scored,
                    away_penalties_scored=away_penalties_scored,
                    home_penalties_attempted=home_penalties_attempted,
                    away_penalties_attempted=away_penalties_attempted,
                    # Determine status
                    status='penalties' if has_penalties else ('extra_time' if match.home_goals_et > 0 or match.away_goals_et > 0 else 'completed')
                )
                db.session.add(match)
                db.session.flush()
                result['matches_created'] += 1
                
                if has_penalties:
                    result['penalty_matches'] += 1

            validation_errors = validate_match_row(row, idx + 1)

            if validation_errors:
                result['rows_failed'] += 1
                result['errors'].append(
                    f"Row {idx+1}: " + "; ".join(validation_errors)
                )
                continue

            # Create match stats for home team
            _create_match_stats(match.id, home_team.id, row, 'home')
            # Create match stats for away team
            _create_match_stats(match.id, away_team.id, row, 'away')

            result['rows_processed'] += 1

        except Exception as e:
            result['rows_failed'] += 1
            print(f"!!! ERROR DATABASE: {str(e)}")
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
    
    # Goals & Possession
    stats.goals = safe_int(row.get(f'{prefix}goals', row.get('home_goals' if side == 'home' else 'away_goals', 0)))
    stats.possession = safe_float(row.get(f'{prefix}possession', 0))
    
    # Shooting
    stats.total_shots = safe_int(row.get(f'{prefix}total_shots', 0))
    stats.shots_on_target = safe_int(row.get(f'{prefix}shots_on_target', 0))
    stats.shots_off_target = safe_int(row.get(f'{prefix}shots_off_target', 0))
    stats.blocked_shots = safe_int(row.get(f'{prefix}blocked_shots', 0)) # Tambahkan ini
    stats.shots_inside_box = safe_int(row.get(f'{prefix}shots_inside_box', 0))
    stats.shots_outside_box = safe_int(row.get(f'{prefix}shots_outside_box', 0))
    stats.hit_woodwork = safe_int(row.get(f'{prefix}hit_woodwork', 0))
    stats.big_chances_scored = safe_int(row.get(f'{prefix}big_chances_scored', 0))
    stats.big_chances_missed = safe_int(row.get(f'{prefix}big_chances_missed', 0))

    # Passing & Playmaking
    stats.total_passes = safe_int(row.get(f'{prefix}total_passes', 0))
    stats.pass_accuracy = safe_float(row.get(f'{prefix}pass_accuracy', 0))
    stats.key_passes = safe_int(row.get(f'{prefix}key_passes', 0)) # Tambahkan ini
    stats.passes_into_final_third = safe_int(row.get(f'{prefix}passes_into_final_third', 0))
    stats.passes_final_third_success = safe_int(row.get(f'{prefix}passes_final_third_success', 0))
    stats.passes_into_penalty_area = safe_int(row.get(f'{prefix}passes_into_penalty_area', 0))
    stats.through_balls = safe_int(row.get(f'{prefix}through_balls', 0))
    stats.crosses = safe_int(row.get(f'{prefix}crosses', 0))
    stats.crosses_success = safe_int(row.get(f'{prefix}crosses_success', 0))
    stats.long_balls = safe_int(row.get(f'{prefix}long_balls', 0))
    stats.long_balls_success = safe_int(row.get(f'{prefix}long_balls_success', 0))
    stats.final_third_entries = safe_int(row.get(f'{prefix}final_third_entries', 0))
    stats.throw_ins = safe_int(row.get(f'{prefix}throw_ins', 0))

    # Defense & Discipline
    stats.tackles_success = safe_int(row.get(f'{prefix}tackles_success', 0))
    stats.tackles_total = safe_int(row.get(f'{prefix}tackles_total', 0))
    stats.duels_won = safe_int(row.get(f'{prefix}duels_won', 0))
    stats.duels_total = safe_int(row.get(f'{prefix}duels_total', 0))
    stats.clearances = safe_int(row.get(f'{prefix}clearances', 0))
    stats.interceptions = safe_int(row.get(f'{prefix}interceptions', 0))
    stats.blocks = safe_int(row.get(f'{prefix}blocks', 0)) # Ini block tembakan lawan oleh bek
    stats.goalkeeper_saves = safe_int(row.get(f'{prefix}goalkeeper_saves', 0))
    stats.corners = safe_int(row.get(f'{prefix}corners', 0))
    stats.fouls = safe_int(row.get(f'{prefix}fouls', 0))
    stats.offsides = safe_int(row.get(f'{prefix}offsides', 0))
    stats.yellow_cards = safe_int(row.get(f'{prefix}yellow_cards', 0))
    stats.red_cards = safe_int(row.get(f'{prefix}red_cards', 0))
    stats.tackles = safe_int(row.get(f'{prefix}tackles', 0))
    # Skill & Advanced
    stats.dribbles_attempted = safe_int(row.get(f'{prefix}dribbles_attempted', 0))
    stats.dribbles_succeeded = safe_int(row.get(f'{prefix}dribbles_succeeded', 0))
    stats.xg = safe_float(row.get(f'{prefix}xg', 0))

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

def load_csv(filepath):
    """
    🔥 MAIN ENTRY POINT (WAJIB ADA)
    Dipanggil dari routes/main.py

    Fungsi ini:
    - baca file
    - deteksi tipe
    - proses ke database
    """

    filename = os.path.basename(filepath)

    result = process_uploaded_file(filepath, filename)

    if not result['success']:
        raise Exception(f"Upload failed: {result['errors']}")

    return result

def validate_match_row(row, idx):
    errors = []

    for side in ['home', 'away']:
        prefix = f'{side}_'

        total_shots = safe_int(row.get(f'{prefix}total_shots', 0))
        on_target = safe_int(row.get(f'{prefix}shots_on_target', 0))
        off_target = safe_int(row.get(f'{prefix}shots_off_target', 0))
        blocked = safe_int(row.get(f'{prefix}blocked_shots', 0))

        # total shots consistency
        if on_target + off_target + blocked > total_shots:
            errors.append(
                f"{side}: shots breakdown ({on_target}+{off_target}+{blocked}) "
                f"> total_shots ({total_shots})"
            )

        # pass accuracy
        pass_acc = safe_float(row.get(f'{prefix}pass_accuracy', 0))
        if pass_acc < 0 or pass_acc > 100:
            errors.append(f"{side}: pass_accuracy must be 0-100")

        # possession
        possession = safe_float(row.get(f'{prefix}possession', 0))
        if possession < 0 or possession > 100:
            errors.append(f"{side}: possession must be 0-100")

        # dribbles
        drib_att = safe_int(row.get(f'{prefix}dribbles_attempted', 0))
        drib_suc = safe_int(row.get(f'{prefix}dribbles_succeeded', 0))
        if drib_suc > drib_att:
            errors.append(
                f"{side}: dribbles_succeeded ({drib_suc}) > attempted ({drib_att})"
            )

        # big chances
        bc_scored = safe_int(row.get(f'{prefix}big_chances_scored', 0))
        goals = safe_int(row.get(f'{prefix}goals', row.get(f'{side}_goals', 0)))
        if bc_scored > goals + 5:
            errors.append(
                f"{side}: suspicious big_chances_scored ({bc_scored})"
            )

    return errors