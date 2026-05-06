from flask import Flask, render_template, jsonify
import random
import datetime

app = Flask(__name__)

def generate_mock_data():
    """Generates a realistic run history for the dashboard presentation."""
    history = []
    base_time = datetime.datetime.now() - datetime.timedelta(days=30)
    
    total_time_saved = 0
    total_compute_saved = 0
    optimization_percentages = []
    
    for i in range(1, 101):
        run_date = base_time + datetime.timedelta(hours=i * 7.2)
        original_time = random.uniform(10.0, 45.0)  # minutes
        
        # Simulate optimization: caching and impact selective testing
        is_cache_hit = random.random() > 0.3
        optimization_factor = random.uniform(0.4, 0.9) if is_cache_hit else random.uniform(0.1, 0.3)
        
        optimized_time = original_time * (1.0 - optimization_factor)
        time_saved = original_time - optimized_time
        
        # Compute saved (CPU hours) = time saved * cores (assume 4 cores) / 60
        compute_saved = (time_saved * 4) / 60.0
        
        opt_percentage = (time_saved / original_time) * 100
        
        total_time_saved += time_saved
        total_compute_saved += compute_saved
        optimization_percentages.append(opt_percentage)
        
        history.append({
            "run_id": f"CI-{1000 + i}",
            "date": run_date.strftime("%Y-%m-%d %H:%M"),
            "original_time": round(original_time, 2),
            "optimized_time": round(optimized_time, 2),
            "time_saved": round(time_saved, 2),
            "compute_saved": round(compute_saved, 2),
            "opt_percentage": round(opt_percentage, 1),
            "cache": "HIT" if is_cache_hit else "MISS",
            "language": random.choice(["Python", "Java", "Node.js", "Go", "Python", "Python"])
        })
        
    history.reverse() # newest first
    
    avg_optimization = sum(optimization_percentages) / len(optimization_percentages)
    
    return {
        "kpis": {
            "total_time_saved_hours": round(total_time_saved / 60.0, 1),
            "total_compute_saved_hours": round(total_compute_saved, 1),
            "avg_optimization": round(avg_optimization, 1)
        },
        "history": history
    }

mock_data = generate_mock_data()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/metrics")
def metrics():
    return jsonify(mock_data)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
