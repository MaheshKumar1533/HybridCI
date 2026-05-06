"""
HybridCI Optimization Framework

A constrained cost-minimizing test selection solver based on:

Mathematical Model:
------------------
F = {f1, f2, ..., fn}  → changed files
T = {t1, t2, ..., tm}  → test suite
L = {l1, ..., lk}      → languages

D(fi, tj) ∈ [0,1]      → dependency weight (coverage)
C(tj)                  → execution cost (time)
P(tj)                  → historical failure probability

Decision Variable:
-----------------
xj = 1 if test tj is selected, 0 otherwise

Optimization Objective:
----------------------
    minimize  Σ C(tj) * xj
    
Subject to:
    Coverage constraint:  Σ D(fi, tj) * xj ≥ 1  ∀ fi ∈ F
    Confidence constraint: Σ P(tj) * xj ≥ θ  (optional)

This transforms HybridCI into a formal Integer Linear Programming (ILP) problem.
"""

import os
import time
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class TestMetrics:
    """Metrics for a single test case."""
    name: str
    execution_cost: float = 1.0  # C(tj) - execution time in seconds
    failure_probability: float = 0.5  # P(tj) - historical failure rate
    coverage: Dict[str, float] = field(default_factory=dict)  # D(fi, tj) for each file
    last_execution_time: float = 0.0
    total_runs: int = 0
    total_failures: int = 0


@dataclass 
class OptimizationResult:
    """Result of the test selection optimization."""
    selected_tests: List[str]
    total_cost: float
    coverage_score: float
    confidence_score: float
    optimization_time: float
    solver_used: str


