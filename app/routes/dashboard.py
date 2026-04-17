from datetime import datetime
import os
import pandas as pd
import numpy as np
from flask import Blueprint, render_template, current_app, request, jsonify, session 
from werkzeug.utils import secure_filename
from app.services.news_service import NewsService
from app.utils import login_required
from app.dbconfig.extensions import db
from app.dbconfig.models import Favorite

dashboard_bp = Blueprint("dashboard", __name__)

# Lazy load CSV to avoid blocking app startup
_df_funds = None

def get_funds_data():
    global _df_funds
    if _df_funds is None:
        csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'dataset', 'cleandata', 'final_cleaned_fundsnumeric.csv')
        try:
            _df_funds = pd.read_csv(csv_path)
            _df_funds = _df_funds.replace({np.nan: None})
        except Exception as e:
            _df_funds = pd.DataFrame()
            print(f"Error loading final_cleaned_fundsnumeric.csv: {e}")
    return _df_funds

def get_news_service():
    return NewsService(
        topic=current_app.config["NEWS_TOPIC"],
        page_size=current_app.config["NEWS_LIMIT"],
        api_key=current_app.config["NEWS_API_KEY"],
        api_provider=current_app.config["NEWS_API_PROVIDER"],
        language=current_app.config["NEWS_LANGUAGE"],
    ) 

def get_factsheet_stats():
    base_dir = os.path.join(current_app.root_path, 'static', 'factsheets')
    amc_count = 0
    pdf_count = 0
    if os.path.exists(base_dir):
        for amc in os.listdir(base_dir):
            amc_path = os.path.join(base_dir, amc)
            if os.path.isdir(amc_path):
                amc_count += 1
                pdf_count += len([f for f in os.listdir(amc_path) if f.lower().endswith('.pdf')])
    return amc_count, pdf_count

@dashboard_bp.route("/dashboard")
def dashboard():
    news_service = get_news_service()
    categories = news_service.get_news_by_category()
    default_category = next(
        (name for name, items in categories.items() if items),
        next(iter(categories.keys()), "Large Cap"),
    )
    default_articles = categories.get(default_category, [])
    featured_article = default_articles[0] if default_articles else {
        "title": f"{default_category} mutual fund updates",
        "summary": "Live mutual-fund headlines will appear here when relevant stories are available.",
        "link": "#",
    }
    total_articles = sum(len(items) for items in categories.values())
    
    total_amcs, total_factsheets = get_factsheet_stats()

    return render_template(
        "dashboard/index.html",
        categories=categories,
        default_category=default_category,
        featured_article=featured_article,
        total_articles=total_articles,
        total_amcs=total_amcs,
        total_factsheets=total_factsheets,
        status_message=news_service.status_message,
        refreshed_at=datetime.now().strftime("%d %b %Y, %I:%M %p"),
    )

@dashboard_bp.route("/factsheets")
def factsheets():
    base_dir = os.path.join(current_app.root_path, 'static', 'factsheets')
    amc_data = {}
    if os.path.exists(base_dir):
        for amc in sorted(os.listdir(base_dir)):
            amc_path = os.path.join(base_dir, amc)
            if os.path.isdir(amc_path):
                files = [f for f in sorted(os.listdir(amc_path)) if f.lower().endswith('.pdf')]
                if files:
                    amc_data[amc] = files
    return render_template("dashboard/factsheets.html", amc_data=amc_data, page_title="Factsheets", page_desc="View and download comprehensive factsheets across all tracked mutual funds.")

@dashboard_bp.route("/factsheets/upload", methods=["POST"])
def upload_factsheet():
    if 'factsheet_file' not in request.files:
        return jsonify({"success": False, "error": "No file uploaded"})
    
    file = request.files['factsheet_file']
    amc_name = request.form.get('amc_name', '').strip()
    
    if not file or not file.filename:
         return jsonify({"success": False, "error": "No file selected"})
    if not amc_name:
         return jsonify({"success": False, "error": "AMC name is required"})
    if not file.filename.lower().endswith('.pdf'):
         return jsonify({"success": False, "error": "Only PDF files are allowed"})
         
    safe_amc_name = secure_filename(amc_name)
    base_dir = os.path.join(current_app.root_path, 'static', 'factsheets', safe_amc_name)
    os.makedirs(base_dir, exist_ok=True)
    
    filename = secure_filename(file.filename)
    file.save(os.path.join(base_dir, filename))
    
    return jsonify({"success": True})

