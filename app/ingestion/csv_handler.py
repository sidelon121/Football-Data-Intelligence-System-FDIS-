"""
FDIS CSV/Excel Data Handler - FINAL FIXED v3
Handles CSV file uploads dengan support lengkap penalty shootout
PERBAIKAN: Smart routing + Complete column mapping + Player upload fix
"""
import json
import os
import pandas as pd
from datetime import datetime
from app import db
from app.models import Team, Player, Match, MatchStats, PlayerStats, UploadHistory


# ===================================================================
# COMPLETE COLUMN MAPPING - SESUAI USER SPEC
# ===================================================================

MATCH_COLUMN_MAP = {
    # Date
    'date': 'date', 'match_date': 'date', 'tanggal': 'date', 'game_date': 'date',
    
    # Teams
    'home_team': 'home_team', 'home': 'home_team', 'tim_tuan_rumah': 'home_team',
    'away_team': 'away_team', 'away': 'away_team', 'tim_tamu': 'away_team',
    
    # Goals
    'home_goals': 'home_goals', 'home_score': 'home_goals', 'hg': 'home_goals', 'fthg': 'home_goals',
    'away_goals': 'away_goals', 'away_score': 'away_goals', 'ag': 'away_goals', 'ftag': 'away_goals',
    
    # Goalscorers
    'home_goalscorers': 'home_goalscorers', 'pencetak_gol_kandang': 'home_goalscorers', 'home_scorers': 'home_goalscorers',
    'away_goalscorers': 'away_goalscorers', 'pencetak_gol_tamu': 'away_goalscorers', 'away_scorers': 'away_goalscorers',
    
    # Extra Time
    'home_goals_et': 'home_goals_et', 'home_goals_extratime': 'home_goals_et',
    'away_goals_et': 'away_goals_et', 'away_goals_extratime': 'away_goals_et',
    
    # Penalty Shootout
    'has_penalties': 'has_penalties', 'went_to_penalties': 'has_penalties',
    'home_penalties_scored': 'home_penalties_scored', 'home_penalty_goals': 'home_penalties_scored',
    'away_penalties_scored': 'away_penalties_scored', 'away_penalty_goals': 'away_penalties_scored',
    'home_penalties_attempted': 'home_penalties_attempted', 'home_penalty_attempts': 'home_penalties_attempted',
    'away_penalties_attempted': 'away_penalties_attempted', 'away_penalty_attempts': 'away_penalties_attempted',
    'penalty_details': 'penalty_details', 'penalty_takers': 'penalty_details',
    'home_penalty_takers': 'home_penalty_takers',
    'away_penalty_takers': 'away_penalty_takers',
    
    # League/Season
    'league': 'league', 'liga': 'league', 'competition': 'league',
    'season': 'season', 'musim': 'season',
    'venue': 'venue', 'stadium': 'venue', 'stadion': 'venue',
    'referee': 'referee', 'wasit': 'referee',
    
    # Possession Stats
    'home_possession': 'home_possession', 'away_possession': 'away_possession',
    
    # Shots
    'home_shots': 'home_total_shots', 'home_total_shots': 'home_total_shots',
    'away_shots': 'away_total_shots', 'away_total_shots': 'away_total_shots',
    'home_shots_on_target': 'home_shots_on_target', 'away_shots_on_target': 'away_shots_on_target',
    'home_shots_off_target': 'home_shots_off_target', 'away_shots_off_target': 'away_shots_off_target',
    'home_blocked_shots': 'home_blocked_shots', 'away_blocked_shots': 'away_blocked_shots',
    'home_shots_inside_box': 'home_shots_inside_box', 'away_shots_inside_box': 'away_shots_inside_box',
    'home_shots_outside_box': 'home_shots_outside_box', 'away_shots_outside_box': 'away_shots_outside_box',
    'home_hit_woodwork': 'home_hit_woodwork', 'away_hit_woodwork': 'away_hit_woodwork',
    'home_big_chances_scored': 'home_big_chances_scored', 'away_big_chances_scored': 'away_big_chances_scored',
    'home_big_chances_missed': 'home_big_chances_missed', 'away_big_chances_missed': 'away_big_chances_missed',
    
    # Passing
    'home_passes': 'home_total_passes', 'home_total_passes': 'home_total_passes',
    'away_passes': 'away_total_passes', 'away_total_passes': 'away_total_passes',
    'home_pass_accuracy': 'home_pass_accuracy', 'away_pass_accuracy': 'away_pass_accuracy',
    'home_key_passes': 'home_key_passes', 'away_key_passes': 'away_key_passes',
    'home_passes_final_third': 'home_passes_final_third', 'away_passes_final_third': 'away_passes_final_third',
    'home_passes_final_third_success': 'home_passes_final_third_success', 'away_passes_final_third_success': 'away_passes_final_third_success',
    'home_passes_into_penalty_area': 'home_passes_into_penalty_area', 'away_passes_into_penalty_area': 'away_passes_into_penalty_area',
    'home_through_balls': 'home_through_balls', 'away_through_balls': 'away_through_balls',
    'home_long_balls': 'home_long_balls', 'away_long_balls': 'away_long_balls',
    'home_long_balls_success': 'home_long_balls_success', 'away_long_balls_success': 'away_long_balls_success',
    'home_crosses': 'home_crosses', 'away_crosses': 'away_crosses',
    'home_crosses_success': 'home_crosses_success', 'away_crosses_success': 'away_crosses_success',
    'home_throw_ins': 'home_throw_ins', 'away_throw_ins': 'away_throw_ins',
    'home_final_third_entries': 'home_final_third_entries', 'away_final_third_entries': 'away_final_third_entries',
    
    # Dribbling
    'home_dribbles_attempted': 'home_dribbles_attempted', 'away_dribbles_attempted': 'away_dribbles_attempted',
    'home_dribbles_succeeded': 'home_dribbles_succeeded', 'away_dribbles_succeeded': 'away_dribbles_succeeded',
    
    # Defense
    'home_tackles': 'home_tackles_total', 'home_tackles_total': 'home_tackles_total',
    'away_tackles': 'away_tackles_total', 'away_tackles_total': 'away_tackles_total',
    'home_tackles_success': 'home_tackles_success', 'away_tackles_success': 'away_tackles_success',
    'home_interceptions': 'home_interceptions', 'away_interceptions': 'away_interceptions',
    'home_blocks': 'home_blocks', 'away_blocks': 'away_blocks',
    'home_clearances': 'home_clearances', 'away_clearances': 'away_clearances',
    'home_duels_won': 'home_duels_won', 'away_duels_won': 'away_duels_won',
    'home_duels_total': 'home_duels_total', 'away_duels_total': 'away_duels_total',
    'home_goalkeeper_saves': 'home_goalkeeper_saves', 'away_goalkeeper_saves': 'away_goalkeeper_saves',
    
    # Set Pieces & Discipline
    'home_corners': 'home_corners', 'away_corners': 'away_corners',
    'home_fouls': 'home_fouls', 'away_fouls': 'away_fouls',
    'home_yellow_cards': 'home_yellow_cards', 'away_yellow_cards': 'away_yellow_cards',
    'home_red_cards': 'home_red_cards', 'away_red_cards': 'away_red_cards',
    'home_offsides': 'home_offsides', 'away_offsides': 'away_offsides',
    
    # Advanced
    'home_xg': 'home_xg', 'away_xg': 'away_xg',
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


# ===================================================================
# HELPER FUNCTIONS
# ===================================================================

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


def parse_penalty_takers(penalty_string):
    """Parse penalty taker string into list of dicts."""
    if not penalty_string or pd.isna(penalty_string):
        return []
    
    penalty_string = str(penalty_string).strip()
    
    # Try JSON format
    if penalty_string.startswith('['):
        try:
            return json.loads(penalty_string)
        except:
            pass
    
    # Parse text format: "Name (g/x), Name (g/x)"
    penalties = []
    for item in penalty_string.split(','):
        item = item.strip()
        if '(' in item and ')' in item:
            name = item[:item.rfind('(')].strip()
            result = item[item.rfind('(')+1:item.rfind(')')].strip().lower()
            scored = result in ['g', 'goal', 'yes', 'berhasil', '1', 'true']
            penalties.append({
                'player': name,
                'scored': scored
            })
    
    return penalties


def build_penalty_details(home_penalties, away_penalties):
    """Combine home and away penalty lists with team info."""
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
    """Calculate penalty stats from penalty_details."""
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


def get_or_create_team(name):
    """Get or create team by name."""
    if not name or pd.isna(name):
        return None
    name = str(name).strip()
    team = Team.query.filter(Team.name.ilike(name)).first()
    if not team:
        team = Team(name=name)
        db.session.add(team)
        db.session.flush()
    return team


def normalize_columns(df, column_map):
    """Normalize column names using mapping."""
    df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]
    rename_map = {}
    for col in df.columns:
        if col in column_map:
            rename_map[col] = column_map[col]
    df = df.rename(columns=rename_map)
    return df


