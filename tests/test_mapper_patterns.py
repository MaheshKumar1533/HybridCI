import unittest
import sys
import os

# Ensure impact_engine can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from impact_engine import DependencyGraph

class TestMapperPatterns(unittest.TestCase):
    def test_webpack_patterns(self):
        mock_graph = {
            "src/index.js": [],
            "test/configCases/asset-modules/index.js": [],
            "components/button.spec.js": [],
            "utils/math.test.ts": []
        }
        dg = DependencyGraph(mock_graph)
        tests = dg.all_tests()
        
        self.assertIn("test/configCases/asset-modules/index.js", tests)
        self.assertIn("components/button.spec.js", tests)
        self.assertIn("utils/math.test.ts", tests)
        self.assertNotIn("src/index.js", tests)

    def test_pandas_patterns(self):
        mock_graph = {
            "pandas/core/frame.py": [],
            "pandas/tests/frame/test_api.py": [],
            "pandas/tests/series/test_constructors.py": []
        }
        dg = DependencyGraph(mock_graph)
        tests = dg.all_tests()
        
        self.assertIn("pandas/tests/frame/test_api.py", tests)
        self.assertIn("pandas/tests/series/test_constructors.py", tests)
        self.assertNotIn("pandas/core/frame.py", tests)

    def test_spring_patterns(self):
        mock_graph = {
            "src/main/java/com/example/App.java": [],
            "src/test/java/com/example/AppTests.java": [],
            "src/test/java/com/example/IntegrationTest.java": []
        }
        dg = DependencyGraph(mock_graph)
        tests = dg.all_tests()
        
        self.assertIn("src/test/java/com/example/AppTests.java", tests)
        self.assertIn("src/test/java/com/example/IntegrationTest.java", tests)
        self.assertNotIn("src/main/java/com/example/App.java", tests)

if __name__ == "__main__":
    unittest.main()
