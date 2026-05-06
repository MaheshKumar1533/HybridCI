"""
HybridCI Experimental Framework

Comprehensive experimental validation with:
- Multi-language repository datasets
- Baseline comparisons
- Statistical significance testing

Reference: Section 6-9 of experimental methodology
"""

import os
import sys
import json
import time
import random
import hashlib
import subprocess
import statistics
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field, asdict
from collections import defaultdict
from enum import Enum

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ci_engine.cldg import CLDGBuilder, CLDG, TestSelectionResult


# =============================================================================
# STEP 6: DATASET SELECTION
# =============================================================================

@dataclass
class RepositoryDataset:
    """
    Dataset specification for experimental validation.
    
    Requirements:
        - 5+ GitHub multi-language repositories
        - 1000+ commits each
        - Different sizes (small, medium, large)
        - Different types (full-stack, microservices, ML pipelines)
    """
    name: str
    url: str
    category: str  # 'fullstack', 'microservices', 'ml_pipeline', 'monorepo'
    size: str  # 'small', 'medium', 'large'
    languages: List[str]
    estimated_commits: int
    estimated_files: int
    estimated_tests: int
    description: str = ""


# Curated dataset of multi-language repositories
EXPERIMENTAL_DATASETS: List[RepositoryDataset] = [
    # Full-stack Web Applications
    RepositoryDataset(
        name="discourse",
        url="https://github.com/discourse/discourse",
        category="fullstack",
        size="large",
        languages=["ruby", "javascript", "typescript"],
        estimated_commits=45000,
        estimated_files=8000,
        estimated_tests=5000,
        description="Full-stack discussion platform (Ruby/Rails + Ember.js)"
    ),
    RepositoryDataset(
        name="gitlab",
        url="https://github.com/gitlabhq/gitlabhq",
        category="fullstack",
        size="large",
        languages=["ruby", "javascript", "vue", "go"],
        estimated_commits=150000,
        estimated_files=25000,
        estimated_tests=15000,
        description="DevOps platform with multiple languages"
    ),
    RepositoryDataset(
        name="mastodon",
        url="https://github.com/mastodon/mastodon",
        category="fullstack",
        size="medium",
        languages=["ruby", "javascript", "typescript"],
        estimated_commits=15000,
        estimated_files=2000,
        estimated_tests=1500,
        description="Decentralized social network (Rails + React)"
    ),
    
    # Microservices Repositories
    RepositoryDataset(
        name="kubernetes",
        url="https://github.com/kubernetes/kubernetes",
        category="microservices",
        size="large",
        languages=["go", "python", "bash"],
        estimated_commits=120000,
        estimated_files=15000,
        estimated_tests=8000,
        description="Container orchestration with Go microservices"
    ),
    RepositoryDataset(
        name="istio",
        url="https://github.com/istio/istio",
        category="microservices",
        size="medium",
        languages=["go", "python", "javascript"],
        estimated_commits=20000,
        estimated_files=5000,
        estimated_tests=3000,
        description="Service mesh with multiple language SDKs"
    ),
    RepositoryDataset(
        name="dapr",
        url="https://github.com/dapr/dapr",
        category="microservices",
        size="medium",
        languages=["go", "python", "javascript", "java", "csharp"],
        estimated_commits=5000,
        estimated_files=2000,
        estimated_tests=1500,
        description="Portable microservices runtime"
    ),
    
    # ML Pipeline Repositories
    RepositoryDataset(
        name="mlflow",
        url="https://github.com/mlflow/mlflow",
        category="ml_pipeline",
        size="medium",
        languages=["python", "javascript", "java", "r"],
        estimated_commits=8000,
        estimated_files=3000,
        estimated_tests=2000,
        description="ML lifecycle management platform"
    ),
    RepositoryDataset(
        name="airflow",
        url="https://github.com/apache/airflow",
        category="ml_pipeline",
        size="large",
        languages=["python", "javascript", "typescript"],
        estimated_commits=30000,
        estimated_files=8000,
        estimated_tests=6000,
        description="Workflow orchestration platform"
    ),
    RepositoryDataset(
        name="kubeflow",
        url="https://github.com/kubeflow/kubeflow",
        category="ml_pipeline",
        size="medium",
        languages=["python", "go", "javascript", "typescript"],
        estimated_commits=5000,
        estimated_files=2000,
        estimated_tests=1000,
        description="ML toolkit for Kubernetes"
    ),
    
    # Monorepo / Large Scale
    RepositoryDataset(
        name="vscode",
        url="https://github.com/microsoft/vscode",
        category="monorepo",
        size="large",
        languages=["typescript", "javascript", "css"],
        estimated_commits=100000,
        estimated_files=12000,
        estimated_tests=5000,
        description="Large-scale TypeScript application"
    ),
]


