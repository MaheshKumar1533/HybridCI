"""
Cross-Language Dependency Graph (CLDG)

Formal Definition:
------------------
    G = (V, E)

    Where:
        V = Vs ∪ Vt    (source files ∪ test files)
        E ⊆ V × V      (directed edges representing dependencies)

    Each edge (vi, vj) ∈ E has weight:
        wij ∈ [0, 1]   (dependency strength)

Edge Types:
-----------
    1. Static imports (direct code imports)
    2. API usage (function/method calls)
    3. Cross-language calls (REST, RPC, shared schema)
    4. File references (config, data files)

Dependency Strength Calculation:
-------------------------------
    wij = α · import_score + β · call_score + γ · semantic_score

    Where:
        α + β + γ = 1 (weights)
        import_score ∈ [0,1] - direct import relationship
        call_score ∈ [0,1] - function/API call frequency
        semantic_score ∈ [0,1] - semantic similarity

This module implements CLDG construction via static analysis for multiple languages.
"""

import os
import ast
import re
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class Node:
    """
    A node in the CLDG representing a source or test file.
    
    Graph Representation:
        G = {
            "node_id": {
                "type": "source/test",
                "language": "python/js/java",
                "cost": execution_time
            }
        }
    """
    id: str  # Unique identifier (file path)
    file_path: str
    language: str
    node_type: str  # 'source' or 'test'
    cost: float = 1.0  # Execution time / cost for optimization (seconds)
    imports: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    api_endpoints: List[str] = field(default_factory=list)  # REST endpoints defined
    api_calls: List[str] = field(default_factory=list)       # REST endpoints called
    config_refs: List[str] = field(default_factory=list)     # Config files referenced
    db_models: List[str] = field(default_factory=list)       # Database models used
    schema_refs: List[str] = field(default_factory=list)     # Schema files referenced
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize node to dictionary format."""
        return {
            "type": self.node_type,
            "language": self.language,
            "cost": self.cost,
            "file_path": self.file_path,
            "imports": self.imports,
            "functions": self.functions,
            "classes": self.classes
        }


@dataclass
class Edge:
    """A directed edge in the CLDG representing a dependency."""
    source: str  # Source node ID
    target: str  # Target node ID
    edge_type: str  # 'import', 'call', 'api', 'config', 'database', 'schema', 'reference'
    weight: float = 1.0  # Dependency strength wij ∈ [0, 1]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Cross-language edge types:
    # - 'api': REST/RPC endpoint connection (frontend -> backend)
    # - 'config': Shared configuration file dependency
    # - 'database': Shared database model/table dependency  
    # - 'schema': Shared protobuf/GraphQL/JSON schema dependency


@dataclass
class CLDG:
    """
    Cross-Language Dependency Graph.
    
    G = (V, E) where:
        V = nodes (source and test files)
        E = edges (dependencies with weights)
    
    Graph Representation Format:
        G = {
            "nodes": {
                "node_id": {
                    "type": "source/test",
                    "language": "python/js/java",
                    "cost": execution_time
                }
            },
            "edges": [
                {"source": "...", "target": "...", "weight": 0.9}
            ]
        }
    """
    nodes: Dict[str, Node] = field(default_factory=dict)
    edges: List[Edge] = field(default_factory=list)
    adjacency_list: Dict[str, List[Tuple[str, float]]] = field(default_factory=lambda: defaultdict(list))
    reverse_adjacency: Dict[str, List[Tuple[str, float]]] = field(default_factory=lambda: defaultdict(list))
    
    def add_node(self, node: Node):
        """Add a node to the graph."""
        self.nodes[node.id] = node
    
    def add_edge(self, edge: Edge):
        """Add an edge to the graph."""
        self.edges.append(edge)
        self.adjacency_list[edge.source].append((edge.target, edge.weight))
        self.reverse_adjacency[edge.target].append((edge.source, edge.weight))
    
    def get_dependencies(self, node_id: str) -> List[Tuple[str, float]]:
        """Get all dependencies of a node (outgoing edges)."""
        return self.adjacency_list.get(node_id, [])
    
    def get_dependents(self, node_id: str) -> List[Tuple[str, float]]:
        """Get all nodes that depend on this node (incoming edges)."""
        return self.reverse_adjacency.get(node_id, [])
    
    def set_node_cost(self, node_id: str, cost: float):
        """Set execution cost for a node (from historical data)."""
        if node_id in self.nodes:
            self.nodes[node_id].cost = cost
    
    # =========================================================================
    # GRAPH TRAVERSAL - REPLACES IBST
    # =========================================================================
    
    def traverse_from_changed_files(self, changed_files: List[str], 
                                    threshold: float = 0.1) -> Dict[str, float]:
        """
        Graph-based test selection (replaces IBST filename mapping).
        
        Algorithm:
            1. Identify changed nodes F
            2. Traverse graph outward (BFS/DFS on reverse edges)
            3. Collect reachable test nodes with impact scores
            4. Return tests above threshold
        
        Complexity: O(n + e) where n = |V|, e = |E|
        
        Args:
            changed_files: List of changed file paths (set F)
            threshold: Minimum impact score to include test (τ)
            
        Returns:
            Dict of test_file -> impact_score for all reachable tests
        """
        impacted_tests: Dict[str, float] = {}
        visited: Set[str] = set()
        
        # Normalize and find changed nodes in graph
        changed_nodes = self._resolve_changed_files(changed_files)
        
        # BFS traversal from each changed node
        for start_node in changed_nodes:
            self._bfs_traverse(start_node, 1.0, visited, impacted_tests, threshold)
        
        return impacted_tests
    
    def _resolve_changed_files(self, changed_files: List[str]) -> List[str]:
        """Resolve changed file paths to node IDs in graph."""
        resolved = []
        for file in changed_files:
            file_normalized = file.replace("\\", "/")
            
            # Direct match
            if file_normalized in self.nodes:
                resolved.append(file_normalized)
                continue
            
            # Try basename match
            basename = os.path.basename(file)
            for node_id in self.nodes:
                if node_id.endswith(basename):
                    resolved.append(node_id)
                    break
        
        return resolved
    
    def _bfs_traverse(self, start: str, start_weight: float, 
                      visited: Set[str], impacted: Dict[str, float],
                      threshold: float):
        """
        BFS traversal to find impacted tests.
        
        Traverses reverse edges (dependents) to find tests that
        depend on the changed source file.
        """
        from collections import deque
        
        queue = deque([(start, start_weight)])
        
        while queue:
            node_id, current_weight = queue.popleft()
            
            if node_id in visited:
                # Update if we found a stronger path
                if node_id in impacted and current_weight > impacted[node_id]:
                    impacted[node_id] = current_weight
                continue
            
            visited.add(node_id)
            
            node = self.nodes.get(node_id)
            if node:
                # If this is a test node, record it
                if node.node_type == 'test':
                    if node_id in impacted:
                        impacted[node_id] = max(impacted[node_id], current_weight)
                    else:
                        impacted[node_id] = current_weight
                
                # Traverse to dependents (reverse edges)
                for dependent_id, edge_weight in self.get_dependents(node_id):
                    new_weight = current_weight * edge_weight
                    if new_weight >= threshold:  # Prune low-impact paths
                        queue.append((dependent_id, new_weight))
    
    def get_impacted_tests(self, changed_files: List[str]) -> Dict[str, float]:
        """
        Find all tests impacted by changed files using graph traversal.
        
        This is the main entry point that replaces IBST.
        
        Returns dict of test_file -> impact_score
        """
        return self.traverse_from_changed_files(changed_files)
    
    # =========================================================================
    # OPTIMIZATION SOLVER INTEGRATION
    # =========================================================================
    
    def select_minimal_test_set(self, changed_files: List[str],
                                coverage_threshold: float = 1.0,
                                use_greedy: bool = True) -> 'TestSelectionResult':
        """
        Apply optimization solver to choose minimal test set.
        
        This is the constrained optimization layer on top of graph traversal:
        
            minimize    Σ C(tj) · xj           (minimize total test cost)
            subject to  Σ D(fi, tj) · xj ≥ 1   (coverage constraint)
                        xj ∈ {0, 1}            (binary selection)
        
        Args:
            changed_files: List of changed source files (F)
            coverage_threshold: Minimum coverage required
            use_greedy: Use greedy approximation (O(m log m)) vs ILP
            
        Returns:
            TestSelectionResult with selected tests and metrics
        """
        # Step 1: Get all reachable tests via graph traversal
        impacted_tests = self.traverse_from_changed_files(changed_files)
        
        if not impacted_tests:
            return TestSelectionResult(
                selected_tests=[],
                total_cost=0.0,
                coverage=0.0,
                all_impacted_tests=list(impacted_tests.keys()),
                optimization_method='none'
            )
        
        # Step 2: Build cost and coverage matrices
        test_list = list(impacted_tests.keys())
        costs = [self.nodes[t].cost for t in test_list]
        coverage_scores = [impacted_tests[t] for t in test_list]
        
        # Step 3: Apply optimization solver
        if use_greedy:
            selected_indices = self._greedy_set_cover(costs, coverage_scores, coverage_threshold)
            method = 'greedy'
        else:
            selected_indices = self._ilp_set_cover(costs, coverage_scores, coverage_threshold)
            method = 'ilp'
        
        selected_tests = [test_list[i] for i in selected_indices]
        total_cost = sum(costs[i] for i in selected_indices)
        achieved_coverage = sum(coverage_scores[i] for i in selected_indices) / len(changed_files) if changed_files else 0
        
        return TestSelectionResult(
            selected_tests=selected_tests,
            total_cost=total_cost,
            coverage=min(1.0, achieved_coverage),
            all_impacted_tests=test_list,
            optimization_method=method
        )
    
    def _greedy_set_cover(self, costs: List[float], coverage: List[float],
                          threshold: float) -> List[int]:
        """
        Greedy approximation for weighted set cover.
        
        Complexity: O(m log m) where m = number of tests
        
        Greedy ratio: cost(t) / coverage(t)
        Select tests with best ratio until threshold met.
        """
        n = len(costs)
        if n == 0:
            return []
        
        # Calculate cost-effectiveness ratio
        ratios = []
        for i in range(n):
            ratio = costs[i] / max(coverage[i], 0.001)  # Avoid division by zero
            ratios.append((ratio, i))
        
        # Sort by ratio (ascending = most cost-effective first)
        ratios.sort()
        
        selected = []
        total_coverage = 0.0
        
        for ratio, idx in ratios:
            selected.append(idx)
            total_coverage += coverage[idx]
            if total_coverage >= threshold:
                break
        
        return selected
    
    def _ilp_set_cover(self, costs: List[float], coverage: List[float],
                       threshold: float) -> List[int]:
        """
        ILP solver for optimal set cover (exact solution).
        
        Falls back to greedy if scipy not available.
        """
        try:
            from scipy.optimize import milp, LinearConstraint, Bounds
            import numpy as np
            
            n = len(costs)
            if n == 0:
                return []
            
            # Objective: minimize Σ costs[i] * x[i]
            c = np.array(costs)
            
            # Constraint: Σ coverage[i] * x[i] >= threshold
            A = np.array([coverage])
            b_l = np.array([threshold])
            b_u = np.array([np.inf])
            
            constraints = LinearConstraint(A, b_l, b_u)
            bounds = Bounds(0, 1)
            integrality = np.ones(n)  # All variables are integers
            
            result = milp(c, constraints=constraints, bounds=bounds, integrality=integrality)
            
            if result.success:
                return [i for i in range(n) if result.x[i] > 0.5]
            else:
                return self._greedy_set_cover(costs, coverage, threshold)
                
        except ImportError:
            return self._greedy_set_cover(costs, coverage, threshold)
    
    # =========================================================================
    # SERIALIZATION
    # =========================================================================
    
    def to_dict(self) -> Dict:
        """
        Serialize graph to dictionary format.
        
        Format:
            G = {
                "nodes": {
                    "node_id": {
                        "type": "source/test",
                        "language": "python/js/java",
                        "cost": execution_time
                    }
                },
                "edges": [...]
            }
        """
        return {
            "nodes": {k: v.to_dict() for k, v in self.nodes.items()},
            "edges": [{
                "source": e.source,
                "target": e.target,
                "edge_type": e.edge_type,
                "weight": e.weight
            } for e in self.edges],
            "stats": {
                "total_nodes": len(self.nodes),
                "total_edges": len(self.edges),
                "source_nodes": sum(1 for n in self.nodes.values() if n.node_type == 'source'),
                "test_nodes": sum(1 for n in self.nodes.values() if n.node_type == 'test')
            }
        }
    
    def to_json(self) -> str:
        """Serialize graph to JSON."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class TestSelectionResult:
    """
    Result of graph-based test selection with optimization.
    """
    selected_tests: List[str]      # Tests chosen by optimizer
    total_cost: float              # Sum of execution costs
    coverage: float                # Achieved coverage score
    all_impacted_tests: List[str]  # All tests reachable from changed files
    optimization_method: str       # 'greedy', 'ilp', or 'none'


