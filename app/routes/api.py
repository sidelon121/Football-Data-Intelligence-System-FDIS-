"""
FDIS REST API Routes
JSON API endpoints for data operations.
"""
from dotenv import load_dotenv
import os
import json
from re import match
from flask import Blueprint, redirect, request, jsonify, current_app, send_file, render_template, url_for
from werkzeug.utils import secure_filename
from app.models import Team, Player, Match, UploadHistory, PlayerStats, MatchStats
from app import db
from app.engine.statistics import get_match_analysis, get_player_overview
from app.engine.nlg import generate_match_summary, generate_player_analysis
from app.utils.pdf_exporter import create_pdf, safe_text
import tempfile
from app.engine.visualizations import chart_match_comparison, chart_match_donut_stats
from app.engine.visualizations import chart_player_radar
from app.utils.chart_exporter import save_chart_as_image
import plotly.graph_objects as go
import json
import requests
import tempfile
from app.engine.ai_engine import generate_ai_match_analysis
from app.engine.statistics import get_match_analysis
from flask import send_file
from app.models import Team, Player
from app.engine.statistics import get_team_comparison, get_player_comparison


load_dotenv()

api_bp = Blueprint('api', __name__)

def get_logo_path(url):
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            tmp.write(r.content)
            tmp.close()
            return tmp.name
    except:
        return None


# ========================
# MATCH PDF
# ========================
@api_bp.route('/export/pdf/match/<int:match_id>')
def export_match_pdf(match_id):
    """Export match report to PDF dengan support penalty shootout & Auto Page Break."""
    
    data = get_match_analysis(match_id)
    if not data:
        return "Match not found", 404

    pdf = create_pdf()  # Custom PDF class
    pdf.add_page()
    match = data['match']
    metrics = data.get('metrics', {})

    home = match['home_team']['name']
    away = match['away_team']['name']

    # LOGIKA STATUS KETAT
    is_penalty = (match.get('status') == 'penalties') or (str(match.get('has_penalties', '')).strip().lower() in ['true', '1', 'yes', 't', 'y'])
    is_et = (match.get('status') == 'extra_time') or (match.get('home_goals_et', 0) > 0) or (match.get('away_goals_et', 0) > 0)

    # ==========================================
    # 🏆 HEADER
    # ==========================================
    pdf.section_header("MATCH REPORT")
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 6, f"{match.get('league','-')} | {match.get('date','-')} | {match.get('venue','-')}", ln=True, align="C")
    pdf.ln(5)
    
    # ==========================================
    # ⚽ SCORE & SCORERS
    # ==========================================
    pdf.set_font("Arial", "B", 24)
    pdf.cell(85, 15, home, align="R")
    
    pdf.set_text_color(102, 126, 234)  # Warna Biru
    pdf.cell(20, 15, f"{match.get('home_goals', 0)} - {match.get('away_goals', 0)}", align="C")
    
    pdf.set_text_color(0, 0, 0) # Kembali ke Hitam
    pdf.cell(85, 15, away, align="L", ln=True)
    
    # STATUS PERTANDINGAN (FT / AET / PEN)
    pdf.set_font("Arial", "B", 10)
    pdf.set_text_color(200, 50, 50) 
    
    status_text = "FT"
    if is_penalty:
        status_text = f"PEN ({match.get('home_penalties_scored', 0)} - {match.get('away_penalties_scored', 0)})"
    elif is_et:
        total_home = match.get('home_goals', 0) + match.get('home_goals_et', 0)
        total_away = match.get('away_goals', 0) + match.get('away_goals_et', 0)
        status_text = f"AET ({total_home} - {total_away})"
    
    pdf.set_x(95)
    pdf.cell(20, 5, status_text, align="C", ln=True)
    pdf.ln(5)

    # PENCETAK GOL
    pdf.set_font("Arial", "I", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(85, 5, f"{match.get('home_goalscorers') or '-'}", align="R")
    pdf.cell(20, 5, "", align="C")
    pdf.cell(85, 5, f"{match.get('away_goalscorers') or '-'}", ln=True, align="L")
    pdf.ln(15)
    
    # ==========================================
    # ⚽ PENALTY SHOOTOUT SECTION (Tabel)
    # ==========================================
    if is_penalty and match.get('penalty_details'):
        # Cek sisa ruang, jika tidak muat, buat halaman baru
        if pdf.get_y() > 200:
            pdf.add_page()
        else:
            pdf.ln(10)

        pdf.set_font("Arial", "B", 14)
        pdf.set_text_color(26, 26, 46)
        pdf.cell(190, 8, "PENALTY SHOOTOUT", ln=True, align="L")
        pdf.set_draw_color(180, 180, 180)
        pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 190, pdf.get_y())
        pdf.ln(5)

        pdf.set_font("Arial", "", 11)
        pdf.set_text_color(0, 0, 0)
        
        home_pen_score = match.get('home_penalties_scored', 0)
        away_pen_score = match.get('away_penalties_scored', 0)
        home_pen_attempts = match.get('home_penalties_attempted', 0)
        away_pen_attempts = match.get('away_penalties_attempted', 0)

        pdf.cell(95, 6, f"{home}: {home_pen_score}/{home_pen_attempts}", align="L")
        pdf.cell(95, 6, f"{away}: {away_pen_score}/{away_pen_attempts}", ln=True, align="R")
        pdf.ln(3)

        pdf.set_font("Arial", "", 9)
        
        home_penalties = [p for p in match.get('penalty_details', []) if p.get('team') == 'home']
        away_penalties = [p for p in match.get('penalty_details', []) if p.get('team') == 'away']

        max_penalties = max(len(home_penalties), len(away_penalties))
        
        for i in range(max_penalties):
            if i < len(home_penalties):
                p = home_penalties[i]
                status = "(O)" if p.get('scored') else "(X)"
                text = f"{status} {p.get('player', 'Unknown')}"
                pdf.cell(95, 5, text, border=1, align="L")
            else:
                pdf.cell(95, 5, "", border=1)
            
            if i < len(away_penalties):
                p = away_penalties[i]
                status = "(O)" if p.get('scored') else "(X)"
                text = f"{status} {p.get('player', 'Unknown')}"
                pdf.cell(95, 5, text, border=1, ln=True, align="L")
            else:
                pdf.cell(95, 5, "", border=1, ln=True)

        pdf.ln(8)

        pdf.set_font("Arial", "B", 11)
        if home_pen_score > away_pen_score:
            pdf.set_text_color(39, 174, 96)
            pdf.cell(190, 6, f"{home} WON on penalties", ln=True, align="C")
        elif away_pen_score > home_pen_score:
            pdf.set_text_color(39, 174, 96)
            pdf.cell(190, 6, f"{away} WON on penalties", ln=True, align="C")
        else:
            pdf.set_text_color(230, 126, 34)
            pdf.cell(190, 6, "Penalty shootout ongoing or tied", ln=True, align="C")
        
        pdf.set_text_color(0, 0, 0)
        pdf.ln(10)

    # ==========================================
    # 📊 STATS BARS (FIXED PAGE BREAK LOGIC)
    # ==========================================
    # Pastikan ada ruang cukup sebelum menggambar Header
    if pdf.get_y() > 250:
        pdf.add_page()
    else:
        pdf.ln(5)
        
    pdf.section_title("Match Statistics")
    
    for key, m in metrics.items():
        if isinstance(m, dict):
            # 🔥 CEK RUANG AMAN (250mm) SEBELUM MENGGAMBAR SETIAP BAR
            if pdf.get_y() > 250: 
                pdf.add_page()
                pdf.ln(5) # Beri jarak sedikit dari atas kertas baru
                
            pdf.stat_vs_bar(m.get('label', key), m.get('home', 0), m.get('away', 0))

    # ==========================================
    # VISUAL MATCH STATS (CIRCLE CHARTS)
    # ==========================================
    # 🔥 SOLUSI: Hapus `pdf.add_page()` yang memaksa halaman baru
    # Ganti dengan logika sisa ruang (Smart Page Break)
    if pdf.get_y() > 210: 
        pdf.add_page()
    else:
        pdf.ln(10) # Beri jarak secukupnya antara grafik batang terakhir dengan section Visual Stats

    pdf.section_title("Visual Match Stats")

    circle_metrics = data.get("circle_metrics", [])
    
    # Jarak awal setelah judul section
    y = pdf.get_y() + 1 

    for m in circle_metrics:
        # Cek batas bawah disesuaikan dengan tinggi elemen yang baru
        if y + 50 > 275: # Saya kembalikan ke batas aman 275 mm agar tidak terpotong footer
            pdf.add_page()
            y = 15 # Jarak atas di halaman baru
        
        # Menggambar Judul Grafik (misal: "Pass Accuracy")
        pdf.set_xy(8, y)
        pdf.set_font("Arial", "B", 11)
        pdf.cell(190, 6, safe_text(m["label"]), align="C")

        # HOME CHART
        fig_home = go.Figure(data=[go.Pie(
            labels=m["labels"],
            values=m["home_values"],
            hole=0.4,
            marker_colors=["#3d08fd", "#fa0909", "#77868D"],
            textposition="auto", 
            texttemplate="<b>%{value}</b><br>(%{percent})", 
            textinfo='value+percent',
            textfont=dict(size=14, color='black')
        )])

        fig_home.update_layout(
            width=300, height=300, showlegend=True,
            legend=dict(orientation="h", yanchor="top", y=-0.1, xanchor="center", x=0.5, font=dict(size=12, color="black")),
            annotations=[dict(text=f"{m['home_values'][0]}/{sum(m['home_values'])}", x=0.5, y=0.5, font=dict(size=16, color='black'), showarrow=False)],
            margin=dict(t=0, b=0, l=0, r=0), 
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
        )
        home_img = save_chart_as_image(fig_home)
        
        # Posisi Y gambar
        pdf.image(home_img, x=35, y=y + 6, w=45)

        # AWAY CHART
        fig_away = go.Figure(data=[go.Pie(
            labels=m["labels"],
            values=m["away_values"],
            hole=0.4,
            marker_colors=["#9b59b6", "#fa0909", "#77868D"],
            textposition="auto", 
            texttemplate="<b>%{value}</b><br>(%{percent})", 
            textinfo='value+percent',
            textfont=dict(size=14, color='black')
        )])

        fig_away.update_layout(
            width=300, height=300, showlegend=True,
            legend=dict(orientation="h", yanchor="top", y=-0.1, xanchor="center", x=0.5, font=dict(size=12, color="black")),
            annotations=[dict(text=f"{m['away_values'][0]}/{sum(m['away_values'])}", x=0.5, y=0.5, font=dict(size=16, color='black'), showarrow=False)],
            margin=dict(t=0, b=0, l=0, r=0), 
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
        )
        away_img = save_chart_as_image(fig_away)
        
        # Posisi Y gambar
        pdf.image(away_img, x=130, y=y + 6, w=45)

        # JARAK ANTAR BARIS GRAFIK DONAT
        y += 45 

    pdf.set_y(y + 5)

    # ==========================================
    # 📝 ANALYSIS & INSIGHTS
    # ==========================================
    summary = generate_ai_match_analysis(data)
    
    if summary:
        # Cek sisa ruang, jika mepet buat halaman baru
        if pdf.get_y() > 200:
            pdf.add_page()
        else:
            pdf.ln(5)
            
        pdf.set_font("Arial", "B", 14)
        pdf.set_text_color(26, 26, 46)
        pdf.cell(190, 8, "ANALYSIS & INSIGHTS", ln=True, align="L")
        pdf.set_draw_color(180, 180, 180)
        pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 190, pdf.get_y())
        pdf.ln(5)

        pdf.render_ai_analysis(summary)

    # ==========================================
    # SAVE & RETURN
    # ==========================================
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp.name)

    filename = f"Match_{home}_vs_{away}.pdf".replace(" ", "_")
    return send_file(temp.name, as_attachment=True, download_name=filename)

