"""
FDIS Visualization Engine
Generates Plotly chart JSON data for frontend rendering.
"""
import plotly.graph_objects as go
import plotly.express as px
import json
from app.engine.statistics import (
    get_team_overview, get_match_analysis, get_player_overview,
    get_league_table, get_team_performance_trend, get_dashboard_summary
)
from app.models import Team, Player, Match, MatchStats, PlayerStats


def _fig_to_json(fig):
    """Convert a Plotly figure to JSON string for frontend."""
    return json.loads(fig.to_json())


# ─── Color Palette ────────────────────────────────────────────────
COLORS = {
    'primary': '#667eea',
    'secondary': '#764ba2',
    'accent': '#43e97b',
    'warning': '#f5af19',
    'danger': '#f85149',
    'info': '#58a6ff',
    'surface': '#161b22',
    'text': '#e6edf3',
    'gradient': ['#667eea', '#764ba2', '#43e97b', '#f5af19', '#58a6ff', '#f85149'],
}

CHART_LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family='Inter, sans-serif', color=COLORS['text'], size=13),
    margin=dict(l=40, r=20, t=50, b=40),
    legend=dict(
        bgcolor='rgba(22,27,34,0.8)',
        bordercolor='rgba(255,255,255,0.1)',
        borderwidth=1,
    ),
    xaxis=dict(gridcolor='rgba(255,255,255,0.06)', zerolinecolor='rgba(255,255,255,0.1)'),
    yaxis=dict(gridcolor='rgba(255,255,255,0.06)', zerolinecolor='rgba(255,255,255,0.1)'),
)


# ─── Team Charts ──────────────────────────────────────────────────

def chart_team_radar(team_id):
    """Radar/spider chart showing multi-metric team profile."""
    data = get_team_overview(team_id)
    if not data or data.get('matches_played', 0) == 0:
        return None

    categories = ['Possession', 'Shots', 'Pass Acc.', 'xG', 'Tackles', 'Interceptions', 'Corners']
    values = [
        data['avg_possession'] / 100,
        min(data['avg_shots'] / 25, 1),
        data['avg_pass_accuracy'] / 100,
        min(data['avg_xg'] / 3, 1),
        min(data['avg_tackles'] / 30, 1),
        min(data['avg_interceptions'] / 20, 1),
        min(data['avg_corners'] / 12, 1),
    ]
    values.append(values[0])  # Close the radar
    categories.append(categories[0])

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=[v * 100 for v in values],
        theta=categories,
        fill='toself',
        fillcolor=f'rgba(102,126,234,0.25)',
        line=dict(color=COLORS['primary'], width=2),
        name=data['team']['name'],
    ))
    fig.update_layout(
        **CHART_LAYOUT,
        title=dict(text=f"{data['team']['name']} — Performance Profile", font=dict(size=16)),
        polar=dict(
            bgcolor='rgba(0,0,0,0)',
            radialaxis=dict(visible=True, range=[0, 100], gridcolor='rgba(255,255,255,0.1)', tickfont=dict(size=10)),
            angularaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
        ),
        showlegend=False,
    )
    return _fig_to_json(fig)


def chart_team_form(team_id):
    """Bar chart showing results of recent matches (W/D/L with goals)."""
    trend = get_team_performance_trend(team_id, last_n=10)
    if not trend:
        return None

    data = trend['trend']
    dates = [d['date'] for d in data]
    opponents = [d['opponent'] for d in data]
    goals_for = [d['goals_for'] for d in data]
    goals_against = [d['goals_against'] for d in data]
    results = [d['result'] for d in data]
    colors = [COLORS['accent'] if r == 'W' else (COLORS['warning'] if r == 'D' else COLORS['danger'])
              for r in results]

    labels = [f"vs {opp}" for opp in opponents]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=labels, y=goals_for, name='Goals Scored',
        marker_color=COLORS['primary'], text=goals_for, textposition='inside',
    ))
    fig.add_trace(go.Bar(
        x=labels, y=[-g for g in goals_against], name='Goals Conceded',
        marker_color=COLORS['danger'], text=goals_against, textposition='inside',
    ))

    fig.update_layout(
        **CHART_LAYOUT,
        title=dict(text=f"{trend['team']['name']} — Recent Form", font=dict(size=16)),
        barmode='relative',
        xaxis=dict(title='', tickangle=-30),
        yaxis=dict(title='Goals'),
    )
    return _fig_to_json(fig)