def _log_upload(filename, source_type, row_count, status, error_message=None, details=None):
    """Log upload to history table."""
    try:
        upload = UploadHistory(
            filename=filename,
            source_type=source_type,
            row_count=row_count,
            status=status,
            error_message=error_message,
            details=json.dumps(details) if details else None,
        )
        db.session.add(upload)
        db.session.commit()
        print(f"✅ Upload logged: {filename} - {status}")
    except Exception as e:
        db.session.rollback()
        print(f"❌ Failed to log upload: {str(e)}")


# ===================================================================
# DETECT FILE TYPE - IMPROVED LOGIC
# ===================================================================

def detect_file_type(df_columns):
    """
    🔥 IMPROVED DETECTION - Deteksi apakah file adalah MATCH atau PLAYER
    Return: 'match', 'player', atau None jika tidak bisa deteksi
    """
    cols_lower = [str(col).lower().replace(' ', '_') for col in df_columns]
    
    print(f"\n🔍 DETECTION ANALYSIS:")
    print(f"   Columns found: {cols_lower}\n")
    
    # MATCH INDICATORS - Strict requirement
    match_required_indicators = ['home_team', 'away_team', 'home_goals', 'away_goals']
    match_found = sum(1 for ind in match_required_indicators if any(ind in col for col in cols_lower))
    
    # PLAYER INDICATORS
    player_required = ['name', 'team']  # Minimal requirement untuk player
    player_found_required = sum(1 for ind in player_required if any(ind in col for col in cols_lower))
    
    player_optional = ['position', 'nationality', 'shirt_number', 'minutes_played', 'rating', 'goals', 'assists', 'passes']
    player_found_optional = sum(1 for ind in player_optional if any(ind in col for col in cols_lower))
    
    print(f"   MATCH indicators: {match_found}/4 (home_team, away_team, home_goals, away_goals)")
    print(f"   PLAYER required: {player_found_required}/2 (name, team)")
    print(f"   PLAYER optional: {player_found_optional}/{len(player_optional)}\n")
    
    # DETECTION LOGIC - Strict
    if match_found >= 3:
        print(f"   ✅ DETECTED: MATCH DATA\n")
        return 'match'
    elif player_found_required == 2:  # HARUS punya 'name' DAN 'team'
        print(f"   ✅ DETECTED: PLAYER DATA\n")
        return 'player'
    else:
        print(f"   ❌ COULD NOT DETECT FILE TYPE\n")
        return None