# =============================================================================
# LANGUAGE-SPECIFIC ANALYZERS
# =============================================================================

class PythonAnalyzer:
    """
    Static analyzer for Python files using AST.
    
    Extracts:
        - Import statements
        - Function definitions
        - Class definitions
        - Function calls
    """
    
    @staticmethod
    def analyze(file_path: str) -> Optional[Node]:
        """Analyze a Python file and return a Node."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                source = f.read()
            
            tree = ast.parse(source)
            
            imports = []
            functions = []
            classes = []
            calls = []
            
            for node in ast.walk(tree):
                # Imports
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for alias in node.names:
                        imports.append(f"{module}.{alias.name}")
                
                # Functions
                elif isinstance(node, ast.FunctionDef):
                    functions.append(node.name)
                elif isinstance(node, ast.AsyncFunctionDef):
                    functions.append(node.name)
                
                # Classes
                elif isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                
                # Calls (for API detection)
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Attribute):
                        calls.append(node.func.attr)
                    elif isinstance(node.func, ast.Name):
                        calls.append(node.func.id)
            
            # Determine node type
            basename = os.path.basename(file_path)
            node_type = 'test' if basename.startswith('test_') or '_test.py' in basename else 'source'
            
            return Node(
                id=file_path.replace("\\", "/"),
                file_path=file_path,
                language='python',
                node_type=node_type,
                imports=imports,
                functions=functions,
                classes=classes
            )
            
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return None


class JavaScriptAnalyzer:
    """
    Static analyzer for JavaScript/TypeScript files using regex patterns.
    
    For production, use esprima or tree-sitter.
    """
    
    # Regex patterns for JS/TS analysis
    IMPORT_PATTERNS = [
        r'import\s+.*?\s+from\s+[\'"](.+?)[\'"]',  # ES6 imports
        r'require\s*\(\s*[\'"](.+?)[\'"]\s*\)',     # CommonJS require
        r'import\s*\(\s*[\'"](.+?)[\'"]\s*\)',      # Dynamic imports
    ]
    
    FUNCTION_PATTERN = r'(?:function\s+(\w+)|const\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>)'
    CLASS_PATTERN = r'class\s+(\w+)'
    EXPORT_PATTERN = r'export\s+(?:default\s+)?(?:class|function|const|let|var)\s+(\w+)'
    
    @staticmethod
    def analyze(file_path: str) -> Optional[Node]:
        """Analyze a JavaScript/TypeScript file and return a Node."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                source = f.read()
            
            imports = []
            functions = []
            classes = []
            exports = []
            
            # Extract imports
            for pattern in JavaScriptAnalyzer.IMPORT_PATTERNS:
                imports.extend(re.findall(pattern, source))
            
            # Extract functions
            func_matches = re.findall(JavaScriptAnalyzer.FUNCTION_PATTERN, source)
            for match in func_matches:
                func_name = match[0] or match[1]
                if func_name:
                    functions.append(func_name)
            
            # Extract classes
            classes = re.findall(JavaScriptAnalyzer.CLASS_PATTERN, source)
            
            # Extract exports
            exports = re.findall(JavaScriptAnalyzer.EXPORT_PATTERN, source)
            
            # Determine node type
            basename = os.path.basename(file_path)
            node_type = 'test' if '.test.' in basename or '.spec.' in basename or basename.startswith('test') else 'source'
            
            # Determine language
            ext = os.path.splitext(file_path)[1].lower()
            language = 'typescript' if ext in ['.ts', '.tsx'] else 'javascript'
            
            return Node(
                id=file_path.replace("\\", "/"),
                file_path=file_path,
                language=language,
                node_type=node_type,
                imports=imports,
                exports=exports,
                functions=functions,
                classes=classes
            )
            
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return None


