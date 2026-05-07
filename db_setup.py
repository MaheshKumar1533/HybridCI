import sqlite3
import random
import datetime

def _init_db(db_path="ci.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Drop existing run_history to apply new schema for the demo
    cursor.execute("DROP TABLE IF EXISTS run_history")
    
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
    primary_language TEXT,
    total_tests INTEGER,
    selected_tests INTEGER,
    test_reduction_percentage FLOAT,
    dlc_status TEXT,
    build_time FLOAT,
    cost_saved FLOAT,
    project_name TEXT
)
    """)
    
    conn.commit()
    conn.close()

def _seed_mock_data(db_path="ci.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if seeded
    cursor.execute("SELECT COUNT(*) FROM commit_history")
    if cursor.fetchone()[0] == 0:
        print("Seeding mock coverage and commit history data...")
        now = datetime.datetime.now()
        
        # Mock commit history (frequencies)
        files = ["src/auth.py", "src/dashboard.js", "src/api.py", "src/components/Button.jsx"]
        for f in files:
            # Randomly give them some commit history
            commits = random.randint(1, 20)
            for i in range(commits):
                ts = now - datetime.timedelta(days=random.randint(1, 30))
                cursor.execute("INSERT INTO commit_history (file_path, commit_hash, timestamp) VALUES (?, ?, ?)", 
                               (f, f"hash_{random.randint(1000,9999)}", ts.strftime("%Y-%m-%d %H:%M:%S")))
                
        # Mock coverage overlap
        tests = ["tests/test_auth.py", "tests/test_dashboard.js", "tests/test_api.py", "tests/test_components.js"]
        for t in tests:
            for f in files:
                # Give high overlap if names match somewhat
                base_t = t.replace("tests/test_", "").replace(".py", "").replace(".js", "")
                base_f = f.replace("src/", "").replace(".py", "").replace(".js", "").replace(".jsx", "").replace("components/", "")
                
                if base_t == base_f:
                    overlap = random.uniform(0.7, 1.0)
                else:
                    overlap = random.uniform(0.0, 0.3)
                    
                cursor.execute("INSERT INTO coverage (test_file, source_file, overlap, last_run) VALUES (?, ?, ?, ?)",
                               (t, f, overlap, now.strftime("%Y-%m-%d %H:%M:%S")))
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    _init_db()
    _seed_mock_data()
    print("Database initialized and seeded successfully.")
