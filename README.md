# Football Data Intelligence System (FDIS)

FDIS is a Flask-based web application for ingesting football match and player data, generating interactive visualizations, and producing automated data-driven analysis.

## Features

- CSV/Excel upload for match and player data
- Manual match entry form
- API-Football integration for automated fixture and stats import
- Interactive dashboards and performance charts powered by Plotly
- Auto-generated match/team/player narratives
- Export reports to PDF and PowerPoint
- Upload history tracking

## Getting Started

### Requirements

- Python 3.11+
- Install dependencies:

```bash
pip install -r requirements.txt
```

### Run the app

```bash
set FLASK_CONFIG=development
set API_FOOTBALL_KEY=your_api_key_here
python run.py
```

Open `http://127.0.0.1:5000` in your browser.

## Upload Templates

A sample upload template is available at `/static/uploads/sample_template.csv`.

## Project Structure

- `app/` — Flask application package
- `app/ingestion/` — data ingestion modules for CSV, API, manual input, and database sources
- `app/engine/` — analytics, visualization, natural language generation, and report export engines
- `app/routes/` — web page and API route definitions
- `app/templates/` — HTML templates
- `app/static/` — CSS, JavaScript, and uploaded files
- `config.py` — application configuration

## Notes

- Configure `API_FOOTBALL_KEY` to use API import features.
- Use the upload page to import match data and view team/player dashboards.
- The report export links are available on team and player pages.