def safe_text(text):
    """Clean text for PDF."""
    if text is None:
        return ""
    return str(text).replace('\n', ' ')



@api_bp.route('/export/pdf/team')
@api_bp.route('/export/pdf/team/<int:team_id>')
def export_team_pdf(team_id=None):
    from flask import request, send_file
    import tempfile
    import plotly.graph_objects as go
    from app.engine.statistics import get_team_overview
    from app.engine.ai_engine import generate_ai_team_analysis
    from app.utils.chart_exporter import save_chart_as_image
    
    data = None 
    if team_id is None:
        team_id = request.args.get('id') or request.args.get('team_id')
    if not team_id:
        return "Team ID diperlukan (bisa lewat URL path atau ?id=)", 400
    try:
        team_id = int(team_id)
    except (ValueError, TypeError):
        return "Team ID harus berupa angka murni", 400
    
    data = get_team_overview(team_id)
    if not data:
        return "Data Team tidak ditemukan di database", 404
    
    pdf = create_pdf()
    pdf.add_page()
    team = data['team']
    
    # ========================================================
    # HEADER REPORT
    # ========================================================
    pdf.section_header(f"CLUB REPORT: {team['name']}")
    
    # ========================================================
    # TABLE PERFORMANCE
    # ========================================================
    pdf.section_title("Seasonal Performance")
    pdf.draw_table(
        ["League", "MP", "W-D-L", "Win Rate", "Points"],
        [[team.get('league', '-'), data.get('matches_played', 0), 
          f"{data.get('wins')}-{data.get('draws')}-{data.get('losses')}", 
          f"{data.get('win_rate')}%", data.get('points', 0)]],
        [60, 20, 40, 35, 35]
    )
    
    # ========================================================
    # TABLE ATTACKING STATS
    # ========================================================
    pdf.section_title("Attacking & Possession Stats")
    pdf.draw_table(
        ["Avg xG", "Possession", "Shots/Match", "Pass Acc", "Corners"],
        [[f"{data.get('avg_xg', 0)}", f"{data.get('avg_possession', 0)}%", 
          f"{data.get('avg_shots', 0)}", f"{data.get('avg_pass_accuracy', 0)}%", 
          f"{data.get('avg_corners', 0)}"]],
        [38, 38, 38, 38, 38]
    )
    
    # ========================================================
    # TABLE DEFENDING STATS
    # ========================================================
    pdf.section_title("Defending & Discipline Stats")
    pdf.draw_table(
        ["Clean Sheets", "Tackles/Match", "Intercepts", "Yellow Cards", "Red Cards"],
        [[f"{data.get('clean_sheets', 0)}", f"{data.get('avg_tackles_total', 0)}", 
          f"{data.get('avg_interceptions', 0)}", f"{data.get('total_yellow_cards', 0)}", 
          f"{data.get('total_red_cards', 0)}"]],
        [38, 38, 38, 38, 38]
    )
    
    # ========================================================
    # GRAFIK PDF TEAM (RADAR & TRENDS BERDAMPINGAN)
    # ========================================================
    pdf.section_title("Performance Analysis")
    
    # 1. RADAR CHART (Sesuai Logika Web)
    radar_categories = ['Possession', 'Shots', 'Pass Acc.', 'xG', 'Tackles', 'Interceptions', 'Corners']
    radar_values = [
        data.get('avg_possession', 0) / 100,
        min(data.get('avg_shots', 0) / 25, 1),
        data.get('avg_pass_accuracy', 0) / 100,
        min(data.get('avg_xg', 0) / 3, 1),
        min(data.get('avg_tackles_total', 0) / 30, 1),
        min(data.get('avg_interceptions', 0) / 20, 1),
        min(data.get('avg_corners', 0) / 12, 1)
    ]
    # Tutup garis radar agar nyambung (seperti di web)
    radar_values.append(radar_values[0])
    radar_categories.append(radar_categories[0])

    fig_radar = go.Figure(data=go.Scatterpolar(
        r=[v * 100 for v in radar_values], # Kalikan 100 sesuai web
        theta=radar_categories,
        fill='toself',
        fillcolor='rgba(67,233,123,0.2)',  # Warna hijau web
        line=dict(color='#43e97b', width=2)
    ))
    
    fig_radar.update_layout(
        width=400, height=300,
        title='Performance Profile',
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], gridcolor='rgba(0,0,0,0.1)', tickfont=dict(size=10)),
            angularaxis=dict(gridcolor='rgba(0,0,0,0.1)')
        ),
        margin=dict(t=40, b=20, l=20, r=20),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(size=10, color='#000000'), showlegend=False
    )
    img_radar = save_chart_as_image(fig_radar)
    
    # 2. TRENDS CHART (Sesuai Logika Web)
    # Gunakan data histori, jika kosong pakai dummy yang dikali 20 untuk xG
    from app.engine.statistics import get_team_performance_trend
    trend = get_team_performance_trend(team_id, last_n=15)
    
    fig_trends = go.Figure()
    if trend and trend.get('trend'):
        trend_data = trend['trend']
        dates = [d['date'] for d in trend_data]
        
        fig_trends.add_trace(go.Scatter(
            x=dates, y=[d['possession'] for d in trend_data], 
            name='Possession %', mode='lines+markers', line=dict(color='#3b82f6', width=2)
        ))
        fig_trends.add_trace(go.Scatter(
            x=dates, y=[d['pass_accuracy'] for d in trend_data], 
            name='Pass Accuracy %', mode='lines+markers', line=dict(color='#43e97b', width=2)
        ))
        fig_trends.add_trace(go.Scatter(
            x=dates, y=[d['xg'] * 20 for d in trend_data], # xG dikali 20 persis seperti web
            name='xG (×20)', mode='lines+markers', line=dict(color='#f59e0b', width=2, dash='dot')
        ))
        fig_trends.update_layout(xaxis_title='Match Date')
    
    fig_trends.update_layout(
        width=400, height=300,
        title='Performance Trends',
        yaxis_title='Value',
        margin=dict(t=40, b=30, l=40, r=20),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(size=10, color='#000000'), hovermode='x unified',
        legend=dict(x=0, y=1, bgcolor='rgba(255,255,255,0.8)')
    )
    img_trends = save_chart_as_image(fig_trends)    
    # 3. MASUKKAN KE PDF BERDAMPINGAN
    current_y = pdf.get_y()
    pdf.image(img_radar, x=15, y=current_y, w=95)
    pdf.image(img_trends, x=110, y=current_y, w=95)
    pdf.ln(40)
    
    
    # ========================================================
    # AI ANALYSIS SECTION
    # ========================================================
    analysis = generate_ai_team_analysis(data)
    if analysis:
        if pdf.get_y() > 220:
            pdf.add_page()
        pdf.section_header("Tactical Analysis")
        for p in analysis.split("\n\n"):
            pdf.section_text(p)
    
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp.name)
    filename = f"Team_{team['name']}.pdf".replace(" ", "_")
    return send_file(temp.name, as_attachment=True, download_name=filename)

