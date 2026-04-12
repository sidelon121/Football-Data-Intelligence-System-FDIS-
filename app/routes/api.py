"""
FDIS REST API Routes
JSON API endpoints for data operations.
"""
import os
import json
from flask import Blueprint, request, jsonify, current_app, send_file
from werkzeug.utils import secure_filename
from app.models import Team, Player, Match, UploadHistory
from app import db

api_bp = Blueprint('api', __name__)


def allowed_file(filename):
    """Check if file extension is allowed."""
    allowed = current_app.config.get('ALLOWED_EXTENSIONS', {'csv', 'xlsx', 'xls'})
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed


# ─── Upload Endpoints ─────────────────────────────────────────────

@api_bp.route('/upload', methods=['POST'])
def upload_file():
    """Handle CSV/Excel file upload."""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'success': False, 'error': 'File type not allowed. Use CSV or Excel files.'}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Process the uploaded data file
    from app.ingestion.csv_handler import process_uploaded_file

    data_type = request.form.get('data_type', 'auto')
    result = process_uploaded_file(filepath, filename, data_type=data_type)

    status_code = 200 if result.get('success') else 400
    response_data = {
        'success': result.get('success', False),
        'data_type': result.get('data_type', data_type),
        'rows_processed': result.get('rows_processed', 0),
        'rows_failed': result.get('rows_failed', 0),
        'errors': result.get('errors', [])[:5],
        'message': result.get('message', '') or (
            f"Successfully processed {result.get('rows_processed', 0)} rows of {result.get('data_type', 'data')}.")
    }

    return jsonify(response_data), status_code


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

@api_bp.route('/stats/team/<int:team_id>')
def team_stats(team_id):
    """Get team statistics."""
    from app.engine.statistics import get_team_overview
    data = get_team_overview(team_id)
    if not data:
        return jsonify({'error': 'Team not found'}), 404
    return jsonify(data)


@api_bp.route('/stats/player/<int:player_id>')
def player_stats(player_id):
    """Get player statistics."""
    from app.engine.statistics import get_player_overview
    data = get_player_overview(player_id)
    if not data:
        return jsonify({'error': 'Player not found'}), 404
    return jsonify(data)


@api_bp.route('/stats/match/<int:match_id>')
def match_stats(match_id):
    """Get match statistics."""
    from app.engine.statistics import get_match_analysis
    data = get_match_analysis(match_id)
    if not data:
        return jsonify({'error': 'Match not found'}), 404
    return jsonify(data)


@api_bp.route('/stats/league-table')
def league_table():
    """Get league table standings."""
    from app.engine.statistics import get_league_table
    league = request.args.get('league')
    season = request.args.get('season')
    table = get_league_table(league=league, season=season)
    return jsonify(table)


# ─── Chart Endpoints ──────────────────────────────────────────────

@api_bp.route('/chart/team-radar/<int:team_id>')
def chart_team_radar(team_id):
    """Get team radar chart JSON."""
    from app.engine.visualizations import chart_team_radar
    chart = chart_team_radar(team_id)
    if not chart:
        return jsonify({'error': 'No data'}), 404
    return jsonify(chart)


@api_bp.route('/chart/team-form/<int:team_id>')
def chart_team_form(team_id):
    """Get team form chart JSON."""
    from app.engine.visualizations import chart_team_form
    chart = chart_team_form(team_id)
    if not chart:
        return jsonify({'error': 'No data'}), 404
    return jsonify(chart)


@api_bp.route('/chart/match/<int:match_id>')
def chart_match(match_id):
    """Get match comparison chart JSON."""
    from app.engine.visualizations import chart_match_comparison
    chart = chart_match_comparison(match_id)
    if not chart:
        return jsonify({'error': 'No data'}), 404
    return jsonify(chart)


@api_bp.route('/chart/player-radar/<int:player_id>')
def chart_player_radar(player_id):
    """Get player radar chart JSON."""
    from app.engine.visualizations import chart_player_radar
    chart = chart_player_radar(player_id)
    if not chart:
        return jsonify({'error': 'No data'}), 404
    return jsonify(chart)


# ─── Analysis Endpoints ──────────────────────────────────────────

