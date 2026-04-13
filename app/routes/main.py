"""
FDIS Main Page Routes - Home, Upload, Dashboard, Teams, Matches, Players, Campare
"""

from flask import Blueprint, render_template, request, redirect, url_for
import os

from app.models import Team, Player, Match, UploadHistory

# 🔥 IMPORT PIPELINE
from app.ingestion.csv_handler import load_csv

main_bp = Blueprint('main', __name__)


# =========================
# HOME
# =========================
@main_bp.route('/')
def index():
    from app.engine.statistics import get_dashboard_summary

    summary = get_dashboard_summary()

    return render_template('index.html', summary=summary)


# =========================
# UPLOAD (FIXED 🔥)
# =========================
@main_bp.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files.get('file')

        if not file or file.filename == '':
            return "No file uploaded", 400

        # 🔹 simpan file
        upload_folder = os.path.join("app", "static", "uploads")
        os.makedirs(upload_folder, exist_ok=True)

        file_path = os.path.join(upload_folder, file.filename)
        file.save(file_path)

        try:
            # 🔥 LOAD CSV → DataFrame
            df = load_csv(file_path)


            # 🔥 simpan history upload
            history = UploadHistory(filename=file.filename)
            from app import db
            db.session.add(history)
            db.session.commit()

        except Exception as e:
            return f"Error processing file: {str(e)}", 500

        return redirect(url_for('main.dashboard'))

    # GET (halaman upload)
    history = UploadHistory.query.order_by(
        UploadHistory.upload_date.desc()
    ).limit(20).all()

    return render_template('upload.html', history=history)


# =========================
# DASHBOARD
# =========================
@main_bp.route('/dashboard')
def dashboard():
    from app.engine.statistics import get_dashboard_summary, get_league_table
    from app.engine.visualizations import (
        chart_goals_distribution,
        chart_points_bar,
        chart_win_rate_donut
    )

    summary = get_dashboard_summary()

    # 🔥 HANDLE DATA KOSONG
    if not summary:
        return render_template("dashboard.html", empty=True)

    league_table = get_league_table()
    teams = Team.query.order_by(Team.name).all()

    charts = {
        'goals_distribution': chart_goals_distribution(),
        'points_bar': chart_points_bar(),
        'win_rate_donut': chart_win_rate_donut(),
    }

    return render_template(
        'dashboard.html',
        summary=summary,
        league_table=league_table,
        teams=teams,
        charts=charts
    )


# =========================
# TEAMS
# =========================
@main_bp.route('/teams')
def teams():
    teams = Team.query.order_by(Team.name).all()
    return render_template('teams.html', teams=teams)


@main_bp.route('/teams/<int:team_id>')
def team_detail(team_id):
    from app.engine.statistics import get_team_overview
    from app.engine.visualizations import (
        chart_team_radar,
        chart_team_form,
        chart_team_trend_lines
    )
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

    return render_template(
        'team.html',
        overview=overview,
        charts=charts,
        analysis_text=analysis_text
    )


# =========================
# MATCHES
# =========================
@main_bp.route('/matches')
def matches():
    page = request.args.get('page', 1, type=int)

    matches = Match.query.order_by(
        Match.date.desc()
    ).paginate(page=page, per_page=20)

    return render_template('matches.html', matches=matches)


@main_bp.route('/matches/<int:match_id>')
def match_detail(match_id):
    from app.engine.statistics import get_match_analysis
    from app.engine.visualizations import chart_match_comparison
    from app.engine.nlg import generate_match_summary
    from app.models import PlayerStats

    analysis = get_match_analysis(match_id)

    if not analysis:
        return render_template('404.html'), 404
    from app.engine.visualizations import chart_match_donut_stats

    charts = chart_match_donut_stats(match_id)
    summary_text = generate_match_summary(match_id)

    player_stats = PlayerStats.query.filter_by(
        match_id=match_id
    ).all()

    return render_template(
        'match.html',
        analysis=analysis,
        charts=charts,
        summary_text=summary_text,
        player_stats=player_stats
    )


# =========================
# PLAYERS
# =========================
@main_bp.route('/players')
def players():
    players = Player.query.order_by(Player.name).all()
    return render_template('players.html', players=players)


@main_bp.route('/players/<int:player_id>')
def player_detail(player_id):
    from app.engine.statistics import get_player_overview
    from app.engine.visualizations import (
        chart_player_radar,
        chart_player_rating_trend
    )
    from app.engine.nlg import generate_player_analysis

    overview = get_player_overview(player_id)

    if not overview:
        return render_template('404.html'), 404

    charts = {
        'radar': chart_player_radar(player_id),
        'rating_trend': chart_player_rating_trend(player_id),
    }

    analysis_text = generate_player_analysis(player_id)

    return render_template(
        'player.html',
        overview=overview,
        charts=charts,
        analysis_text=analysis_text
    )


# =========================
# COMPARE
# =========================
@main_bp.route('/compare')
def compare():
    teams = Team.query.order_by(Team.name).all()
    players = Player.query.order_by(Player.name).all()

    return render_template('compare.html', teams=teams, players=players)