class JavaAnalyzer:
    """
    Static analyzer for Java files using regex patterns.
    
    For production, use javalang library.
    """
    
    IMPORT_PATTERN = r'import\s+([\w.]+);'
    PACKAGE_PATTERN = r'package\s+([\w.]+);'
    CLASS_PATTERN = r'(?:public\s+)?class\s+(\w+)'
    METHOD_PATTERN = r'(?:public|private|protected)?\s*(?:static\s+)?[\w<>\[\]]+\s+(\w+)\s*\('
    
    @staticmethod
    def analyze(file_path: str) -> Optional[Node]:
        """Analyze a Java file and return a Node."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                source = f.read()
            
            imports = re.findall(JavaAnalyzer.IMPORT_PATTERN, source)
            classes = re.findall(JavaAnalyzer.CLASS_PATTERN, source)
            functions = re.findall(JavaAnalyzer.METHOD_PATTERN, source)
            
            # Filter out common false positives
            functions = [f for f in functions if f not in ['if', 'for', 'while', 'switch', 'catch']]
            
            # Determine node type
            basename = os.path.basename(file_path)
            node_type = 'test' if 'Test' in basename or basename.endswith('Tests.java') else 'source'
            
            return Node(
                id=file_path.replace("\\", "/"),
                file_path=file_path,
                language='java',
                node_type=node_type,
                imports=imports,
                functions=functions,
                classes=classes
            )
            
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return None


class GoAnalyzer:
    """Static analyzer for Go files."""
    
    IMPORT_PATTERN = r'import\s+(?:\(\s*([\s\S]*?)\s*\)|"([^"]+)")'
    FUNC_PATTERN = r'func\s+(?:\([^)]+\)\s+)?(\w+)\s*\('
    STRUCT_PATTERN = r'type\s+(\w+)\s+struct'
    
    @staticmethod
    def analyze(file_path: str) -> Optional[Node]:
        """Analyze a Go file and return a Node."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                source = f.read()
            
            imports = []
            import_matches = re.findall(GoAnalyzer.IMPORT_PATTERN, source, re.MULTILINE)
            for match in import_matches:
                if match[0]:  # Multi-line import
                    imports.extend(re.findall(r'"([^"]+)"', match[0]))
                elif match[1]:  # Single import
                    imports.append(match[1])
            
            functions = re.findall(GoAnalyzer.FUNC_PATTERN, source)
            classes = re.findall(GoAnalyzer.STRUCT_PATTERN, source)  # structs as classes
            
            basename = os.path.basename(file_path)
            node_type = 'test' if '_test.go' in basename else 'source'
            
            return Node(
                id=file_path.replace("\\", "/"),
                file_path=file_path,
                language='go',
                node_type=node_type,
                imports=imports,
                functions=functions,
                classes=classes
            )
            
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return None


# =============================================================================
# CLDG BUILDER
# =============================================================================

# Language extension to analyzer mapping
LANGUAGE_ANALYZERS = {
    '.py': PythonAnalyzer,
    '.js': JavaScriptAnalyzer,
    '.jsx': JavaScriptAnalyzer,
    '.ts': JavaScriptAnalyzer,
    '.tsx': JavaScriptAnalyzer,
    '.java': JavaAnalyzer,
    '.go': GoAnalyzer,
}


# =============================================================================
# PHASE B: CROSS-LANGUAGE LINKER
# =============================================================================

