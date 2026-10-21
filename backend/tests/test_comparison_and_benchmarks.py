"""
test_comparison_and_benchmarks.py - Tests for Comparison and Benchmark Services

Validates:
- Comparison service produces consistent lower bounds and comparative analysis
- Random DAG generator produces valid acyclic graphs
- Random DAG generator with identical seed produces identical graphs
- Benchmark suite runs and compiles aggregate statistics
"""

import pytest
from backend.models import Task, Workflow, BenchmarkRequest
from backend.algorithms.comparison import compare_algorithms
from backend.algorithms.random_dag import generate_random_dag
from backend.algorithms.benchmark import run_benchmark
from backend.graph.validator import validate_workflow


def test_comparison_service():
    """Verify comparison structure and lower bounds."""
    tasks = [
        Task(task_id="T1", name="Task 1", duration=4.0, dependencies=[]),
        Task(task_id="T2", name="Task 2", duration=6.0, dependencies=["T1"]),
    ]
    wf = Workflow(workflow_id="comp_test", name="Comp Test", tasks=tasks, number_of_workers=2)
    comp = compare_algorithms(wf)

    assert comp.precedence_lower_bound == 10.0
    assert comp.workload_lower_bound == 5.0
    assert comp.theoretical_lower_bound == 10.0
    assert "Greedy (Critical Path)" in comp.algorithms
    assert "Branch and Bound" in comp.algorithms
    assert comp.best_makespan == 10.0


def test_random_dag_generator_is_valid_dag():
    """Synthetic workflows must always pass static DAG validation and cycle checks."""
    for s in [1, 42, 999]:
        wf = generate_random_dag(num_tasks=10, dependency_density=0.4, seed=s, number_of_workers=2)
        val_res = validate_workflow(wf)
        assert val_res.valid is True
        assert len(wf.tasks) == 10


def test_random_dag_seed_reproducibility():
    """Identical seed must produce bit-for-bit identical tasks and dependencies."""
    wf1 = generate_random_dag(num_tasks=8, dependency_density=0.3, seed=123)
    wf2 = generate_random_dag(num_tasks=8, dependency_density=0.3, seed=123)

    assert [t.task_id for t in wf1.tasks] == [t.task_id for t in wf2.tasks]
    assert [t.duration for t in wf1.tasks] == [t.duration for t in wf2.tasks]
    assert [t.dependencies for t in wf1.tasks] == [t.dependencies for t in wf2.tasks]


def test_benchmark_suite_execution():
    """Benchmark runner should execute configurations and aggregate statistics."""
    req = BenchmarkRequest(
        task_counts=[4],
        worker_counts=[2],
        dependency_densities=[0.3],
        algorithms=["greedy_critical_path", "branch_and_bound"],
        repetitions=1,
        seed=77
    )
    resp = run_benchmark(req)
    assert resp.total_runs == 2
    assert "Greedy (CP)" in resp.summary
    assert "Branch and Bound" in resp.summary
    assert resp.total_runtime_ms > 0.0