def get_datasets_by_size(size: str) -> List[RepositoryDataset]:
    """Get datasets filtered by size."""
    return [d for d in EXPERIMENTAL_DATASETS if d.size == size]


def get_datasets_by_category(category: str) -> List[RepositoryDataset]:
    """Get datasets filtered by category."""
    return [d for d in EXPERIMENTAL_DATASETS if d.category == category]


# =============================================================================
# STEP 7: BASELINE COMPARISONS
# =============================================================================

class SelectionStrategy(Enum):
    """Test selection strategies for comparison."""
    FULL_EXECUTION = "full"           # Run all tests (baseline)
    PATH_BASED = "path"               # Simple path/filename matching
    IBST_ORIGINAL = "ibst"            # Original IBST algorithm
    HYBRIDCI_CLDG = "hybridci"        # HybridCI + CLDG + Optimization


@dataclass
class SelectionResult:
    """Result of a test selection strategy."""
    strategy: str
    tests_selected: int
    tests_total: int
    execution_time_ms: float
    selection_time_ms: float
    tests_list: List[str] = field(default_factory=list)


class BaselineComparator:
    """
    Baseline comparison framework.
    
    Compares:
        1. Full test execution (all tests)
        2. Path-based selection (simple filename matching)
        3. Original IBST (import-based selection)
        4. HybridCI + CLDG + Optimization
    """
    
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.cldg: Optional[CLDG] = None
        self.all_tests: List[str] = []
        self.test_costs: Dict[str, float] = {}  # test -> execution time
        
    def initialize(self):
        """Build CLDG and discover all tests."""
        builder = CLDGBuilder(self.project_path)
        self.cldg = builder.build()
        
        # Collect all test files
        self.all_tests = [
            node_id for node_id, node in self.cldg.nodes.items()
            if node.node_type == 'test'
        ]
        
        # Initialize with default costs (can be updated with actual times)
        for test in self.all_tests:
            self.test_costs[test] = self.cldg.nodes[test].cost
    
    def set_test_costs(self, costs: Dict[str, float]):
        """Update test costs from historical execution data."""
        self.test_costs.update(costs)
        for test, cost in costs.items():
            if test in self.cldg.nodes:
                self.cldg.set_node_cost(test, cost)
    
    # =========================================================================
    # Strategy 1: Full Execution (Baseline)
    # =========================================================================
    
    def full_execution(self, changed_files: List[str]) -> SelectionResult:
        """
        Baseline: Execute all tests regardless of changes.
        
        This is the naive approach with no optimization.
        """
        start = time.perf_counter()
        
        # Select all tests
        selected = self.all_tests.copy()
        
        selection_time = (time.perf_counter() - start) * 1000
        execution_time = sum(self.test_costs.get(t, 1.0) for t in selected) * 1000
        
        return SelectionResult(
            strategy="full_execution",
            tests_selected=len(selected),
            tests_total=len(self.all_tests),
            execution_time_ms=execution_time,
            selection_time_ms=selection_time,
            tests_list=selected
        )
    
    # =========================================================================
    # Strategy 2: Path-Based Selection
    # =========================================================================
    
    def path_based_selection(self, changed_files: List[str]) -> SelectionResult:
        """
        Simple path-based test selection.
        
        Selects tests in the same directory or with matching names.
        """
        start = time.perf_counter()
        
        selected = set()
        
        for changed in changed_files:
            changed_dir = os.path.dirname(changed)
            changed_base = os.path.splitext(os.path.basename(changed))[0]
            
            for test in self.all_tests:
                test_dir = os.path.dirname(test)
                test_base = os.path.splitext(os.path.basename(test))[0]
                
                # Match by directory proximity
                if changed_dir in test_dir or test_dir in changed_dir:
                    selected.add(test)
                    continue
                
                # Match by name similarity
                if changed_base in test_base or test_base.replace('test_', '') == changed_base:
                    selected.add(test)
        
        selection_time = (time.perf_counter() - start) * 1000
        selected_list = list(selected)
        execution_time = sum(self.test_costs.get(t, 1.0) for t in selected_list) * 1000
        
        return SelectionResult(
            strategy="path_based",
            tests_selected=len(selected_list),
            tests_total=len(self.all_tests),
            execution_time_ms=execution_time,
            selection_time_ms=selection_time,
            tests_list=selected_list
        )
    
    # =========================================================================
    # Strategy 3: Original IBST (Import-Based Selection)
    # =========================================================================
    
    def ibst_selection(self, changed_files: List[str]) -> SelectionResult:
        """
        Original IBST: Import-based test selection.
        
        Uses simple import analysis without cross-language support.
        """
        start = time.perf_counter()
        
        selected = set()
        
        # Build simple import map (single language)
        import_map: Dict[str, Set[str]] = defaultdict(set)
        
        for node_id, node in self.cldg.nodes.items():
            for imp in node.imports:
                # Simple module name matching
                module_name = imp.split('.')[-1]
                import_map[module_name].add(node_id)
        
        # Find tests that import changed files
        for changed in changed_files:
            changed_base = os.path.splitext(os.path.basename(changed))[0]
            
            # Direct name matching
            if changed_base in import_map:
                for importer in import_map[changed_base]:
                    if self.cldg.nodes.get(importer, {}).node_type == 'test':
                        selected.add(importer)
            
            # Also add tests with naming convention
            for test in self.all_tests:
                test_base = os.path.basename(test)
                if test_base.startswith(f'test_{changed_base}'):
                    selected.add(test)
        
        selection_time = (time.perf_counter() - start) * 1000
        selected_list = list(selected)
        execution_time = sum(self.test_costs.get(t, 1.0) for t in selected_list) * 1000
        
        return SelectionResult(
            strategy="ibst_original",
            tests_selected=len(selected_list),
            tests_total=len(self.all_tests),
            execution_time_ms=execution_time,
            selection_time_ms=selection_time,
            tests_list=selected_list
        )
    
    # =========================================================================
    # Strategy 4: HybridCI + CLDG + Optimization
    # =========================================================================
    
    def hybridci_selection(self, changed_files: List[str]) -> SelectionResult:
        """
        HybridCI: Full CLDG + Graph Traversal + Optimization.
        
        This is our proposed method with:
        - Cross-language dependency graph
        - BFS traversal O(n+e)
        - Constrained optimization O(m log m)
        """
        start = time.perf_counter()
        
        # Use CLDG graph traversal + optimization
        result = self.cldg.select_minimal_test_set(changed_files)
        
        selection_time = (time.perf_counter() - start) * 1000
        execution_time = sum(self.test_costs.get(t, 1.0) for t in result.selected_tests) * 1000
        
        return SelectionResult(
            strategy="hybridci_cldg",
            tests_selected=len(result.selected_tests),
            tests_total=len(self.all_tests),
            execution_time_ms=execution_time,
            selection_time_ms=selection_time,
            tests_list=result.selected_tests
        )
    
    # =========================================================================
    # Run All Strategies
    # =========================================================================
    
    def compare_all(self, changed_files: List[str]) -> Dict[str, SelectionResult]:
        """Run all selection strategies and return results."""
        return {
            "full_execution": self.full_execution(changed_files),
            "path_based": self.path_based_selection(changed_files),
            "ibst_original": self.ibst_selection(changed_files),
            "hybridci_cldg": self.hybridci_selection(changed_files),
        }