from flask import render_template, request, jsonify, session
# Make sure you have your blueprint, db, and Favorite model imported

@dashboard_bp.route("/favorites")
@login_required
def favorites():
    user_id = session.get('user_id')
    
    # 1. Fetch the user's saved fund names from the SQLite Database
    fav_records = Favorite.query.filter_by(user_id=user_id).all()
    fav_fund_names = [fav.fund_id for fav in fav_records]

    favorite_funds_list = []

    # 2. Filter your CSV/Pandas DataFrame to only show the funds they saved
    df_funds = get_funds_data()
    if not df_funds.empty and fav_fund_names:
        # Match the 'scheme_name' column with the user's saved list
        filtered_df = df_funds[df_funds['scheme_name'].isin(fav_fund_names)]
        
        # Select key columns to display on the UI cards
        cols_to_keep = ['scheme_name', 'category', 'returns_1yr', 'returns_3yr', 'risk_level']
        available_cols = [col for col in cols_to_keep if col in filtered_df.columns]
        
        # Convert it to a dictionary so Jinja2 HTML can read it easily
        favorite_funds_list = filtered_df[available_cols].to_dict(orient='records')

    # 3. Render the correct HTML file!
    return render_template(
        "dashboard/favorites.html", 
        favorite_funds=favorite_funds_list, 
        page_title="My Watchlist", 
        page_desc="Manage your bookmarked mutual funds and analyze your customized portfolio."
    )



# 2. The API Route (Handles the frontend JavaScript clicking logic)
@dashboard_bp.route("/api/toggle_favorite", methods=["POST"])
@login_required
def toggle_favorite():
    user_id = session.get('user_id')
    data = request.json
    
    # We will pass the exact name of the mutual fund from the frontend
    fund_name = data.get('fund_id') 

    if not fund_name:
        return jsonify({"error": "Fund ID is required"}), 400

    # Look for an existing favorite for this user and this specific fund
    existing_fav = Favorite.query.filter_by(user_id=user_id, fund_id=fund_name).first()
    
    if existing_fav:
        # If it exists, the user is un-favoriting it. Delete it.
        db.session.delete(existing_fav)
        db.session.commit()
        return jsonify({"status": "removed", "fund": fund_name})
    else:
        # If it doesn't exist, create a new record.
        new_fav = Favorite(user_id=user_id, fund_id=fund_name)
        db.session.add(new_fav)
        db.session.commit()
        return jsonify({"status": "added", "fund": fund_name})
    
@dashboard_bp.route("/compare")
def compare():
    return render_template("dashboard/compare.html")

@dashboard_bp.route("/api/funds", methods=["GET"])
def get_funds():
    df_funds = get_funds_data()
    if df_funds.empty or 'scheme_name' not in df_funds.columns:
        return jsonify([])
    fund_names = df_funds['scheme_name'].dropna().unique().tolist()
    return jsonify(fund_names)

@dashboard_bp.route("/api/compare-data", methods=["POST"])
def compare_data():
    data = request.json
    selected_funds = data.get('funds', [])
    
    df_funds = get_funds_data()
    if not selected_funds or df_funds.empty:
        return jsonify([])

    compare_df = df_funds[df_funds['scheme_name'].isin(selected_funds)]
    
    columns_to_return = [
        'scheme_name', 'category', 'returns_1yr', 'returns_3yr', 
        'returns_5yr', 'expense_ratio', 'fund_size_cr', 'rating', 'risk_level'
    ]
    
    available_cols = [col for col in columns_to_return if col in compare_df.columns]
    
    result = compare_df[available_cols].to_dict(orient='records')
    return jsonify(result)

@dashboard_bp.route("/settings")
@login_required
def settings():
    # We pass the session variables to display the user's profile info
    return render_template(
        "dashboard/settings.html", 
        page_title="Account Settings", 
        page_desc="Manage your profile, preferences, and security.",
        user_name=session.get('user_name', 'User'),
        user_email=session.get('user_email', 'user@example.com')
    )
