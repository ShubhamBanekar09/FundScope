import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors

def get_ml_recommendations(filtered_pool, risk_score):
    """
    Advanced KNN Engine using Dynamic Feature Weighting, Percentile Targeting, 
    and Distance-to-Score conversion to find the perfect mutual funds.
    """
    # --- EDGE CASE HANDLING ---
    # 1. Drop missing values just in case the dataset updates with nulls
    base_features = ['returns_3yr', 'sharpe', 'fund_size_cr', 'expense_ratio']
    pool = filtered_pool.dropna(subset=base_features).copy()
    
    # 2. Small Pool Fallback: If < 10 funds, KNN is overkill. Just return the best by Return/Sharpe.
    if len(pool) < 10:
        # Sort by returns if high risk, else sort by sharpe
        sort_col = 'returns_3yr' if risk_score >= 7.5 else 'sharpe'
        fallback = pool.sort_values(by=sort_col, ascending=False).head(5).copy()
        fallback['match_score'] = "N/A (Direct Sort)"
        return fallback

    # --- FEATURE ENGINEERING ---
    # 3. Invert Expense Ratio so "Higher is Better" across all features
    pool['inv_expense'] = -pool['expense_ratio']
    ml_features = ['returns_3yr', 'sharpe', 'fund_size_cr', 'inv_expense']

    # Normalize data (Z-Scores)
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(pool[ml_features])

    # 4. Create the "Ideal Fund" using 90th Percentile (Avoids Max-Value Bias)
    target_ret = np.percentile(scaled_data[:, 0], 90)
    target_sharpe = np.percentile(scaled_data[:, 1], 90)
    target_aum = np.percentile(scaled_data[:, 2], 90)
    target_exp = np.percentile(scaled_data[:, 3], 90) # 90th percentile of inverted = lowest expenses

    # --- DYNAMIC WEIGHTING & IDEAL VECTOR ---
    # We warp the multi-dimensional space based on the user's risk profile
    if risk_score >= 7.5:
        # Aggressive: Huge weight on Returns, moderate on size/expense, low on Sharpe
        weights = np.array([1.5, 0.6, 0.9, 1.0])
        ideal_vector = np.array([[target_ret, target_sharpe * 0.5, target_aum * 0.8, target_exp]])
        
    elif risk_score >= 4.5:
        # Moderate: Balanced weights. High emphasis on Sharpe and Returns.
        weights = np.array([1.1, 1.2, 1.0, 1.0])
        ideal_vector = np.array([[target_ret * 0.8, target_sharpe, target_aum * 0.9, target_exp]])
        
    else:
        # Conservative: Huge weight on Sharpe (Stability) and AUM (Trust). Low weight on raw returns.
        weights = np.array([0.5, 1.5, 1.3, 1.0])
        ideal_vector = np.array([[target_ret * 0.4, target_sharpe, target_aum, target_exp]])

    # 5. Apply Feature Weighting BEFORE running KNN
    scaled_data_weighted = scaled_data * weights
    ideal_weighted = ideal_vector * weights

    # --- K-NEAREST NEIGHBORS ---
    knn = NearestNeighbors(n_neighbors=5, metric='euclidean')
    knn.fit(scaled_data_weighted)

    distances, indices = knn.kneighbors(ideal_weighted)

    # --- SCORE INTERPRETATION ---
    recommendations = pool.iloc[indices[0]].copy()
    
    # 6. Convert abstract distance into a highly readable UI Match Score (%)
    # Formula: (1 / (1 + distance)) * 100
    recommendations['match_score'] = np.round((1 / (1 + distances[0])) * 100, 1)

    # Format the final output columns
    final_columns = [
        'scheme_name', 'category', 'sub_category', 
        'returns_3yr', 'sharpe', 'fund_size_cr', 'expense_ratio', 'match_score'
    ]
    
    return recommendations[final_columns]