# ===================================================================
# PROCESS MATCH DATA
# ===================================================================

def process_uploaded_file(filepath, filename):
    """Process matches CSV/Excel file."""
    result = {
        'success': True,
        'rows_processed': 0,
        'rows_failed': 0,
        'errors': [],
        'matches_created': 0,
        'penalty_matches': 0,
        'source_type': 'csv',
        'data_type': 'matches',
    }

    print(f"\n{'='*80}")
    print(f"🔥 STARTING MATCH FILE PROCESSING: {filename}")
    print(f"{'='*80}\n")

    try:
        print(f"📂 Reading file: {filepath}")
        
        file_ext = filename.lower()
        if file_ext.endswith('.csv'):
            df = pd.read_csv(filepath, sep=None, engine='python')
        elif file_ext.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(filepath)
            result['source_type'] = 'excel'
        else:
            raise Exception("Unsupported file format. Please upload a .csv or .xlsx file.")

        print(f"✅ File read successfully - {len(df)} rows found")
        print(f"📋 Columns before normalization: {list(df.columns)}\n")
        
        df = normalize_columns(df, MATCH_COLUMN_MAP)
        print(f"📋 Columns after normalization: {list(df.columns)}\n")
        
        df = df.where(pd.notnull(df), None)
        
    except Exception as e:
        error_msg = f'Failed to read file: {str(e)}'
        print(f"❌ ERROR: {error_msg}")
        result['success'] = False
        result['errors'].append(error_msg)
        _log_upload(filename, 'file', 0, 'failed', error_msg, result) 
        return result

    # Check required columns
    required = ['home_team', 'away_team']
    missing = [col for col in required if col not in df.columns]
    if missing:
        error_msg = f'Missing required columns: {", ".join(missing)}. This file appears to be PLAYER data, not MATCH data.'
        print(f"❌ ERROR: {error_msg}")
        result['success'] = False
        result['errors'].append(error_msg)
        _log_upload(filename, result['source_type'], 0, 'failed', error_msg, result)
        return result

    # Process each row
    for idx, row in df.iterrows():
        try:
            print(f"\n--- ROW {idx + 1} ---")
            
            home_team = get_or_create_team(row.get('home_team'))
            away_team = get_or_create_team(row.get('away_team'))

            if not home_team or not away_team:
                result['rows_failed'] += 1
                error = f'Row {idx + 1}: Missing team name'
                print(f"❌ {error}")
                result['errors'].append(error)
                continue

            print(f"🏟️  Teams: {home_team.name} vs {away_team.name}")

            match_date = parse_date(row.get('date', None))
            print(f"📅 Date: {match_date}")

            # Check for duplicate
            existing = Match.query.filter_by(
                home_team_id=home_team.id,
                away_team_id=away_team.id,
                date=match_date
            ).first()

            if existing:
                print(f"🔄 Match already exists - updating")
                match = existing
            else:
                print(f"🆕 Creating new match")
                
                # PENALTY DATA PROCESSING
                has_penalties = False
                penalty_details = None
                home_penalties_scored = 0
                away_penalties_scored = 0
                home_penalties_attempted = 0
                away_penalties_attempted = 0
                
                penalty_flag = row.get('has_penalties', False)
                if penalty_flag and str(penalty_flag).lower() in ['true', 'yes', '1', 'y']:
                    has_penalties = True
                    print(f"⚽ Penalty flag detected: True")
                
                if has_penalties or row.get('home_penalty_takers') is not None:
                    home_pens = parse_penalty_takers(row.get('home_penalty_takers'))
                    away_pens = parse_penalty_takers(row.get('away_penalty_takers'))
                    
                    if home_pens or away_pens:
                        penalty_details = build_penalty_details(home_pens, away_pens)
                        has_penalties = bool(penalty_details)
                        
                        if penalty_details:
                            h_scored, h_attempted, a_scored, a_attempted = calculate_penalty_stats(penalty_details)
                            home_penalties_scored = h_scored
                            home_penalties_attempted = h_attempted
                            away_penalties_scored = a_scored
                            away_penalties_attempted = a_attempted
                
                elif row.get('home_penalties_scored') is not None or row.get('away_penalties_scored') is not None:
                    has_penalties = True
                    home_penalties_scored = safe_int(row.get('home_penalties_scored', 0))
                    away_penalties_scored = safe_int(row.get('away_penalties_scored', 0))
                    home_penalties_attempted = safe_int(row.get('home_penalties_attempted', home_penalties_scored + 1))
                    away_penalties_attempted = safe_int(row.get('away_penalties_attempted', away_penalties_scored + 1))
                
                home_et = safe_int(row.get('home_goals_et', 0))
                away_et = safe_int(row.get('away_goals_et', 0))
                
                if has_penalties:
                    match_status = 'penalties'
                elif home_et > 0 or away_et > 0:
                    match_status = 'extra_time'
                else:
                    match_status = 'completed'
                
                match = Match(
                    home_team_id=home_team.id,
                    away_team_id=away_team.id,
                    date=match_date,
                    home_goals=safe_int(row.get('home_goals', 0)),
                    away_goals=safe_int(row.get('away_goals', 0)),
                    home_goals_et=home_et,
                    away_goals_et=away_et,
                    league=str(row.get('league', '')) if row.get('league') is not None else None,
                    season=str(row.get('season', '')) if row.get('season') is not None else None,
                    venue=str(row.get('venue', '')) if row.get('venue') is not None else None,
                    referee=str(row.get('referee', '')) if row.get('referee') is not None else None,
                    home_goalscorers=str(row.get('home_goalscorers', '')) if row.get('home_goalscorers') is not None else None,
                    away_goalscorers=str(row.get('away_goalscorers', '')) if row.get('away_goalscorers') is not None else None,
                    has_penalties=has_penalties,
                    penalty_details=penalty_details,
                    home_penalties_scored=home_penalties_scored,
                    away_penalties_scored=away_penalties_scored,
                    home_penalties_attempted=home_penalties_attempted,
                    away_penalties_attempted=away_penalties_attempted,
                    status=match_status
                )
                db.session.add(match)
                db.session.flush()
                result['matches_created'] += 1
                
                if has_penalties:
                    result['penalty_matches'] += 1

            try:
                _create_match_stats(match.id, home_team.id, row, 'home')
                _create_match_stats(match.id, away_team.id, row, 'away')
                print(f"✅ Match stats created")
            except Exception as e:
                print(f"⚠️  Warning creating stats: {str(e)}")

            result['rows_processed'] += 1
            print(f"✅ Row {idx + 1} processed successfully")

        except Exception as e:
            result['rows_failed'] += 1
            error = f'Row {idx + 1}: {str(e)}'
            print(f"❌ ERROR: {error}")
            result['errors'].append(error)
            continue

    try:
        print(f"\n💾 Committing {result['rows_processed']} rows to database...")
        db.session.commit()
        print(f"✅ Database commit successful")
    except Exception as e:
        db.session.rollback()
        result['success'] = False
        error = f'Database commit failed: {str(e)}'
        print(f"❌ {error}")
        result['errors'].append(error)
        _log_upload(filename, result['source_type'], result['rows_processed'], 'failed', error, result)
        return result

    status = 'success' if result['success'] and result['rows_processed'] > 0 else 'partial'
    error_summary = '; '.join(result['errors'][:5]) if result['errors'] else None
    _log_upload(filename, result['source_type'], result['rows_processed'], status, error_summary, result)

    print(f"\n{'='*80}")
    print(f"📊 MATCH UPLOAD SUMMARY")
    print(f"{'='*80}")
    print(f"✅ Rows Processed: {result['rows_processed']}")
    print(f"❌ Rows Failed: {result['rows_failed']}")
    print(f"🆕 Matches Created: {result['matches_created']}")
    print(f"⚽ Penalty Matches: {result['penalty_matches']}")
    print(f"Status: {status.upper()}")
    if result['errors']:
        print(f"\n⚠️  Errors ({len(result['errors'])} total):")
        for error in result['errors'][:5]:
            print(f"   - {error}")
    print(f"{'='*80}\n")

    return result