def chart_team_trend_lines(team_id):
    """Line chart showing performance metrics over time."""
    trend = get_team_performance_trend(team_id, last_n=15)
    if not trend:
        return None

    data = trend['trend']
    dates = [d['date'] for d in data]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, y=[d['possession'] for d in data], name='Possession %',
        line=dict(color=COLORS['primary'], width=2), mode='lines+markers',
    ))
    fig.add_trace(go.Scatter(
        x=dates, y=[d['pass_accuracy'] for d in data], name='Pass Accuracy %',
        line=dict(color=COLORS['accent'], width=2), mode='lines+markers',
    ))
    fig.add_trace(go.Scatter(
        x=dates, y=[d['xg'] * 20 for d in data], name='xG (×20)',
        line=dict(color=COLORS['warning'], width=2, dash='dot'), mode='lines+markers',
    ))

    fig.update_layout(
        **CHART_LAYOUT,
        title=dict(text=f"{trend['team']['name']} — Performance Trends", font=dict(size=16)),
        xaxis=dict(title='Match Date'),
        yaxis=dict(title='Value'),
    )
    return _fig_to_json(fig)


# ─── Match Charts ─────────────────────────────────────────────────

def chart_match_comparison(match_id):
    """Horizontal bar chart comparing two teams' stats in a match."""
    analysis = get_match_analysis(match_id)
    if not analysis or 'metrics' not in analysis:
        return None

    metrics = analysis['metrics']
    match_info = analysis['match']
    home_name = match_info['home_team']['name']
    away_name = match_info['away_team']['name']

    labels = []
    home_vals = []
    away_vals = []

    for key, metric in metrics.items():
        labels.append(metric['label'])
        home_vals.append(metric['home'])
        away_vals.append(metric['away'])

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=labels, x=home_vals, name=home_name, orientation='h',
        marker_color=COLORS['primary'], text=[f"{v}" for v in home_vals],
        textposition='inside',
    ))
    fig.add_trace(go.Bar(
        y=labels, x=[-v for v in away_vals], name=away_name, orientation='h',
        marker_color=COLORS['danger'], text=[f"{v}" for v in away_vals],
        textposition='inside',
    ))

    fig.update_layout(
        **CHART_LAYOUT,
        title=dict(
            text=f"{home_name} {match_info['home_goals']}–{match_info['away_goals']} {away_name}",
            font=dict(size=16),
        ),
        barmode='relative',
        yaxis=dict(autorange='reversed'),
        height=450,
    )
    return _fig_to_json(fig)


# ─── Player Charts ────────────────────────────────────────────────

def chart_player_radar(player_id):
    """Radar chart for player multi-metric profile."""
    data = get_player_overview(player_id)
    if not data or data.get('matches_played', 0) == 0:
        return None

    categories = ['Goals/90', 'Assists/90', 'Shot Acc.', 'Pass Acc.', 'Key Passes/90',
                  'Tackles/90', 'Dribble %']
    values = [
        min(data['goals_per_90'] / 1.5, 1),
        min(data['assists_per_90'] / 1.0, 1),
        data['shot_accuracy'] / 100,
        data['avg_pass_accuracy'] / 100,
        min(data['key_passes_per_90'] / 4, 1),
        min(data['tackles_per_90'] / 4, 1),
        data['dribble_success_rate'] / 100,
    ]
    values.append(values[0])
    categories.append(categories[0])

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=[v * 100 for v in values],
        theta=categories,
        fill='toself',
        fillcolor='rgba(67,233,123,0.2)',
        line=dict(color=COLORS['accent'], width=2),
        name=data['player']['name'],
    ))
    fig.update_layout(
        **CHART_LAYOUT,
        title=dict(text=f"{data['player']['name']} — Player Profile", font=dict(size=16)),
        polar=dict(
            bgcolor='rgba(0,0,0,0)',
            radialaxis=dict(visible=True, range=[0, 100], gridcolor='rgba(255,255,255,0.1)'),
            angularaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
        ),
        showlegend=False,
    )
    return _fig_to_json(fig)


def chart_player_rating_trend(player_id):
    """Line chart showing player rating over matches."""
    data = get_player_overview(player_id)
    if not data or data.get('matches_played', 0) == 0:
        return None

    ratings_data = data.get('ratings_trend', [])
    if not ratings_data:
        return None

    match_labels = [f"Match {r['match_id']}" for r in ratings_data]
    ratings = [r['rating'] for r in ratings_data]
    avg_rating = data['avg_rating']

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=match_labels, y=ratings, name='Rating',
        line=dict(color=COLORS['primary'], width=3),
        mode='lines+markers',
        marker=dict(size=8),
    ))
    fig.add_hline(y=avg_rating, line_dash='dash',
                  line_color=COLORS['warning'],
                  annotation_text=f'Avg: {avg_rating}')

    fig.update_layout(
        **CHART_LAYOUT,
        title=dict(text=f"{data['player']['name']} — Rating Trend", font=dict(size=16)),
        yaxis=dict(title='Rating', range=[4, 10]),
    )
    return _fig_to_json(fig)


# ─── Comparison Charts ────────────────────────────────────────────

