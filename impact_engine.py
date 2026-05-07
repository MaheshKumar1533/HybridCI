import ast
import sqlite3
import os
import re
from collections import deque
from db_setup import _init_db

class DependencyGraph:
    def __init__(self, graph):
        self.graph = graph
        
    def all_tests(self):
        # Return all files that match common test naming patterns
        tests = []
        for f in self.graph.keys():
            base = os.path.basename(f)
            path_lower = f.replace("\\", "/").lower()
            
            # 1. Standard: test_ prefix or _test in name
            if base.startswith("test_") or "_test" in base:
                tests.append(f)
            # 2. JS/Webpack: .test.js, .spec.js, or inside test/ folder
            elif ".test." in base or ".spec." in base or "/test/" in path_lower or "/tests/" in path_lower or path_lower.startswith("test/") or path_lower.startswith("tests/"):
                tests.append(f)
            # 3. Java/Spring: Test.java, Tests.java
            elif base.endswith("Test.java") or base.endswith("Tests.java"):
                tests.append(f)
                
        return list(set(tests))
        
    def get_shortest_path(self, test, changed_file):
        # Simple BFS to find shortest path from changed_file to test
        # We need to reverse the graph logic: "who imports me?"
        # The graph is {file: [imported_modules]}
        # We'll map file to a normalized module name
        changed_module = self._get_module_name(changed_file)
        test_module = self._get_module_name(test)
        
        # Build adjacency list: module -> list of modules that import it
        adj = {}
        for f, imports in self.graph.items():
            mod_f = self._get_module_name(f)
            if mod_f not in adj:
                adj[mod_f] = []
            for imp in imports:
                if imp not in adj:
                    adj[imp] = []
                adj[imp].append(mod_f)
                
        # BFS from changed_module
        if changed_module not in adj:
            # Fallback
            if changed_module in test_module:
                return 1
            return float('inf')
            
        queue = deque([(changed_module, 0)])
        visited = set([changed_module])
        
        while queue:
            curr, dist = queue.popleft()
            if curr == test_module:
                return dist
            
            for neighbor in adj.get(curr, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, dist + 1))
                    
        # Fallback naming check
        if changed_module in test_module:
            return 1
            
        return float('inf')

    def _get_module_name(self, filepath):
        base = os.path.basename(filepath)
        name, _ = os.path.splitext(base)
        return name

class ImpactEngine:
    def __init__(self, db_path="ci.db"):
        _init_db(db_path)
        self.db_path = db_path

    def build_dependency_graph(self, root_dir):
        graph = {}
        # Regex for JS/TS imports
        js_import_re = re.compile(r'(?:import|require)\s*\(?[\'"]([^\'"]+)[\'"]')
        # Regex for Java imports
        java_import_re = re.compile(r'import\s+([a-zA-Z0-9_.]+);')
        
        for root, dirs, files in os.walk(root_dir):
            if any(ignore in root for ignore in ["venv", ".venv", ".git", "node_modules", "__pycache__", ".gradle", ".idea", "target", "build", "repos"]):
                continue
                
            for file in files:
                path = os.path.join(root, file)
                if file.endswith(".py"):
                    try:
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
                            graph[path.replace("\\", "/")] = imports
                    except Exception:
                        pass
                elif file.endswith(".js") or file.endswith(".jsx") or file.endswith(".ts") or file.endswith(".tsx"):
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            content = f.read()
                            imports = js_import_re.findall(content)
                            # Clean up relative paths
                            clean_imports = [imp.split("/")[-1] for imp in imports]
                            graph[path.replace("\\", "/")] = clean_imports
                    except Exception:
                        pass
                elif file.endswith(".java"):
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            content = f.read()
                            imports = java_import_re.findall(content)
                            # Get class name only from java imports
                            clean_imports = [imp.split(".")[-1] for imp in imports]
                            graph[path.replace("\\", "/")] = clean_imports
                    except Exception:
                        pass
        return graph

    def get_commit_frequency(self, changed_file):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # Normalize path
            c_file = changed_file.replace("\\", "/")
            cursor.execute("SELECT COUNT(*) FROM commit_history WHERE file_path LIKE ?", (f"%{c_file}%",))
            count = cursor.fetchone()[0]
            conn.close()
            # Normalize frequency 0-1 (assuming max 20 for normalization)
            return min(count / 20.0, 1.0)
        except Exception:
            return 0.5

    def get_overlap(self, test, changed_file):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            t_file = test.replace("\\", "/")
            c_file = changed_file.replace("\\", "/")
            cursor.execute("SELECT overlap FROM coverage WHERE test_file LIKE ? AND source_file LIKE ?", (f"%{t_file}%", f"%{c_file}%"))
            row = cursor.fetchone()
            conn.close()
            if row:
                return row[0]
            # Fallback mock overlap if missing
            return 0.3
        except Exception:
            return 0.3

def calculate_impact_score(modified_files, dependency_graph, impact_engine, weights=(0.5, 0.3, 0.2)):
    impact_scores = {}
    w1, w2, w3 = weights
    all_tests = dependency_graph.all_tests()
    
    for test in all_tests:
        total_score = 0
        for changed_file in modified_files:
            distance = dependency_graph.get_shortest_path(test, changed_file)
            if distance == float('inf'):
                continue
                
            term1 = (1.0 / distance) if distance > 0 else 1.0
            overlap = impact_engine.get_overlap(test, changed_file)
            term2 = overlap
            frequency = impact_engine.get_commit_frequency(changed_file)
            term3 = frequency
            
            is_score = (w1 * term1) + (w2 * term2) + (w3 * term3)
            total_score += is_score
            
        if total_score > 0:
            impact_scores[test] = total_score 
            
    return impact_scores

def select_tests(impact_scores, threshold=0.4):
    return [test for test, score in impact_scores.items() if score >= threshold]