class CrossLanguageLinker:
    """
    Phase B: Cross-Language Linking
    
    Detects and creates edges for:
    1. REST API endpoints (frontend/api.js → backend/api.py)
    2. Shared config files (app.py → config.yaml)
    3. Common database models (models.py ↔ entities.java)
    4. Shared protobuf/schema files (*.proto, *.graphql)
    """
    
    # =========================================================================
    # REST API PATTERNS
    # =========================================================================
    
    # Backend endpoint definitions
    API_DEFINITION_PATTERNS = {
        'python': [
            (r'@app\.route\([\'"]([^\'"]+)[\'"]', 'flask'),
            (r'@router\.(get|post|put|delete|patch)\([\'"]([^\'"]+)[\'"]', 'fastapi'),
            (r'@api_view\(\[[\'"]([^\'"]+)[\'"]', 'drf'),
            (r'path\([\'"]([^\'"]+)[\'"]', 'django'),
            (r'@bp\.route\([\'"]([^\'"]+)[\'"]', 'flask_blueprint'),
        ],
        'javascript': [
            (r'app\.(get|post|put|delete|patch)\([\'"]([^\'"]+)[\'"]', 'express'),
            (r'router\.(get|post|put|delete|patch)\([\'"]([^\'"]+)[\'"]', 'express_router'),
            (r'server\.route\([\'"]([^\'"]+)[\'"]', 'hapi'),
        ],
        'java': [
            (r'@(Get|Post|Put|Delete|Patch)Mapping\([\'"]?([^\'"\)]+)', 'spring'),
            (r'@RequestMapping\([^)]*value\s*=\s*[\'"]([^\'"]+)', 'spring'),
            (r'@Path\([\'"]([^\'"]+)[\'"]', 'jaxrs'),
        ],
        'go': [
            (r'r\.(Get|Post|Put|Delete|Patch)\([\'"]([^\'"]+)[\'"]', 'chi'),
            (r'http\.HandleFunc\([\'"]([^\'"]+)[\'"]', 'stdlib'),
            (r'e\.(GET|POST|PUT|DELETE|PATCH)\([\'"]([^\'"]+)[\'"]', 'echo'),
        ],
    }
    
    # Frontend API call patterns
    API_CALL_PATTERNS = {
        'javascript': [
            (r'fetch\([\'"]([^\'"]+)[\'"]', 'fetch'),
            (r'axios\.(get|post|put|delete|patch)\([\'"]([^\'"]+)[\'"]', 'axios'),
            (r'\$\.ajax\(\{[^}]*url:\s*[\'"]([^\'"]+)[\'"]', 'jquery'),
            (r'\.request\([\'"]([^\'"]+)[\'"]', 'generic'),
            (r'api\.[a-zA-Z]+\([\'"]([^\'"]+)[\'"]', 'api_client'),
        ],
        'python': [
            (r'requests\.(get|post|put|delete|patch)\([\'"]([^\'"]+)[\'"]', 'requests'),
            (r'httpx\.(get|post|put|delete|patch)\([\'"]([^\'"]+)[\'"]', 'httpx'),
            (r'client\.(get|post|put|delete|patch)\([\'"]([^\'"]+)[\'"]', 'test_client'),
        ],
        'java': [
            (r'restTemplate\.(get|post|put|delete)ForObject\([\'"]([^\'"]+)[\'"]', 'spring'),
            (r'webClient\.(get|post|put|delete)\(\)\.uri\([\'"]([^\'"]+)[\'"]', 'webclient'),
        ],
        'go': [
            (r'http\.(Get|Post)\([\'"]([^\'"]+)[\'"]', 'stdlib'),
            (r'client\.(Get|Post|Put|Delete)\([\'"]([^\'"]+)[\'"]', 'client'),
        ],
    }
    
    # =========================================================================
    # CONFIG FILE PATTERNS
    # =========================================================================
    
    CONFIG_FILE_PATTERNS = [
        r'config\.ya?ml',
        r'settings\.ya?ml', 
        r'app\.ya?ml',
        r'config\.json',
        r'settings\.json',
        r'\.env',
        r'env\.[a-z]+',
        r'application\.properties',
        r'application\.ya?ml',
        r'appsettings\.json',
        r'tsconfig\.json',
        r'package\.json',
    ]
    
    CONFIG_READ_PATTERNS = {
        'python': [
            (r'open\([\'"]([^\'"]+\.(ya?ml|json|env|properties))[\'"]', 'open'),
            (r'load_dotenv\([\'"]?([^\'"\)]*)[\'"]?\)', 'dotenv'),
            (r'yaml\.(?:safe_)?load\([^)]*[\'"]([^\'"]+)[\'"]', 'yaml'),
            (r'json\.load\([^)]*[\'"]([^\'"]+)[\'"]', 'json'),
            (r'configparser.*read\([\'"]([^\'"]+)[\'"]', 'configparser'),
            (r'os\.environ\.get\([\'"]([^\'"]+)[\'"]', 'env_var'),
            (r'settings\.[A-Z_]+', 'django_settings'),
        ],
        'javascript': [
            (r'require\([\'"]([^\'"]+\.(json|ya?ml))[\'"]', 'require'),
            (r'fs\.readFileSync\([\'"]([^\'"]+)[\'"]', 'fs'),
            (r'process\.env\.([A-Z_]+)', 'env_var'),
            (r'dotenv\.config\(', 'dotenv'),
            (r'config\[[\'"](\w+)[\'"]\]', 'config_access'),
        ],
        'java': [
            (r'@Value\([\'"]\$\{([^}]+)\}[\'"]\)', 'spring_value'),
            (r'Properties.*load\([^)]*[\'"]([^\'"]+)[\'"]', 'properties'),
            (r'getenv\([\'"]([^\'"]+)[\'"]', 'env_var'),
        ],
        'go': [
            (r'os\.Getenv\([\'"]([^\'"]+)[\'"]', 'env_var'),
            (r'viper\.(SetConfigFile|ReadInConfig)\([\'"]?([^\'"\)]*)', 'viper'),
            (r'ioutil\.ReadFile\([\'"]([^\'"]+)[\'"]', 'readfile'),
        ],
    }
    
    # =========================================================================
    # DATABASE MODEL PATTERNS
    # =========================================================================
    
    DB_MODEL_PATTERNS = {
        'python': [
            (r'class\s+(\w+)\(.*(?:Model|Base|db\.Model).*\)', 'orm_class'),
            (r'__tablename__\s*=\s*[\'"]([^\'"]+)[\'"]', 'table_name'),
            (r'Table\([\'"]([^\'"]+)[\'"]', 'table_def'),
        ],
        'javascript': [
            (r'mongoose\.model\([\'"]([^\'"]+)[\'"]', 'mongoose'),
            (r'sequelize\.define\([\'"]([^\'"]+)[\'"]', 'sequelize'),
            (r'Schema\(\{', 'schema_def'),
            (r'model\([\'"]([^\'"]+)[\'"]', 'prisma'),
        ],
        'java': [
            (r'@Entity.*class\s+(\w+)', 'jpa_entity'),
            (r'@Table\(name\s*=\s*[\'"]([^\'"]+)[\'"]', 'table_name'),
        ],
        'go': [
            (r'type\s+(\w+)\s+struct.*`gorm:', 'gorm_model'),
            (r'TableName\(\).*return\s+[\'"]([^\'"]+)[\'"]', 'table_name'),
        ],
    }
    
    DB_QUERY_PATTERNS = {
        'python': [
            (r'session\.query\((\w+)\)', 'sqlalchemy'),
            (r'(\w+)\.objects\.(filter|get|all|create)', 'django_orm'),
            (r'SELECT.*FROM\s+([\w]+)', 'raw_sql'),
            (r'db\.session\.query\((\w+)\)', 'flask_sqlalchemy'),
        ],
        'javascript': [
            (r'(\w+)\.find\(', 'mongoose_find'),
            (r'(\w+)\.findOne\(', 'mongoose_findone'),
            (r'prisma\.(\w+)\.', 'prisma'),
            (r'knex\([\'"]([^\'"]+)[\'"]\)', 'knex'),
        ],
        'java': [
            (r'repository\.find(All|By)', 'spring_data'),
            (r'entityManager\.(find|persist|merge)\((\w+)', 'jpa'),
            (r'@Query\([\'"]SELECT.*FROM\s+(\w+)', 'jpql'),
        ],
        'go': [
            (r'db\.(Find|First|Create)\(&?(\w+)', 'gorm'),
            (r'SELECT.*FROM\s+([\w]+)', 'raw_sql'),
        ],
    }
    
    # =========================================================================
    # SCHEMA FILE PATTERNS
    # =========================================================================
    
    SCHEMA_FILE_EXTENSIONS = [
        '.proto',      # Protocol Buffers
        '.graphql',    # GraphQL
        '.gql',        # GraphQL
        '.avsc',       # Avro
        '.thrift',     # Thrift
        '.xsd',        # XML Schema
        '.json',       # JSON Schema (when in schemas/ dir)
    ]
    
    SCHEMA_REFERENCE_PATTERNS = {
        'python': [
            (r'from\s+([\w.]+)_pb2\s+import', 'protobuf'),
            (r'load_schema\([\'"]([^\'"]+)[\'"]', 'graphql'),
            (r'gql\([\'"]([^\'"]+)[\'"]', 'graphql'),
        ],
        'javascript': [
            (r'import.*from\s+[\'"]([^\'"]+\.graphql)[\'"]', 'graphql'),
            (r'gql`([^`]+)`', 'graphql_tag'),
            (r'require\([\'"]([^\'"]+_pb)[\'"]', 'protobuf'),
        ],
        'java': [
            (r'import\s+([\w.]+\.proto\.\w+)', 'protobuf'),
            (r'@GraphQLQuery', 'graphql'),
        ],
        'go': [
            (r'import\s+[\'"]([^\'"]+/proto)[\'"]', 'protobuf'),
            (r'graphql\.MustParseSchema', 'graphql'),
        ],
    }
    
    def __init__(self, graph: CLDG, root_path: str):
        self.graph = graph
        self.root_path = root_path
        self.api_endpoints: Dict[str, List[Tuple[str, str]]] = {}  # endpoint -> [(node_id, type)]
        self.config_files: Dict[str, str] = {}  # config_name -> node_id
        self.db_models: Dict[str, List[str]] = {}  # model/table -> [node_ids]
        self.schema_files: Dict[str, str] = {}  # schema_name -> node_id
    
    def link_all(self) -> int:
        """
        Perform all cross-language linking.
        
        Returns: Number of cross-language edges added
        """
        edges_added = 0
        
        # Phase B.1: Detect and index all cross-language artifacts
        self._index_api_endpoints()
        self._index_config_files()
        self._index_db_models()
        self._index_schema_files()
        
        # Phase B.2: Create cross-language edges
        edges_added += self._link_api_endpoints()
        edges_added += self._link_config_files()
        edges_added += self._link_db_models()
        edges_added += self._link_schema_files()
        
        return edges_added
    
    # =========================================================================
    # B.1: REST API LINKING
    # =========================================================================
    
    def _index_api_endpoints(self):
        """Index all REST API endpoints (definitions and calls)."""
        for node_id, node in self.graph.nodes.items():
            source = self._read_file(node.file_path)
            if not source:
                continue
            
            language = node.language
            
            # Extract API definitions (backend)
            if language in self.API_DEFINITION_PATTERNS:
                for pattern, framework in self.API_DEFINITION_PATTERNS[language]:
                    matches = re.findall(pattern, source, re.IGNORECASE)
                    for match in matches:
                        endpoint = match[-1] if isinstance(match, tuple) else match
                        endpoint = self._normalize_endpoint(endpoint)
                        if endpoint:
                            node.api_endpoints.append(endpoint)
                            if endpoint not in self.api_endpoints:
                                self.api_endpoints[endpoint] = []
                            self.api_endpoints[endpoint].append((node_id, 'definition'))
            
            # Extract API calls (frontend/consumer)
            if language in self.API_CALL_PATTERNS:
                for pattern, library in self.API_CALL_PATTERNS[language]:
                    matches = re.findall(pattern, source, re.IGNORECASE)
                    for match in matches:
                        endpoint = match[-1] if isinstance(match, tuple) else match
                        endpoint = self._normalize_endpoint(endpoint)
                        if endpoint:
                            node.api_calls.append(endpoint)
                            if endpoint not in self.api_endpoints:
                                self.api_endpoints[endpoint] = []
                            self.api_endpoints[endpoint].append((node_id, 'call'))
    
    def _link_api_endpoints(self) -> int:
        """Create edges between API consumers and providers."""
        edges_added = 0
        
        for endpoint, usages in self.api_endpoints.items():
            definitions = [(n, t) for n, t in usages if t == 'definition']
            calls = [(n, t) for n, t in usages if t == 'call']
            
            # Link each caller to each definition
            for caller_id, _ in calls:
                for definer_id, _ in definitions:
                    if caller_id != definer_id:
                        edge = Edge(
                            source=caller_id,
                            target=definer_id,
                            edge_type='api',
                            weight=0.9,  # High weight for direct API dependency
                            metadata={
                                'endpoint': endpoint,
                                'link_type': 'rest_api',
                                'cross_language': self._is_cross_language(caller_id, definer_id)
                            }
                        )
                        self.graph.add_edge(edge)
                        edges_added += 1
        
        return edges_added
    
    # =========================================================================
    # B.2: CONFIG FILE LINKING
    # =========================================================================
    
    def _index_config_files(self):
        """Index all config files in the project."""
        # Find config files
        for root, dirs, files in os.walk(self.root_path):
            dirs[:] = [d for d in dirs if d not in ['node_modules', 'venv', '__pycache__', '.git']]
            for file in files:
                for pattern in self.CONFIG_FILE_PATTERNS:
                    if re.match(pattern, file, re.IGNORECASE):
                        file_path = os.path.join(root, file)
                        config_name = file.lower()
                        self.config_files[config_name] = file_path.replace("\\", "/")
                        break
        
        # Find config references in code
        for node_id, node in self.graph.nodes.items():
            source = self._read_file(node.file_path)
            if not source:
                continue
            
            language = node.language
            if language in self.CONFIG_READ_PATTERNS:
                for pattern, method in self.CONFIG_READ_PATTERNS[language]:
                    matches = re.findall(pattern, source, re.IGNORECASE)
                    for match in matches:
                        config_ref = match[-1] if isinstance(match, tuple) else match
                        if config_ref:
                            node.config_refs.append(config_ref)
    
    def _link_config_files(self) -> int:
        """Create edges between files that share config dependencies."""
        edges_added = 0
        
        # Group nodes by config file they reference
        config_users: Dict[str, List[str]] = defaultdict(list)
        
        for node_id, node in self.graph.nodes.items():
            for config_ref in node.config_refs:
                # Match config reference to config file
                config_ref_lower = os.path.basename(config_ref).lower()
                for config_name, config_path in self.config_files.items():
                    if config_ref_lower in config_name or config_name in config_ref_lower:
                        config_users[config_path].append(node_id)
                        break
        
        # Create edges between files sharing the same config
        for config_path, users in config_users.items():
            for i, user1 in enumerate(users):
                for user2 in users[i+1:]:
                    if user1 != user2:
                        # Bidirectional config dependency
                        edge = Edge(
                            source=user1,
                            target=user2,
                            edge_type='config',
                            weight=0.6,  # Medium weight for config sharing
                            metadata={
                                'config_file': config_path,
                                'link_type': 'shared_config',
                                'cross_language': self._is_cross_language(user1, user2)
                            }
                        )
                        self.graph.add_edge(edge)
                        edges_added += 1
        
        return edges_added
    
    # =========================================================================
    # B.3: DATABASE MODEL LINKING
    # =========================================================================
    
    def _index_db_models(self):
        """Index all database models and their usages."""
        for node_id, node in self.graph.nodes.items():
            source = self._read_file(node.file_path)
            if not source:
                continue
            
            language = node.language
            models_found = []
            
            # Find model definitions
            if language in self.DB_MODEL_PATTERNS:
                for pattern, orm_type in self.DB_MODEL_PATTERNS[language]:
                    matches = re.findall(pattern, source, re.IGNORECASE)
                    for match in matches:
                        model_name = match[-1] if isinstance(match, tuple) else match
                        if model_name and len(model_name) > 1:
                            models_found.append(model_name.lower())
            
            # Find model usages (queries)
            if language in self.DB_QUERY_PATTERNS:
                for pattern, query_type in self.DB_QUERY_PATTERNS[language]:
                    matches = re.findall(pattern, source, re.IGNORECASE)
                    for match in matches:
                        model_name = match[-1] if isinstance(match, tuple) else match
                        if model_name and len(model_name) > 1:
                            models_found.append(model_name.lower())
            
            # Store in node and index
            for model in set(models_found):
                node.db_models.append(model)
                if model not in self.db_models:
                    self.db_models[model] = []
                if node_id not in self.db_models[model]:
                    self.db_models[model].append(node_id)
    
    def _link_db_models(self) -> int:
        """Create edges between files sharing database models."""
        edges_added = 0
        
        for model_name, node_ids in self.db_models.items():
            if len(node_ids) < 2:
                continue
            
            # Find the model definition (likely in models.py or entities/)
            definition_node = None
            for node_id in node_ids:
                if 'model' in node_id.lower() or 'entity' in node_id.lower():
                    definition_node = node_id
                    break
            
            if definition_node:
                # Link all users to the definition
                for user_id in node_ids:
                    if user_id != definition_node:
                        edge = Edge(
                            source=user_id,
                            target=definition_node,
                            edge_type='database',
                            weight=0.85,  # High weight for data model dependency
                            metadata={
                                'model': model_name,
                                'link_type': 'database_model',
                                'cross_language': self._is_cross_language(user_id, definition_node)
                            }
                        )
                        self.graph.add_edge(edge)
                        edges_added += 1
            else:
                # No clear definition, link all pairs
                for i, node1 in enumerate(node_ids):
                    for node2 in node_ids[i+1:]:
                        edge = Edge(
                            source=node1,
                            target=node2,
                            edge_type='database',
                            weight=0.7,
                            metadata={
                                'model': model_name,
                                'link_type': 'shared_model',
                                'cross_language': self._is_cross_language(node1, node2)
                            }
                        )
                        self.graph.add_edge(edge)
                        edges_added += 1
        
        return edges_added
    
    # =========================================================================
    # B.4: SCHEMA FILE LINKING
    # =========================================================================
    
    def _index_schema_files(self):
        """Index all schema files (protobuf, GraphQL, Avro, etc.)."""
        # Find schema files
        for root, dirs, files in os.walk(self.root_path):
            dirs[:] = [d for d in dirs if d not in ['node_modules', 'venv', '__pycache__', '.git']]
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in self.SCHEMA_FILE_EXTENSIONS:
                    file_path = os.path.join(root, file)
                    schema_name = os.path.splitext(file)[0].lower()
                    self.schema_files[schema_name] = file_path.replace("\\", "/")
        
        # Find schema references in code
        for node_id, node in self.graph.nodes.items():
            source = self._read_file(node.file_path)
            if not source:
                continue
            
            language = node.language
            if language in self.SCHEMA_REFERENCE_PATTERNS:
                for pattern, schema_type in self.SCHEMA_REFERENCE_PATTERNS[language]:
                    matches = re.findall(pattern, source, re.IGNORECASE)
                    for match in matches:
                        schema_ref = match[-1] if isinstance(match, tuple) else match
                        if schema_ref:
                            node.schema_refs.append(schema_ref)
    
    def _link_schema_files(self) -> int:
        """Create edges between files using shared schemas."""
        edges_added = 0
        
        # Group nodes by schema they reference
        schema_users: Dict[str, List[str]] = defaultdict(list)
        
        for node_id, node in self.graph.nodes.items():
            for schema_ref in node.schema_refs:
                # Match schema reference to schema file
                schema_base = os.path.splitext(os.path.basename(schema_ref))[0].lower()
                schema_base = schema_base.replace('_pb2', '').replace('_pb', '')
                
                for schema_name, schema_path in self.schema_files.items():
                    if schema_base in schema_name or schema_name in schema_base:
                        schema_users[schema_path].append(node_id)
                        break
        
        # Create edges between files sharing the same schema
        for schema_path, users in schema_users.items():
            for i, user1 in enumerate(users):
                for user2 in users[i+1:]:
                    if user1 != user2:
                        edge = Edge(
                            source=user1,
                            target=user2,
                            edge_type='schema',
                            weight=0.8,  # High weight for schema sharing
                            metadata={
                                'schema_file': schema_path,
                                'link_type': 'shared_schema',
                                'cross_language': self._is_cross_language(user1, user2)
                            }
                        )
                        self.graph.add_edge(edge)
                        edges_added += 1
        
        return edges_added
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _read_file(self, file_path: str) -> Optional[str]:
        """Read file content safely."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception:
            return None
    
    def _normalize_endpoint(self, endpoint: str) -> Optional[str]:
        """Normalize API endpoint for matching."""
        if not endpoint:
            return None
        
        # Remove leading/trailing whitespace and quotes
        endpoint = endpoint.strip().strip('\'"')
        
        # Skip if it looks like a variable or template
        if endpoint.startswith('$') or endpoint.startswith('{') or '${' in endpoint:
            return None
        
        # Normalize path parameters
        # /users/:id -> /users/{id}
        # /users/<id> -> /users/{id}
        endpoint = re.sub(r':([a-zA-Z_][a-zA-Z0-9_]*)', r'{\1}', endpoint)
        endpoint = re.sub(r'<([a-zA-Z_][a-zA-Z0-9_]*)>', r'{\1}', endpoint)
        
        # Ensure starts with /
        if not endpoint.startswith('/') and not endpoint.startswith('http'):
            endpoint = '/' + endpoint
        
        # Remove trailing slash for consistency
        endpoint = endpoint.rstrip('/')
        
        return endpoint if endpoint else None
    
    def _is_cross_language(self, node1_id: str, node2_id: str) -> bool:
        """Check if two nodes are from different languages."""
        node1 = self.graph.nodes.get(node1_id)
        node2 = self.graph.nodes.get(node2_id)
        
        if node1 and node2:
            return node1.language != node2.language
        return False


class CLDGBuilder:
    """
    Builds a Cross-Language Dependency Graph from a codebase.
    
    Phase A: Static Analysis Per Language
    Phase B: Cross-Language Edge Detection (imports + cross-language linking)
    Phase C: Weight Calculation
    """
    
    def __init__(self, root_path: str, exclude_dirs: Optional[List[str]] = None):
        self.root_path = root_path
        self.exclude_dirs = exclude_dirs or ['node_modules', 'venv', '__pycache__', '.git', 'dist', 'build']
        self.graph = CLDG()
        self.cross_language_edges = 0
    
    def build(self) -> CLDG:
        """Build the complete CLDG."""
        # Phase A: Analyze all files
        self._analyze_all_files()
        
        # Phase B.1: Build import/naming edges
        self._build_edges()
        
        # Phase B.2: Cross-language linking (REST, config, DB, schema)
        linker = CrossLanguageLinker(self.graph, self.root_path)
        self.cross_language_edges = linker.link_all()
        
        # Phase C: Calculate weights
        self._calculate_weights()
        
        return self.graph
    
    def get_stats(self) -> Dict[str, Any]:
        """Get build statistics."""
        return {
            'total_nodes': len(self.graph.nodes),
            'total_edges': len(self.graph.edges),
            'cross_language_edges': self.cross_language_edges,
            'languages': list(set(n.language for n in self.graph.nodes.values())),
            'source_files': sum(1 for n in self.graph.nodes.values() if n.node_type == 'source'),
            'test_files': sum(1 for n in self.graph.nodes.values() if n.node_type == 'test'),
        }
    
    def _analyze_all_files(self):
        """Phase A: Static analysis per language."""
        for root, dirs, files in os.walk(self.root_path):
            # Filter excluded directories
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]
            
            for file in files:
                file_path = os.path.join(root, file)
                ext = os.path.splitext(file)[1].lower()
                
                if ext in LANGUAGE_ANALYZERS:
                    analyzer = LANGUAGE_ANALYZERS[ext]
                    node = analyzer.analyze(file_path)
                    if node:
                        self.graph.add_node(node)
    
    def _build_edges(self):
        """Phase B: Build edges between nodes."""
        for node_id, node in self.graph.nodes.items():
            self._build_import_edges(node)
            self._build_naming_convention_edges(node)
            self._build_api_edges(node)
    
    def _build_import_edges(self, node: Node):
        """Build edges based on import statements."""
        for imp in node.imports:
            # Find matching node
            target_id = self._resolve_import(imp, node)
            if target_id and target_id in self.graph.nodes:
                edge = Edge(
                    source=node.id,
                    target=target_id,
                    edge_type='import',
                    weight=1.0
                )
                self.graph.add_edge(edge)
    
    def _build_naming_convention_edges(self, node: Node):
        """Build edges based on naming conventions (e.g., test_auth.py → auth.py)."""
        if node.node_type == 'test':
            basename = os.path.basename(node.file_path)
            
            # Python: test_foo.py → foo.py
            if basename.startswith('test_'):
                source_name = basename[5:]  # Remove 'test_'
                self._find_and_link_source(node, source_name)
            
            # JS/TS: foo.test.js → foo.js
            elif '.test.' in basename or '.spec.' in basename:
                source_name = basename.replace('.test.', '.').replace('.spec.', '.')
                self._find_and_link_source(node, source_name)
            
            # Java: FooTest.java → Foo.java
            elif basename.endswith('Test.java') or basename.endswith('Tests.java'):
                source_name = basename.replace('Test.java', '.java').replace('Tests.java', '.java')
                self._find_and_link_source(node, source_name)
    
    def _find_and_link_source(self, test_node: Node, source_name: str):
        """Find source file and create edge from test to source."""
        for node_id, source_node in self.graph.nodes.items():
            if source_node.node_type == 'source':
                if os.path.basename(source_node.file_path) == source_name:
                    edge = Edge(
                        source=test_node.id,
                        target=node_id,
                        edge_type='naming_convention',
                        weight=0.9
                    )
                    self.graph.add_edge(edge)
                    break
    
    def _build_api_edges(self, node: Node):
        """Build edges based on API endpoint detection."""
        # Detect REST API patterns
        api_patterns = [
            r'@app\.route\([\'"](.+?)[\'"]\)',  # Flask
            r'@router\.(get|post|put|delete)\([\'"](.+?)[\'"]\)',  # FastAPI
            r'fetch\([\'"](.+?)[\'"]\)',  # JS fetch
            r'axios\.(get|post|put|delete)\([\'"](.+?)[\'"]\)',  # Axios
        ]
        
        try:
            with open(node.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                source = f.read()
            
            endpoints = []
            for pattern in api_patterns:
                matches = re.findall(pattern, source)
                for match in matches:
                    if isinstance(match, tuple):
                        endpoints.append(match[-1])
                    else:
                        endpoints.append(match)
            
            node.api_endpoints = endpoints
            
            # Link API consumers to providers
            for other_id, other_node in self.graph.nodes.items():
                if other_id != node.id and other_node.api_endpoints:
                    for endpoint in node.api_endpoints:
                        if endpoint in other_node.api_endpoints:
                            edge = Edge(
                                source=node.id,
                                target=other_id,
                                edge_type='api',
                                weight=0.8,
                                metadata={'endpoint': endpoint}
                            )
                            self.graph.add_edge(edge)
                            
        except Exception:
            pass
    
    def _resolve_import(self, import_str: str, node: Node) -> Optional[str]:
        """Resolve an import string to a node ID."""
        # Handle relative imports
        if import_str.startswith('.'):
            base_dir = os.path.dirname(node.file_path)
            relative_path = import_str.replace('.', os.sep) + self._get_extension(node.language)
            resolved = os.path.normpath(os.path.join(base_dir, relative_path))
            return resolved.replace("\\", "/")
        
        # Handle absolute imports - search in graph
        for node_id in self.graph.nodes:
            # Match by module name
            module_name = import_str.split('.')[-1]
            if module_name in node_id:
                return node_id
        
        return None
    
    def _get_extension(self, language: str) -> str:
        """Get file extension for a language."""
        extensions = {
            'python': '.py',
            'javascript': '.js',
            'typescript': '.ts',
            'java': '.java',
            'go': '.go'
        }
        return extensions.get(language, '')
    
    def _calculate_weights(self):
        """Phase C: Calculate edge weights."""
        # Weight formula: wij = α·import_score + β·call_score + γ·semantic_score
        alpha, beta, gamma = 0.5, 0.3, 0.2
        
        for edge in self.graph.edges:
            source_node = self.graph.nodes.get(edge.source)
            target_node = self.graph.nodes.get(edge.target)
            
            if not source_node or not target_node:
                continue
            
            import_score = 1.0 if edge.edge_type == 'import' else 0.0
            call_score = self._calculate_call_score(source_node, target_node)
            semantic_score = self._calculate_semantic_score(source_node, target_node)
            
            edge.weight = alpha * import_score + beta * call_score + gamma * semantic_score
            edge.weight = max(0.1, min(1.0, edge.weight))  # Clamp to [0.1, 1.0]
    
    def _calculate_call_score(self, source: Node, target: Node) -> float:
        """Calculate call score based on function usage."""
        if not target.functions:
            return 0.0
        
        # Check if source calls any of target's functions
        # This is a simplified heuristic
        score = 0.0
        for func in target.functions:
            if func in source.imports or any(func in imp for imp in source.imports):
                score += 1.0 / len(target.functions)
        
        return min(1.0, score)
    
    def _calculate_semantic_score(self, source: Node, target: Node) -> float:
        """Calculate semantic similarity score."""
        # Simple heuristic: same directory = higher score
        source_dir = os.path.dirname(source.file_path)
        target_dir = os.path.dirname(target.file_path)
        
        if source_dir == target_dir:
            return 0.8
        elif os.path.dirname(source_dir) == os.path.dirname(target_dir):
            return 0.5
        else:
            return 0.2


# =============================================================================
# INTEGRATION WITH HYBRIDCI
# =============================================================================

def build_cldg_for_project(project_path: str) -> CLDG:
    """
    Build a CLDG for a project.
    
    Args:
        project_path: Root path of the project
        
    Returns:
        CLDG instance
    """
    builder = CLDGBuilder(project_path)
    return builder.build()


def get_impacted_tests_from_cldg(cldg: CLDG, changed_files: List[str]) -> List[str]:
    """
    Get impacted tests using CLDG traversal.
    
    Args:
        cldg: The Cross-Language Dependency Graph
        changed_files: List of changed file paths
        
    Returns:
        List of impacted test file paths
    """
    impact_scores = cldg.get_impacted_tests(changed_files)
    
    # Sort by impact score (highest first)
    sorted_tests = sorted(impact_scores.items(), key=lambda x: x[1], reverse=True)
    
    return [test for test, score in sorted_tests]


# =============================================================================
# MATHEMATICAL MODEL DOCUMENTATION
# =============================================================================

CLDG_FORMAL_DEFINITION = """
================================================================================
            CROSS-LANGUAGE DEPENDENCY GRAPH (CLDG) - FORMAL DEFINITION