# ===================================================================
# PROCESS PLAYER DATA
# ===================================================================

def process_players_file(filepath, filename):
    """Process a player stats CSV/Excel file and insert into database."""
    result = {
        'success': True,
        'rows_processed': 0,
        'rows_failed': 0,
        'errors': [],
        'players_created': 0,
        'source_type': 'csv',
        'data_type': 'players'
    }

    print(f"\n{'='*80}")
    print(f"🔥 STARTING PLAYER DATA PROCESSING: {filename}")
    print(f"{'='*80}\n")

    try:
        file_ext = filename.lower()
        if file_ext.endswith('.csv'):
            df = pd.read_csv(filepath, sep=None, engine='python')
            result['source_type'] = 'csv'
        elif file_ext.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(filepath)
            result['source_type'] = 'excel'
        else:
            raise Exception("Unsupported file format. Please upload .csv or .xlsx")

        print(f"✅ File read successfully - {len(df)} rows found")
        print(f"📋 Original columns: {list(df.columns)}\n")

        df = normalize_columns(df, PLAYER_COLUMN_MAP)
        
        print(f"📋 Normalized columns: {list(df.columns)}\n")
        
        df = df.where(pd.notnull(df), None)
        
    except Exception as e:
        error_msg = f'Failed to read file: {str(e)}'
        print(f"❌ ERROR: {error_msg}")
        result['success'] = False
        result['errors'].append(error_msg)
        _log_upload(filename, result['source_type'], 0, 'failed', error_msg, result)
        return result

    # Validasi Kolom Wajib - STRICT CHECK
    if 'name' not in df.columns:
        error_msg = 'Missing required column: name (player name) - PLAYER file must have "name" column'
        print(f"❌ ERROR: {error_msg}")
        result['success'] = False
        result['errors'].append(error_msg)
        _log_upload(filename, result['source_type'], 0, 'failed', error_msg, result)
        return result
    
    if 'team' not in df.columns:
        error_msg = 'Missing required column: team - PLAYER file must have "team" column'
        print(f"❌ ERROR: {error_msg}")
        result['success'] = False
        result['errors'].append(error_msg)
        _log_upload(filename, result['source_type'], 0, 'failed', error_msg, result)
        return result

    print(f"✅ Column validation passed (name, team found)\n")

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
                error = f'Row {idx + 1}: Missing player name'
                print(f"❌ {error}")
                result['errors'].append(error)
                continue

            print(f"--- ROW {idx + 1} ---")
            print(f"👤 Player: {player.name} | Team: {player.team.name if player.team else 'No Team'} | Pos: {player.position or 'N/A'}")

            result['players_created'] += 1

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
            print(f"✅ Row {idx + 1} processed\n")

        except Exception as e:
            result['rows_failed'] += 1
            error = f'Row {idx + 1}: {str(e)}'
            print(f"❌ ERROR: {error}\n")
            result['errors'].append(error)
            continue

    try:
        print(f"\n💾 Committing {result['rows_processed']} player rows to database...")
        db.session.commit()
        print(f"✅ Database commit successful")
    except Exception as e:
        db.session.rollback()
        result['success'] = False
        error = f'Database commit failed: {str(e)}'
        print(f"❌ {error}")
        result['errors'].append(error)
        _log_upload(filename, result['source_type'], result['rows_processed'], 'failed', error, result)
        return result

    status = 'success' if result['success'] and result['rows_processed'] > 0 else 'partial'
    error_summary = '; '.join(result['errors'][:5]) if result['errors'] else None
    
    _log_upload(filename, result['source_type'], result['rows_processed'], status, error_summary, result)

    print(f"\n{'='*80}")
    print(f"📊 PLAYER UPLOAD SUMMARY")
    print(f"{'='*80}")
    print(f"✅ Players Processed: {result['rows_processed']}")
    print(f"❌ Rows Failed: {result['rows_failed']}")
    print(f"Status: {status.upper()}")
    if result['errors']:
        print(f"\n⚠️  Errors ({len(result['errors'])} total):")
        for error in result['errors'][:5]:
            print(f"   - {error}")
    print(f"{'='*80}\n")

    return result


