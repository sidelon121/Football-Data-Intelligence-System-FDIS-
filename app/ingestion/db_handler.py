"""
FDIS External Database Handler
Connects to external databases and imports football data.
"""
from sqlalchemy import create_engine, text
from app import db
from app.models import UploadHistory
from app.ingestion.csv_handler import get_or_create_team, safe_int, safe_float, parse_date
from app.models import Match, MatchStats
import pandas as pd


class ExternalDBConnector:
    """Connect to external databases and pull match/player data."""

    SUPPORTED_ENGINES = ['postgresql', 'mysql', 'sqlite', 'mssql']

    def __init__(self, connection_string):
        """
        Initialize with a SQLAlchemy connection string.
        
        Examples:
            postgresql://user:password@host:port/dbname
            mysql://user:password@host:port/dbname
            sqlite:///path/to/database.db
        """
        self.connection_string = connection_string
        self.engine = None

    def connect(self):
        """Establish connection to external database."""
        try:
            self.engine = create_engine(self.connection_string)
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text('SELECT 1'))
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': f'Connection failed: {str(e)}'}

    def list_tables(self):
        """List available tables in the external database."""
        if not self.engine:
            return {'success': False, 'error': 'Not connected'}
        try:
            from sqlalchemy import inspect
            inspector = inspect(self.engine)
            tables = inspector.get_table_names()
            return {'success': True, 'tables': tables}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def preview_table(self, table_name, limit=10):
        """Preview rows from a table."""
        if not self.engine:
            return {'success': False, 'error': 'Not connected'}
        try:
            df = pd.read_sql(f'SELECT * FROM {table_name} LIMIT {limit}', self.engine)
            return {
                'success': True,
                'columns': list(df.columns),
                'rows': df.to_dict('records'),
                'total_preview': len(df),
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def import_matches(self, query, column_mapping=None):
        """
        Import matches from external DB using a custom SQL query.
        
        Args:
            query: SQL query that returns match data.
            column_mapping: Optional dict mapping external columns to internal names.
        
        Returns:
            Dictionary with import results.
        """
        if not self.engine:
            return {'success': False, 'error': 'Not connected', 'rows_imported': 0}

        result = {'success': True, 'rows_imported': 0, 'errors': []}

        try:
            df = pd.read_sql(query, self.engine)

            if column_mapping:
                df = df.rename(columns=column_mapping)

            for idx, row in df.iterrows():
                try:
                    home_team = get_or_create_team(row.get('home_team'))
                    away_team = get_or_create_team(row.get('away_team'))

                    if not home_team or not away_team:
                        result['errors'].append(f'Row {idx}: Missing team')
                        continue

                    match = Match(
                        home_team_id=home_team.id,
                        away_team_id=away_team.id,
                        date=parse_date(row.get('date')),
                        home_goals=safe_int(row.get('home_goals', 0)),
                        away_goals=safe_int(row.get('away_goals', 0)),
                        league=str(row.get('league', '')) or None,
                        season=str(row.get('season', '')) or None,
                    )
                    db.session.add(match)
                    result['rows_imported'] += 1

                except Exception as e:
                    result['errors'].append(f'Row {idx}: {str(e)}')
                    continue

            db.session.commit()

        except Exception as e:
            db.session.rollback()
            result['success'] = False
            result['errors'].append(str(e))

        # Log upload
        upload = UploadHistory(
            filename=f'External DB Import',
            source_type='database',
            row_count=result['rows_imported'],
            status='success' if result['success'] else 'failed',
            error_message='; '.join(result['errors'][:5]) if result['errors'] else None,
        )
        db.session.add(upload)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()

        return result

    def close(self):
        """Close the database connection."""
        if self.engine:
            self.engine.dispose()
            self.engine = None