class TestSelectionOptimizer:
    """
    Constrained cost-minimizing test selection solver.
    
    Solves the Integer Linear Programming problem:
        minimize  Σ C(tj) * xj
        subject to:
            Σ D(fi, tj) * xj ≥ 1  ∀ fi ∈ F  (coverage)
            Σ P(tj) * xj ≥ θ                 (confidence, optional)
    """
    
    def __init__(self, test_map: Dict[str, List[str]], 
                 test_metrics: Optional[Dict[str, TestMetrics]] = None,
                 confidence_threshold: float = 0.0):
        """
        Initialize optimizer.
        
        Args:
            test_map: Mapping of test files to source files they cover
            test_metrics: Historical metrics for each test
            confidence_threshold: θ - minimum confidence score required
        """
        self.test_map = test_map
        self.test_metrics = test_metrics or {}
        self.confidence_threshold = confidence_threshold
        
        # Initialize default metrics for tests without history
        self._initialize_default_metrics()
        
        # Build dependency matrix D(fi, tj)
        self.dependency_matrix = self._build_dependency_matrix()
    
    def _initialize_default_metrics(self):
        """Initialize default metrics for tests without historical data."""
        for test_name in self.test_map.keys():
            if test_name not in self.test_metrics:
                # Default metrics based on covered files
                covered_files = self.test_map[test_name]
                self.test_metrics[test_name] = TestMetrics(
                    name=test_name,
                    execution_cost=1.0 * len(covered_files),  # Cost proportional to coverage
                    failure_probability=0.5,  # Neutral prior
                    coverage={f: 1.0 for f in covered_files}
                )
    
    def _build_dependency_matrix(self) -> Dict[str, Dict[str, float]]:
        """
        Build dependency matrix D(fi, tj).
        
        Returns:
            Nested dict: dependency_matrix[file][test] = weight
        """
        matrix = {}
        
        for test_name, covered_files in self.test_map.items():
            for file in covered_files:
                if file not in matrix:
                    matrix[file] = {}
                
                # Get weight from metrics or default to 1.0
                if test_name in self.test_metrics:
                    weight = self.test_metrics[test_name].coverage.get(file, 1.0)
                else:
                    weight = 1.0
                
                matrix[file][test_name] = weight
        
        return matrix
    
    def get_cost(self, test_name: str) -> float:
        """Get execution cost C(tj) for a test."""
        if test_name in self.test_metrics:
            return self.test_metrics[test_name].execution_cost
        return 1.0
    
    def get_failure_probability(self, test_name: str) -> float:
        """Get historical failure probability P(tj) for a test."""
        if test_name in self.test_metrics:
            metrics = self.test_metrics[test_name]
            if metrics.total_runs > 0:
                return metrics.total_failures / metrics.total_runs
            return metrics.failure_probability
        return 0.5
    
    def get_dependency_weight(self, file: str, test_name: str) -> float:
        """Get dependency weight D(fi, tj)."""
        if file in self.dependency_matrix:
            return self.dependency_matrix[file].get(test_name, 0.0)
        return 0.0
    
    def solve_greedy(self, changed_files: List[str]) -> OptimizationResult:
        """
        Greedy approximation solver for test selection.
        
        Uses a cost-effectiveness heuristic:
            score(tj) = coverage_gain(tj) / C(tj)
        
        Selects tests greedily until all files are covered.
        
        Args:
            changed_files: List of changed files F
            
        Returns:
            OptimizationResult with selected tests
        """
        start_time = time.time()
        
        # Filter to only files we have coverage for
        F = [f for f in changed_files if f in self.dependency_matrix or 
             os.path.basename(f) in self.dependency_matrix]
        
        # Normalize file names
        F_normalized = []
        for f in changed_files:
            if f in self.dependency_matrix:
                F_normalized.append(f)
            elif os.path.basename(f) in self.dependency_matrix:
                F_normalized.append(os.path.basename(f))
        
        F = F_normalized if F_normalized else [os.path.basename(f) for f in changed_files]
        
        # Track which files are covered
        uncovered_files = set(F)
        selected_tests = []
        total_cost = 0.0
        
        # All available tests
        available_tests = set(self.test_map.keys())
        
        while uncovered_files and available_tests:
            best_test = None
            best_score = -1
            best_coverage = set()
            
            for test_name in available_tests:
                # Calculate coverage gain for this test
                coverage_gain = 0.0
                files_covered = set()
                
                for file in uncovered_files:
                    weight = self.get_dependency_weight(file, test_name)
                    if weight > 0:
                        coverage_gain += weight
                        files_covered.add(file)
                
                if coverage_gain > 0:
                    # Cost-effectiveness score
                    cost = self.get_cost(test_name)
                    score = coverage_gain / cost
                    
                    # Boost score by failure probability (prefer tests likely to fail)
                    failure_prob = self.get_failure_probability(test_name)
                    score *= (1 + failure_prob)
                    
                    if score > best_score:
                        best_score = score
                        best_test = test_name
                        best_coverage = files_covered
            
            if best_test is None:
                break
            
            # Select this test
            selected_tests.append(best_test)
            total_cost += self.get_cost(best_test)
            uncovered_files -= best_coverage
            available_tests.remove(best_test)
        
        # Check confidence constraint
        confidence_score = sum(
            self.get_failure_probability(t) for t in selected_tests
        )
        
        # If confidence threshold not met, add high-probability tests
        if self.confidence_threshold > 0 and confidence_score < self.confidence_threshold:
            remaining_tests = sorted(
                available_tests,
                key=lambda t: self.get_failure_probability(t),
                reverse=True
            )
            for test_name in remaining_tests:
                if confidence_score >= self.confidence_threshold:
                    break
                selected_tests.append(test_name)
                total_cost += self.get_cost(test_name)
                confidence_score += self.get_failure_probability(test_name)
        
        # Calculate coverage score
        coverage_score = 1.0 - (len(uncovered_files) / max(len(F), 1))
        
        optimization_time = time.time() - start_time
        
        return OptimizationResult(
            selected_tests=selected_tests,
            total_cost=total_cost,
            coverage_score=coverage_score,
            confidence_score=confidence_score,
            optimization_time=optimization_time,
            solver_used="greedy"
        )
    
    def solve_ilp(self, changed_files: List[str]) -> OptimizationResult:
        """
        Exact Integer Linear Programming solver.
        
        Solves:
            minimize  Σ C(tj) * xj
            subject to:
                Σ D(fi, tj) * xj ≥ 1  ∀ fi ∈ F
                Σ P(tj) * xj ≥ θ
                xj ∈ {0, 1}
        
        Falls back to greedy if scipy not available.
        """
        try:
            from scipy.optimize import milp, LinearConstraint, Bounds
            import numpy as np
        except ImportError:
            # Fallback to greedy solver
            return self.solve_greedy(changed_files)
        
        start_time = time.time()
        
        # Normalize file names
        F = []
        for f in changed_files:
            if f in self.dependency_matrix:
                F.append(f)
            elif os.path.basename(f) in self.dependency_matrix:
                F.append(os.path.basename(f))
        
        if not F:
            F = [os.path.basename(f) for f in changed_files]
        
        T = list(self.test_map.keys())
        m = len(T)
        n = len(F)
        
        if m == 0 or n == 0:
            return OptimizationResult(
                selected_tests=[],
                total_cost=0.0,
                coverage_score=0.0,
                confidence_score=0.0,
                optimization_time=time.time() - start_time,
                solver_used="ilp"
            )
        
        # Cost vector c = [C(t1), C(t2), ..., C(tm)]
        c = np.array([self.get_cost(t) for t in T])
        
        # Coverage constraint matrix A
        # Each row i: Σ D(fi, tj) * xj ≥ 1
        A_coverage = np.zeros((n, m))
        for i, file in enumerate(F):
            for j, test in enumerate(T):
                A_coverage[i, j] = self.get_dependency_weight(file, test)
        
        # Confidence constraint (optional)
        # Σ P(tj) * xj ≥ θ
        A_confidence = np.array([[self.get_failure_probability(t) for t in T]])
        
        # Combined constraints
        if self.confidence_threshold > 0:
            A = np.vstack([A_coverage, A_confidence])
            b_l = np.array([1.0] * n + [self.confidence_threshold])
        else:
            A = A_coverage
            b_l = np.array([1.0] * n)
        
        b_u = np.array([np.inf] * len(b_l))
        
        # Variable bounds: xj ∈ {0, 1}
        bounds = Bounds(lb=0, ub=1)
        integrality = np.ones(m)  # All variables are integers
        
        # Solve
        try:
            result = milp(
                c=c,
                constraints=LinearConstraint(A, b_l, b_u),
                bounds=bounds,
                integrality=integrality
            )
            
            if result.success:
                selected_indices = np.where(result.x > 0.5)[0]
                selected_tests = [T[i] for i in selected_indices]
                total_cost = result.fun
            else:
                # Fallback to greedy
                return self.solve_greedy(changed_files)
                
        except Exception:
            # Fallback to greedy
            return self.solve_greedy(changed_files)
        
        # Calculate scores
        coverage_score = 1.0  # ILP guarantees coverage if feasible
        confidence_score = sum(self.get_failure_probability(t) for t in selected_tests)
        
        optimization_time = time.time() - start_time
        
        return OptimizationResult(
            selected_tests=selected_tests,
            total_cost=total_cost,
            coverage_score=coverage_score,
            confidence_score=confidence_score,
            optimization_time=optimization_time,
            solver_used="ilp"
        )
    
    def solve(self, changed_files: List[str], method: str = "auto") -> OptimizationResult:
        """
        Solve test selection optimization.
        
        Args:
            changed_files: List of changed files F
            method: "greedy", "ilp", or "auto"
            
        Returns:
            OptimizationResult with optimal test selection
        """
        if method == "greedy":
            return self.solve_greedy(changed_files)
        elif method == "ilp":
            return self.solve_ilp(changed_files)
        else:
            # Auto: use ILP for small problems, greedy for large
            if len(self.test_map) <= 100 and len(changed_files) <= 50:
                return self.solve_ilp(changed_files)
            else:
                return self.solve_greedy(changed_files)
    
    def update_metrics(self, test_name: str, execution_time: float, failed: bool):
        """
        Update test metrics after execution.
        
        Args:
            test_name: Name of the test
            execution_time: Actual execution time
            failed: Whether the test failed
        """
        if test_name not in self.test_metrics:
            self.test_metrics[test_name] = TestMetrics(name=test_name)
        
        metrics = self.test_metrics[test_name]
        metrics.total_runs += 1
        metrics.last_execution_time = execution_time
        
        # Update execution cost (exponential moving average)
        alpha = 0.3
        metrics.execution_cost = alpha * execution_time + (1 - alpha) * metrics.execution_cost
        
        if failed:
            metrics.total_failures += 1
        
        # Update failure probability
        metrics.failure_probability = metrics.total_failures / metrics.total_runs


