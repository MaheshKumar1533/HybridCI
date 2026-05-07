from flask import Flask, render_template, jsonify, request
import random
import datetime
import sqlite3

app = Flask(__name__)

def get_real_data(project_name=None):
    """Fetches real run history from the SQLite database."""
    history = []
    
    try:
        conn = sqlite3.connect("ci.db")
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='run_history'")
        if not cursor.fetchone():
            return {"kpis": {"total_time_saved_hours": 0, "total_cost_saved": 0, "avg_optimization": 0, "avg_test_reduction": 0}, "history": []}
            
        if project_name and project_name != "all":
            cursor.execute("SELECT run_id, run_date, original_time, optimized_time, time_saved, compute_saved, opt_percentage, cache_status, primary_language, total_tests, selected_tests, test_reduction_percentage, dlc_status, build_time, cost_saved, project_name FROM run_history WHERE project_name = ? ORDER BY run_date DESC", (project_name,))
        else:
            cursor.execute("SELECT run_id, run_date, original_time, optimized_time, time_saved, compute_saved, opt_percentage, cache_status, primary_language, total_tests, selected_tests, test_reduction_percentage, dlc_status, build_time, cost_saved, project_name FROM run_history ORDER BY run_date DESC")
            
        rows = cursor.fetchall()
        conn.close()
    except Exception as e:
        print(f"Database error: {e}")
        return {"kpis": {"total_time_saved_hours": 0, "total_cost_saved": 0, "avg_optimization": 0, "avg_test_reduction": 0}, "history": []}
        
    total_time_saved = 0
    total_cost_saved = 0
    optimization_percentages = []
    reduction_percentages = []
    
    for row in rows:
        # Unpack, note that older rows might not have project_name depending on schema version
        # but since we dropped table, they all will.
        if len(row) == 16:
            run_id, run_date, original_time, optimized_time, time_saved, compute_saved, opt_percentage, cache_status, lang, total_tests, selected_tests, test_reduction_percentage, dlc_status, build_time, cost_saved, p_name = row
        else:
            run_id, run_date, original_time, optimized_time, time_saved, compute_saved, opt_percentage, cache_status, lang, total_tests, selected_tests, test_reduction_percentage, dlc_status, build_time, cost_saved = row
            p_name = "unknown"
            
        total_time_saved += time_saved
        if cost_saved is not None:
            total_cost_saved += cost_saved
            
        optimization_percentages.append(opt_percentage)
        if test_reduction_percentage is not None:
            reduction_percentages.append(test_reduction_percentage)
        
        history.append({
            "run_id": run_id,
            "date": run_date,
            "original_time": round(original_time, 2),
            "optimized_time": round(optimized_time, 2),
            "time_saved": round(time_saved, 2),
            "compute_saved": round(compute_saved, 2),
            "opt_percentage": round(opt_percentage, 1),
            "cache": cache_status,
            "language": lang,
            "total_tests": total_tests or 0,
            "selected_tests": selected_tests or 0,
            "test_reduction": round(test_reduction_percentage or 0, 1),
            "dlc_status": dlc_status or "DISABLED",
            "build_time": round(build_time or 0, 2),
            "cost_saved": round(cost_saved or 0, 4),
            "project": p_name
        })
        
    avg_optimization = sum(optimization_percentages) / len(optimization_percentages) if optimization_percentages else 0
    avg_reduction = sum(reduction_percentages) / len(reduction_percentages) if reduction_percentages else 0
    
    return {
        "kpis": {
            "total_time_saved_hours": round(total_time_saved / 3600.0, 4), 
            "total_cost_saved": round(total_cost_saved, 2),
            "avg_optimization": round(avg_optimization, 1),
            "avg_test_reduction": round(avg_reduction, 1)
        },
        "history": history
    }

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/metrics")
def metrics():
    project = request.args.get('project', 'all')
    return jsonify(get_real_data(project))

if __name__ == "__main__":
    app.run(debug=True, port=5000)