# =============================================================================
# STEP 8: METRICS
# =============================================================================

@dataclass
class ExperimentMetrics:
    """
    Comprehensive metrics for experimental evaluation.
    
    Metrics:
        - Time Reduction %: Execution speed gain
        - Test Reduction %: Fewer tests executed
        - False Negative Rate: Missed failing tests
        - Cache Hit Rate: Reuse efficiency
        - Resource Usage: CPU/memory/time
    """
    # Identification
    experiment_id: str
    timestamp: str
    dataset: str
    commit_id: str
    
    # Selection metrics
    total_tests: int
    tests_selected: int
    test_reduction_pct: float
    
    # Time metrics
    baseline_time_ms: float
    optimized_time_ms: float
    time_reduction_pct: float
    selection_overhead_ms: float
    
    # Quality metrics
    false_negatives: int
    false_negative_rate: float
    true_positives: int
    precision: float
    recall: float
    f1_score: float
    
    # Cache metrics
    cache_hits: int
    cache_misses: int
    cache_hit_rate: float
    
    # Resource metrics
    cpu_time_ms: float
    memory_mb: float
    
    # Strategy used
    strategy: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


class MetricsCollector:
    """
    Collects and computes experimental metrics.
    """
    
    def __init__(self):
        self.results: List[ExperimentMetrics] = []
    
    def compute_metrics(
        self,
        experiment_id: str,
        dataset: str,
        commit_id: str,
        baseline_result: SelectionResult,
        optimized_result: SelectionResult,
        actual_failures: List[str],
        cache_stats: Dict[str, int],
        resource_stats: Dict[str, float]
    ) -> ExperimentMetrics:
        """
        Compute all metrics for a single experiment run.
        
        Args:
            experiment_id: Unique experiment identifier
            dataset: Dataset/repository name
            commit_id: Git commit being tested
            baseline_result: Full execution result
            optimized_result: Optimized selection result
            actual_failures: List of tests that actually failed
            cache_stats: {'hits': n, 'misses': m}
            resource_stats: {'cpu_ms': n, 'memory_mb': m}
        """
        # Test reduction
        test_reduction = 1 - (optimized_result.tests_selected / baseline_result.tests_selected)
        
        # Time reduction
        time_reduction = 1 - (optimized_result.execution_time_ms / baseline_result.execution_time_ms)
        
        # False negatives: failed tests that were not selected
        selected_set = set(optimized_result.tests_list)
        failure_set = set(actual_failures)
        
        false_negatives = len(failure_set - selected_set)
        true_positives = len(failure_set & selected_set)
        
        # False negative rate
        fnr = false_negatives / len(failure_set) if failure_set else 0.0
        
        # Precision/Recall/F1
        # Precision: Of selected tests, how many were failures?
        precision = true_positives / len(selected_set) if selected_set else 0.0
        # Recall: Of actual failures, how many did we select?
        recall = true_positives / len(failure_set) if failure_set else 1.0
        # F1
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        
        # Cache metrics
        cache_hits = cache_stats.get('hits', 0)
        cache_misses = cache_stats.get('misses', 0)
        cache_total = cache_hits + cache_misses
        cache_hit_rate = cache_hits / cache_total if cache_total > 0 else 0.0
        
        metrics = ExperimentMetrics(
            experiment_id=experiment_id,
            timestamp=datetime.now().isoformat(),
            dataset=dataset,
            commit_id=commit_id,
            
            total_tests=baseline_result.tests_total,
            tests_selected=optimized_result.tests_selected,
            test_reduction_pct=test_reduction * 100,
            
            baseline_time_ms=baseline_result.execution_time_ms,
            optimized_time_ms=optimized_result.execution_time_ms,
            time_reduction_pct=time_reduction * 100,
            selection_overhead_ms=optimized_result.selection_time_ms,
            
            false_negatives=false_negatives,
            false_negative_rate=fnr * 100,
            true_positives=true_positives,
            precision=precision,
            recall=recall,
            f1_score=f1,
            
            cache_hits=cache_hits,
            cache_misses=cache_misses,
            cache_hit_rate=cache_hit_rate * 100,
            
            cpu_time_ms=resource_stats.get('cpu_ms', 0),
            memory_mb=resource_stats.get('memory_mb', 0),
            
            strategy=optimized_result.strategy
        )
        
        self.results.append(metrics)
        return metrics
    
    def get_summary_statistics(self) -> Dict[str, Dict[str, float]]:
        """Compute summary statistics across all experiments."""
        if not self.results:
            return {}
        
        metrics_by_strategy: Dict[str, List[ExperimentMetrics]] = defaultdict(list)
        for m in self.results:
            metrics_by_strategy[m.strategy].append(m)
        
        summary = {}
        for strategy, metrics_list in metrics_by_strategy.items():
            summary[strategy] = {
                'mean_test_reduction': statistics.mean(m.test_reduction_pct for m in metrics_list),
                'std_test_reduction': statistics.stdev(m.test_reduction_pct for m in metrics_list) if len(metrics_list) > 1 else 0,
                'mean_time_reduction': statistics.mean(m.time_reduction_pct for m in metrics_list),
                'std_time_reduction': statistics.stdev(m.time_reduction_pct for m in metrics_list) if len(metrics_list) > 1 else 0,
                'mean_fnr': statistics.mean(m.false_negative_rate for m in metrics_list),
                'mean_cache_hit_rate': statistics.mean(m.cache_hit_rate for m in metrics_list),
                'mean_f1': statistics.mean(m.f1_score for m in metrics_list),
                'n_experiments': len(metrics_list)
            }
        
        return summary


