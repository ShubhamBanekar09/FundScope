# FundScope

FundScope is a Flask-based mutual fund recommendation and insights platform. It includes user authentication, dashboard views, AI-assisted fund recommendations, chatbot support, and news integration.

## Features

- User registration, login, and session-based authentication
- Dashboard and comparison pages for mutual fund data
- AI-driven fund recommendations based on user profile, risk, and investment horizon
- Gemini chatbot integration for finance-related questions
- News provider configuration and scraping support
- SQLite database initialization on startup

## Repository Structure

- `run.py` - application entry point
- `config.py` - environment-based app configuration
- `app/` - main Flask application package
  - `routes/` - web routes and blueprints
  - `dbconfig/` - database models and extensions
  - `src/` - recommendation engine logic and ML helpers
  - `static/` - static assets, datasets, and styles
  - `templates/` - HTML templates
- `requirements.txt` - Python dependencies

## Requirements

- Python 3.11+ (recommended)
- `pip`

## Installation

1. Clone the repository:

```bash
git clone <repo-url>
cd FundScope
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root with values like:

```env
DEBUG=true
SECRET_KEY=your-secret-key
NEWS_TOPIC=mutual fund india
NEWS_LIMIT=7
NEWS_API_KEY=
NEWS_API_PROVIDER=newsapi
NEWS_LANGUAGE=en
```

Create `app/chatbot.env` for Gemini configuration:

```env
GEMINI_API_KEY=your-gemini-api-key
```

## Running the App

Start the application with:

```bash
python run.py
```

Then open:

- `http://127.0.0.1:5000/`

The app will initialize an SQLite database file named `fundscope.db` automatically in the project root.

## Notes

- If `GEMINI_API_KEY` is missing or invalid, the chatbot API will return an offline error.
- The Flask app uses `DEBUG` mode value from `.env`.
- The AI recommendation endpoint reads data from `app/static/dataset/cleandata/final_cleaned_fundsnumeric.csv`.

## GitHub Workflow

1. Check repository status:

```bash
git status
```

2. Stage changes:

```bash
git add .
```

3. Commit:

```bash
git commit -m "Add README and project documentation"
```

4. Push:

```bash
git push origin <branch-name>
```

---

Enjoy using FundScope!