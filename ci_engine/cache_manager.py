import hashlib
import os
import pickle
import json
from pathlib import Path

CACHE_DIR = ".ci_cache"
LANGUAGE_AWARE_CACHE_DIR = os.path.join(CACHE_DIR, "language_aware")

# Mapping of file extensions to programming languages
LANGUAGE_EXTENSIONS = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".jsx": "jsx",
    ".tsx": "tsx",
    ".java": "java",
    ".class": "java",
    ".cs": "csharp",
    ".cpp": "cpp",
    ".c": "c",
    ".h": "c",
    ".go": "go",
    ".rs": "rust",
    ".rb": "ruby",
    ".php": "php",
    ".swift": "swift",
    ".kt": "kotlin",
    ".scala": "scala",
}

def get_file_language(filepath):
    """Extract language from file extension."""
    ext = Path(filepath).suffix.lower()
    return LANGUAGE_EXTENSIONS.get(ext, "unknown")

def hash_dependencies(requirements_file):
    with open(requirements_file, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def load_cache(cache_key):
    """Load standard cache."""
    path = os.path.join(CACHE_DIR, cache_key)
    if os.path.exists(path):
        with open(path, "rb") as f:
            return pickle.load(f)
    return None

def save_cache(cache_key, data):
    """Save standard cache."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(os.path.join(CACHE_DIR, cache_key), "wb") as f:
        pickle.dump(data, f)

def load_language_aware_cache(cache_key, language=None):
    """Load language-aware cache. If language is None, loads the language map."""
    lang_dir = LANGUAGE_AWARE_CACHE_DIR
    if language:
        path = os.path.join(lang_dir, f"{cache_key}_{language}.pkl")
    else:
        path = os.path.join(lang_dir, f"{cache_key}_map.json")
    
    if os.path.exists(path):
        if language:
            with open(path, "rb") as f:
                return pickle.load(f)
        else:
            with open(path, "r") as f:
                return json.load(f)
    return None

def save_language_aware_cache(cache_key, data, language):
    """Save language-aware cache for a specific language."""
    os.makedirs(LANGUAGE_AWARE_CACHE_DIR, exist_ok=True)
    path = os.path.join(LANGUAGE_AWARE_CACHE_DIR, f"{cache_key}_{language}.pkl")
    with open(path, "wb") as f:
        pickle.dump(data, f)

def save_language_map(cache_key, language_map):
    """Save the language distribution map for a cache key."""
    os.makedirs(LANGUAGE_AWARE_CACHE_DIR, exist_ok=True)
    path = os.path.join(LANGUAGE_AWARE_CACHE_DIR, f"{cache_key}_map.json")
    with open(path, "w") as f:
        json.dump(language_map, f, indent=2)

def get_cache_stats():
    """Get statistics about cached items, including language breakdown."""
    stats = {
        "total_caches": 0,
        "total_language_caches": 0,
        "languages": {},
        "cache_dir": CACHE_DIR,
        "language_aware_dir": LANGUAGE_AWARE_CACHE_DIR
    }
    
    if os.path.exists(CACHE_DIR):
        stats["total_caches"] = len([f for f in os.listdir(CACHE_DIR) if f.endswith(".pkl")])
    
    if os.path.exists(LANGUAGE_AWARE_CACHE_DIR):
        for file in os.listdir(LANGUAGE_AWARE_CACHE_DIR):
            if file.endswith(".pkl"):
                stats["total_language_caches"] += 1
                # Extract language from filename (format: key_language.pkl)
                parts = file.replace(".pkl", "").rsplit("_", 1)
                if len(parts) == 2:
                    language = parts[1]
                    stats["languages"][language] = stats["languages"].get(language, 0) + 1
    
    return stats