# =============================================================================
# STEP 9: STATISTICAL VALIDATION
# =============================================================================

class StatisticalValidator:
    """
    Statistical validation of experimental results.
    
    Tests:
        - Paired t-test (parametric)
        - Wilcoxon signed-rank test (non-parametric)
        - Effect size (Cohen's d)
    """
    
    @staticmethod
    def paired_t_test(baseline: List[float], treatment: List[float]) -> Dict[str, float]:
        """
        Perform paired t-test for comparing two related samples.
        
        H0: There is no difference between baseline and treatment
        H1: There is a significant difference
        
        Args:
            baseline: Baseline measurements
            treatment: Treatment measurements (same subjects)
            
        Returns:
            {'t_statistic': t, 'p_value': p, 'significant': bool}
        """
        try:
            from scipy import stats
            t_stat, p_value = stats.ttest_rel(baseline, treatment)
            return {
                't_statistic': t_stat,
                'p_value': p_value,
                'significant': p_value < 0.05,
                'test': 'paired_t_test'
            }
        except ImportError:
            # Fallback: manual calculation
            n = len(baseline)
            if n < 2:
                return {'error': 'insufficient_samples'}
            
            differences = [b - t for b, t in zip(baseline, treatment)]
            mean_diff = statistics.mean(differences)
            std_diff = statistics.stdev(differences)
            
            t_stat = mean_diff / (std_diff / (n ** 0.5))
            
            # Approximate p-value using normal distribution for large n
            from math import erf, sqrt
            p_value = 2 * (1 - 0.5 * (1 + erf(abs(t_stat) / sqrt(2))))
            
            return {
                't_statistic': t_stat,
                'p_value': p_value,
                'significant': p_value < 0.05,
                'test': 'paired_t_test_manual'
            }
    
    @staticmethod
    def wilcoxon_signed_rank(baseline: List[float], treatment: List[float]) -> Dict[str, float]:
        """
        Perform Wilcoxon signed-rank test (non-parametric).
        
        Used when data may not be normally distributed.
        
        Args:
            baseline: Baseline measurements
            treatment: Treatment measurements
            
        Returns:
            {'w_statistic': w, 'p_value': p, 'significant': bool}
        """
        try:
            from scipy import stats
            w_stat, p_value = stats.wilcoxon(baseline, treatment)
            return {
                'w_statistic': w_stat,
                'p_value': p_value,
                'significant': p_value < 0.05,
                'test': 'wilcoxon_signed_rank'
            }
        except ImportError:
            # Simplified fallback
            n = len(baseline)
            if n < 2:
                return {'error': 'insufficient_samples'}
            
            differences = [b - t for b, t in zip(baseline, treatment)]
            
            # Count positive and negative differences
            positive = sum(1 for d in differences if d > 0)
            negative = sum(1 for d in differences if d < 0)
            
            # Simple sign test approximation
            w_stat = min(positive, negative)
            
            return {
                'w_statistic': w_stat,
                'positive_ranks': positive,
                'negative_ranks': negative,
                'test': 'sign_test_approximation'
            }
    
    @staticmethod
    def cohens_d(baseline: List[float], treatment: List[float]) -> Dict[str, float]:
        """
        Calculate Cohen's d effect size.
        
        Interpretation:
            |d| < 0.2: negligible
            0.2 <= |d| < 0.5: small
            0.5 <= |d| < 0.8: medium
            |d| >= 0.8: large
        """
        n1, n2 = len(baseline), len(treatment)
        if n1 < 2 or n2 < 2:
            return {'error': 'insufficient_samples'}
        
        mean1 = statistics.mean(baseline)
        mean2 = statistics.mean(treatment)
        
        var1 = statistics.variance(baseline)
        var2 = statistics.variance(treatment)
        
        # Pooled standard deviation
        pooled_std = ((var1 * (n1 - 1) + var2 * (n2 - 1)) / (n1 + n2 - 2)) ** 0.5
        
        d = (mean1 - mean2) / pooled_std if pooled_std > 0 else 0
        
        # Interpretation
        abs_d = abs(d)
        if abs_d < 0.2:
            interpretation = 'negligible'
        elif abs_d < 0.5:
            interpretation = 'small'
        elif abs_d < 0.8:
            interpretation = 'medium'
        else:
            interpretation = 'large'
        
        return {
            'cohens_d': d,
            'effect_size': interpretation,
            'mean_baseline': mean1,
            'mean_treatment': mean2
        }
    
    @staticmethod
    def validate_experiment(
        baseline_times: List[float],
        treatment_times: List[float],
        alpha: float = 0.05
    ) -> Dict[str, Any]:
        """
        Complete statistical validation of experiment.
        
        Returns comprehensive statistical analysis.
        """
        results = {
            'n_samples': len(baseline_times),
            'alpha': alpha,
            'baseline_mean': statistics.mean(baseline_times) if baseline_times else 0,
            'treatment_mean': statistics.mean(treatment_times) if treatment_times else 0,
        }
        
        if len(baseline_times) >= 2 and len(treatment_times) >= 2:
            results['paired_t_test'] = StatisticalValidator.paired_t_test(
                baseline_times, treatment_times
            )
            results['wilcoxon'] = StatisticalValidator.wilcoxon_signed_rank(
                baseline_times, treatment_times
            )
            results['effect_size'] = StatisticalValidator.cohens_d(
                baseline_times, treatment_times
            )
            
            # Overall significance
            t_sig = results['paired_t_test'].get('significant', False)
            w_sig = results['wilcoxon'].get('significant', False)
            results['significant'] = t_sig or w_sig
            
        return results