# ─── Upload Endpoints ─────────────────────────────────────────────
def allowed_file(filename):
    if not filename:
        return False
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'csv', 'xlsx', 'xls'}


@api_bp.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'success': False, 'error': 'File type not allowed'}), 400

    upload_dir = current_app.config.get('UPLOAD_FOLDER', 'uploads')

    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)

    filename = secure_filename(file.filename)
    filepath = os.path.join(upload_dir, filename)

    file.save(filepath)

    from app.ingestion.csv_handler import process_uploaded_file

    result = process_uploaded_file(filepath, filename)

    return redirect(url_for('main.dashboard'))
    

@api_bp.route('/manual-entry', methods=['POST'])
def manual_entry():
    """Handle manual match data entry."""
    from app.ingestion.manual_handler import process_manual_match
    data = request.get_json() or request.form.to_dict()

    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400

    result = process_manual_match(data)
    return jsonify(result)


@api_bp.route('/manual-player', methods=['POST'])
def manual_player_entry():
    """Handle manual player stats entry."""
    from app.ingestion.manual_handler import process_manual_player_stats
    data = request.get_json() or request.form.to_dict()

    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400

    result = process_manual_player_stats(data)
    return jsonify(result)


@api_bp.route('/fetch-api', methods=['POST'])
def fetch_api():
    """Trigger API-Football data fetch."""
    data = request.get_json() or request.form.to_dict()
    league_id = data.get('league_id')
    season = data.get('season')

    if not league_id or not season:
        return jsonify({'success': False, 'error': 'league_id and season are required'}), 400

    from app.ingestion.api_handler import APIFootballClient
    client = APIFootballClient()
    result = client.fetch_and_store_fixtures(
        league_id=int(league_id),
        season=int(season),
        last=data.get('last')
    )
    return jsonify(result)


