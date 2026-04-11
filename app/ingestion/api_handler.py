"""
FDIS API-Football Integration Handler
Fetches football data from API-Football (api-sports.io).
"""
import time
import requests
from datetime import datetime
from flask import current_app
from app import db
from app.models import Team, Match, MatchStats, UploadHistory
from app.ingestion.csv_handler import get_or_create_team, safe_int, safe_float


class APIFootballClient:
    """Client for API-Football v3."""

    def __init__(self, api_key=None):
        self.api_key = api_key or current_app.config.get('API_FOOTBALL_KEY', '')
        self.base_url = current_app.config.get('API_FOOTBALL_BASE_URL',
                                                'https://v3.football.api-sports.io')
        self.headers = {
            'x-apisports-key': self.api_key,
        }
        self._request_count = 0
        self._last_request_time = 0

    def _rate_limit(self):
        """Enforce rate limiting: 10 requests per minute."""
        now = time.time()
        if now - self._last_request_time < 6:  # ~10 per minute
            time.sleep(6 - (now - self._last_request_time))
        self._last_request_time = time.time()
        self._request_count += 1

    def _make_request(self, endpoint, params=None):
        """Make an API request with rate limiting."""
        if not self.api_key:
            return {'error': 'API key not configured. Set API_FOOTBALL_KEY environment variable.'}

        self._rate_limit()

        try:
            url = f'{self.base_url}/{endpoint}'
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if data.get('errors'):
                return {'error': str(data['errors'])}

            return data
        except requests.exceptions.RequestException as e:
            return {'error': f'API request failed: {str(e)}'}

    def get_leagues(self, country=None, season=None):
        """Get available leagues."""
        params = {}
        if country:
            params['country'] = country
        if season:
            params['season'] = season
        return self._make_request('leagues', params)

    def get_teams(self, league_id, season):
        """Get teams in a league for a specific season."""
        params = {'league': league_id, 'season': season}
        return self._make_request('teams', params)

    def get_fixtures(self, league_id=None, season=None, team_id=None,
                     date_from=None, date_to=None, last=None):
        """Get fixtures (matches)."""
        params = {}
        if league_id:
            params['league'] = league_id
        if season:
            params['season'] = season
        if team_id:
            params['team'] = team_id
        if date_from:
            params['from'] = date_from
        if date_to:
            params['to'] = date_to
        if last:
            params['last'] = last
        return self._make_request('fixtures', params)

    def get_fixture_statistics(self, fixture_id):
        """Get statistics for a specific fixture."""
        params = {'fixture': fixture_id}
        return self._make_request('fixtures/statistics', params)

    def get_fixture_players(self, fixture_id):
        """Get player statistics for a specific fixture."""
        params = {'fixture': fixture_id}
        return self._make_request('fixtures/players', params)

    def fetch_and_store_fixtures(self, league_id, season, last=None):
        """
        Fetch fixtures from API and store them in the database.
        
        Returns:
            Dictionary with import results.
        """
        result = {
            'success': True,
            'matches_imported': 0,
            'errors': [],
        }

        fixtures_data = self.get_fixtures(
            league_id=league_id, season=season, last=last
        )
        if 'error' in fixtures_data:
            result['success'] = False
            result['errors'].append(fixtures_data['error'])
            return result

        responses = fixtures_data.get('response', [])
        for fixture in responses:
            try:
                fixture_info = fixture.get('fixture', {})
                teams_info = fixture.get('teams', {})
                goals_info = fixture.get('goals', {})
                league_info = fixture.get('league', {})

                # Get or create teams
                home_name = teams_info.get('home', {}).get('name', 'Unknown')
                away_name = teams_info.get('away', {}).get('name', 'Unknown')
                home_team = get_or_create_team(home_name)
                away_team = get_or_create_team(away_name)

                if not home_team or not away_team:
                    continue

                # Parse date
                date_str = fixture_info.get('date', '')[:10]
                try:
                    match_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    match_date = datetime.now().date()

                fixture_id = fixture_info.get('id')

                # Check for existing match
                existing = Match.query.filter_by(api_fixture_id=fixture_id).first()
                if existing:
                    continue

                match = Match(
                    home_team_id=home_team.id,
                    away_team_id=away_team.id,
                    date=match_date,
                    home_goals=safe_int(goals_info.get('home', 0)),
                    away_goals=safe_int(goals_info.get('away', 0)),
                    league=league_info.get('name', ''),
                    season=str(league_info.get('season', '')),
                    venue=fixture_info.get('venue', {}).get('name', ''),
                    referee=fixture_info.get('referee', ''),
                    api_fixture_id=fixture_id,
                )
                db.session.add(match)
                db.session.flush()

                # Fetch and store match statistics
                stats_data = self.get_fixture_statistics(fixture_id)
                if 'error' not in stats_data:
                    self._store_match_stats(match.id, stats_data.get('response', []))

                result['matches_imported'] += 1

            except Exception as e:
                result['errors'].append(f'Fixture error: {str(e)}')
                continue

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            result['success'] = False
            result['errors'].append(f'Database commit failed: {str(e)}')

        # Log the upload
        _log_api_upload(league_id, season, result)

        return result

    def _store_match_stats(self, match_id, stats_response):
        """Parse and store match statistics from API response."""
        for team_stats in stats_response:
            team_info = team_stats.get('team', {})
            statistics = team_stats.get('statistics', [])

            team = get_or_create_team(team_info.get('name', 'Unknown'))
            if not team:
                continue

            # Convert statistics list to dict
            stats_dict = {}
            for stat in statistics:
                stats_dict[stat.get('type', '')] = stat.get('value')

            ms = MatchStats(
                match_id=match_id,
                team_id=team.id,
                goals=0,  # Set from match goals
                possession=safe_float(str(stats_dict.get('Ball Possession', '0')).replace('%', '')),
                total_shots=safe_int(stats_dict.get('Total Shots', 0)),
                shots_on_target=safe_int(stats_dict.get('Shots on Goal', 0)),
                shots_off_target=safe_int(stats_dict.get('Shots off Goal', 0)),
                blocked_shots=safe_int(stats_dict.get('Blocked Shots', 0)),
                total_passes=safe_int(stats_dict.get('Total passes', 0)),
                pass_accuracy=safe_float(str(stats_dict.get('Passes %', '0')).replace('%', '')),
                corners=safe_int(stats_dict.get('Corner Kicks', 0)),
                fouls=safe_int(stats_dict.get('Fouls', 0)),
                yellow_cards=safe_int(stats_dict.get('Yellow Cards', 0)),
                red_cards=safe_int(stats_dict.get('Red Cards', 0)),
                offsides=safe_int(stats_dict.get('Offsides', 0)),
                goalkeeper_saves=safe_int(stats_dict.get('Goalkeeper Saves', 0)),
                xg=safe_float(stats_dict.get('expected_goals', 0)),
            )
            db.session.add(ms)


def _log_api_upload(league_id, season, result):
    """Log API import to upload history."""
    upload = UploadHistory(
        filename=f'API-Football: League {league_id}, Season {season}',
        source_type='api',
        row_count=result['matches_imported'],
        status='success' if result['success'] else 'partial',
        error_message='; '.join(result['errors'][:5]) if result['errors'] else None,
    )
    db.session.add(upload)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