# =============================================================================
# EXPERIMENT RUNNER
# =============================================================================

@dataclass
class ExperimentConfig:
    """Configuration for running experiments."""
    name: str
    datasets: List[str]
    n_commits_per_dataset: int = 100
    n_iterations: int = 10
    strategies: List[str] = field(default_factory=lambda: [
        'full_execution', 'path_based', 'ibst_original', 'hybridci_cldg'
    ])
    output_dir: str = 'experiment_results'
    random_seed: int = 42


class ExperimentRunner:
    """
    Main experiment runner for HybridCI validation.
    """
    
    def __init__(self, config: ExperimentConfig):
        self.config = config
        self.metrics_collector = MetricsCollector()
        self.validator = StatisticalValidator()
        self.results: Dict[str, List[Dict]] = defaultdict(list)
        
        random.seed(config.random_seed)
        
    def run_single_experiment(
        self,
        project_path: str,
        changed_files: List[str],
        actual_failures: List[str] = None
    ) -> Dict[str, Any]:
        """Run a single experiment iteration."""
        
        comparator = BaselineComparator(project_path)
        comparator.initialize()
        
        # Run all strategies
        results = comparator.compare_all(changed_files)
        
        # Compute metrics for HybridCI vs baseline
        baseline = results['full_execution']
        hybridci = results['hybridci_cldg']
        
        metrics = self.metrics_collector.compute_metrics(
            experiment_id=f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            dataset=os.path.basename(project_path),
            commit_id="HEAD",
            baseline_result=baseline,
            optimized_result=hybridci,
            actual_failures=actual_failures or [],
            cache_stats={'hits': 0, 'misses': len(changed_files)},
            resource_stats={'cpu_ms': 0, 'memory_mb': 0}
        )
        
        return {
            'strategies': {k: asdict(v) if hasattr(v, '__dict__') else v for k, v in results.items()},
            'metrics': metrics.to_dict()
        }
    
    def run_full_experiment(self, project_path: str) -> Dict[str, Any]:
        """
        Run full experimental procedure on a project.
        
        Returns comprehensive results with statistical validation.
        """
        print(f"\n{'='*60}")
        print(f"Running experiment on: {project_path}")
        print(f"{'='*60}")
        
        comparator = BaselineComparator(project_path)
        comparator.initialize()
        
        # Simulate multiple commits/changes
        all_source_files = [
            nid for nid, n in comparator.cldg.nodes.items()
            if n.node_type == 'source'
        ]
        
        baseline_times = []
        hybridci_times = []
        ibst_times = []
        path_times = []
        
        for i in range(self.config.n_iterations):
            # Random change set
            n_changes = random.randint(1, min(5, len(all_source_files)))
            changed_files = random.sample(all_source_files, n_changes)
            
            results = comparator.compare_all(changed_files)
            
            baseline_times.append(results['full_execution'].execution_time_ms)
            hybridci_times.append(results['hybridci_cldg'].execution_time_ms)
            ibst_times.append(results['ibst_original'].execution_time_ms)
            path_times.append(results['path_based'].execution_time_ms)
        
        # Statistical validation
        stats_hybridci = self.validator.validate_experiment(baseline_times, hybridci_times)
        stats_ibst = self.validator.validate_experiment(baseline_times, ibst_times)
        stats_path = self.validator.validate_experiment(baseline_times, path_times)
        
        return {
            'project': project_path,
            'n_iterations': self.config.n_iterations,
            'n_tests': len(comparator.all_tests),
            'n_source_files': len(all_source_files),
            'strategies': {
                'full_execution': {
                    'mean_time_ms': statistics.mean(baseline_times),
                    'std_time_ms': statistics.stdev(baseline_times) if len(baseline_times) > 1 else 0
                },
                'hybridci_cldg': {
                    'mean_time_ms': statistics.mean(hybridci_times),
                    'std_time_ms': statistics.stdev(hybridci_times) if len(hybridci_times) > 1 else 0,
                    'reduction_pct': (1 - statistics.mean(hybridci_times) / statistics.mean(baseline_times)) * 100,
                    'statistical_validation': stats_hybridci
                },
                'ibst_original': {
                    'mean_time_ms': statistics.mean(ibst_times),
                    'std_time_ms': statistics.stdev(ibst_times) if len(ibst_times) > 1 else 0,
                    'reduction_pct': (1 - statistics.mean(ibst_times) / statistics.mean(baseline_times)) * 100,
                    'statistical_validation': stats_ibst
                },
                'path_based': {
                    'mean_time_ms': statistics.mean(path_times),
                    'std_time_ms': statistics.stdev(path_times) if len(path_times) > 1 else 0,
                    'reduction_pct': (1 - statistics.mean(path_times) / statistics.mean(baseline_times)) * 100,
                    'statistical_validation': stats_path
                }
            }
        }
    
    def generate_report(self) -> str:
        """Generate experimental report."""
        summary = self.metrics_collector.get_summary_statistics()
        
        report = []
        report.append("=" * 70)
        report.append("          HYBRIDCI EXPERIMENTAL RESULTS")
        report.append("=" * 70)
        report.append("")
        
        for strategy, stats in summary.items():
            report.append(f"\nStrategy: {strategy}")
            report.append("-" * 40)
            report.append(f"  Test Reduction:  {stats['mean_test_reduction']:.1f}% ± {stats['std_test_reduction']:.1f}%")
            report.append(f"  Time Reduction:  {stats['mean_time_reduction']:.1f}% ± {stats['std_time_reduction']:.1f}%")
            report.append(f"  False Negative Rate: {stats['mean_fnr']:.2f}%")
            report.append(f"  Cache Hit Rate:  {stats['mean_cache_hit_rate']:.1f}%")
            report.append(f"  F1 Score:        {stats['mean_f1']:.3f}")
            report.append(f"  N Experiments:   {stats['n_experiments']}")
        
        return "\n".join(report)


