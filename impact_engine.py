import ast
import sqlite3
import os
from db_setup import _init_db

class DependencyGraphMock:
    def __init__(self, graph):
        self.graph = graph
        
    def all_tests(self):
        # Return all files ending with test_
        return [f for f in self.graph.keys() if os.path.basename(f).startswith("test_")]
        
    def get_shortest_path(self, test, changed_file):
        changed_module = os.path.splitext(os.path.basename(changed_file))[0]
        
        # Check if the test file directly imports the changed module
        test_imports = self.graph.get(test, [])
        if changed_module in test_imports:
            return 1
            
        # Fallback: check standard naming convention (test_xyz.py depends on xyz.py)
        test_name = os.path.basename(test)
        if changed_module in test_name:
            return 1
            
        # No dependency path found
        return float('inf')

    def get_commit_frequency(self, changed_file):
        return 0.5

class CoverageMatrixMock:
    def get_overlap(self, test, changed_file):
        return 0.8

class ImpactEngine:
    def __init__(self, db_path="ci.db"):
        _init_db(db_path)
        self.conn = sqlite3.connect(db_path)

    def build_dependency_graph(self, root_dir):
        graph = {}
        for root, dirs, files in os.walk(root_dir):
            if "venv" in dirs:
                dirs.remove("venv")
            if ".venv" in dirs:
                dirs.remove(".venv")
            if ".git" in dirs:
                dirs.remove(".git")
            for file in files:
                if file.endswith(".py"):
                    path = os.path.join(root, file)
                    with open(path, "r", encoding="utf-8") as f:
                        tree = ast.parse(f.read())
                        imports = []
                        for node in ast.walk(tree):
                            if isinstance(node, ast.Import):
                                for alias in node.names:
                                    imports.append(alias.name)
                            elif isinstance(node, ast.ImportFrom):
                                if node.module:
                                    imports.append(node.module)
                        graph[path] = imports
        return graph

def calculate_impact_score(modified_files, dependency_graph, coverage_matrix, weights=(0.5, 0.3, 0.2)):
    impact_scores = {}
    w1, w2, w3 = weights
    for test in dependency_graph.all_tests():
        total_score = 0
        for changed_file in modified_files:
            distance = dependency_graph.get_shortest_path(test, changed_file)
            if distance == float('inf'):
                continue  # No path means 0 impact
                
            term1 = (1.0 / distance) if distance > 0 else 0
            overlap = coverage_matrix.get_overlap(test, changed_file)
            term2 = overlap
            frequency = dependency_graph.get_commit_frequency(changed_file)
            term3 = frequency
            is_score = (w1 * term1) + (w2 * term2) + (w3 * term3)
            total_score += is_score
        impact_scores[test] = total_score 
    return impact_scores

def select_tests(impact_scores, threshold=0.4):
    return [test for test, score in impact_scores.items() if score >= threshold]
