"""
Unit tests for language-aware caching functionality.
"""

import os
import sys
import tempfile
import json
import pytest
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ci_engine.cache_manager import (
    get_file_language,
    LANGUAGE_EXTENSIONS,
    save_language_aware_cache,
    load_language_aware_cache,
    save_language_map,
    get_cache_stats
)
from ci_engine.language_utils import (
    get_language_stats,
    analyze_file_impact,
    get_language_test_runners,
    format_language_report
)

class TestLanguageDetection:
    """Test language detection from file extensions."""
    
    def test_python_detection(self):
        assert get_file_language("test.py") == "python"
        assert get_file_language("script.py") == "python"
    
    def test_javascript_detection(self):
        assert get_file_language("index.js") == "javascript"
        assert get_file_language("app.js") == "javascript"
    
    def test_typescript_detection(self):
        assert get_file_language("types.ts") == "typescript"
        assert get_file_language("main.tsx") == "tsx"
    
    def test_java_detection(self):
        assert get_file_language("Main.java") == "java"
    
    def test_csharp_detection(self):
        assert get_file_language("Program.cs") == "csharp"
    
    def test_cpp_detection(self):
        assert get_file_language("main.cpp") == "cpp"
        assert get_file_language("header.h") == "c"
    
    def test_rust_detection(self):
        assert get_file_language("lib.rs") == "rust"
    
    def test_go_detection(self):
        assert get_file_language("main.go") == "go"
    
    def test_unknown_detection(self):
        assert get_file_language("readme.txt") == "unknown"
        assert get_file_language("config.json") == "unknown"

class TestLanguageExtensions:
    """Test LANGUAGE_EXTENSIONS mapping."""
    
    def test_mapping_contains_common_languages(self):
        assert ".py" in LANGUAGE_EXTENSIONS
        assert ".js" in LANGUAGE_EXTENSIONS
        assert ".ts" in LANGUAGE_EXTENSIONS
        assert ".java" in LANGUAGE_EXTENSIONS
    
    def test_all_values_are_strings(self):
        for ext, lang in LANGUAGE_EXTENSIONS.items():
            assert isinstance(lang, str)
            assert lang != ""

class TestFileImpactAnalysis:
    """Test file impact analysis."""
    
    def test_test_file_marked_as_test(self):
        impact = analyze_file_impact("test_main.py")
        assert impact["is_test"] == True
        assert impact["language"] == "python"
    
    def test_config_file_marked_as_config(self):
        impact = analyze_file_impact("requirements.txt")
        assert impact["is_config"] == True
    
    def test_utils_file_marked_as_shared(self):
        impact = analyze_file_impact("src/utils.py")
        assert impact["is_shared"] == True
    
    def test_test_file_high_impact(self):
        impact = analyze_file_impact("test_auth.py")
        assert impact["estimated_impact"] == "high"
    
    def test_regular_file_low_impact(self):
        impact = analyze_file_impact("src/models/user.py")
        assert impact["estimated_impact"] == "low"

class TestLanguageTestRunners:
    """Test language to test runner mapping."""
    
    def test_python_runners(self):
        runners = get_language_test_runners("python")
        assert "pytest" in runners
        assert "unittest" in runners
    
    def test_javascript_runners(self):
        runners = get_language_test_runners("javascript")
        assert "jest" in runners
        assert "mocha" in runners
    
    def test_java_runners(self):
        runners = get_language_test_runners("java")
        assert "junit" in runners
    
    def test_unknown_language_returns_empty(self):
        runners = get_language_test_runners("unknown")
        assert runners == []

class TestLanguageReportFormatting:
    """Test report formatting."""
    
    def test_format_language_report(self):
        breakdown = {
            "python": 15,
            "javascript": 10,
            "typescript": 5
        }
        report = format_language_report(breakdown)
        
        assert "python" in report.lower()
        assert "javascript" in report.lower()
        assert "15" in report
        assert "10" in report
        assert "5" in report
        assert "30" in report  # Total
    
    def test_report_includes_percentages(self):
        breakdown = {"python": 50, "java": 50}
        report = format_language_report(breakdown)
        
        # Should show 50% for both
        assert "50" in report

def test_language_aware_cache_operations():
    """Test language-aware cache save and load operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Monkey-patch the cache directory
        import ci_engine.cache_manager as cm
        original_dir = cm.LANGUAGE_AWARE_CACHE_DIR
        cm.LANGUAGE_AWARE_CACHE_DIR = tmpdir
        
        try:
            cache_key = "test_cache_123"
            language = "python"
            data = {"tests": ["test_1.py", "test_2.py"], "time": 2.5}
            
            # Save and load
            save_language_aware_cache(cache_key, data, language)
            loaded = load_language_aware_cache(cache_key, language)
            
            assert loaded is not None
            assert loaded["tests"] == data["tests"]
            assert loaded["time"] == data["time"]
        
        finally:
            cm.LANGUAGE_AWARE_CACHE_DIR = original_dir

def test_language_map_operations():
    """Test language map save and load operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        import ci_engine.cache_manager as cm
        original_dir = cm.LANGUAGE_AWARE_CACHE_DIR
        cm.LANGUAGE_AWARE_CACHE_DIR = tmpdir
        
        try:
            from ci_engine.cache_manager import save_language_map, load_language_aware_cache
            
            cache_key = "test_map_456"
            lang_map = {
                "python": ["src/main.py", "src/utils.py"],
                "javascript": ["src/app.js"]
            }
            
            save_language_map(cache_key, lang_map)
            loaded = load_language_aware_cache(cache_key, None)
            
            assert loaded is not None
            assert loaded["python"] == lang_map["python"]
            assert loaded["javascript"] == lang_map["javascript"]
        
        finally:
            cm.LANGUAGE_AWARE_CACHE_DIR = original_dir

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
