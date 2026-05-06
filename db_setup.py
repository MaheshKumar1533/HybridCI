import sqlite3

def _init_db(db_path="ci.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. coverage: Stores the coverage ratio used in calculating test overlaps
    cursor.execute("""
CREATE TABLE IF NOT EXISTS coverage (
    test_file TEXT,
    source_file TEXT, 
    overlap FLOAT,
    last_run TIMESTAMP
)
    """)
    
    # 2. commit_history: A log of file modifications to calculate a 'Hotspot Score'
    cursor.execute("""
CREATE TABLE IF NOT EXISTS commit_history (
    file_path TEXT,
    commit_hash TEXT,
    timestamp TIMESTAMP
)
    """)
    
    # 3. test_telemetry: Stores metadata for each test run
    cursor.execute("""
CREATE TABLE IF NOT EXISTS test_telemetry (
    test_file TEXT,
    duration FLOAT,
    memory_usage FLOAT,
    flaky_count INTEGER,
    stability_score FLOAT
)
    """)
    
    # 4. run_history: Stores metrics for the dashboard
    cursor.execute("""
CREATE TABLE IF NOT EXISTS run_history (
    run_id TEXT,
    run_date TIMESTAMP,
    original_time FLOAT,
    optimized_time FLOAT,
    time_saved FLOAT,
    compute_saved FLOAT,
    opt_percentage FLOAT,
    cache_status TEXT,
    primary_language TEXT
)
    """)
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    _init_db()
    print("Database initialized successfully.")