# ─── Statistics Endpoints ─────────────────────────────────────────

def serialize(obj):
    if isinstance(obj, list):
        return [serialize(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: serialize(v) for k, v in obj.items()}
    elif hasattr(obj, "to_dict"):
        return obj.to_dict()
    else:
        return obj

@api_bp.route('/stats/team/<int:team_id>')
def team_stats(team_id):
    """Get team statistics."""
    from app.engine.statistics import get_team_overview
    from app.utils.serializers import serialize
    data = get_team_overview(team_id)
    if not data:
        return jsonify({'error': 'Team not found'}), 404
    return jsonify(serialize(data))


@api_bp.route('/stats/player/<int:player_id>')
def player_stats(player_id):
    """Get player statistics."""
    from app.engine.statistics import get_player_overview
    data = get_player_overview(player_id)
    if not data:
        return jsonify({'error': 'Player not found'}), 404
    return jsonify(serialize(data))


@api_bp.route('/stats/match/<int:match_id>')
def match_stats(match_id):
    """Get match statistics."""
    from app.engine.statistics import get_match_analysis
    data = get_match_analysis(match_id)
    if not data:
        return jsonify({'error': 'Match not found'}), 404
    return jsonify(serialize(data))



@api_bp.route('/stats/league-table')
def league_table():
    """Get league table standings."""
    from app.engine.statistics import get_league_table
    league = request.args.get('league')
    season = request.args.get('season')
    table = get_league_table(league=league, season=season)
    return jsonify(table)


# ─── Chart Endpoints ──────────────────────────────────────────────
@api_bp.route('/teams/<int:team_id>')
def team_detail(team_id):
    from app.engine.statistics import get_team_overview 
    from app.engine.visualizations import chart_team_radar, chart_team_trend_lines
    # 🔥 1. IMPORT FUNGSI AI TEAM DARI ENGINE
    from app.engine.ai_engine import generate_ai_team_analysis

    team_data = get_team_overview(team_id) 

    # 🔥 2. LOGIKA AI SUMMARY
    analysis_text = generate_ai_team_analysis(team_data)
    
    # Biar rapi di HTML (membentuk paragraf baru)
    if analysis_text:
        analysis_text = analysis_text.replace(". ", ".\n\n")
    else:
        # Fallback jika gagal/kuota habis
        analysis_text = "⚠️ Analisis AI saat ini tidak tersedia."

    # --- JARING PENGAMAN GRAFIK ---
    radar_data = chart_team_radar(team_id)
    trend_data = chart_team_trend_lines(team_id)

    if trend_data is None:
        print(f"DEBUG: Data trend untuk tim {team_id} kosong dari engine!")
        trend_data = {} 

    charts = {
        'radar': radar_data,
        'performance_trends': trend_data 
    }
    # ------------------------------

    return render_template(
        'team.html', 
        team=team_data,
        charts=charts,
        analysis_text=analysis_text  # 🔥 3. KIRIM KE HTML
    )

@api_bp.route('/chart/match/<int:match_id>')
def chart_match(match_id):
    """Get match comparison chart JSON."""
    from app.engine.visualizations import chart_match_comparison
    chart = chart_match_comparison(match_id)
    if not chart:
        return jsonify({'error': 'No data'}), 404
    return jsonify(chart)


@api_bp.route('/players/<int:player_id>')
def player_detail(player_id):
    from app.engine.statistics import get_player_overview
    from app.engine.visualizations import chart_player_radar, chart_player_rating_trend
    # 🔥 1. IMPORT FUNGSI AI PLAYER DARI ENGINE
    from app.engine.ai_engine import generate_ai_player_analysis

    player_data = get_player_overview(player_id)
    
    # 🔥 2. LOGIKA AI SUMMARY
    summary_text = generate_ai_player_analysis(player_data)
    
    # Biar rapi di HTML (membentuk paragraf baru)
    if summary_text:
        summary_text = summary_text.replace(". ", ".\n\n")
    else:
        # Fallback jika gagal
        summary_text = "⚠️ Analisis AI saat ini tidak tersedia."

    # PROSES KEDUA GRAFIK DI SINI
    radar_json = chart_player_radar(player_id)
    rating_trend_json = chart_player_rating_trend(player_id) 

    # Satukan ke dalam dictionary charts
    charts = {
        'radar': radar_json,
        'rating_trend': rating_trend_json
    }

    return render_template(
        'player.html', 
        overview=player_data.get('overview'), 
        charts=charts, 
        player=player_data,
        summary_text=summary_text  # 🔥 3. KIRIM KE HTML
    )

# ─── Analysis Endpoints ──────────────────────────────────────────
import json
import plotly
import json
import plotly
from flask import render_template
# Pastikan fungsi-fungsi ini sudah di-import di bagian atas file Anda:
# from app.engine.statistics import get_match_analysis
# from app.engine.ai_summary import generate_ai_match_analysis, generate_match_summary
# from app.engine.visualisasi import chart_match_donut_stats

@api_bp.route('/match/<int:match_id>')
def match_detail(match_id):
    # 1. Ambil data match
    data = get_match_analysis(match_id)

    if not data:
        return "Match not found", 404

    # 2. 🔥 LOGIKA AI SUMMARY (Milik Anda)
    summary_text = generate_ai_match_analysis(data)

    # Fallback kalau AI gagal
    if not summary_text or "failed" in summary_text.lower():
        summary_text = generate_match_summary(match_id)

    # Biar rapi di HTML
    if summary_text:
        summary_text = summary_text.replace(". ", ".\n\n")

    print("FINAL WEB SUMMARY:", summary_text)
    
    # 3. 🔥 LOGIKA GRAFIK BULAT (DONUT)
    # Memanggil fungsi yang mengembalikan banyak dictionary (bukan 1 chart)
    donut_charts_dict = chart_match_donut_stats(match_id)

    # Konversi ke String JSON yang aman menggunakan PlotlyJSONEncoder
    charts_json = json.dumps(donut_charts_dict, cls=plotly.utils.PlotlyJSONEncoder) if donut_charts_dict else "{}"

    # 4. Kirim semua data ke Template
    return render_template(
        "match_detail.html",
        summary_text=summary_text,
        match=data['match'],
        data=data,
        charts_json=charts_json,
    )

@api_bp.route('/analysis/team/<int:team_id>')
def analysis_team(team_id):
    """Get auto-generated team analysis text."""
    from app.engine.nlg import generate_team_analysis
    text = generate_team_analysis(team_id)
    return jsonify({'analysis': text})


@api_bp.route('/analysis/player/<int:player_id>')
def analysis_player(player_id):
    """Get auto-generated player analysis text."""
    from app.engine.nlg import generate_player_analysis
    text = generate_player_analysis(player_id)
    return jsonify({'analysis': text})


# ─── Comparison Endpoint ─────────────────────────────────────────
import json
import tempfile
from flask import request, send_file, render_template
import plotly.graph_objects as go
from app.models import Team, Player
# Impor internal system Anda
from app.engine.statistics import get_team_comparison, get_player_comparison
from app.engine.ai_engine import generate_ai_comparison_analysis
from app.utils.chart_exporter import save_chart_as_image
# Asumsi fungsi helper pembentuk PDF Anda
# dari modul PDF creator Anda (misal: from app.utils.pdf_exporter import create_pdf)

@api_bp.route('/export/pdf/compare')
def export_compare_pdf():
    from app.utils.pdf_exporter import create_pdf  # Pastikan di-import sesuai struktur Anda

    compare_type = request.args.get('type', 'team')
    id1 = request.args.get('id1', type=int)
    id2 = request.args.get('id2', type=int)

    if not id1 or not id2:
        return "Invalid request", 400

    if compare_type == "team":
        data = get_team_comparison(id1, id2)
    else:
        data = get_player_comparison(id1, id2)

    if not data:
        return "Comparison data not found", 404

    # Safe meta access & fallback
    meta = data.get('meta', {}) if isinstance(data, dict) else {}
    if not isinstance(meta, dict):
        meta = {}
    data['meta'] = meta

    if not meta.get('name1'):
        obj1 = Team.query.get(id1) if compare_type == "team" else Player.query.get(id1)
        meta['name1'] = obj1.name if obj1 else "Item 1"
    if not meta.get('name2'):
        obj2 = Team.query.get(id2) if compare_type == "team" else Player.query.get(id2)
        meta['name2'] = obj2.name if obj2 else "Item 2"

    name1 = meta['name1']
    name2 = meta['name2']
    chart_data = data.get('chart_data', {})

    # ==========================================
    # GENERATE PLOTLY CHART DENGAN UKURAN PASTI
    # ==========================================
    if compare_type == "team":
        # Bar Chart untuk Team
        fig = go.Figure(data=[
            go.Bar(name=name1, x=chart_data.get('labels', []), y=chart_data.get('team1', []), marker_color="#4807fd"),
            go.Bar(name=name2, x=chart_data.get('labels', []), y=chart_data.get('team2', []), marker_color="#9b59b6")
        ])
        # Mengunci resolusi gambar (Rasio 2:1) dan memiringkan label sumbu X agar tidak bertumpuk
        fig.update_layout(
            barmode='group', 
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)', 
            width=800,
            height=400,
            xaxis=dict(tickangle=-35, tickfont=dict(size=10)),
            margin=dict(t=30, b=70, l=40, r=20)
        )
    else:
        # Radar Chart untuk Player
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(r=chart_data.get('player1', []), theta=chart_data.get('labels', []), fill='toself', name=name1, marker_color='#4807fd'))
        fig.add_trace(go.Scatterpolar(r=chart_data.get('player2', []), theta=chart_data.get('labels', []), fill='toself', name=name2, marker_color='#9b59b6'))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])), 
            showlegend=True, 
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)',
            width=800,
            height=450,
            margin=dict(t=40, b=40, l=40, r=40)
        )

    img_path = save_chart_as_image(fig)
    
    # INISIALISASI PDF
    pdf = create_pdf()
    pdf.add_page()

    # 1. HEADER
    pdf.section_header(f"COMPARISON: {name1} VS {name2}")
    
    # 2. VISUAL CHART SECTION
    pdf.section_title("Visual Performance Analysis")
    start_y = pdf.get_y()
    
    # Penempatan gambar dan pergeseran kursor Y secara presisi berdasarkan tipe chart
    if compare_type == "team":
        # Lebar 180mm, Tinggi 90mm (menjaga rasio 800x400)
        pdf.image(img_path, x=15, y=start_y, w=180, h=90)
        pdf.set_y(start_y + 95)  # Beri ruang kosong 5mm di bawah gambar
    else:
        # Lebar 160mm, Tinggi 90mm (menjaga rasio radar chart tetap proporsional di tengah)
        pdf.image(img_path, x=25, y=start_y, w=160, h=90)
        pdf.set_y(start_y + 95)

