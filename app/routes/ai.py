from flask import Blueprint, render_template, request, jsonify
import pandas as pd
from app.src.expert_rules import calculate_risk_profile, get_target_sub_categories, apply_hard_filters
from app.src.ml_engine import get_ml_recommendations
import os
from pathlib import Path
from dotenv import load_dotenv

# --- 1. Load Environment Variables ---
# Navigate up from app/src/ai.py to the app/ folder where chatbot.env lives
current_dir = Path(__file__).resolve().parent.parent
env_path = current_dir / 'chatbot.env'

print(f"🔍 DEBUG: Loading env from: {env_path}")
load_dotenv(dotenv_path=env_path)

# --- 2. Initialize AI Blueprint ---
ai_bp = Blueprint("ai", __name__)

# --- 3. Lazy initialize Gemini Client ---
_client = None
_client_initialized = False

def get_gemini_client():
    global _client, _client_initialized
    if not _client_initialized:
        _client_initialized = True
        try:
            from google import genai
        except ImportError:
            print("⚠️ WARNING: google-genai package is not installed. Install it with: pip install google-genai")
            _client = None
            return _client
            
        API_KEY = os.getenv("GEMINI_API_KEY")
        if not API_KEY:
            print("⚠️ WARNING: GEMINI_API_KEY is not set in the environment. Check the path!")
            _client = None
        else:
            try:
                _client = genai.Client(api_key=API_KEY)
                print("✅ Gemini API connected successfully via new SDK.")
            except Exception as e:
                print(f"❌ Gemini API connection failed: {e}")
                _client = None
    return _client

# --- 4. Core Logic & Routes ---

def map_timeframe(ui_value):
    if not ui_value:
        return 5
    ui_value = ui_value.lower()
    if "short" in ui_value:
        return 3
    elif "medium" in ui_value or "mid" in ui_value:
        return 7
    elif "long" in ui_value:
        return 12
    elif "retirement" in ui_value:
        return 15
    return 5

@ai_bp.route("/ai-insights")
def ai_insights():
    return render_template("ai/insights.html")

@ai_bp.route("/recommend", methods=["POST"])
def recommend():
    data = request.json
    print("DATA RECEIVED:", data)

    user_name = data.get("user_name")
    age = int(data.get("age", 30))
    amount = int(data.get("amount", 10000))
    time_frame = map_timeframe(data.get("time_frame"))
    stated_risk = data.get("risk")
    user_category = data.get("category")

    csv_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'dataset', 'cleandata', 'final_cleaned_fundsnumeric.csv')
    df = pd.read_csv(csv_path)

    risk_score = calculate_risk_profile(age, stated_risk, time_frame)
    target_caps = get_target_sub_categories(risk_score)
    filtered_pool = apply_hard_filters(df, amount, user_category, target_caps)

    if len(filtered_pool) == 0:
        return jsonify({"error": "No funds found"})

    recommendations = get_ml_recommendations(filtered_pool, risk_score).head(7)

    result = []
    for _, row in recommendations.iterrows():
        result.append({
            "fund_name": row['scheme_name'],
            "category": row['sub_category'],
            "returns_3yr": row['returns_3yr'],
            "sharpe": round(row['sharpe'], 2),
            "score": row['match_score']
        })

    print("SENDING:", result)
    return jsonify({
        "recommendations": result
    })

@ai_bp.route("/chatbot")
def chatbot():
    return render_template("ai/chatbot.html")

@ai_bp.route("/chat-api", methods=["POST"])
def chat_api():
    client = get_gemini_client()
    if not client:
        return jsonify({"error": "Chatbot is currently offline due to API configuration issues."}), 503

    user_msg = request.json.get("message", "")
    if not user_msg:
        return jsonify({"error": "No message provided"}), 400
        
    try:
        prompt = (
            "You are FundScope_Bot, an expert financial advisor specializing strictly in mutual funds and investments. "
            "You MUST answer only questions related to mutual funds, SIPs, personal finance, or investing. "
            "If the user asks about ANY topic outside of this scope, you must actively decline to answer by politely replying: "
            "'I am programmed to only assist with mutual fund and investment related inquiries.' Be concise, professional, and helpful.\n\n"
            f"User query: {user_msg}"
        )
        
        # Generating content using the new SDK syntax
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        
        return jsonify({"reply": response.text})
        
    except Exception as e:
        print(f"Chat API Error: {str(e)}")
        return jsonify({"error": "An error occurred while processing your request."}), 500