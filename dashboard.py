from flask import Flask, render_template, jsonify
import random
import datetime

app = Flask(__name__)

import sqlite3

def get_real_data():
    """Fetches real run history from the SQLite database."""
    history = []
    
    try:
        conn = sqlite3.connect("ci.db")
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='run_history'")
        if not cursor.fetchone():
            return {"kpis": {"total_time_saved_hours": 0, "total_compute_saved_hours": 0, "avg_optimization": 0}, "history": []}
            
        cursor.execute("SELECT run_id, run_date, original_time, optimized_time, time_saved, compute_saved, opt_percentage, cache_status, primary_language FROM run_history ORDER BY run_date DESC")
        rows = cursor.fetchall()
        conn.close()
    except Exception as e:
        print(f"Database error: {e}")
        return {"kpis": {"total_time_saved_hours": 0, "total_compute_saved_hours": 0, "avg_optimization": 0}, "history": []}
        
    total_time_saved = 0
    total_compute_saved = 0
    optimization_percentages = []
    
    for row in rows:
        run_id, run_date, original_time, optimized_time, time_saved, compute_saved, opt_percentage, cache_status, lang = row
        
        total_time_saved += time_saved
        total_compute_saved += compute_saved
        optimization_percentages.append(opt_percentage)
        
        history.append({
            "run_id": run_id,
            "date": run_date,
            "original_time": round(original_time, 2),
            "optimized_time": round(optimized_time, 2),
            "time_saved": round(time_saved, 2),
            "compute_saved": round(compute_saved, 2),
            "opt_percentage": round(opt_percentage, 1),
            "cache": cache_status,
            "language": lang
        })
        
    avg_optimization = sum(optimization_percentages) / len(optimization_percentages) if optimization_percentages else 0
    
    return {
        "kpis": {
            "total_time_saved_hours": round(total_time_saved / 3600.0, 4),  # Convert seconds to hours
            "total_compute_saved_hours": round(total_compute_saved / 60.0, 4), # Convert compute minutes to hours
            "avg_optimization": round(avg_optimization, 1)
        },
        "history": history
    }

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/metrics")
def metrics():
    return jsonify(get_real_data())

if __name__ == "__main__":
    app.run(debug=True, port=5000)