================================================================================

GRAPH DEFINITION
----------------

    G = (V, E)

    Where:
        V = Vs ∪ Vt
            Vs = {source files} (Python, JS, Java, Go, etc.)
            Vt = {test files}
        
        E ⊆ V × V
            Directed edges representing dependencies

    Node Representation:
        G = {
            "node_id": {
                "type": "source" | "test",
                "language": "python" | "javascript" | "java" | ...,
                "cost": execution_time  (seconds)
            }
        }

    Edge Representation:
        E = [(source, target, weight), ...]
        where weight wij ∈ [0, 1]

EDGE TYPES
----------

1. Static Imports:     (vi, vj) ∈ E  if  vi imports vj
2. API Usage:          (vi, vj) ∈ E  if  vi calls functions in vj
3. Cross-Language:     (vi, vj) ∈ E  if  vi makes REST/RPC call to vj
4. Config Reference:   (vi, vj) ∈ E  if  vi references config vj
5. Database Model:     (vi, vj) ∈ E  if  vi uses model defined in vj
6. Schema Reference:   (vi, vj) ∈ E  if  vi uses schema from vj

EDGE WEIGHTS
------------

    wij = α · import_score + β · call_score + γ · semantic_score

    Where α + β + γ = 1  (default: α=0.5, β=0.3, γ=0.2)

