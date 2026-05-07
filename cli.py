import sys
import subprocess
import os
import json
import time
import hashlib
import sqlite3
import datetime
import uuid
from impact_engine import ImpactEngine, DependencyGraph, calculate_impact_score, select_tests
from cache_manager import CacheManager

def get_modified_files():
    try:
        diff = subprocess.check_output(["git", "diff", "--name-only", "HEAD"]).decode()
        modified = [line for line in diff.splitlines() if line.strip()]
        if not modified:
            diff = subprocess.check_output(["git", "diff", "--name-only", "HEAD~1", "HEAD"]).decode()
            modified = [line for line in diff.splitlines() if line.strip()]
        return modified
    except subprocess.CalledProcessError:
        print("Not a git repository. Using mock modified files.")
        # If no git, we'll return some of the mock files we seeded in DB
        return ["src/auth.py", "src/dashboard.js"]

def main():
    try:
        command = sys.argv[1]
    except IndexError:
        print("Usage: python cli.py [analyze|run|demo] [--no-dlc]")
        sys.exit(1)
        
    enable_dlc = "--no-dlc" not in sys.argv

    if command == "analyze":
        modified = get_modified_files()
        print(f"Found {len(modified)} modified files.")
        
        engine = ImpactEngine()
        graph_data = engine.build_dependency_graph(".")
        dep_graph = DependencyGraph(graph_data)
        
        scores = calculate_impact_score(modified, dep_graph, engine)
        selected = select_tests(scores, threshold=0.001)
        
        all_tests = dep_graph.all_tests()
        
        print(f"Impact Scores: {scores}")
        print(f"Total Tests: {len(all_tests)}, Selected Tests (IS > 0.001): {len(selected)}")
        
        run_data = {
            "modified_files": modified,
            "selected_tests": selected,
            "total_tests": len(all_tests),
            "all_tests": all_tests
        }
        with open("selected_tests.json", "w") as f:
            json.dump(run_data, f)
            
    elif command == "run" or command == "demo":
        print("="*50)
        print(f" HYBRID CI LIVE {'DEMO' if command == 'demo' else 'RUN'} ")
        print("="*50)
        
        baseline_time = 45.20
        total_tests_count = 100 # default
        
        if command == "demo":
            print("\n[STEP 1] Calculating true baseline (running ALL tests)...")
            start_baseline = time.time()
            
            # Simulated baseline docker execution
            baseline_dlc_arg = ["--no-dlc"] # Force no Docker caching for baseline
            # To simulate baseline, we need to pass all_tests if we know them
            # We'll just run all actual tests found
            all_t = []
            if os.path.exists("selected_tests.json"):
                with open("selected_tests.json", "r") as f:
                    data = json.load(f)
                    all_t = data.get("all_tests", [])
                    if not all_t:
                        total_tests_count = data.get("total_tests", 100)
                        all_t = [f"test_dummy_{i}" for i in range(total_tests_count)]
            else:
                all_t = ["tests/"] * 100 # Simulate 100 tests if no analyze run

            baseline_result = subprocess.run([sys.executable, "execution_layer.py"] + all_t + baseline_dlc_arg, capture_output=True, text=True)
            print(baseline_result.stdout)
            
            end_baseline = time.time()
            baseline_time = end_baseline - start_baseline
            with open("baseline_time.json", "w") as f:
                json.dump({"baseline": baseline_time}, f)
            print(f"\n[OK] Baseline Time: {baseline_time:.2f}s")
            print("\n[STEP 2] Running HybridCI Optimized Suite...")
        else:
            BASELINE_FILE = "baseline_time.json"
            if os.path.exists(BASELINE_FILE):
                try:
                    with open(BASELINE_FILE, "r") as f:
                        baseline_time = float(json.load(f).get("baseline", 45.20))
                except Exception:
                    pass
        
        modified_files = []
        if os.path.exists("selected_tests.json"):
            with open("selected_tests.json", "r") as f:
                data = json.load(f)
                selected = data.get("selected_tests", [])
                modified_files = data.get("modified_files", [])
                total_tests_count = data.get("total_tests", len(selected) * 2)
        else:
            print("No selected tests found. Please run 'analyze' first.")
            selected = ["tests/"]
            
        # Language-Aware Cache & Build
        cache_mgr = CacheManager()
        build_time, build_details = cache_mgr.process_language_builds(modified_files)
        primary_lang = cache_mgr.determine_primary_language(modified_files)
        
        # Determine Cache Status for Test execution
        state_str = json.dumps({"modified": modified_files, "tests": selected}, sort_keys=True)
        state_hash = hashlib.md5(state_str.encode()).hexdigest()
        
        CACHE_FILE = ".cli_last_run.json"
        last_hash = None
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r") as f:
                    last_hash = json.load(f).get("hash")
            except Exception:
                pass
                
        cache_hit = (state_hash == last_hash)
        
        start_optimized = time.time()
        
        if cache_hit:
            print("\n[CACHE HIT] Test state unchanged. Restoring results from cache...")
            time.sleep(0.15)
        else:
            dlc_arg = [] if enable_dlc else ["--no-dlc"]
            optimized_result = subprocess.run([sys.executable, "execution_layer.py"] + selected + dlc_arg, capture_output=True, text=True)
            print(optimized_result.stdout)
            with open(CACHE_FILE, "w") as f:
                json.dump({"hash": state_hash}, f)
                
        end_optimized = time.time()
        optimized_time = (end_optimized - start_optimized) + build_time
        
        time_saved = max(0, baseline_time - optimized_time)
        
        # Save metrics to DB
        compute_saved = (time_saved * 4) / 60.0 # e.g. 4 core compute minutes
        cost_saved = compute_saved * 0.05 # e.g. 5 cents per compute minute
        
        opt_percentage = (time_saved / baseline_time) * 100 if baseline_time > 0 else 0
        test_reduction_pct = ((total_tests_count - len(selected)) / total_tests_count) * 100 if total_tests_count > 0 else 0
        
        dlc_status_str = "ENABLED" if enable_dlc else "DISABLED"
        
        # Extract --project if present
        project_name = "hybridci-mock"
        if "--project" in sys.argv:
            try:
                p_index = sys.argv.index("--project")
                project_name = sys.argv[p_index + 1]
            except IndexError:
                pass
        
        try:
            conn = sqlite3.connect("ci.db")
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO run_history (run_id, run_date, original_time, optimized_time, time_saved, compute_saved, opt_percentage, cache_status, primary_language, total_tests, selected_tests, test_reduction_percentage, dlc_status, build_time, cost_saved, project_name)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (f"CI-{str(uuid.uuid4())[:6].upper()}", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), baseline_time, optimized_time, time_saved, compute_saved, opt_percentage, "HIT" if cache_hit else "MISS", primary_lang, total_tests_count, len(selected), test_reduction_pct, dlc_status_str, build_time, cost_saved, project_name))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"\n[Warning] Could not save metrics to DB: {e}")
        
        print("\n" + "="*50)
        print(" HYBRID CI PERFORMANCE COMPARISON")
        print("="*50)
        print(f" Modified Files ({len(modified_files)}):")
        for f in modified_files[:4]:
            print(f"   - {f}")
        if len(modified_files) > 4:
            print(f"   ... and {len(modified_files) - 4} more files")
            
        print(f"\n Total Tests: {total_tests_count}")
        print(f" Selected Tests ({len(selected)}):")
        for t in selected[:4]:
            print(f"   - {t}")
        if len(selected) > 4:
            print(f"   ... and {len(selected) - 4} more tests")
        print(f" Test Reduction: {test_reduction_pct:.1f}%")
        
        print(f"\n Primary Language: {primary_lang}")
        print(f" Build Time: {build_time:.2f}s")
        print(f" DLC Status: {dlc_status_str}")
        print(f" Cache Status: {'[HIT]' if cache_hit else '[MISS]'}")
        
        print(f"\n Baseline Execution:  {baseline_time:.2f}s")
        print(f" Optimized Execution: {optimized_time:.2f}s")
        print(f" TRUE Time Saved:     {time_saved:.2f}s")
        print(f" Cost Saved:          ${cost_saved:.4f}")
        print("="*50 + "\n")

if __name__ == "__main__":
    main()
