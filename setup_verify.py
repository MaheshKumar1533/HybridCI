#!/usr/bin/env python
"""
Setup and verification script for HybridCI with Language-Aware Caching.
Checks all components are properly installed and configured.
"""

import os
import sys
from pathlib import Path

def check_python_version():
    """Check Python version is 3.8+."""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
        return True
    print(f"✗ Python {version.major}.{version.minor}.{version.micro} (3.8+ required)")
    return False

def check_dependencies():
    """Check required packages are installed."""
    required = ["flask", "pytest"]
    installed = []
    missing = []
    
    for pkg in required:
        try:
            __import__(pkg)
            installed.append(pkg)
        except ImportError:
            missing.append(pkg)
    
    for pkg in installed:
        print(f"✓ {pkg}")
    
    for pkg in missing:
        print(f"✗ {pkg} (install with: pip install {pkg})")
    
    return len(missing) == 0

def check_project_structure():
    """Check all required project files exist."""
    root = Path(__file__).parent
    files_to_check = [
        "ci_engine/__init__.py",
        "ci_engine/cache_manager.py",
        "ci_engine/change_detector.py",
        "ci_engine/dependency_graph.py",
        "ci_engine/ibst.py",
        "ci_engine/language_utils.py",
        "ci_engine/pipeline_runner.py",
        "ci_engine/test_mapper.py",
        "ci_engine/test_language_aware.py",
        "dashboard/__init__.py",
        "dashboard/app.py",
        "dashboard/models.py",
        "dashboard/static/styles.css",
        "dashboard/static/charts.js",
        "dashboard/templates/index.html",
        "dashboard/templates/runs.html",
        "dashboard/templates/cache_stats.html",
        "sample_repo/src/auth.py",
        "sample_repo/src/calculator.py",
        "sample_repo/src/utils.py",
        "sample_repo/tests/test_auth.py",
        "sample_repo/tests/test_calculator.py",
        "sample_repo/tests/test_utils.py",
        "LANGUAGE_AWARE_CACHING.md",
        "README.md",
        "demo_language_aware.py"
    ]
    
    all_exist = True
    for file in files_to_check:
        path = root / file
        if path.exists():
            print(f"✓ {file}")
        else:
            print(f"✗ {file} (missing)")
            all_exist = False
    
    return all_exist

def check_database():
    """Check/create database."""
    try:
        from dashboard.models import init_db
        db_path = Path("ci.db")
        
        if not db_path.exists():
            print("Creating database...")
            init_db()
        
        print(f"✓ Database ({db_path})")
        return True
    except Exception as e:
        print(f"✗ Database error: {e}")
        return False

def check_imports():
    """Check all critical imports work."""
    imports_to_check = [
        ("ci_engine.cache_manager", ["get_file_language", "load_language_aware_cache"]),
        ("ci_engine.change_detector", ["get_changed_files_by_language"]),
        ("ci_engine.pipeline_runner", ["run_pipeline"]),
        ("ci_engine.language_utils", ["get_language_stats"]),
        ("dashboard.app", ["app"]),
    ]
    
    all_ok = True
    for module_name, items in imports_to_check:
        try:
            module = __import__(module_name, fromlist=items)
            for item in items:
                if not hasattr(module, item):
                    print(f"✗ {module_name}.{item} not found")
                    all_ok = False
            print(f"✓ {module_name}")
        except ImportError as e:
            print(f"✗ {module_name}: {e}")
            all_ok = False
    
    return all_ok

def main():
    """Run all checks."""
    print("\n")
    print("=" * 60)
    print("HybridCI Setup Verification".center(60))
    print("=" * 60 + "\n")
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Project Structure", check_project_structure),
        ("Database", check_database),
        ("Imports", check_imports),
    ]
    
    results = {}
    for name, check in checks:
        print(f"\n{'='*60}")
        print(f"  {name}")
        print('='*60)
        try:
            results[name] = check()
        except Exception as e:
            print(f"✗ Error during check: {e}")
            results[name] = False
    
    # Summary
    print(f"\n{'='*60}")
    print("  SUMMARY")
    print('='*60)
    
    all_passed = all(results.values())
    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")
    
    print()
    if all_passed:
        print("✨ All checks passed! Setup is complete.\n")
        print("Next steps:")
        print("  1. Run the demo: python demo_language_aware.py")
        print("  2. Start the dashboard: python dashboard/app.py")
        print("  3. Open http://localhost:5000")
        print("  4. Run tests: pytest ci_engine/test_language_aware.py -v\n")
    else:
        print("⚠️  Some checks failed. Please fix the issues above.\n")
        print("Common fixes:")
        print("  • Install dependencies: pip install flask pytest")
        print("  • Ensure you're in the project root directory")
        print("  • Check file paths and permissions\n")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
