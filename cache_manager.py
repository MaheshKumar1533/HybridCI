import hashlib
import os
import time

class CacheManager:
    def __init__(self, cache_dir=".ci_cache"):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def get_manifest_hash(self, files):
        # Create a hash representing the state of the changed files
        state = "".join(sorted(files))
        return hashlib.sha256(state.encode()).hexdigest()

    def process_language_builds(self, modified_files):
        build_times = {"Python": 0, "JavaScript": 0, "Java": 0}
        
        js_files = [f for f in modified_files if f.endswith(".js") or f.endswith(".jsx") or f.endswith(".ts")]
        py_files = [f for f in modified_files if f.endswith(".py")]
        java_files = [f for f in modified_files if f.endswith(".java")]
        
        if js_files:
            js_hash = self.get_manifest_hash(js_files)
            js_dest = os.path.join(self.cache_dir, "JavaScript", js_hash)
            if not os.path.exists(js_dest):
                print(f"[BUILD] JavaScript changes detected. Running language-aware build (npm run build)...")
                # Simulate npm build time
                time.sleep(1.2)
                os.makedirs(js_dest, exist_ok=True)
                build_times["JavaScript"] = 1.2
            else:
                print(f"[CACHE HIT] JavaScript build cache hit ({js_hash[:8]}).")
                
        if py_files:
            py_hash = self.get_manifest_hash(py_files)
            py_dest = os.path.join(self.cache_dir, "Python", py_hash)
            if not os.path.exists(py_dest):
                print(f"[BUILD] Python changes detected. Running language-aware build (pip install)...")
                # Simulate pip install time
                time.sleep(0.8)
                os.makedirs(py_dest, exist_ok=True)
                build_times["Python"] = 0.8
            else:
                print(f"[CACHE HIT] Python build cache hit ({py_hash[:8]}).")
                
        if java_files:
            java_hash = self.get_manifest_hash(java_files)
            java_dest = os.path.join(self.cache_dir, "Java", java_hash)
            if not os.path.exists(java_dest):
                print(f"[BUILD] Java changes detected. Running language-aware build (mvn package / gradle build)...")
                # Simulate java build time
                time.sleep(2.5)
                os.makedirs(java_dest, exist_ok=True)
                build_times["Java"] = 2.5
            else:
                print(f"[CACHE HIT] Java build cache hit ({java_hash[:8]}).")
                
        total_build_time = sum(build_times.values())
        return total_build_time, build_times

    def determine_primary_language(self, modified_files):
        js_count = sum(1 for f in modified_files if f.endswith(".js") or f.endswith(".jsx") or f.endswith(".ts"))
        py_count = sum(1 for f in modified_files if f.endswith(".py"))
        java_count = sum(1 for f in modified_files if f.endswith(".java"))
        
        if java_count > py_count and java_count > js_count:
            return "Java"
        elif js_count > py_count:
            return "JavaScript"
        return "Python"