# ===================================================================
# MAIN ROUTER
# ===================================================================

def load_csv(filepath):
    """
    🔥 MAIN ENTRY POINT - Smart router untuk MATCH vs PLAYER
    """
    import os
    filename = os.path.basename(filepath)
    print(f"\n🚀 LOAD_CSV ROUTER: {filename}\n")
    
    try:
        # Read kolom pertama untuk deteksi
        file_ext = filename.lower()
        if file_ext.endswith('.csv'):
            df_detect = pd.read_csv(filepath, sep=None, engine='python', nrows=0)
        elif file_ext.endswith(('.xlsx', '.xls')):
            df_detect = pd.read_excel(filepath, nrows=0)
        else:
            raise Exception("Unsupported file format. Use .csv or .xlsx")
        
        # DETECTION
        detected_type = detect_file_type(df_detect.columns)
        
        if detected_type == 'match':
            print("➡️  ROUTING: MATCH file detected → process_uploaded_file()")
            result = process_uploaded_file(filepath, filename)
        elif detected_type == 'player':
            print("➡️  ROUTING: PLAYER file detected → process_players_file()")
            result = process_players_file(filepath, filename)
        else:
            raise Exception(
                f"❌ Could not auto-detect file type!\n"
                f"Required columns:\n"
                f"  - MATCH: home_team, away_team, home_goals, away_goals\n"
                f"  - PLAYER: name, team\n"
                f"Found columns: {list(df_detect.columns)}"
            )
        
        # Error handling
        if not result.get('success', False) and result.get('rows_processed', 0) == 0:
            error_msg = result['errors'][0] if result.get('errors') else 'Unknown error'
            raise Exception(f"❌ Upload failed: {error_msg}")
        
        return result
        
    except Exception as e:
        print(f"❌ ROUTER ERROR: {str(e)}")
        raise