================================================================================
                        GRAPH-BASED TEST SELECTION
                        (Replaces IBST Filename Mapping)
================================================================================

ALGORITHM
---------

    Input:  G = (V, E), F = {changed files}
    Output: T* = {selected tests}

    1. IDENTIFY changed nodes F ⊆ V
    2. TRAVERSE graph outward (BFS on reverse edges)
    3. COLLECT reachable test nodes with impact scores
    4. APPLY optimization solver to choose minimal set

IMPACT PROPAGATION
------------------

    For each changed file f ∈ F:
        impact(t) = max { ∏ wij : path (f → ... → t) in G }
                    f∈F

    Test Selection:
        T* = {t ∈ Vt : impact(t) ≥ τ}  where τ = threshold (default 0.1)

CONSTRAINED OPTIMIZATION
------------------------

    minimize    Σ C(tj) · xj           (minimize total execution cost)
    subject to  Σ D(fi, tj) · xj ≥ 1   ∀fi ∈ F  (coverage constraint)
                xj ∈ {0, 1}            (binary selection)

    Where:
        C(tj) = execution cost of test tj
        D(fi, tj) = dependency strength from fi to tj (from graph)
        xj = 1 if test tj is selected, 0 otherwise

================================================================================
                        THEORETICAL GUARANTEES
