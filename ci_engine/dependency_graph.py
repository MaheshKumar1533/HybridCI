# ci_engine/dependency_graph.py
import ast
from pathlib import Path

def build_dependency_graph(src_dir):
    graph = {}
    for file in Path(src_dir).rglob("*.py"):
        with open(file) as f:
            tree = ast.parse(f.read())
        imports = [n.names[0].name for n in ast.walk(tree) if isinstance(n, ast.Import)]
        graph[file.name] = imports
    return graph
