#!/usr/bin/env python
"""
Demonstration script for language-aware caching functionality.
Shows how the system detects languages, manages caches, and provides insights.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ci_engine.cache_manager import (
    get_file_language,
    LANGUAGE_EXTENSIONS,
    get_cache_stats
)
from ci_engine.language_utils import (
    get_language_stats,
    analyze_file_impact,
    get_language_test_runners,
    format_language_report
)
from ci_engine.change_detector import get_changed_files_by_language

def demo_language_detection():
    """Demonstrate language detection capabilities."""
    print("\n" + "="*60)
    print("[LANGUAGE DETECTION DEMO]")
    print("="*60)
    
    test_files = [
        "src/main.py",
        "src/app.js",
        "src/types.ts",
        "src/Main.java",
        "src/Program.cs",
        "src/main.cpp",
        "src/lib.rs",
        "README.md",
        "package.json"
    ]
    
    print(f"\nSupported languages: {len(LANGUAGE_EXTENSIONS)}")
    print(f"Extensions: {', '.join(sorted(set(LANGUAGE_EXTENSIONS.values())))}\n")
    
    print("File Language Detection:")
    print("-" * 40)
    for file in test_files:
        lang = get_file_language(file)
        status = "OK" if lang != "unknown" else "?"
        print(f"  {status} {file:25} -> {lang}")

def demo_file_impact_analysis():
    """Demonstrate file impact analysis."""
    print("\n" + "="*60)
    print("[FILE IMPACT ANALYSIS DEMO]")
    print("="*60)
    
    test_files = [
        "test_main.py",
        "src/utils.py",
        "requirements.txt",
        "src/models/user.py",
        "src/common/helpers.js"
    ]
    
    print("\nFile Impact Assessment:")
    print("-" * 40)
    for file in test_files:
        impact = analyze_file_impact(file)
        print(f"\n[FILE] {file}")
        print(f"   Language: {impact['language']}")
        print(f"   Is Test: {impact['is_test']}")
        print(f"   Is Config: {impact['is_config']}")
        print(f"   Is Shared: {impact['is_shared']}")
        print(f"   Impact Level: {impact['estimated_impact'].upper()}")

def demo_test_runners():
    """Demonstrate language to test runner mapping."""
    print("\n" + "="*60)
    print("[TEST RUNNER RECOMMENDATIONS]")
    print("="*60)
    
    languages = ["python", "javascript", "typescript", "java", "csharp", "go", "rust"]
    
    print("\nRecommended Test Runners by Language:")
    print("-" * 40)
    for lang in languages:
        runners = get_language_test_runners(lang)
        runners_str = ", ".join(runners) if runners else "None"
        print(f"  {lang:15} -> {runners_str}")

def demo_language_report():
    """Demonstrate language report formatting."""
    print("\n" + "="*60)
    print("[LANGUAGE EXECUTION REPORT]")
    print("="*60)
    
    # Simulate a multi-language test execution
    breakdown = {
        "python": 25,
        "javascript": 18,
        "typescript": 12,
        "java": 8,
        "csharp": 5
    }
    
    print("\n" + format_language_report(breakdown))

def demo_cache_statistics():
    """Demonstrate cache statistics."""
    print("\n" + "="*60)
    print("[CACHE STATISTICS]")
    print("="*60)
    
    stats = get_cache_stats()
    
    print(f"\nCache Directory: {stats['cache_dir']}")
    print(f"Language-Aware Dir: {stats['language_aware_dir']}")
    print(f"\nTotal Caches: {stats['total_caches']}")
    print(f"Language-Aware Caches: {stats['total_language_caches']}")
    print(f"\nLanguage Breakdown:")
    print("-" * 40)
    if stats['languages']:
        for lang, count in sorted(stats['languages'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {lang:15} {count:3} cache(s)")
    else:
        print("  No language-specific caches yet")

def demo_project_analysis():
    """Demonstrate project language analysis."""
    print("\n" + "="*60)
    print("[PROJECT LANGUAGE ANALYSIS]")
    print("="*60)
    
    try:
        stats = get_language_stats()
        
        print(f"\nTotal Files: {stats['total_files']}")
        print(f"Languages Found: {len(stats['by_language'])}\n")
        
        if stats['by_language']:
            print("Language Distribution:")
            print("-" * 40)
            
            # Sort by file count
            sorted_langs = sorted(
                stats['by_language'].items(),
                key=lambda x: len(x[1]),
                reverse=True
            )
            
            for lang, files in sorted_langs:
                count = len(files)
                print(f"  {lang:15} {count:3} file(s)")
                # Show first 2 files as examples
                for f in files[:2]:
                    print(f"    * {f}")
                if count > 2:
                    print(f"    * ... and {count-2} more")
        else:
            print("No supported language files found in project")
    
    except Exception as e:
        print(f"Note: Project analysis skipped ({e})")

def demo_changed_files():
    """Demonstrate changed files detection."""
    print("\n" + "="*60)
    print("[CHANGED FILES DETECTION]")
    print("="*60)
    
    try:
        language_map, all_files = get_changed_files_by_language()
        
        if all_files:
            print(f"\nTotal Changed Files: {len(all_files)}")
            print(f"Languages Affected: {len(language_map)}\n")
            
            print("Changes by Language:")
            print("-" * 40)
            for lang, files in sorted(language_map.items()):
                print(f"\n  {lang.upper()}: {len(files)} file(s)")
                for f in files:
                    print(f"    * {f}")
        else:
            print("\nNo recent changes detected (not in git repo or clean working tree)")
    
    except Exception as e:
        print(f"\nNote: Change detection skipped ({e})")
        print("Ensure you're in a git repository for change detection demo")

def main():
    """Run all demonstrations."""
    print("\n")
    print("=" * 60)
    print("HYBRIDCI - Language-Aware Caching Demonstration".center(60))
    print("=" * 60)
    
    # Run demonstrations
    demo_language_detection()
    demo_file_impact_analysis()
    demo_test_runners()
    demo_language_report()
    demo_cache_statistics()
    demo_project_analysis()
    demo_changed_files()
    
    # Summary
    print("\n" + "="*60)
    print("[DEMONSTRATION COMPLETE]")
    print("="*60)
    print("\nKey Features Demonstrated:")
    print("  [OK] Language detection from file extensions")
    print("  [OK] File impact analysis for change assessment")
    print("  [OK] Language-specific test runner recommendations")
    print("  [OK] Multi-language execution reports")
    print("  [OK] Cache statistics and breakdown")
    print("  [OK] Project language composition analysis")
    print("  [OK] Git-based change detection by language")
    
    print("\nNext Steps:")
    print("  1. Visit http://localhost:5000 to see the dashboard")
    print("  2. Run: python dashboard/app.py")
    print("  3. Click 'Run CI Pipeline' to test language-aware caching")
    print("  4. View /cache-stats for detailed analytics")
    
    print("\nDocumentation:")
    print("  * See LANGUAGE_AWARE_CACHING.md for detailed guide")
    print("  * See README.md for project overview")
    print("  * Run: pytest ci_engine/test_language_aware.py -v for tests\n")

if __name__ == "__main__":
    main()