@api_bp.route('/analysis/match/<int:match_id>')
def analysis_match(match_id):
    """Get auto-generated match analysis text."""
    from app.engine.nlg import generate_match_summary
    text = generate_match_summary(match_id)
    return jsonify({'analysis': text})


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

@api_bp.route('/compare')
def compare():
    """Compare two teams or players."""
    compare_type = request.args.get('type', 'team')
    id1 = request.args.get('id1', type=int)
    id2 = request.args.get('id2', type=int)

    if not id1 or not id2:
        return jsonify({'error': 'Both id1 and id2 are required'}), 400

    if compare_type == 'team':
        from app.engine.statistics import get_team_comparison
        from app.engine.visualizations import chart_comparison_radar
        from app.engine.nlg import generate_comparison_narrative

        data = get_team_comparison(id1, id2)
        chart = chart_comparison_radar(id1, id2)
        narrative = generate_comparison_narrative(id1, id2)

        if not data:
            return jsonify({'error': 'Teams not found'}), 404

        return jsonify({
            'comparison': data,
            'chart': chart,
            'narrative': narrative,
        })
    elif compare_type == 'player':
        from app.engine.statistics import get_player_comparison
        data = get_player_comparison(id1, id2)
        if not data:
            return jsonify({'error': 'Players not found'}), 404
        return jsonify({'comparison': data})

    return jsonify({'error': 'Invalid comparison type'}), 400


# ─── Export Endpoints ─────────────────────────────────────────────

@api_bp.route('/export/pdf/team/<int:team_id>')
def export_team_pdf(team_id):
    """Download team report as PDF."""
    from app.engine.reports import generate_team_report_pdf
    pdf_bytes = generate_team_report_pdf(team_id)
    if not pdf_bytes:
        return jsonify({'error': 'Could not generate report'}), 404

    team = Team.query.get(team_id)
    filename = f"FDIS_{team.name.replace(' ', '_')}_Report.pdf" if team else 'report.pdf'

    reports_dir = current_app.config['REPORTS_FOLDER']
    filepath = os.path.join(reports_dir, filename)
    with open(filepath, 'wb') as f:
        f.write(pdf_bytes)

    return send_file(filepath, as_attachment=True, download_name=filename)


@api_bp.route('/export/pdf/player/<int:player_id>')
def export_player_pdf(player_id):
    """Download player report as PDF."""
    from app.engine.reports import generate_player_report_pdf
    pdf_bytes = generate_player_report_pdf(player_id)
    if not pdf_bytes:
        return jsonify({'error': 'Could not generate report'}), 404

    player = Player.query.get(player_id)
    filename = f"FDIS_{player.name.replace(' ', '_')}_Report.pdf" if player else 'report.pdf'
    reports_dir = current_app.config['REPORTS_FOLDER']
    filepath = os.path.join(reports_dir, filename)
    with open(filepath, 'wb') as f:
        f.write(pdf_bytes)

    return send_file(filepath, as_attachment=True, download_name=filename)


@api_bp.route('/export/pdf/match/<int:match_id>')
def export_match_pdf(match_id):
    """Download match report as PDF."""
    from app.engine.reports import generate_match_report_pdf
    pdf_bytes = generate_match_report_pdf(match_id)
    if not pdf_bytes:
        return jsonify({'error': 'Could not generate report'}), 404

    filename = f'FDIS_Match_{match_id}_Report.pdf'
    reports_dir = current_app.config['REPORTS_FOLDER']
    filepath = os.path.join(reports_dir, filename)
    with open(filepath, 'wb') as f:
        f.write(pdf_bytes)

    return send_file(filepath, as_attachment=True, download_name=filename)


@api_bp.route('/export/pptx/team/<int:team_id>')
def export_team_pptx(team_id):
    """Download team report as PowerPoint."""
    from app.engine.reports import generate_team_report_pptx
    pptx_bytes = generate_team_report_pptx(team_id)
    if not pptx_bytes:
        return jsonify({'error': 'Could not generate report'}), 404

    team = Team.query.get(team_id)
    filename = f"FDIS_{team.name.replace(' ', '_')}_Report.pptx" if team else 'report.pptx'

    reports_dir = current_app.config['REPORTS_FOLDER']
    filepath = os.path.join(reports_dir, filename)
    with open(filepath, 'wb') as f:
        f.write(pptx_bytes)

    return send_file(filepath, as_attachment=True, download_name=filename)


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