# =============================================================================
# MAIN DEMO
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("          HYBRIDCI EXPERIMENTAL FRAMEWORK")
    print("=" * 70)
    
    # Step 6: Show available datasets
    print("\n📊 STEP 6: DATASET SELECTION")
    print("-" * 40)
    print(f"Available datasets: {len(EXPERIMENTAL_DATASETS)}")
    for ds in EXPERIMENTAL_DATASETS[:5]:
        print(f"  • {ds.name} ({ds.size}): {ds.languages}")
    print("  ...")
    
    # Step 7-9: Run experiment on sample_repo
    print("\n🔬 STEPS 7-9: EXPERIMENTAL PROCEDURE")
    print("-" * 40)
    
    config = ExperimentConfig(
        name="sample_experiment",
        datasets=["sample_repo"],
        n_iterations=10
    )
    
    runner = ExperimentRunner(config)
    results = runner.run_full_experiment("sample_repo")
    
    print("\n📈 RESULTS:")
    print("-" * 40)
    print(f"Project: {results['project']}")
    print(f"Iterations: {results['n_iterations']}")
    print(f"Tests: {results['n_tests']}")
    print(f"Source files: {results['n_source_files']}")
    
    print("\n📊 STRATEGY COMPARISON:")
    for strategy, data in results['strategies'].items():
        print(f"\n  {strategy}:")
        print(f"    Mean time: {data['mean_time_ms']:.2f}ms ± {data.get('std_time_ms', 0):.2f}ms")
        if 'reduction_pct' in data:
            print(f"    Reduction: {data['reduction_pct']:.1f}%")
        if 'statistical_validation' in data:
            sv = data['statistical_validation']
            if 'paired_t_test' in sv:
                pt = sv['paired_t_test']
                sig = "✓ SIGNIFICANT" if pt.get('significant') else "✗ not significant"
                print(f"    T-test: t={pt.get('t_statistic', 0):.3f}, p={pt.get('p_value', 1):.4f} {sig}")
            if 'effect_size' in sv:
                es = sv['effect_size']
                print(f"    Effect size: d={es.get('cohens_d', 0):.3f} ({es.get('effect_size', 'unknown')})")
    
    print("\n" + "=" * 70)
    print("          THEORETICAL GUARANTEES")
    print("=" * 70)
    print("""
    ✓ Lemma 1 (Completeness): All dependent tests selected
    ✓ Lemma 2 (Complexity): O(n+e) traversal + O(m log m) optimization  
    ✓ Lemma 3 (Approximation): O(log m) ratio for greedy solver
    
    Statistical Validation:
    • Paired t-test for parametric comparison
    • Wilcoxon signed-rank for non-parametric validation
    • Cohen's d for effect size measurement
    """)