def get_or_create_player(name, team_name=None, position=None, nationality=None, shirt_number=None):
    """Get existing player or create new one."""
    if not name:
        return None
        
    name = str(name).strip()

    query = Player.query.filter(Player.name.ilike(name))
    
    team = None
    if team_name:
        team = get_or_create_team(team_name)
        if team:
            query = query.filter_by(team_id=team.id)

    player = query.first()
    
    if not player:
        player = Player(
            name=name,
            team_id=team.id if team else None,
            position=str(position).strip() if position else None,
            nationality=str(nationality).strip() if nationality else None,
            shirt_number=safe_int(shirt_number) if shirt_number else None,
        )
        db.session.add(player)
        db.session.flush()
        
    return player


def _create_match_stats(match_id, team_id, row, side):
    """Create or update MatchStats for a team."""
    try:
        existing = MatchStats.query.filter_by(match_id=match_id, team_id=team_id).first()
        if existing:
            stats = existing
        else:
            stats = MatchStats(match_id=match_id, team_id=team_id)

        prefix = f'{side}_'
        
        stats.possession = safe_float(row.get(f'{prefix}possession', 0))
        stats.total_shots = safe_int(row.get(f'{prefix}total_shots', 0))
        stats.shots_on_target = safe_int(row.get(f'{prefix}shots_on_target', 0))
        stats.shots_off_target = safe_int(row.get(f'{prefix}shots_off_target', 0))
        stats.blocked_shots = safe_int(row.get(f'{prefix}blocked_shots', 0))
        stats.shots_inside_box = safe_int(row.get(f'{prefix}shots_inside_box', 0))
        stats.shots_outside_box = safe_int(row.get(f'{prefix}shots_outside_box', 0))
        stats.big_chances_scored = safe_int(row.get(f'{prefix}big_chances_scored', 0))
        stats.big_chances_missed = safe_int(row.get(f'{prefix}big_chances_missed', 0))
        stats.hit_woodwork = safe_int(row.get(f'{prefix}hit_woodwork', 0))
        
        stats.total_passes = safe_int(row.get(f'{prefix}total_passes', 0))
        stats.pass_accuracy = safe_float(row.get(f'{prefix}pass_accuracy', 0))
        stats.key_passes = safe_int(row.get(f'{prefix}key_passes', 0))
        stats.passes_into_final_third = safe_int(row.get(f'{prefix}passes_into_final_third', 0))
        stats.passes_final_third_success = safe_int(row.get(f'{prefix}passes_final_third_success', 0))
        stats.passes_into_penalty_area = safe_int(row.get(f'{prefix}passes_into_penalty_area', 0))
        stats.through_balls = safe_int(row.get(f'{prefix}through_balls', 0))
        stats.crosses = safe_int(row.get(f'{prefix}crosses', 0))
        stats.crosses_success = safe_int(row.get(f'{prefix}crosses_success', 0))
        stats.long_balls = safe_int(row.get(f'{prefix}long_balls', 0))
        stats.long_balls_success = safe_int(row.get(f'{prefix}long_balls_success', 0))
        stats.throw_ins = safe_int(row.get(f'{prefix}throw_ins', 0))
        stats.final_third_entries = safe_int(row.get(f'{prefix}final_third_entries', 0))
        
        stats.tackles_success = safe_int(row.get(f'{prefix}tackles_success', 0))
        stats.tackles_total = safe_int(row.get(f'{prefix}tackles_total', 0))
        stats.duels_won = safe_int(row.get(f'{prefix}duels_won', 0))
        stats.duels_total = safe_int(row.get(f'{prefix}duels_total', 0))
        stats.clearances = safe_int(row.get(f'{prefix}clearances', 0))
        stats.interceptions = safe_int(row.get(f'{prefix}interceptions', 0))
        stats.blocks = safe_int(row.get(f'{prefix}blocks', 0))
        stats.goalkeeper_saves = safe_int(row.get(f'{prefix}goalkeeper_saves', 0))
        
        stats.corners = safe_int(row.get(f'{prefix}corners', 0))
        stats.fouls = safe_int(row.get(f'{prefix}fouls', 0))
        stats.yellow_cards = safe_int(row.get(f'{prefix}yellow_cards', 0))
        stats.red_cards = safe_int(row.get(f'{prefix}red_cards', 0))
        stats.offsides = safe_int(row.get(f'{prefix}offsides', 0))
        
        stats.dribbles_attempted = safe_int(row.get(f'{prefix}dribbles_attempted', 0))
        stats.dribbles_succeeded = safe_int(row.get(f'{prefix}dribbles_succeeded', 0))
        stats.xg = safe_float(row.get(f'{prefix}xg', 0))

        if not existing:
            db.session.add(stats)
            
    except Exception as e:
        print(f"⚠️  Error creating match stats: {str(e)}")
        raise