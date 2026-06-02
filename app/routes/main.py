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
    from app.engine.statistics import get_dashboard_summary, get_all_league_standings
    from app.engine.visualizations import (
        chart_goals_distribution,
        chart_points_bar,
        chart_win_rate_donut
    )

    summary = get_dashboard_summary()

    # 🔥 HANDLE DATA KOSONG
    if not summary:
        return render_template("dashboard.html", empty=True)

    league_standings = get_all_league_standings()
    teams = Team.query.order_by(Team.name).all()

    charts = {
        'goals_distribution': chart_goals_distribution(),
        'points_bar': chart_points_bar(),
        'win_rate_donut': chart_win_rate_donut(),
    }

    return render_template(
        'dashboard.html',
        summary=summary,
        league_standings=league_standings,
        teams=teams,
        charts=charts
    )
# =======================================================
# BUKA FILE: main.py
# =======================================================

@main_bp.route('/teams/<int:team_id>')
def team_detail(team_id):
    from app.engine.statistics import get_team_overview
    from app.engine.visualizations import chart_team_radar, chart_team_form, chart_team_trend_lines
    from app.engine.ai_engine import generate_ai_team_analysis
    from app.engine.nlg import generate_team_analysis

    overview = get_team_overview(team_id)

    if not overview:
        return render_template('404.html'), 404

    charts = {
        'radar': chart_team_radar(team_id),
        'form': chart_team_form(team_id),
        'trends': chart_team_trend_lines(team_id),
    }

    # 🔥 LOGIKA AI DENGAN FALLBACK GANDA (PASTI MUNCUL)
    analysis_text = generate_ai_team_analysis(overview)

    if analysis_text:
        analysis_text = analysis_text.replace(". ", ".\n\n")
    else:
        # Jika Gemini gagal, coba gunakan sistem NLG lama Anda
        fallback_text = generate_team_analysis(team_id)
        if fallback_text:
            analysis_text = fallback_text.replace(". ", ".\n\n")
        else:
            # Jika semua gagal, paksa HTML menampilkan pesan ini
            analysis_text = "⚠️ Gemini AI gagal merespons. Kemungkinan data statistik tim ini belum lengkap di database, atau koneksi API terputus."

    return render_template(
        'team.html',
        overview=overview,
        charts=charts,              
        analysis_text=analysis_text # Variabel ini pasti terisi sekarang
    )


@main_bp.route('/players/<int:player_id>')
def player_detail(player_id):
    from app.engine.statistics import get_player_overview
    from app.engine.visualizations import chart_player_radar, chart_player_rating_trend
    from app.engine.ai_engine import generate_ai_player_analysis

    player_data = get_player_overview(player_id)
    if not player_data:
        return render_template('404.html'), 404

    charts = {
        'radar': chart_player_radar(player_id),
        'rating_trend': chart_player_rating_trend(player_id)
    }

    # 🔥 LOGIKA AI DENGAN FALLBACK (PASTI MUNCUL)
    analysis_text = generate_ai_player_analysis(player_data)
    
    if analysis_text:
        analysis_text = analysis_text.replace(". ", ".\n\n")
    else:
        # Jika Gemini gagal, paksa HTML menampilkan pesan ini
        analysis_text = "⚠️ Gemini AI gagal memproses analisis pemain ini. Silakan cek terminal VS Code Anda untuk melihat detail pesan error."

    return render_template(
        'player.html', 
        overview=player_data,             
        data=player_data,                 
        player=player_data.get('player', player_data), 
        charts=charts, 
        analysis_text=analysis_text # Variabel ini pasti terisi sekarang
    )
# =========================
# TEAMS
# =========================
@main_bp.route('/teams')
def teams():
    teams = Team.query.order_by(Team.name).all()
    return render_template('teams.html', teams=teams)

@main_bp.route('/players')
def players():
    players = Player.query.order_by(Player.name).all()
    return render_template('players.html', players=players)

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
    from app.engine.visualizations import chart_match_comparison, chart_match_donut_stats
    from app.engine.nlg import generate_match_summary
    from app.engine.ai_engine import generate_ai_match_analysis
    from app.models import PlayerStats
    import plotly
    import json

    data = get_match_analysis(match_id)

    if not data:
        return "Match not found", 404

    # AI
    summary_text = generate_ai_match_analysis(data)
    if not summary_text:
        summary_text = generate_match_summary(match_id)

    summary_text = summary_text.replace(". ", ".\n\n")

    # 🔥 CHART WAJIB ADA DI SINI
    donut_charts_dict = chart_match_donut_stats(match_id)

    # Konversi ke String JSON yang aman menggunakan PlotlyJSONEncoder
    charts_json = json.dumps(donut_charts_dict, cls=plotly.utils.PlotlyJSONEncoder) if donut_charts_dict else "{}"

    player_stats = PlayerStats.query.filter_by(match_id=match_id).all()

    return render_template(
        'match.html',
        summary_text=summary_text,
        match=data['match'],
        data=data,
        charts_json=charts_json,   # 🔥 INI YANG SEBELUMNYA HILANG
        player_stats=player_stats
    )
# =========================
# PLAYERS
# =========================


# =========================
# COMPARE
# =========================
@main_bp.route('/compare')
def compare():
    from app.engine.statistics import get_team_comparison, get_player_comparison
    from app.engine.ai_engine import generate_ai_comparison_analysis

    compare_type = request.args.get('type', 'team')
    id1 = request.args.get('id1', type=int)
    id2 = request.args.get('id2', type=int)

    # 🔥 FIX: jangan langsung proses kalau kosong
    if not id1 or not id2:
        teams = Team.query.all()
        players = Player.query.all()

        return render_template(
            'compare.html',
            teams=teams,
            players=players,
            data=None,
            ai_text=None
        )

    # 🔥 ambil data
    if compare_type == "team":
        data = get_team_comparison(id1, id2)
    else:
        data = get_player_comparison(id1, id2)

    if not data:
        return "Comparison data not found", 404

    # Ensure template-safe meta payload even if comparison engine returns partial data.
    meta = data.get("meta") if isinstance(data, dict) else None
    if not isinstance(meta, dict):
        meta = {}
    data["meta"] = meta

    if not meta.get("name1"):
        obj1 = Team.query.get(id1) if compare_type == "team" else Player.query.get(id1)
        meta["name1"] = obj1.name if obj1 else "Item 1"
    if not meta.get("name2"):
        obj2 = Team.query.get(id2) if compare_type == "team" else Player.query.get(id2)
        meta["name2"] = obj2.name if obj2 else "Item 2"

    ai_text = generate_ai_comparison_analysis(data, compare_type)

    return render_template(
        'compare.html',
        teams=Team.query.all(),
        players=Player.query.all(),
        data=data,
        ai_text=ai_text
    )