# investigation/scoring.py

import math
from typing import List, Dict, Any

def calculate_evidence_score(hypothesis_data: Dict[str, Any], sql_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Evaluates SQL execution results and calculates a deterministic evidence score (0-100).
    
    Args:
        hypothesis_data (dict): Metadata about the hypothesis (e.g., expected impact, noise indicators).
        sql_results (list): List of dictionaries representing the rows returned from the SQL query.
        
    Returns:
        dict: A dictionary containing the final_score, challenged_score, status, and breakdown.
    """
    
    if not sql_results:
        return {
            "final_score": 0,
            "challenged_score": 0,
            "status": "weak",
            "breakdown": {"volume": 0.0, "impact": 0.0, "consistency": 0.0}
        }

    # ---------------------------------------------------------
    # 1. Data Volume / Coverage (Max 20 Points)
    # ---------------------------------------------------------
    total_volume = 0
    volume_keywords = ['count', 'total', 'volume', 'sessions', 'events', 'users']
    
    for row in sql_results:
        for col_name, value in row.items():
            if value is not None and any(kw in col_name.lower() for kw in volume_keywords) and isinstance(value, (int, float)):
                total_volume += value

    # Fallback: if no volume column is found, assume each row represents a distinct aggregated segment
    if total_volume == 0:
        total_volume = len(sql_results) * 50  

    volume_score = min(20.0, (total_volume / 10000.0) * 20.0)
    
    # ---------------------------------------------------------
    # 2. Anomaly Severity / Impact (Max 50 Points)
    # ---------------------------------------------------------
    max_impact_val = 0.0
    impact_keywords = ['rate', 'drop', 'increase', 'diff', 'impact', 'ratio', 'severity', 'variance', 'cost']
    
    for row in sql_results:
        for col_name, value in row.items():
            if value is not None and any(kw in col_name.lower() for kw in impact_keywords) and isinstance(value, (int, float)):
                normalized_val = abs(value) if abs(value) <= 1.0 else abs(value) / 100.0
                max_impact_val = max(max_impact_val, normalized_val)

    # Fallback: Use hypothesis metadata if no explicit column is matched
    if max_impact_val == 0.0:
        max_impact_val = float(hypothesis_data.get('expected_impact_ratio', 0.5))

    impact_score = min(50.0, max_impact_val * 50.0)

    # ---------------------------------------------------------
    # 3. Consistency (Max 30 Points)
    # ---------------------------------------------------------
    anomaly_threshold = max_impact_val * 0.5 if max_impact_val > 0 else 0.1
    consistent_rows = 0
    
    for row in sql_results:
        row_is_anomalous = False
        for col_name, value in row.items():
            if value is not None and any(kw in col_name.lower() for kw in impact_keywords) and isinstance(value, (int, float)):
                val = abs(value) if abs(value) <= 1.0 else abs(value) / 100.0
                if val >= anomaly_threshold:
                    row_is_anomalous = True
                    break
        
        if row_is_anomalous or max_impact_val == float(hypothesis_data.get('expected_impact_ratio', 0.5)):
            consistent_rows += 1

    consistency_ratio = consistent_rows / len(sql_results)
    consistency_score = min(30.0, consistency_ratio * 30.0)

    # ---------------------------------------------------------
    # Final Score & Challenged Score Computations
    # ---------------------------------------------------------
    # Fixed: Bound max score explicitly to 100
    calculated_sum = volume_score + impact_score + consistency_score
    final_score = min(100, int(math.ceil(calculated_sum)))

    penalty = 0
    
    if len(sql_results) < 3 and total_volume < 500:
        penalty += 10 
        
    if hypothesis_data.get('has_counter_evidence', False):
        penalty += 15
    if hypothesis_data.get('high_baseline_noise', False):
        penalty += 10

    challenged_score = max(0, final_score - penalty)

    # ---------------------------------------------------------
    # Status Evaluation
    # ---------------------------------------------------------
    if final_score >= 75:
        status = 'leading'
    elif final_score >= 40:
        status = 'moderate'
    else:
        status = 'weak'

    return {
        "final_score": final_score,
        "challenged_score": challenged_score,
        "status": status,
        "breakdown": {
            "volume": round(volume_score, 2),
            "impact": round(impact_score, 2),
            "consistency": round(consistency_score, 2)
        }
    }

# --- Example Usage / Tests ---
if __name__ == "__main__":
    test_hypothesis = {
        "description": "API Gateway 5xx errors spiked due to timeout",
        "has_counter_evidence": False,
        "high_baseline_noise": False
    }
    
    test_results = [
        {"endpoint": "/api/v1/checkout", "total_requests": 15000, "error_rate": 65.5, "avg_latency_ms": 5000},
        {"endpoint": "/api/v1/cart", "total_requests": 8000, "error_rate": 45.0, "avg_latency_ms": 3000},
    ]

    score = calculate_evidence_score(test_hypothesis, test_results)
    import json
    print(json.dumps(score, indent=2))