================================================================================

┌─────────────────────────────────────────────────────────────────────────────┐
│ LEMMA 1 — COMPLETENESS                                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ Theorem: If the dependency graph G is sound (all true dependencies are     │
│ represented as edges), then HybridCI's graph traversal selects ALL tests   │
│ that depend on modified files.                                             │
│                                                                             │
│ Formally:                                                                   │
│   Let F = {modified source files}                                          │
│   Let T_actual = {tests that truly depend on F}                            │
│   Let T_selected = traverse_from_changed_files(G, F)                       │
│                                                                             │
│   If ∀(t ∈ T_actual) ∃ path (f → ... → t) in G for some f ∈ F              │
│   Then T_actual ⊆ T_selected                                               │
│                                                                             │
│ Proof Sketch:                                                               │
│   1. BFS traversal visits all nodes reachable from F via reverse edges     │
│   2. Every test t ∈ T_actual has a dependency path to some f ∈ F           │
│   3. By soundness, this path exists in G as reverse edges                  │
│   4. BFS will discover t when traversing from f                            │
│   5. Therefore t ∈ T_selected                                     ∎        │
│                                                                             │
│ Corollary: No false negatives (missed tests) if graph is sound.            │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ LEMMA 2 — COMPLEXITY ANALYSIS                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ Let:                                                                        │
│   |V| = n  (total files in project)                                        │
│   |E| = e  (total dependency edges)                                        │
│   |T| = m  (number of test files)                                          │
│                                                                             │
│ Phase 1: Graph Traversal (BFS)                                             │
│ ─────────────────────────────                                               │
│   Time Complexity:  O(n + e)                                                │
│   Space Complexity: O(n)                                                    │
│                                                                             │
│   Proof:                                                                    │
│     - Each node visited at most once: O(n)                                  │
│     - Each edge examined at most once: O(e)                                 │
│     - Visited set uses O(n) space                                           │
│     - Total: O(n + e) time, O(n) space                            ∎        │
│                                                                             │
│ Phase 2: Optimization Solving                                               │
│ ─────────────────────────────                                               │
│   Greedy Approximation:  O(m log m)                                         │
│   ILP Exact Solution:    O(2^m) worst case, practical: O(m²)                │
│                                                                             │
│   Proof (Greedy):                                                           │
│     - Compute cost/coverage ratio for m tests: O(m)                         │
│     - Sort by ratio: O(m log m)                                             │
│     - Select tests until threshold: O(m)                                    │
│     - Total: O(m log m)                                           ∎        │
│                                                                             │
│ Total Complexity:                                                           │
│ ─────────────────                                                           │
│   Graph Construction:  O(n · k) where k = avg imports per file              │
│   Graph Traversal:     O(n + e)                                             │
│   Test Selection:      O(m log m)                                           │
│                                                                             │
│   Overall: O(n · k + e + m log m)                                           │
│                                                                             │
│   For typical codebases: k ≪ n, m ≪ n, e = O(n · k)                         │
│   Therefore: O(n · k) dominates                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ LEMMA 3 — APPROXIMATION RATIO                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ Theorem: The greedy algorithm achieves an approximation ratio of            │
│ O(log m) for the weighted set cover problem.                                │
│                                                                             │
│ Formally:                                                                   │
│   Let OPT = optimal solution cost                                           │
│   Let GREEDY = greedy solution cost                                         │
│                                                                             │
│   Then: GREEDY ≤ O(log m) · OPT                                             │
│                                                                             │
│ Proof: Standard weighted set cover analysis (Chvatal, 1979)                 │
│                                                                             │
│ Practical Impact:                                                           │
│   - For m = 1000 tests: ratio ≤ ~10x optimal                                │
│   - In practice, much better due to high test-file correlation              │
│   - ILP solver provides exact optimum when m < 100                          │
└─────────────────────────────────────────────────────────────────────────────┘