def chart_comparison_radar(team_id_1, team_id_2):
    """Dual radar chart comparing two teams."""
    from app.engine.statistics import get_team_comparison
    comp = get_team_comparison(team_id_1, team_id_2)
    if not comp:
        return None

    s1, s2 = comp['team1'], comp['team2']
    categories = ['Win Rate', 'Possession', 'Pass Acc.', 'Shots', 'xG', 'Tackles', 'Clean Sheet %']

    def normalize(val, max_val):
        return min(val / max_val * 100, 100) if max_val > 0 else 0

    vals1 = [
        s1['win_rate'], s1['avg_possession'], s1['avg_pass_accuracy'],
        normalize(s1['avg_shots'], 25), normalize(s1['avg_xg'], 3) * 100 / 100 * s1['avg_xg'] / 3 * 100 if s1['avg_xg'] else 0,
        normalize(s1['avg_tackles'], 30), s1['clean_sheet_rate'],
    ]
    vals2 = [
        s2['win_rate'], s2['avg_possession'], s2['avg_pass_accuracy'],
        normalize(s2['avg_shots'], 25), normalize(s2['avg_xg'], 3) * 100 / 100 * s2['avg_xg'] / 3 * 100 if s2['avg_xg'] else 0,
        normalize(s2['avg_tackles'], 30), s2['clean_sheet_rate'],
    ]

    vals1.append(vals1[0])
    vals2.append(vals2[0])
    categories.append(categories[0])

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=vals1, theta=categories, fill='toself',
        fillcolor='rgba(102,126,234,0.2)', line=dict(color=COLORS['primary'], width=2),
        name=s1['team']['name'],
    ))
    fig.add_trace(go.Scatterpolar(
        r=vals2, theta=categories, fill='toself',
        fillcolor='rgba(248,81,73,0.2)', line=dict(color=COLORS['danger'], width=2),
        name=s2['team']['name'],
    ))
    fig.update_layout(
        **CHART_LAYOUT,
        title=dict(text=f"{s1['team']['name']} vs {s2['team']['name']}", font=dict(size=16)),
        polar=dict(
            bgcolor='rgba(0,0,0,0)',
            radialaxis=dict(visible=True, range=[0, 100], gridcolor='rgba(255,255,255,0.1)'),
            angularaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
        ),
    )
    return _fig_to_json(fig)


# ─── Dashboard Charts ────────────────────────────────────────────

def chart_goals_distribution():
    """Bar chart of goals scored by each team."""
    table = get_league_table()
    if not table:
        return None

    teams = [t['team_name'] for t in table]
    goals_for = [t['goals_for'] for t in table]
    goals_against = [t['goals_against'] for t in table]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=teams, y=goals_for, name='Goals Scored',
        marker=dict(color=COLORS['accent'], line=dict(width=0)),
    ))
    fig.add_trace(go.Bar(
        x=teams, y=goals_against, name='Goals Conceded',
        marker=dict(color=COLORS['danger'], line=dict(width=0)),
    ))
    fig.update_layout(
        **CHART_LAYOUT,
        title=dict(text='Goals Scored vs Conceded', font=dict(size=16)),
        barmode='group',
        xaxis=dict(tickangle=-30),
    )
    return _fig_to_json(fig)


def chart_points_bar():
    """Horizontal bar chart of team points."""
    table = get_league_table()
    if not table:
        return None

    teams = [t['team_name'] for t in reversed(table)]
    points = [t['points'] for t in reversed(table)]

    colors = [COLORS['gradient'][i % len(COLORS['gradient'])] for i in range(len(teams))]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=teams, x=points, orientation='h',
        marker=dict(color=list(reversed(colors))),
        text=points, textposition='inside',
    ))
    fig.update_layout(
        **CHART_LAYOUT,
        title=dict(text='League Standings — Points', font=dict(size=16)),
        showlegend=False,
        height=max(300, len(teams) * 50),
    )
    return _fig_to_json(fig)


def chart_win_rate_donut():
    """Donut chart showing win/draw/loss distribution across all matches."""
    table = get_league_table()
    if not table:
        return None

    total_wins = sum(t['wins'] for t in table)
    total_draws = sum(t['draws'] for t in table)
    total_losses = sum(t['losses'] for t in table)

    # Since each match produces one win+loss or two draws, normalize
    fig = go.Figure(data=[go.Pie(
        labels=['Home Wins', 'Away Wins', 'Draws'],
        values=[total_wins, total_losses, total_draws],
        hole=0.55,
        marker=dict(colors=[COLORS['primary'], COLORS['danger'], COLORS['warning']]),
        textinfo='label+percent',
        textfont=dict(size=13),
    )])
    fig.update_layout(
        **CHART_LAYOUT,
        title=dict(text='Match Outcome Distribution', font=dict(size=16)),
        showlegend=True,
    )
    return _fig_to_json(fig)