# 3. STATISTICAL COMPARISON TABLE
    # Jika sisa halaman terlalu sempit (< 45mm dari bawah), pindah ke halaman baru agar judul tidak gantung
    if pdf.get_y() > 240:
        pdf.add_page()
        
    pdf.section_title("Statistical Comparison")
    
    # --- TAMBAHAN: Membuat Header Tabel agar rapi ---
    # Mengasumsikan lebar A4 = 210mm, margin kiri-kanan = 10mm (Total lebar area = 190mm)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(45, 8, name1, border=0, align='C')
    pdf.cell(100, 8, "Metrics", border=0, align='C')
    pdf.cell(45, 8, name2, border=0, ln=1, align='C')
    
    # Membuat garis pemisah tipis di bawah header
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3) # Spasi kecil setelah garis
    # -----------------------------------------------

    for m in data.get('metrics', []):
        # Defensive check: Jika baris tabel sudah mendekati batas bawah kertas
        if pdf.get_y() > 270:
            pdf.add_page()
            
        label = str(m.get('label', ''))
        val1 = str(m.get('t1', 0))
        val2 = str(m.get('t2', 0))

        # Render format teks biasa: [Angka T1] | [Label Metrik] | [Angka T2]
        pdf.set_font("Arial", "", 10)  # Font normal untuk angka
        pdf.cell(45, 8, val1, border=0, align='C')
        
        pdf.set_font("Arial", "B", 10) # Font tebal untuk nama metrik di tengah
        pdf.cell(100, 8, label, border=0, align='C')
        
        pdf.set_font("Arial", "", 10)  # Font normal untuk angka
        pdf.cell(45, 8, val2, border=0, ln=1, align='C') # ln=1 untuk pindah baris

    # 4. AI TACTICAL ANALYSIS SECTION
    ai_text = generate_ai_comparison_analysis(data, compare_type)
    if ai_text:
        # Beri batas halaman baru jika ruang analisis AI tersisa sedikit
        if pdf.get_y() > 220:
            pdf.add_page()
            
        pdf.section_header("Tactical Insights")
        for p in ai_text.split("\n\n"):
            if p.strip():
                if pdf.get_y() > 265:
                    pdf.add_page()
                pdf.section_text(p)

    # OUTPUT FILE HANDLING
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp.name)

    filename = f"Compare_{name1}_vs_{name2}.pdf".replace(" ", "_")
    return send_file(temp.name, as_attachment=True, download_name=filename)


def clean_for_json(obj):
    if isinstance(obj, dict):
        return {k: clean_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_for_json(i) for i in obj]
    elif hasattr(obj, "to_dict"):
        return obj.to_dict()
    else:
        return obj


