import time
import hashlib
from pathlib import Path
from ci_engine.change_detector import get_changed_files, get_changed_files_by_language, filter_changes_by_language
from ci_engine.ibst import select_tests
from ci_engine.cache_manager import (
    load_cache, save_cache,
    load_language_aware_cache, save_language_aware_cache, save_language_map,
    get_file_language
)
from ci_engine.optimizer import select_tests_optimized, OptimizationResult

def run_pipeline(test_map, dependency_graph, baseline=False, language_aware=True, use_optimizer=False):
    start = time.time()

    # ---------- BASELINE MODE ----------
    if baseline:
        selected_tests = list(test_map.keys())
        time.sleep(0.5 * len(selected_tests))
        end = time.time()

        return {
            "tests": selected_tests,
            "time": end - start,
            "cache_hit": False,
            "mode": "baseline",
            "changed_files": [],
            "executed_tests": selected_tests
        }

    # ---------- HYBRIDCI MODE ----------
    changed_files = get_changed_files()

    # 🔥 SAFETY NET
    if not changed_files:
        changed_files = []
        for files in test_map.values():
            changed_files.extend(files)

    # Use optimization framework if requested
    if use_optimizer:
        return _run_pipeline_optimized(changed_files, test_map, dependency_graph, start)

    # Language-aware caching
    if language_aware:
        return _run_pipeline_language_aware(changed_files, test_map, dependency_graph, start)
    else:
        return _run_pipeline_standard(changed_files, test_map, dependency_graph, start)


def _run_pipeline_optimized(changed_files, test_map, dependency_graph, start):
    """
    Optimized test selection using constrained optimization.
    
    Solves: minimize Σ C(tj) * xj
            subject to: Σ D(fi, tj) * xj ≥ 1  ∀ fi ∈ F
    """
    # Use the mathematical optimizer
    selected_tests, opt_result = select_tests_optimized(
        changed_files=changed_files,
        test_map=test_map,
        confidence_threshold=0.0,
        method="auto"
    )
    
    time.sleep(0.5 * len(selected_tests))
    end = time.time()
    
    return {
        "tests": selected_tests,
        "time": end - start,
        "cache_hit": False,
        "mode": "optimized",
        "changed_files": changed_files,
        "executed_tests": selected_tests,
        "cached_files": [],
        "optimization": {
            "total_cost": opt_result.total_cost,
            "coverage_score": opt_result.coverage_score,
            "confidence_score": opt_result.confidence_score,
            "solver_used": opt_result.solver_used,
            "optimization_time_ms": opt_result.optimization_time * 1000
        }
    }

def _run_pipeline_standard(changed_files, test_map, dependency_graph, start):
    """Standard caching mode (non-language-aware)."""
    cached_count = 0
    cached_files = []
    merged_tests = set()

    for file in changed_files:
        file_key = generate_file_cache_key(file)
        cached = load_cache(file_key)
        if cached:
            cached_count += 1
            cached_files.append(file)
            merged_tests.update(cached["tests"])
            continue

        file_tests = select_tests([file], dependency_graph, test_map)
        merged_tests.update(file_tests)

        save_cache(file_key, {
            "tests": file_tests,
            "time": 0,
            "file": file
        })

    time.sleep(0.5 * len(merged_tests))
    end = time.time()

    return {
        "tests": list(merged_tests),
        "time": end - start,
        "cache_hit": cached_count == len(changed_files) and len(changed_files) > 0,
        "mode": "hybrid",
        "changed_files": changed_files,
        "executed_tests": list(merged_tests),
        "cached_files": cached_files
    }

def _run_pipeline_language_aware(changed_files, test_map, dependency_graph, start):
    """Language-aware caching mode."""
    language_map, _ = get_changed_files_by_language()

    cached_count = 0
    cached_files = []
    total_files = sum(len(files) for files in language_map.values())
    selected_tests_by_language = {}
    all_selected_tests = set()

    for language, lang_files in language_map.items():
        lang_tests = set()
        for file in lang_files:
            file_key = generate_file_cache_key(file)
            lang_cache = load_language_aware_cache(file_key, language)
            if lang_cache:
                cached_count += 1
                cached_files.append(file)
                lang_tests.update(lang_cache["tests"])
                continue

            file_tests = select_tests([file], dependency_graph, test_map)
            lang_tests.update(file_tests)

            save_language_aware_cache(file_key, {
                "tests": file_tests,
                "time": 0,
                "language": language,
                "file": file
            }, language)

        selected_tests_by_language[language] = list(lang_tests)
        all_selected_tests.update(lang_tests)

    time.sleep(0.5 * len(all_selected_tests))
    end = time.time()

    # Save language map for visibility
    save_language_map(generate_cache_key(changed_files), language_map)

    return {
        "tests": list(all_selected_tests),
        "time": end - start,
        "cache_hit": total_files > 0 and cached_count == total_files,
        "mode": "language_aware",
        "languages": list(language_map.keys()),
        "language_breakdown": {lang: len(tests) for lang, tests in selected_tests_by_language.items()},
        "changed_files": changed_files,
        "executed_tests": list(all_selected_tests),
        "cached_files": cached_files
    }

def generate_cache_key(files):
    normalized = sorted([f.replace("\\", "/") for f in files])
    joined = "|".join(normalized)
    return hashlib.md5(joined.encode()).hexdigest()

def generate_file_cache_key(file_path):
    normalized = file_path.replace("\\", "/")
    content_hash = "missing"
    try:
        content = Path(file_path).read_bytes()
        content_hash = hashlib.md5(content).hexdigest()
    except Exception:
        content_hash = "unreadable"
    return hashlib.md5(f"{normalized}|{content_hash}".encode()).hexdigest()
