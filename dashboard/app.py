import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, render_template, jsonify
from ci_engine.pipeline_runner import run_pipeline
from ci_engine.cache_manager import get_cache_stats
from ci_engine.language_utils import get_language_stats, get_changed_languages
from dashboard.models import init_db, store_run_result, get_runs, get_cache_statistics
import sqlite3
import json

app = Flask(__name__)
init_db()
# -------- IBST INPUT DATA --------

from ci_engine.test_mapper import generate_test_map

TEST_MAP = generate_test_map(
    "sample_repo/tests",
    "sample_repo/src"
)


DEP_GRAPH = {
    "main.py": []
}

@app.route("/run")
def run_ci():
    print("TEST_MAP:", TEST_MAP)

    try:
        result = run_pipeline(TEST_MAP, DEP_GRAPH, language_aware=True)
        baseline_result = run_pipeline(TEST_MAP, DEP_GRAPH, baseline=True)

        # Store result with language information and file details
        languages = result.get("languages")
        language_breakdown = result.get("language_breakdown")
        changed_files = result.get("changed_files", [])
        executed_tests = result.get("executed_tests", [])
        cached_files = result.get("cached_files", [])
        
        store_run_result(
            len(result["tests"]),
            float(result["time"]),
            float(baseline_result.get("time", 0)),
            int(result["cache_hit"]),
            mode=result.get("mode", "hybrid"),
            languages=json.dumps(languages) if languages else None,
            language_breakdown=json.dumps(language_breakdown) if language_breakdown else None,
            changed_files=json.dumps(changed_files),
            executed_tests=json.dumps(executed_tests),
            cached_files=json.dumps(cached_files)
        )

        return jsonify({
            "status": "success",
            "tests": result["tests"],
            "time": result["time"],
            "time_baseline": baseline_result.get("time", 0),
            "cache_hit": result["cache_hit"],
            "mode": result.get("mode"),
            "languages": result.get("languages"),
            "language_breakdown": result.get("language_breakdown"),
            "changed_files": changed_files,
            "executed_tests": executed_tests,
            "cached_files": cached_files
        })

    except Exception as e:
        print("ERROR IN /run:", e)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route("/runs")
def runs():
    rows = get_runs()
    
    # Parse language data for display
    runs_formatted = []
    for r in rows:
        # Parse JSON strings back to lists
        try:
            changed_files = json.loads(r[8]) if r[8] else []
        except:
            changed_files = []
        
        try:
            executed_tests = json.loads(r[9]) if r[9] else []
        except:
            executed_tests = []

        try:
            cached_files = json.loads(r[10]) if r[10] else []
        except:
            cached_files = []
        
        run_data = {
            "id": r[0],
            "tests_run": r[1],
            "time_taken": r[2],
            "time_baseline": r[3],
            "cache_hit": r[4],
            "mode": r[5],
            "languages": r[6],
            "language_breakdown": r[7],
            "changed_files": changed_files,
            "executed_tests": executed_tests,
            "cached_files": cached_files
        }
        runs_formatted.append(run_data)

    return render_template("runs.html", runs=runs_formatted)

@app.route("/baseline")
def run_baseline():
    result = run_pipeline(TEST_MAP, DEP_GRAPH, baseline=True)
    return jsonify(result)

@app.route("/cache-stats")
def cache_stats_page():
    """Render cache statistics dashboard page."""
    return render_template("cache_stats.html")

@app.route("/cache-stats-api")
def cache_stats():
    """API endpoint for cache statistics including language breakdown."""
    cache_stats = get_cache_stats()
    db_stats = get_cache_statistics()
    lang_stats = get_language_stats()
    changed_langs = get_changed_languages()
    
    return jsonify({
        "cache": cache_stats,
        "database": db_stats,
        "project_languages": lang_stats,
        "recently_changed_languages": changed_langs
    })

@app.route("/")
def index():
    conn = sqlite3.connect("ci.db")
    c = conn.cursor()
    c.execute("SELECT time_taken, tests_run FROM runs")
    data = c.fetchall()

    times = [r[0] for r in data]
    tests = [r[1] for r in data]

    c.execute("SELECT AVG(time_taken), AVG(tests_run) FROM runs")
    avg_time, avg_tests = c.fetchone()
    
    # Get cache statistics
    cache_stats = get_cache_statistics()
    
    conn.close()
    
    return render_template(
        "index.html",
        avg_time=avg_time,
        avg_tests=avg_tests,
        times=times,
        tests=tests,
        cache_stats=cache_stats
    )

if __name__ == "__main__":
    app.run(debug=True)

