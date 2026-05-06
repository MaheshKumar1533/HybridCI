import hashlib
import os

class CacheManager:
    def __init__(self, cache_dir=".ci_cache"):
        self.cache_dir = cache_dir

    def get_manifest_hash(self, manifest_path):
        with open(manifest_path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()

    def restore_cache(self, language, manifest_path):
        h = self.get_manifest_hash(manifest_path)
        dest = os.path.join(self.cache_dir, language, h)
        if os.path.exists(dest):
            print(f"[CACHE] Hit for {language} ({h})") 
            return True
        print(f"[CACHE] Miss for {language}")
        return False
