import sqlite3

def init_db():
    conn = sqlite3.connect("ci.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tests_run INTEGER,
            time_taken REAL,
            time_baseline REAL,
            cache_hit INTEGER,
            mode TEXT DEFAULT 'hybrid',
            languages TEXT,
            language_breakdown TEXT,
            changed_files TEXT,
            executed_tests TEXT,
            cached_files TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def store_run_result(tests_run, time_taken, time_baseline, cache_hit, mode='hybrid', languages=None, language_breakdown=None, changed_files=None, executed_tests=None, cached_files=None):
    """Store a CI run result with language information and file details."""
    conn = sqlite3.connect("ci.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO runs (tests_run, time_taken, time_baseline, cache_hit, mode, languages, language_breakdown, changed_files, executed_tests, cached_files) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (tests_run, time_taken, time_baseline, cache_hit, mode, languages, language_breakdown, changed_files, executed_tests, cached_files)
    )
    conn.commit()
    conn.close()

def get_runs(limit=None):
    """Fetch recent runs from database."""
    conn = sqlite3.connect("ci.db")
    c = conn.cursor()
    query = "SELECT id, tests_run, time_taken, time_baseline, cache_hit, mode, languages, language_breakdown, changed_files, executed_tests, cached_files FROM runs ORDER BY id DESC"
    if limit:
        query += f" LIMIT {limit}"
    c.execute(query)
    rows = c.fetchall()
    conn.close()
    return rows

def get_cache_statistics():
    """Get cache hit statistics."""
    conn = sqlite3.connect("ci.db")
    c = conn.cursor()
    c.execute("SELECT COUNT(*), SUM(cache_hit), AVG(time_taken) FROM runs")
    total, hits, avg_time = c.fetchone()
    conn.close()
    
    return {
        "total_runs": total or 0,
        "cache_hits": hits or 0,
        "cache_hit_rate": (hits / total * 100) if total else 0,
        "avg_execution_time": avg_time or 0
    }