@api_bp.route('/compare')
def compare_page():
    compare_type = request.args.get('type', 'team')
    id1 = request.args.get('id1', type=int)
    id2 = request.args.get('id2', type=int)

    # Pastikan list untuk select dropdown terambil lengkap
    teams = [{"id": t.id, "name": t.name} for t in Team.query.all()]
    players = [{"id": p.id, "name": p.name} for p in Player.query.all()]

    data = None

    if id1 and id2:
        if compare_type == "team":
            data = get_team_comparison(id1, id2)
        else:
            data = get_player_comparison(id1, id2)

        # Injeksi data penamaan item ke metadata untuk sinkronisasi FE/BE
        if data:
            obj1 = Team.query.get(id1) if compare_type == "team" else Player.query.get(id1)
            obj2 = Team.query.get(id2) if compare_type == "team" else Player.query.get(id2)

            data["meta"] = {
                "name1": obj1.name if obj1 else "Item 1",
                "name2": obj2.name if obj2 else "Item 2"
            }

    return render_template(
        "compare.html",
        teams=teams,
        players=players,
        data=data,
        data_json=json.dumps(data) if data else "null"
    )
# ─── Export Endpoints ─────────────────────────────────────────────


@api_bp.route('/export/pdf/player')
@api_bp.route('/export/pdf/player/<int:player_id>')
def export_player_pdf(player_id=None):
    from flask import request, send_file
    import tempfile
    import plotly.graph_objects as go
    from app.engine.statistics import get_player_overview
    from app.engine.ai_engine import generate_ai_player_analysis
    from app.utils.chart_exporter import save_chart_as_image
    
    # Set awal untuk menghindari NameError
    data = None 
    
    # Ambil ID secara fleksibel (dari URL Path atau Query Parameter)
    if player_id is None:
        player_id = request.args.get('id') or request.args.get('player_id')
    if not player_id:
        return "Player ID diperlukan (bisa lewat URL path atau ?id=)", 400
    try:
        player_id = int(player_id)
    except (ValueError, TypeError):
        return "Player ID harus berupa angka murni", 400
    
    # Ambil data overview player
    data = get_player_overview(player_id)
    if not data:
        return "Data Player tidak ditemukan di database", 404
    
    # Inisialisasi dan Render PDF
    pdf = create_pdf()
    pdf.add_page()
    player = data['player']
    
    # ========================================================
    # HEADER REPORT
    # ========================================================
    pdf.section_header(f"PLAYER PROFILE: {player['name']}")
    
    # ========================================================
    # BASIC INFO TABLE
    # ========================================================
    pdf.section_title("Personal Information")
    pdf.draw_table(
        ["Position", "Team", "Matches", "Minutes", "Avg Rating"],
        [[player.get('position', '-'), player.get('team_name', '-'), 
          data.get('matches_played', 0), data.get('total_minutes', 0), 
          data.get('avg_rating', 0)]],
        [38, 50, 30, 36, 36]
    )
    
    # ========================================================
    # TECHNICAL STATISTICS TABLE
    # ========================================================
    pdf.section_title("Detailed Technical Statistics")
    pdf.draw_table(
        ["Goals", "Assists", "Shots On Target", "Key Passes", "Pass Acc"],
        [[f"{data.get('total_goals', 0)}", f"{data.get('total_assists', 0)}", 
          f"{data.get('total_shots_on_target', 0)}", f"{data.get('total_key_passes', 0)}", 
          f"{data.get('avg_pass_accuracy', 0)}%"]],
        [38, 38, 38, 38, 38]
    )
    
    # ========================================================
    # DEFENSIVE STATISTICS TABLE
    # ========================================================
    pdf.draw_table(
        ["Tackles/90", "Intercepts/90", "Dribbles Succ", "Yellow Cards", "Red Cards"],
        [[f"{data.get('tackles_per_90', 0)}", f"{data.get('interceptions_per_90', 0)}", 
          f"{data.get('total_dribbles_succeeded', 0)}", f"{data.get('total_yellow_cards', 0)}", 
          f"{data.get('total_red_cards', 0)}"]],
        [38, 38, 38, 38, 38]
    )
    # ========================================================
    # GRAFIK PDF PLAYER (RADAR & RATING TREND BERDAMPINGAN)
    # ========================================================
    pdf.section_title("Performance Analysis")
    
    # 1. RADAR CHART (Sesuai Logika Web)
    radar_categories = ['Goals/90', 'Assists/90', 'Shot Acc.', 'Pass Acc.', 'Key Passes/90', 'Tackles/90', 'Dribble %']
    radar_values = [
        min(data.get('goals_per_90', 0) / 1.5, 1),
        min(data.get('assists_per_90', 0) / 1.0, 1),
        data.get('shot_accuracy', 0) / 100,
        data.get('avg_pass_accuracy', 0) / 100,
        min(data.get('key_passes_per_90', 0) / 4, 1),
        min(data.get('tackles_per_90', 0) / 4, 1),
        data.get('dribble_success_rate', 0) / 100
    ]
    radar_values.append(radar_values[0])
    radar_categories.append(radar_categories[0])

    fig_radar = go.Figure(data=[go.Scatterpolar(
        r=[v * 100 for v in radar_values], # Kalikan 100 sesuai web
        theta=radar_categories,
        fill='toself',
        fillcolor='rgba(67,233,123,0.2)',
        line=dict(color='#43e97b', width=2),
        name=player['name']
    )])
    
    fig_radar.update_layout(
        width=400, height=300,
        title='Radar Profile',
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], gridcolor='rgba(0,0,0,0.1)'),
            angularaxis=dict(gridcolor='rgba(0,0,0,0.1)')
        ),
        margin=dict(t=40, b=20, l=20, r=20),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(size=10, color='#000000'), showlegend=False
    )
    img_radar = save_chart_as_image(fig_radar)
    
    # 2. RATING TREND CHART (Sesuai Logika Web)
    ratings_data = data.get('ratings_trend', [])
    fig_rating = go.Figure()
    
    if ratings_data:
        match_labels = [f"Match {r['match_id']}" for r in ratings_data]
        ratings = [r['rating'] for r in ratings_data]
        
        fig_rating.add_trace(go.Scatter(
            x=match_labels, y=ratings, name='Rating', mode='lines+markers',
            line=dict(color='#3b82f6', width=3), marker=dict(size=8)
        ))
        
    avg_rating = data.get('avg_rating', 0)
    fig_rating.add_hline(
        y=avg_rating, line_dash='dash', line_color='#f59e0b', 
        annotation_text=f'Avg: {avg_rating}'
    )
    
    fig_rating.update_layout(
        width=400, height=300,
        title='Rating Trend',
        yaxis=dict(title='Rating', range=[4, 10]), # Range dikunci 4-10 seperti web
        margin=dict(t=40, b=30, l=40, r=20),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(size=10, color='#000000'), showlegend=False
    )
    img_rating = save_chart_as_image(fig_rating)    
    # 3. MASUKKAN KE PDF BERDAMPINGAN
    current_y = pdf.get_y()
    pdf.image(img_radar, x=15, y=current_y, w=95)
    pdf.image(img_rating, x=110, y=current_y, w=95)
    pdf.ln(40)
    
    
    # ========================================================
    # AI ANALYSIS SECTION
    # ========================================================
    analysis = generate_ai_player_analysis(data)
    if analysis:
        if pdf.get_y() > 220:
            pdf.add_page()
        pdf.section_header("Tactical Evaluation")
        for p in analysis.split("\n\n"):
            pdf.section_text(p)
    
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp.name)
    filename = f"Player_{player['name']}.pdf".replace(" ", "_")
    return send_file(temp.name, as_attachment=True, download_name=filename)

