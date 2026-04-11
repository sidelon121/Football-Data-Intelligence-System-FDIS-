"""
FDIS Configuration
Football Data Intelligence System
"""
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'fdis-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f'sqlite:///{os.path.join(BASE_DIR, "instance", "fdis.db")}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'app', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload

    # API-Football Configuration
    API_FOOTBALL_KEY = os.environ.get('API_FOOTBALL_KEY', '')
    API_FOOTBALL_BASE_URL = 'https://v3.football.api-sports.io'
    API_FOOTBALL_DAILY_LIMIT = 100
    API_FOOTBALL_RATE_LIMIT = 10  # requests per minute

    # Report settings
    REPORTS_FOLDER = os.path.join(BASE_DIR, 'app', 'static', 'reports')

    # Allowed upload extensions
    ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False


config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}