def select_tests_optimized(changed_files: List[str], 
                           test_map: Dict[str, List[str]],
                           confidence_threshold: float = 0.0,
                           method: str = "auto") -> Tuple[List[str], OptimizationResult]:
    """
    Optimized test selection using constrained optimization.
    
    This is the main entry point for the optimization framework.
    
    Args:
        changed_files: Files that changed (F)
        test_map: Mapping of tests to files they cover
        confidence_threshold: θ - minimum confidence required
        method: Solver method ("greedy", "ilp", "auto")
        
    Returns:
        Tuple of (selected_tests, optimization_result)
    """
    optimizer = TestSelectionOptimizer(
        test_map=test_map,
        confidence_threshold=confidence_threshold
    )
    
    result = optimizer.solve(changed_files, method=method)
    
    return result.selected_tests, result


# Mathematical model documentation
MATHEMATICAL_MODEL = """
================================================================================
                    HybridCI MATHEMATICAL OPTIMIZATION MODEL
================================================================================

PROBLEM FORMULATION
-------------------

Sets:
    F = {f₁, f₂, ..., fₙ}    Changed files
    T = {t₁, t₂, ..., tₘ}    Test suite  
    L = {l₁, ..., lₖ}        Programming languages

Parameters:
    D(fᵢ, tⱼ) ∈ [0,1]        Dependency weight (test coverage of file)
    C(tⱼ) > 0                Execution cost (time in seconds)
    P(tⱼ) ∈ [0,1]            Historical failure probability
    θ ∈ [0,1]                Confidence threshold

Decision Variables:
    xⱼ ∈ {0, 1}              1 if test tⱼ is selected, 0 otherwise

OPTIMIZATION OBJECTIVE
----------------------

    minimize    Σⱼ C(tⱼ) · xⱼ
    
    (Minimize total execution cost)

CONSTRAINTS
-----------

1. Coverage Constraint (Required):
   
    Σⱼ D(fᵢ, tⱼ) · xⱼ ≥ 1    ∀ fᵢ ∈ F
    
    (Every changed file must be covered by at least one selected test)

2. Confidence Constraint (Optional):
   
    Σⱼ P(tⱼ) · xⱼ ≥ θ
    
    (Selected tests must have sufficient historical failure probability
     to catch regressions with confidence θ)

SOLUTION METHODS
----------------

1. Greedy Approximation (O(m·n)):
   - Cost-effectiveness heuristic: score(tⱼ) = coverage_gain(tⱼ) / C(tⱼ)
   - Iteratively select best test until all files covered
   - Approximation ratio: O(log n) for set cover

2. Integer Linear Programming (Exact):
   - Uses scipy.optimize.milp solver
   - Guaranteed optimal solution
   - Exponential worst-case, but fast for practical sizes

3. Auto Selection:
   - ILP for small problems (|T| ≤ 100, |F| ≤ 50)
   - Greedy for larger problems

COMPLEXITY ANALYSIS
-------------------

This is a variant of the Weighted Set Cover problem:
- NP-hard in general
- Greedy gives O(log n) approximation
- ILP gives exact solution for practical sizes

================================================================================
"""


if __name__ == "__main__":
    # Demo
    print(MATHEMATICAL_MODEL)
    
    # Example usage
    test_map = {
        "test_auth.py": ["auth.py"],
        "test_calculator.py": ["calculator.py"],
        "test_utils.py": ["utils.py", "helpers.py"],
        "test_integration.py": ["auth.py", "calculator.py", "utils.py"]
    }
    
    changed_files = ["calculator.py", "utils.py"]
    
    selected, result = select_tests_optimized(
        changed_files=changed_files,
        test_map=test_map,
        confidence_threshold=0.0,
        method="greedy"
    )
    
    print(f"\nChanged files: {changed_files}")
    print(f"Selected tests: {selected}")
    print(f"Total cost: {result.total_cost:.2f}")
    print(f"Coverage score: {result.coverage_score:.2%}")
    print(f"Solver used: {result.solver_used}")
    print(f"Optimization time: {result.optimization_time*1000:.2f}ms")
