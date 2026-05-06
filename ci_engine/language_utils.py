"""
Language-aware utilities for cache management and test selection.
Provides functions to analyze code changes by programming language.
"""

from pathlib import Path
from ci_engine.cache_manager import get_file_language, LANGUAGE_EXTENSIONS
from ci_engine.change_detector import get_changed_files

def get_language_stats():
    """Analyze all project files and return language distribution."""
    stats = {
        "total_files": 0,
        "by_language": {}
    }
    
    # Scan current directory recursively
    for file in Path(".").rglob("*"):
        if file.is_file() and not file.parts[0].startswith("."):
            lang = get_file_language(str(file))
            if lang != "unknown":
                stats["total_files"] += 1
                if lang not in stats["by_language"]:
                    stats["by_language"][lang] = []
                stats["by_language"][lang].append(str(file))
    
    return stats

def get_changed_languages():
    """Get list of languages affected by recent changes."""
    changed_files = get_changed_files()
    languages = set()
    
    for file in changed_files:
        lang = get_file_language(file)
        if lang != "unknown":
            languages.add(lang)
    
    return sorted(list(languages))

def get_language_file_count(directory, language=None):
    """Count files of a specific language in a directory."""
    count = 0
    for file in Path(directory).rglob("*"):
        if file.is_file():
            if language is None or get_file_language(str(file)) == language:
                count += 1
    return count

def analyze_file_impact(filepath):
    """Analyze potential impact of a file change based on language and type."""
    lang = get_file_language(filepath)
    name = Path(filepath).name
    
    impact = {
        "language": lang,
        "filename": name,
        "is_test": "test" in name.lower(),
        "is_config": name in ["package.json", "pyproject.toml", "requirements.txt", "pom.xml", "build.gradle"],
        "is_shared": any(x in str(filepath).lower() for x in ["utils", "common", "shared", "helpers"]),
        "estimated_impact": "high" if any([
            "test" in name.lower(),
            name in ["package.json", "pyproject.toml", "requirements.txt", "pom.xml", "build.gradle"],
            "utils" in str(filepath).lower()
        ]) else "low"
    }
    
    return impact

def get_language_test_runners(language):
    """Get recommended test runners for a given language."""
    runners = {
        "python": ["pytest", "unittest", "nose"],
        "javascript": ["jest", "mocha", "jasmine"],
        "typescript": ["jest", "mocha", "vitest"],
        "java": ["junit", "testng"],
        "csharp": ["nunit", "xunit", "mstest"],
        "go": ["testing", "testify"],
        "rust": ["cargo test"],
        "ruby": ["rspec", "minitest"],
        "php": ["phpunit", "pest"],
    }
    return runners.get(language, [])

def format_language_report(language_breakdown):
    """Format language breakdown data into a readable report."""
    report = "Language-Aware Test Execution Report\n"
    report += "=" * 40 + "\n"
    
    total_tests = sum(language_breakdown.values())
    for lang, count in sorted(language_breakdown.items(), key=lambda x: x[1], reverse=True):
        pct = (count / total_tests * 100) if total_tests > 0 else 0
        report += f"{lang:15} {count:3} tests ({pct:5.1f}%)\n"
    
    report += "=" * 40 + "\n"
    report += f"{'Total':15} {total_tests:3} tests\n"
    
    return report
