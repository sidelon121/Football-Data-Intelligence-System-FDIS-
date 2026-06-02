"""
FDIS Database Models
Football Data Intelligence System
"""
from datetime import datetime, timezone
from typing import final
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class User(db.Model, UserMixin):
    """User model for authentication."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)  # Nullable for OAuth users
    name = db.Column(db.String(100), nullable=True)
    google_id = db.Column(db.String(100), unique=True, nullable=True)
    github_id = db.Column(db.String(100), unique=True, nullable=True)
    avatar_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email}>'

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'avatar_url': self.avatar_url
        }


class Team(db.Model):
    """Football team model."""
    __tablename__ = 'teams'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    short_name = db.Column(db.String(10), nullable=True)
    logo_url = db.Column(db.String(255), nullable=True)
    league = db.Column(db.String(100), nullable=True)
    country = db.Column(db.String(100), nullable=True)
    founded = db.Column(db.Integer, nullable=True)
    venue = db.Column(db.String(150), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    players = db.relationship('Player', backref='team', lazy='dynamic')
    home_matches = db.relationship('Match', foreign_keys='Match.home_team_id', backref='home_team', lazy='dynamic')
    away_matches = db.relationship('Match', foreign_keys='Match.away_team_id', backref='away_team', lazy='dynamic')
    match_stats = db.relationship('MatchStats', backref='team', lazy='dynamic')

    def __repr__(self):
        return f'<Team {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'short_name': self.short_name,
            'logo_url': self.logo_url,
            'league': self.league,
            'country': self.country,
            'founded': self.founded,
            'venue': self.venue,
        }


class Player(db.Model):
    """Football player model."""
    __tablename__ = 'players'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(30), nullable=True)
    nationality = db.Column(db.String(80), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    shirt_number = db.Column(db.Integer, nullable=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=True)
    height = db.Column(db.String(10), nullable=True)
    weight = db.Column(db.String(10), nullable=True)
    photo_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    player_stats = db.relationship('PlayerStats', backref='player', lazy='dynamic')

    def __repr__(self):
        return f'<Player {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'position': self.position,
            'nationality': self.nationality,
            'shirt_number': self.shirt_number,
            'team_id': self.team_id,
            'team_name': self.team.name if self.team else None,
            'photo_url': self.photo_url,
        }


class Match(db.Model):
    """Football match model dengan penalty shootout support."""
    __tablename__ = 'matches'

    id = db.Column(db.Integer, primary_key=True)
    home_team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    away_team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    
    # ❌ HASIL REGULAR TIME
    home_goals = db.Column(db.Integer, default=0)
    away_goals = db.Column(db.Integer, default=0)
    home_goalscorers = db.Column(db.String(255), nullable=True)
    away_goalscorers = db.Column(db.String(255), nullable=True)
    
    # ❌ EXTRA TIME (JIKA ADA)
    home_goals_et = db.Column(db.Integer, default=0)
    away_goals_et = db.Column(db.Integer, default=0)
    
    # ❌ PENALTY SHOOTOUT (JIKA ADA)
    has_penalties = db.Column(db.Boolean, default=False)
    home_penalties_scored = db.Column(db.Integer, default=0)  # Gol penalti
    away_penalties_scored = db.Column(db.Integer, default=0)
    home_penalties_attempted = db.Column(db.Integer, default=0)  # Total tendangan
    away_penalties_attempted = db.Column(db.Integer, default=0)
    penalty_details = db.Column(db.JSON, nullable=True)  # Detail setiap penalti: [{"player": "name", "scored": true}, ...]
    
    # METADATA
    date = db.Column(db.Date, nullable=False)
    league = db.Column(db.String(100), nullable=True)
    season = db.Column(db.String(20), nullable=True)
    venue = db.Column(db.String(150), nullable=True)
    referee = db.Column(db.String(100), nullable=True)
    
    # STATUS: completed, scheduled, live, extra_time, penalties
    status = db.Column(db.String(20), default='completed')
    api_fixture_id = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    match_stats = db.relationship('MatchStats', backref='match', lazy='dynamic', cascade='all, delete-orphan')
    player_stats = db.relationship('PlayerStats', backref='match', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        home_name = self.home_team.name if self.home_team else "?"
        away_name = self.away_team.name if self.away_team else "?"
        return f'<Match {home_name} vs {away_name} ({self.date})>'

    @property
    def match_result_text(self):
        """Return hasil match dengan format: 'home_goals-away_goals' + penalty info jika ada."""
        result = f"{self.home_goals}-{self.away_goals}"
        
        if self.home_goals_et > 0 or self.away_goals_et > 0:
            result += f" ({self.home_goals + self.home_goals_et}-{self.away_goals + self.away_goals_et} AET)"
        
        if self.has_penalties:
            result += f" ({self.home_penalties_scored}-{self.away_penalties_scored} pen)"
        
        return result

    @property
    def total_home_goals(self):
        """Total gol home team (regular + extra time)."""
        return self.home_goals + self.home_goals_et

    @property
    def total_away_goals(self):
        """Total gol away team (regular + extra time)."""
        return self.away_goals + self.away_goals_et

    def to_dict(self):
        return {
            'id': self.id,
            'home_team': self.home_team.to_dict() if self.home_team else None,
            'away_team': self.away_team.to_dict() if self.away_team else None,
            
            # Regular time
            'home_goals': self.home_goals,
            'away_goals': self.away_goals,
            'home_goalscorers': self.home_goalscorers,
            'away_goalscorers': self.away_goalscorers,
            
            # Extra time
            'home_goals_et': self.home_goals_et,
            'away_goals_et': self.away_goals_et,
            'total_home_goals': self.total_home_goals,
            'total_away_goals': self.total_away_goals,
            
            # Penalties
            'has_penalties': self.has_penalties,
            'home_penalties_scored': self.home_penalties_scored,
            'away_penalties_scored': self.away_penalties_scored,
            'home_penalties_attempted': self.home_penalties_attempted,
            'away_penalties_attempted': self.away_penalties_attempted,
            'penalty_details': self.penalty_details,
            
            'date': self.date.isoformat() if self.date else None,
            'league': self.league,
            'season': self.season,
            'venue': self.venue,
            'referee': self.referee,
            'status': self.status,
            'match_result_text': self.match_result_text,
        }


# ==========================================
# MATCH STATS MODEL (TIDAK PERLU DIUBAH)
# ==========================================
class MatchStats(db.Model):
    """Match statistics untuk team dalam specific match."""
    __tablename__ = 'match_stats'

    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey('matches.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    
    # Core stats
    goals = db.Column(db.Integer, default=0)
    possession = db.Column(db.Float, default=0.0)
    total_shots = db.Column(db.Integer, default=0)
    shots_on_target = db.Column(db.Integer, default=0)
    shots_off_target = db.Column(db.Integer, default=0)
    blocked_shots = db.Column(db.Integer, default=0)
    shots_inside_box = db.Column(db.Integer, default=0)
    shots_outside_box = db.Column(db.Integer, default=0)
    big_chances_scored = db.Column(db.Integer, default=0)
    big_chances_missed = db.Column(db.Integer, default=0)
    dribbles_attempted = db.Column(db.Integer, default=0)
    dribbles_succeeded = db.Column(db.Integer, default=0)

    # Passing
    total_passes = db.Column(db.Integer, default=0)
    pass_accuracy = db.Column(db.Float, default=0.0)
    key_passes = db.Column(db.Integer, default=0)
    passes_into_final_third = db.Column(db.Integer, default=0)
    passes_final_third_success = db.Column(db.Integer, default=0)
    passes_into_penalty_area = db.Column(db.Integer, default=0)
    through_balls = db.Column(db.Integer, default=0)
    throw_ins = db.Column(db.Integer, default=0)
    final_third_entries = db.Column(db.Integer, default=0)
    long_balls = db.Column(db.Integer, default=0)
    long_balls_success = db.Column(db.Integer, default=0)
    crosses = db.Column(db.Integer, default=0)
    crosses_success = db.Column(db.Integer, default=0)
    hit_woodwork = db.Column(db.Integer, default=0)

    # Defense
    tackles_success = db.Column(db.Integer, default=0)
    tackles_total = db.Column(db.Integer, default=0)
    duels_won = db.Column(db.Integer, default=0)
    duels_total = db.Column(db.Integer, default=0)
    clearances = db.Column(db.Integer, default=0)
    interceptions = db.Column(db.Integer, default=0)
    blocks = db.Column(db.Integer, default=0)

    # Set pieces & discipline
    corners = db.Column(db.Integer, default=0)
    fouls = db.Column(db.Integer, default=0)
    yellow_cards = db.Column(db.Integer, default=0)
    red_cards = db.Column(db.Integer, default=0)
    offsides = db.Column(db.Integer, default=0)

    # Advanced
    xg = db.Column(db.Float, default=0.0)
    goalkeeper_saves = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.UniqueConstraint('match_id', 'team_id', name='uq_match_team_stats'),
    )

    def __repr__(self):
        return f'<MatchStats match={self.match_id} team={self.team_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'match_id': self.match_id,
            'team_id': self.team_id,
            'team_name': self.team.name if self.team else None,
            'goals': self.goals,
            'possession': self.possession,
            'total_shots': self.total_shots,
            'shots_on_target': self.shots_on_target,
            'shots_off_target': self.shots_off_target,
            'blocked_shots': self.blocked_shots,
            'shots_inside_box': self.shots_inside_box,
            'shots_outside_box': self.shots_outside_box,
            'big_chances_scored': self.big_chances_scored,
            'big_chances_missed': self.big_chances_missed,
            'dribbles_attempted': self.dribbles_attempted,
            'dribbles_succeeded': self.dribbles_succeeded,
            'total_passes': self.total_passes,
            'pass_accuracy': self.pass_accuracy,
            'passes_into_final_third': self.passes_into_final_third,
            'passes_final_third_success': self.passes_final_third_success,
            'passes_into_penalty_area': self.passes_into_penalty_area,
            'through_balls': self.through_balls,
            'throw_ins': self.throw_ins,
            'final_third_entries': self.final_third_entries,
            'long_balls': self.long_balls,
            'long_balls_success': self.long_balls_success,
            'crosses': self.crosses,
            'crosses_success': self.crosses_success,
            'hit_woodwork': self.hit_woodwork,
            'key_passes': self.key_passes,
            'tackles_success': self.tackles_success,
            'tackles_total': self.tackles_total,
            'duels_won': self.duels_won,
            'duels_total': self.duels_total,
            'clearances': self.clearances,
            'interceptions': self.interceptions,
            'blocks': self.blocks,
            'corners': self.corners,
            'fouls': self.fouls,
            'yellow_cards': self.yellow_cards,
            'red_cards': self.red_cards,
            'offsides': self.offsides,
            'xg': self.xg,
            'goalkeeper_saves': self.goalkeeper_saves,
        }

class PlayerStats(db.Model):
    """Player statistics for a specific match."""
    __tablename__ = 'player_stats'

    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey('matches.id'), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)

    # Performance
    minutes_played = db.Column(db.Integer, default=0)
    rating = db.Column(db.Float, nullable=True)  # 0-10 scale
    goals = db.Column(db.Integer, default=0)
    assists = db.Column(db.Integer, default=0)
    shots = db.Column(db.Integer, default=0)
    shots_on_target = db.Column(db.Integer, default=0)

    # Passing
    passes = db.Column(db.Integer, default=0)
    pass_accuracy = db.Column(db.Float, default=0.0)
    key_passes = db.Column(db.Integer, default=0)
    crosses = db.Column(db.Integer, default=0)

    # Defense
    tackles = db.Column(db.Integer, default=0)
    interceptions = db.Column(db.Integer, default=0)
    blocks = db.Column(db.Integer, default=0)
    clearances = db.Column(db.Integer, default=0)

    # Discipline
    fouls_committed = db.Column(db.Integer, default=0)
    fouls_drawn = db.Column(db.Integer, default=0)
    yellow_cards = db.Column(db.Integer, default=0)
    red_cards = db.Column(db.Integer, default=0)

    # Dribbling
    dribbles_attempted = db.Column(db.Integer, default=0)
    dribbles_succeeded = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.UniqueConstraint('match_id', 'player_id', name='uq_match_player_stats'),
    )

    def __repr__(self):
        return f'<PlayerStats match={self.match_id} player={self.player_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'match_id': self.match_id,
            'player_id': self.player_id,
            'player_name': self.player.name if self.player else None,
            'minutes_played': self.minutes_played,
            'rating': self.rating,
            'goals': self.goals,
            'assists': self.assists,
            'shots': self.shots,
            'shots_on_target': self.shots_on_target,
            'passes': self.passes,
            'pass_accuracy': self.pass_accuracy,
            'key_passes': self.key_passes,
            'tackles': self.tackles,
            'interceptions': self.interceptions,
            'yellow_cards': self.yellow_cards,
            'red_cards': self.red_cards,
            'dribbles_attempted': self.dribbles_attempted,
            'dribbles_succeeded': self.dribbles_succeeded,
        }


class UploadHistory(db.Model):
    """Track data upload history."""
    __tablename__ = 'upload_history'

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    source_type = db.Column(db.String(30), nullable=False)  # csv, excel, api, manual, database
    upload_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    row_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='success')  # success, failed, partial
    error_message = db.Column(db.Text, nullable=True)
    details = db.Column(db.Text, nullable=True)  # JSON string with extra info

    def __repr__(self):
        return f'<Upload {self.filename} ({self.status})>'

    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'source_type': self.source_type,
            'upload_date': self.upload_date.isoformat() if self.upload_date else None,
            'row_count': self.row_count,
            'status': self.status,
            'error_message': self.error_message,
        }

class Goal(db.Model):
    __tablename__ = 'goals'

    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey('matches.id'), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)

    minute = db.Column(db.Integer)  # opsional (menit gol)
    is_own_goal = db.Column(db.Boolean, default=False)
    is_penalty = db.Column(db.Boolean, default=False)

    player = db.relationship('Player')
    team = db.relationship('Team')
    match = db.relationship('Match')

    def __repr__(self):
        return f'<Goal {self.player.name} in {self.match.home_team.name} vs {self.match.away_team.name}>'