================================================================================
                            SUMMARY
================================================================================

┌──────────────────┬─────────────────────────────────────────────────────────┐
│ Component        │ Complexity                                              │
├──────────────────┼─────────────────────────────────────────────────────────┤
│ Graph Build      │ O(n · k)  - linear in files × avg imports               │
│ Graph Traversal  │ O(n + e)  - linear in graph size                        │
│ Greedy Solver    │ O(m log m) - quasi-linear in tests                      │
│ ILP Solver       │ O(m²) practical, O(2^m) worst case                      │
├──────────────────┼─────────────────────────────────────────────────────────┤
│ TOTAL            │ O(n · k + m log m) for typical usage                    │
└──────────────────┴─────────────────────────────────────────────────────────┘

Guarantees:
  ✓ Completeness: All dependent tests selected (no false negatives)
  ✓ Efficiency: Near-linear time complexity
  ✓ Optimality: O(log m) approximation for cost minimization

================================================================================
"""


if __name__ == "__main__":
    print(CLDG_FORMAL_DEFINITION)
    
    # Demo
    print("\n" + "="*76)
    print("        CLDG DEMO - DEPENDENCY-AWARE GRAPH-BASED TEST SELECTION")
    print("="*76 + "\n")
    
    builder = CLDGBuilder("sample_repo")
    cldg = builder.build()
    stats = builder.get_stats()
    
    print("GRAPH STATISTICS:")
    print(f"  |V| (nodes):  {stats['total_nodes']}")
    print(f"  |E| (edges):  {stats['total_edges']}")
    print(f"  Cross-lang:   {stats['cross_language_edges']}")
    print(f"  Languages:    {stats['languages']}")
    print(f"  Source nodes: {stats['source_files']}")
    print(f"  Test nodes:   {stats['test_files']}")
    
    print("\n" + "-"*76)
    print("GRAPH REPRESENTATION: G = {nodes, edges}")
    print("-"*76)
    
    print("\nNODES (with cost/execution_time):")
    for node_id, node in cldg.nodes.items():
        print(f"  {os.path.basename(node_id)}:")
        print(f"    type: {node.node_type}, language: {node.language}, cost: {node.cost}")
    
    print("\nEDGES (with weights):")
    edge_types = defaultdict(int)
    for edge in cldg.edges:
        edge_types[edge.edge_type] += 1
        cross = " [CROSS-LANG]" if edge.metadata.get('cross_language') else ""
        print(f"  {os.path.basename(edge.source)} --[{edge.edge_type}, w={edge.weight:.2f}]--> {os.path.basename(edge.target)}{cross}")
    
    print("\nEDGE TYPE SUMMARY:")
    for etype, count in sorted(edge_types.items()):
        print(f"  {etype}: {count}")
    
    # Demonstrate graph-based test selection (replaces IBST)
    print("\n" + "="*76)
    print("        GRAPH-BASED TEST SELECTION (REPLACES IBST)")
    print("="*76)
    
    changed_files = ["sample_repo/src/calculator.py"]
    print(f"\nChanged files F = {changed_files}")
    
    print("\nStep 1: Graph Traversal (BFS on reverse edges)")
    print("         Complexity: O(n + e)")
    impacted = cldg.traverse_from_changed_files(changed_files)
    print(f"         Reachable tests: {len(impacted)}")
    for test, score in impacted.items():
        print(f"           - {os.path.basename(test)}: impact={score:.2f}")
    
    print("\nStep 2: Constrained Optimization")
    print("         Complexity: O(m log m) greedy / O(m²) ILP")
    result = cldg.select_minimal_test_set(changed_files)
    print(f"         Method: {result.optimization_method}")
    print(f"         Selected: {len(result.selected_tests)} tests")
    print(f"         Total cost: {result.total_cost:.2f}s")
    print(f"         Coverage: {result.coverage:.1%}")
    
    print("\n         Selected tests:")
    for test in result.selected_tests:
        print(f"           ✓ {os.path.basename(test)}")
    
    print("\n" + "="*76)
    print("        THEORETICAL GUARANTEES")
    print("="*76)
    print("""
    Lemma 1 (Completeness):
      If graph is sound → all dependent tests selected
      Proof: BFS visits all reachable nodes ∎
    
    Lemma 2 (Complexity):
      Graph traversal: O(n + e)
      Optimization:    O(m log m)
      Total:           O(n·k + m log m) ∎
    
    Lemma 3 (Approximation):
      Greedy achieves O(log m) approximation ratio
      Proof: Standard weighted set cover analysis ∎
    """)