# ─── Utility Endpoints ───────────────────────────────────────────

@api_bp.route('/teams')
def list_teams():
    """List all teams."""
    teams = Team.query.order_by(Team.name).all()
    return jsonify([t.to_dict() for t in teams])


@api_bp.route('/players')
def list_players():
    """List all players."""
    players = Player.query.order_by(Player.name).all()
    return jsonify([p.to_dict() for p in players])


@api_bp.route('/matches')
def list_matches():
    """List all matches."""
    matches = Match.query.order_by(Match.date.desc()).all()
    return jsonify([m.to_dict() for m in matches])


@api_bp.route('/upload-history')
def upload_history():
    """Get upload history."""
    history = UploadHistory.query.order_by(UploadHistory.upload_date.desc()).limit(50).all()
    return jsonify([h.to_dict() for h in history])

# ═══════════════════════════════════════════════════════════════════════════════
# FINAL DELETE ENDPOINTS - COPY KE app/routes/api.py
# DELETE endpoints dengan proper database deletion yang benar-benar hapus
# ═══════════════════════════════════════════════════════════════════════════════

@api_bp.route('/delete/match/<int:match_id>', methods=['DELETE', 'POST'])
def delete_match(match_id):
    """🗑️ Delete a match and ALL related data - PERMANENT DELETION"""
    try:
        print(f"\n🗑️ DELETE MATCH: ID {match_id}")
        
        match = Match.query.get(match_id)
        if not match:
            print(f"❌ Match not found: {match_id}")
            return jsonify({'success': False, 'error': 'Match not found'}), 404
        
        match_info = f"{match.home_team.name if match.home_team else '?'} vs {match.away_team.name if match.away_team else '?'}"
        print(f"   Match: {match_info}")
        
        # Delete PlayerStats related to this match
        player_stats_count = PlayerStats.query.filter_by(match_id=match_id).count()
        print(f"   Deleting {player_stats_count} player stats records...")
        PlayerStats.query.filter_by(match_id=match_id).delete()
        
        # Delete MatchStats related to this match
        match_stats_count = MatchStats.query.filter_by(match_id=match_id).count()
        print(f"   Deleting {match_stats_count} match stats records...")
        MatchStats.query.filter_by(match_id=match_id).delete()
        
        # Delete the match itself
        print(f"   Deleting match record...")
        db.session.delete(match)
        
        # Commit ALL deletions
        db.session.commit()
        
        print(f"✅ Match {match_id} PERMANENTLY DELETED")
        return jsonify({
            'success': True, 
            'message': f'Match {match_info} has been permanently deleted'
        })
        
    except Exception as e:
        db.session.rollback()
        error_msg = str(e)
        print(f"❌ Delete match error: {error_msg}")
        return jsonify({'success': False, 'error': error_msg}), 500


@api_bp.route('/delete/player/<int:player_id>', methods=['DELETE', 'POST'])
def delete_player(player_id):
    """🗑️ Delete a player and ALL related data - PERMANENT DELETION"""
    try:
        print(f"\n🗑️ DELETE PLAYER: ID {player_id}")
        
        player = Player.query.get(player_id)
        if not player:
            print(f"❌ Player not found: {player_id}")
            return jsonify({'success': False, 'error': 'Player not found'}), 404
        
        player_name = player.name
        print(f"   Player: {player_name}")
        
        # Delete all player stats
        player_stats_count = PlayerStats.query.filter_by(player_id=player_id).count()
        print(f"   Deleting {player_stats_count} player stats records...")
        PlayerStats.query.filter_by(player_id=player_id).delete()
        
        # Delete the player
        print(f"   Deleting player record...")
        db.session.delete(player)
        
        # Commit ALL deletions
        db.session.commit()
        
        print(f"✅ Player {player_id} ({player_name}) PERMANENTLY DELETED")
        return jsonify({
            'success': True, 
            'message': f'Player {player_name} has been permanently deleted'
        })
        
    except Exception as e:
        db.session.rollback()
        error_msg = str(e)
        print(f"❌ Delete player error: {error_msg}")
        return jsonify({'success': False, 'error': error_msg}), 500


@api_bp.route('/delete/team/<int:team_id>', methods=['DELETE', 'POST'])
def delete_team(team_id):
    """🗑️ Delete a team and related data - WITH VALIDATION"""
    try:
        print(f"\n🗑️ DELETE TEAM: ID {team_id}")
        
        team = Team.query.get(team_id)
        if not team:
            print(f"❌ Team not found: {team_id}")
            return jsonify({'success': False, 'error': 'Team not found'}), 404
        
        team_name = team.name
        print(f"   Team: {team_name}")
        
        # Check if team has matches
        home_matches = Match.query.filter_by(home_team_id=team_id).count()
        away_matches = Match.query.filter_by(away_team_id=team_id).count()
        total_matches = home_matches + away_matches
        
        if total_matches > 0:
            error_msg = f'Cannot delete team with {total_matches} match records. Please delete related matches first.'
            print(f"❌ {error_msg}")
            return jsonify({
                'success': False, 
                'error': error_msg
            }), 400
        
        # Delete all players in this team
        players = Player.query.filter_by(team_id=team_id).all()
        for player in players:
            player_id = player.id
            print(f"   Deleting player: {player.name}")
            
            # Delete player stats
            PlayerStats.query.filter_by(player_id=player_id).delete()
            # Delete player
            db.session.delete(player)
        
        # Delete the team
        print(f"   Deleting team record...")
        db.session.delete(team)
        
        # Commit ALL deletions
        db.session.commit()
        
        print(f"✅ Team {team_id} ({team_name}) PERMANENTLY DELETED")
        return jsonify({
            'success': True, 
            'message': f'Team {team_name} has been permanently deleted'
        })
        
    except Exception as e:
        db.session.rollback()
        error_msg = str(e)
        print(f"❌ Delete team error: {error_msg}")
        return jsonify({'success': False, 'error': error_msg}), 500


