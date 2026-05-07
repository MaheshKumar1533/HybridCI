import os
import subprocess
import time
import random
import shutil

REPOS = {
    "webpack": "https://github.com/webpack/webpack.git",
    "pandas": "https://github.com/pandas-dev/pandas.git",
    "spring-boot": "https://github.com/spring-projects/spring-boot.git"
}

REPOS_DIR = "repos"

def clone_repos():
    if not os.path.exists(REPOS_DIR):
        os.makedirs(REPOS_DIR)
        
    for name, url in REPOS.items():
        repo_path = os.path.join(REPOS_DIR, name)
        if not os.path.exists(repo_path):
            print(f"Cloning {name} (shallow clone to save time)...")
            subprocess.run(["git", "clone", "--depth", "1", url, repo_path])
        else:
            print(f"Repo {name} already exists.")

def get_random_source_file(repo_path):
    """Finds a random source file in the repository to modify."""
    source_files = []
    for root, _, files in os.walk(repo_path):
        if any(ignore in root for ignore in [".git", "node_modules", "venv", "target", "build"]):
            continue
        for file in files:
            if file.endswith((".py", ".js", ".ts", ".java")):
                source_files.append(os.path.join(root, file))
                
    if not source_files:
        return None
    return random.choice(source_files)

def simulate_modification(file_path):
    """Appends a random comment to simulate a file change."""
    try:
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(f"\n// HybridCI Test Mutation {random.randint(1000, 9999)}\n")
        return True
    except Exception as e:
        print(f"Failed to modify {file_path}: {e}")
        return False

def run_experiment(iterations_list):
    clone_repos()
    
    # We will copy the cli.py, impact_engine.py, cache_manager.py, execution_layer.py, db_setup.py, ci.db into the root so they can be run on the repos.
    # Actually, it's better to run cli.py from the root of HybridCI but pointing to the repo, OR just change directory.
    # Since HybridCI assumes it's running in the root of the project, we'll cd into the repo, 
    # but cli.py is in the parent dir. Let's just run `python ../../cli.py analyze` etc.
    
    # Wait, cli.py uses `.` for analyze. So yes, we cd into the repo.
    # However, cli.py writes to `ci.db` in the current directory. We should pass absolute paths or copy the DB.
    # To keep it simple, let's just copy the HybridCI core files into each repo temporarily, or modify cli.py to take a path.
    # For this experiment, we will just copy the necessary HybridCI files into the repo.
    hybridci_files = ["cli.py", "impact_engine.py", "cache_manager.py", "execution_layer.py", "db_setup.py", "ci.db", "selected_tests.json", "baseline_time.json", ".cli_last_run.json"]
    
    for name in REPOS.keys():
        repo_path = os.path.join(REPOS_DIR, name)
        
        # Copy HybridCI files into the repo
        for f in hybridci_files:
            if os.path.exists(f):
                shutil.copy(f, repo_path)
                
        print(f"\n{'='*50}\nStarting Experiment on {name.upper()}\n{'='*50}")
        
        for iterations in iterations_list:
            print(f"\n--- Running {iterations} Iterations Loop ---")
            for i in range(iterations):
                print(f"[{name}] Iteration {i+1}/{iterations}")
                
                # 1. Modify a random file
                target_file = get_random_source_file(repo_path)
                if not target_file:
                    print(f"No source files found in {name}! Skipping.")
                    continue
                    
                simulate_modification(target_file)
                
                # Note: `cli.py` relies on git diff. Since we modified a file, git diff will pick it up!
                # 2. Run Analyze
                subprocess.run(["python", "cli.py", "analyze"], cwd=repo_path, stdout=subprocess.DEVNULL)
                
                # 3. Run Demo (Metrics recording)
                subprocess.run(["python", "cli.py", "demo", "--project", name], cwd=repo_path, stdout=subprocess.DEVNULL)
                
        # Copy the updated ci.db back to root so dashboard can see it
        shutil.copy(os.path.join(repo_path, "ci.db"), "ci.db")

if __name__ == "__main__":
    # The user asked for 1, 10, 50, 100 times. 
    # For testing, we can do [1, 10]. Doing 50 and 100 will take a while but we'll do what is requested.
    iterations = [1, 10, 50, 100]
    # For the sake of the automated environment, we might want to reduce this if it times out,
    # but we will stick to the plan.
    run_experiment(iterations)
    print("\nExperiment completed! Run `python dashboard.py` to view results.")
