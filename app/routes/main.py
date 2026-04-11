"""
FDIS Main Page Routes
Serves HTML pages for the web application.
"""
from flask import Blueprint, render_template, request
from app.models import Team, Player, Match, UploadHistory

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Landing page / overview dashboard."""
    from app.engine.statistics import get_dashboard_summary
    summary = get_dashboard_summary()
    return render_template('index.html', summary=summary)


@main_bp.route('/upload')
def upload():
    """Data upload page."""
    history = UploadHistory.query.order_by(UploadHistory.upload_date.desc()).limit(20).all()
    return render_template('upload.html', history=history)


@main_bp.route('/dashboard')
def dashboard():
    """Main analytics dashboard."""
    from app.engine.statistics import get_dashboard_summary, get_league_table
    from app.engine.visualizations import chart_goals_distribution, chart_points_bar, chart_win_rate_donut

    summary = get_dashboard_summary()
    league_table = get_league_table()
    teams = Team.query.order_by(Team.name).all()

    charts = {
        'goals_distribution': chart_goals_distribution(),
        'points_bar': chart_points_bar(),
        'win_rate_donut': chart_win_rate_donut(),
    }

    return render_template('dashboard.html',
                           summary=summary, league_table=league_table,
                           teams=teams, charts=charts)


@main_bp.route('/teams')
def teams():
    """Team listing page."""
    teams = Team.query.order_by(Team.name).all()
    return render_template('teams.html', teams=teams)


@main_bp.route('/teams/<int:team_id>')
def team_detail(team_id):
    """Individual team analysis page."""
    from app.engine.statistics import get_team_overview
    from app.engine.visualizations import chart_team_radar, chart_team_form, chart_team_trend_lines
    from app.engine.nlg import generate_team_analysis

    overview = get_team_overview(team_id)
    if not overview:
        return render_template('404.html'), 404

    charts = {
        'radar': chart_team_radar(team_id),
        'form': chart_team_form(team_id),
        'trends': chart_team_trend_lines(team_id),
    }
    analysis_text = generate_team_analysis(team_id)

    return render_template('team.html',
                           overview=overview, charts=charts,
                           analysis_text=analysis_text)


@main_bp.route('/matches')
def matches():
    """Match listing page."""
    page = request.args.get('page', 1, type=int)
    matches = Match.query.order_by(Match.date.desc()).paginate(page=page, per_page=20)
    return render_template('matches.html', matches=matches)


@main_bp.route('/matches/<int:match_id>')
def match_detail(match_id):
    """Individual match analysis page."""
    from app.engine.statistics import get_match_analysis
    from app.engine.visualizations import chart_match_comparison
    from app.engine.nlg import generate_match_summary

    analysis = get_match_analysis(match_id)
    if not analysis:
        return render_template('404.html'), 404

    chart = chart_match_comparison(match_id)
    summary_text = generate_match_summary(match_id)

    # Get player stats for this match
    from app.models import PlayerStats
    player_stats = PlayerStats.query.filter_by(match_id=match_id).all()

    return render_template('match.html',
                           analysis=analysis, chart=chart,
                           summary_text=summary_text,
                           player_stats=player_stats)


@main_bp.route('/players')
def players():
    """Player listing page."""
    players = Player.query.order_by(Player.name).all()
    return render_template('players.html', players=players)


@main_bp.route('/players/<int:player_id>')
def player_detail(player_id):
    """Individual player analysis page."""
    from app.engine.statistics import get_player_overview
    from app.engine.visualizations import chart_player_radar, chart_player_rating_trend
    from app.engine.nlg import generate_player_analysis

    overview = get_player_overview(player_id)
    if not overview:
        return render_template('404.html'), 404

    charts = {
        'radar': chart_player_radar(player_id),
        'rating_trend': chart_player_rating_trend(player_id),
    }
    analysis_text = generate_player_analysis(player_id)

    return render_template('player.html',
                           overview=overview, charts=charts,
                           analysis_text=analysis_text)


@main_bp.route('/compare')
def compare():
    """Comparison tool page."""
    teams = Team.query.order_by(Team.name).all()
    players = Player.query.order_by(Player.name).all()
    return render_template('compare.html', teams=teams, players=players)