# ═══════════════════════════════════════════════════════════════════════════════
# COLUMN MAPPING INFO ENDPOINT
# ═══════════════════════════════════════════════════════════════════════════════

@api_bp.route('/info/column-mapping')
def column_mapping_info():
    """📋 Provide complete column mapping information"""
    info = {
        'match_data': {
            'required': [
                {'name': 'date', 'description': 'Match date', 'format': '2024-01-15 or 15/01/2024'},
                {'name': 'home_team', 'description': 'Home team name', 'format': 'Arsenal'},
                {'name': 'away_team', 'description': 'Away team name', 'format': 'Chelsea'},
                {'name': 'home_goals', 'description': 'Goals scored by home team', 'format': '2'},
                {'name': 'away_goals', 'description': 'Goals scored by away team', 'format': '1'},
            ],
            'optional': [
                {'name': 'league', 'description': 'Competition name', 'format': 'Premier League'},
                {'name': 'season', 'description': 'Season', 'format': '2023/2024'},
                {'name': 'venue', 'description': 'Stadium name', 'format': 'Emirates Stadium'},
                {'name': 'referee', 'description': 'Match referee name', 'format': 'Andre Marriner'},
                {'name': 'home_goalscorers', 'description': 'Goal scorers comma-separated', 'format': 'Saka, Odegaard'},
                {'name': 'away_goalscorers', 'description': 'Goal scorers comma-separated', 'format': 'Mount'},
            ],
            'stats': [
                {'name': 'home_possession', 'description': 'Ball possession %'},
                {'name': 'away_possession', 'description': 'Ball possession %'},
                {'name': 'home_shots', 'description': 'Total shots'},
                {'name': 'away_shots', 'description': 'Total shots'},
                {'name': 'home_passes', 'description': 'Total passes'},
                {'name': 'away_passes', 'description': 'Total passes'},
                {'name': 'home_tackles', 'description': 'Tackles made'},
                {'name': 'away_tackles', 'description': 'Tackles made'},
                {'name': 'home_xg', 'description': 'Expected Goals'},
                {'name': 'away_xg', 'description': 'Expected Goals'},
            ],
            'penalties': [
                {'name': 'has_penalties', 'description': 'Whether match had penalty shootout', 'format': 'true/false'},
                {'name': 'home_penalty_takers', 'description': 'Penalty takers format', 'format': '"Name (g), Name (x)"'},
                {'name': 'away_penalty_takers', 'description': 'Penalty takers format', 'format': '"Name (g), Name (x)"'},
                {'name': 'home_penalties_scored', 'description': 'Penalties scored by home'},
                {'name': 'away_penalties_scored', 'description': 'Penalties scored by away'},
            ]
        },
        'player_data': {
            'required': [
                {'name': 'name', 'description': 'Player name', 'format': 'Mohamed Salah'},
                {'name': 'team', 'description': 'Team name (must match existing team)', 'format': 'Liverpool'},
            ],
            'optional': [
                {'name': 'position', 'description': 'Player position', 'format': 'RW'},
                {'name': 'nationality', 'description': 'Player nationality', 'format': 'Egypt'},
                {'name': 'shirt_number', 'description': 'Jersey number', 'format': '11'},
                {'name': 'match_id', 'description': 'Match ID (if linking to match)', 'format': '1'},
            ],
            'stats': [
                {'name': 'minutes_played', 'description': 'Minutes in match'},
                {'name': 'rating', 'description': 'Match rating', 'format': '0-10'},
                {'name': 'goals', 'description': 'Goals scored'},
                {'name': 'assists', 'description': 'Assists provided'},
                {'name': 'passes', 'description': 'Passes completed'},
                {'name': 'pass_accuracy', 'description': 'Pass accuracy %'},
                {'name': 'shots', 'description': 'Shots attempted'},
                {'name': 'shots_on_target', 'description': 'Shots on target'},
                {'name': 'tackles', 'description': 'Tackles made'},
                {'name': 'interceptions', 'description': 'Interceptions'},
                {'name': 'blocks', 'description': 'Blocks made'},
                {'name': 'clearances', 'description': 'Clearances'},
                {'name': 'fouls_committed', 'description': 'Fouls committed'},
                {'name': 'fouls_drawn', 'description': 'Fouls drawn'},
                {'name': 'yellow_cards', 'description': 'Yellow cards'},
                {'name': 'red_cards', 'description': 'Red cards'},
                {'name': 'dribbles_attempted', 'description': 'Dribbles attempted'},
                {'name': 'dribbles_succeeded', 'description': 'Dribbles succeeded'},
                {'name': 'key_passes', 'description': 'Key passes'},
                {'name': 'crosses', 'description': 'Crosses attempted'},
            ]
        }
    }
    return jsonify(info)


# ═══════════════════════════════════════════════════════════════════════════════
# DOWNLOAD TEMPLATE ENDPOINT
# ═══════════════════════════════════════════════════════════════════════════════

@api_bp.route('/info/download-template/<template_type>')
def download_template(template_type):
    """📥 Download CSV template for match or player data"""
    import csv
    import tempfile
    
    if template_type == 'match':
        headers = [
            'date', 'home_team', 'away_team', 'home_goals', 'away_goals',
            'league', 'season', 'venue', 'referee',
            'home_possession', 'away_possession',
            'home_shots', 'away_shots', 'home_passes', 'away_passes'
        ]
        sample_rows = [
            ['2024-01-15', 'Arsenal', 'Chelsea', '2', '1',
             'Premier League', '2023/2024', 'Emirates Stadium', 'Andre Marriner',
             '55', '45', '18', '12', '520', '480'],
            ['2024-01-16', 'Liverpool', 'Manchester City', '1', '1',
             'Premier League', '2023/2024', 'Anfield', 'Stuart Attwell',
             '48', '52', '15', '16', '480', '540']
        ]
        filename = 'template_match_data.csv'
        
    elif template_type == 'player':
        headers = [
            'name', 'team', 'position', 'nationality', 'shirt_number',
            'match_id', 'minutes_played', 'rating',
            'goals', 'assists', 'passes', 'pass_accuracy', 'shots'
        ]
        sample_rows = [
            ['Mohamed Salah', 'Liverpool', 'RW', 'Egypt', '11',
             '1', '90', '8.2', '1', '1', '45', '85', '5'],
            ['Bukayo Saka', 'Arsenal', 'RW', 'England', '7',
             '1', '85', '7.8', '0', '2', '42', '82', '4']
        ]
        filename = 'template_player_data.csv'
    else:
        return "Invalid template type", 400
    
    # Create CSV file
    temp = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='')
    writer = csv.writer(temp)
    writer.writerow(headers)
    for row in sample_rows:
        writer.writerow(row)
    temp.close()
    
    return send_file(
        temp.name,
        as_attachment=True,
        download_name=filename,
        mimetype='text/csv'
    )