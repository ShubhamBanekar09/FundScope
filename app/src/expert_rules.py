def calculate_risk_profile(age, stated_risk, time_frame):
    """
    Calculates a Blended Risk Capacity Score on a scale of 0 to 10.
    """
    # 1. Age Factor: Using the smoothed 100-minus-age rule
    age_score = max(0, min(10, (100 - age) / 10))
    
    # 2. Time Factor: Smoother scaling (caps at 8.3 years)
    time_score = min(10, time_frame * 1.2)
    
    # 3. User Stated Risk Level
    risk_mapping = {
        'Low': 2.0, 
        'Moderate': 5.0, 
        'High': 7.5, 
        'Very High': 10.0
    }
    user_score = risk_mapping.get(stated_risk, 5.0)
    
    # Blended Score (40% User Preference, 40% Time Horizon, 20% Age)
    final_score = (user_score * 0.4) + (time_score * 0.4) + (age_score * 0.2)
    
    return round(final_score, 2)

def get_target_sub_categories(risk_score):
    """
    Maps the calculated risk score (0-10) to the exact 'sub_category' 
    names present in the final_cleaned_fundsnumeric.csv dataset.
    """
    if risk_score >= 7.5:
        # Aggressive Growth (High Risk / High Return)
        return [
            'Small Cap Mutual Funds', 
            'Mid Cap Mutual Funds', 
            'Sectoral / Thematic Mutual Funds', 
            'Flexi Cap Funds', 
            'Multi Cap Funds',
            'Focused Funds',           # Added: High conviction, higher risk
            'Contra Funds'             # Added: High risk, contrarian strategy
        ]
        
    elif risk_score >= 4.5:
        # Moderate Growth (Balanced Risk & Return)
        return [
            'Large Cap Mutual Funds', 
            'Large & Mid Cap Funds', 
            'Aggressive Hybrid Mutual Funds', 
            'Value Funds', 
            'ELSS Mutual Funds',
            'Dynamic Asset Allocation or Balanced Advantage', # Added: Excellent moderate hybrid
            'Dividend Yield Funds',                           # Added: Value-oriented equity
            'Equity Savings Mutual Funds'                     # Added: Lower volatility equity
        ]
        
    else:
        # Conservative / Capital Preservation (Low Risk / Stability)
        return [
            'Liquid Mutual Funds', 
            'Short Duration Funds', 
            'Corporate Bond Mutual Funds',
            'Ultra Short Duration Funds', 
            'Low Duration Funds', 
            'Banking and PSU Mutual Funds',
            'Money Market Funds',                  # Added: Ultra-safe debt
            'Overnight Mutual Funds',              # Added: Safest possible fund type
            'Conservative Hybrid Mutual Funds',    # Added: Safe debt with a tiny equity kicker
            'Gilt Mutual Funds'                    # Added: Sovereign backed safe debt
        ]

def apply_hard_filters(df, amount, user_category, target_sub_caps):
    """
    Filters the dataset with strict matching.
    """
    # 1. Budget Filter
    pool = df[df['min_lumpsum'] <= amount].copy()
    
    # 2. Exact Match Category Filter (Defensive Programming)
    if user_category.lower() != 'any':
        pool = pool[pool['category'].str.lower() == user_category.lower()]
        
    # 3. Target Sub-Category matching
    sub_pool = pool[pool['sub_category'].isin(target_sub_caps)]
    
    # Fallback: If sub_pool is too small, return the broader pool 
    # so the KNN ML engine has enough data to mathematically sort through.
    if len(sub_pool) >= 5:
        return sub_pool
    
    return pool

# --- Test Block ---
if __name__ == "__main__":
    score = calculate_risk_profile(age=60, stated_risk='High', time_frame=10)
    print(f"Test Age 60, High Risk, 10 Years -> Score: {score}/10")
    print(f"Target Segments: {get_target_sub_categories(score)}")