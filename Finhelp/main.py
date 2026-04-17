from flask import Flask, request, jsonify, render_template
import pandas as pd
from src.expert_rules import calculate_risk_profile, get_target_sub_categories, apply_hard_filters
from src.ml_engine import get_ml_recommendations

app = Flask(__name__)

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

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/recommend', methods=['POST'])
def recommend():
    data = request.json
    print("DATA RECEIVED:", data)

    user_name = data.get("user_name")
    age = int(data.get("age"))
    amount = int(data.get("amount"))
    time_frame = map_timeframe(data.get("time_frame"))
    stated_risk = data.get("risk")
    user_category = data.get("category")

    df = pd.read_csv('Finhelp/dataset/cleandata/final_cleaned_fundsnumeric.csv')

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

if __name__ == "__main__":
    app.run(debug=True)