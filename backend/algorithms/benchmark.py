"""
benchmark.py - Systematic Algorithmic Benchmark Engine

Executes rigorous performance experiments across varying:
- Workflow sizes (|V| = 4, 6, 8, 12, 16, etc.)
- Worker capacities (W = 1, 2, 4, 8)
- Dependency densities (sparse vs. dense DAGs)
- Random seeds for statistical variance and reproducibility

Records:
- Real wall-clock execution time (ms)
- Makespans achieved
- States explored and pruned
- Optimality status
"""

import time
from typing import List, Dict, Any, Optional

from backend.models import (
    BenchmarkRequest,
    BenchmarkResponse,
    BenchmarkItem
)
from backend.graph.dag import DAG
from backend.algorithms.random_dag import generate_random_dag
from backend.algorithms.critical_path import calculate_critical_path
from backend.algorithms.greedy_scheduler import schedule_greedy
from backend.algorithms.exact_backtracking import schedule_backtrack
from backend.algorithms.branch_and_bound import schedule_branch_and_bound


def run_benchmark(request: BenchmarkRequest) -> BenchmarkResponse:
    """
    Executes a structured benchmark suite based on the provided request parameters.

    Args:
        request: BenchmarkRequest specifying task counts, worker counts, densities, algorithms.

    Returns:
        BenchmarkResponse with per-configuration results and summary statistics.
    """
    suite_start = time.perf_counter()
    results: List[BenchmarkItem] = []

    base_seed = request.seed if request.seed is not None else 42
    run_counter = 0

    for rep in range(request.repetitions):
        current_seed = base_seed + (rep * 1000)

        for n_tasks in request.task_counts:
            # Bound n_tasks safely
            safe_n = max(2, min(n_tasks, 40))

            for density in request.dependency_densities:
                safe_density = max(0.0, min(density, 1.0))

                for n_workers in request.worker_counts:
                    safe_workers = max(1, min(n_workers, 16))

                    # Generate reproducible synthetic DAG
                    wf = generate_random_dag(
                        num_tasks=safe_n,
                        dependency_density=safe_density,
                        seed=current_seed + n_tasks,
                        number_of_workers=safe_workers
                    )
                    dag = DAG(wf.tasks)
                    cp_res = calculate_critical_path(dag)
                    lower_bound = cp_res.project_duration if cp_res.valid else 0.0

                    for alg_name in request.algorithms:
                        alg_lower = alg_name.lower().strip()
                        run_counter += 1

                        if alg_lower in ("greedy", "greedy_critical_path", "greedy_cp"):
                            res = schedule_greedy(wf, priority_policy="CRITICAL_PATH", dag=dag)
                            results.append(
                                BenchmarkItem(
                                    num_tasks=safe_n,
                                    num_workers=safe_workers,
                                    density=safe_density,
                                    seed=current_seed + n_tasks,
                                    algorithm="Greedy (CP)",
                                    makespan=res.makespan,
                                    runtime_ms=res.runtime_ms,
                                    states_explored=res.states_explored,
                                    states_pruned=res.states_pruned,
                                    optimality_status=res.status,
                                    lower_bound=round(lower_bound, 4)
                                )
                            )

                        elif alg_lower in ("greedy_lpt", "lpt"):
                            res = schedule_greedy(wf, priority_policy="LPT", dag=dag)
                            results.append(
                                BenchmarkItem(
                                    num_tasks=safe_n,
                                    num_workers=safe_workers,
                                    density=safe_density,
                                    seed=current_seed + n_tasks,
                                    algorithm="Greedy (LPT)",
                                    makespan=res.makespan,
                                    runtime_ms=res.runtime_ms,
                                    states_explored=res.states_explored,
                                    states_pruned=res.states_pruned,
                                    optimality_status=res.status,
                                    lower_bound=round(lower_bound, 4)
                                )
                            )

                        elif alg_lower in ("greedy_spt", "spt"):
                            res = schedule_greedy(wf, priority_policy="SPT", dag=dag)
                            results.append(
                                BenchmarkItem(
                                    num_tasks=safe_n,
                                    num_workers=safe_workers,
                                    density=safe_density,
                                    seed=current_seed + n_tasks,
                                    algorithm="Greedy (SPT)",
                                    makespan=res.makespan,
                                    runtime_ms=res.runtime_ms,
                                    states_explored=res.states_explored,
                                    states_pruned=res.states_pruned,
                                    optimality_status=res.status,
                                    lower_bound=round(lower_bound, 4)
                                )
                            )

                        elif alg_lower in ("exact", "backtracking", "exact_backtracking"):
                            # Apply conservative limits for large task counts
                            limit = request.backtrack_state_limit
                            if safe_n > 14:
                                limit = min(limit, 3000)
                            res = schedule_backtrack(
                                wf,
                                max_states=limit,
                                time_limit_sec=1.5,
                                dag=dag
                            )
                            results.append(
                                BenchmarkItem(
                                    num_tasks=safe_n,
                                    num_workers=safe_workers,
                                    density=safe_density,
                                    seed=current_seed + n_tasks,
                                    algorithm="Exact Backtracking",
                                    makespan=res.makespan,
                                    runtime_ms=res.runtime_ms,
                                    states_explored=res.states_explored,
                                    states_pruned=None,
                                    optimality_status=res.status,
                                    lower_bound=round(lower_bound, 4)
                                )
                            )

                        elif alg_lower in ("branch_and_bound", "bnb"):
                            limit = request.backtrack_state_limit
                            if safe_n > 14:
                                limit = min(limit, 5000)
                            res = schedule_branch_and_bound(
                                wf,
                                max_states=limit,
                                time_limit_sec=2.0,
                                dag=dag
                            )
                            results.append(
                                BenchmarkItem(
                                    num_tasks=safe_n,
                                    num_workers=safe_workers,
                                    density=safe_density,
                                    seed=current_seed + n_tasks,
                                    algorithm="Branch and Bound",
                                    makespan=res.makespan,
                                    runtime_ms=res.runtime_ms,
                                    states_explored=res.states_explored,
                                    states_pruned=res.states_pruned,
                                    optimality_status=res.status,
                                    lower_bound=round(lower_bound, 4)
                                )
                            )

    total_time_ms = (time.perf_counter() - suite_start) * 1000.0

    # Summary statistics by algorithm
    summary: Dict[str, Any] = {}
    for item in results:
        alg = item.algorithm
        if alg not in summary:
            summary[alg] = {
                "count": 0,
                "avg_runtime_ms": 0.0,
                "avg_makespan": 0.0,
                "optimal_count": 0,
                "total_states_explored": 0,
                "total_states_pruned": 0
            }
        summary[alg]["count"] += 1
        summary[alg]["avg_runtime_ms"] += item.runtime_ms
        summary[alg]["avg_makespan"] += item.makespan
        if item.optimality_status in ("OPTIMAL", "PROVEN_OPTIMAL"):
            summary[alg]["optimal_count"] += 1
        if item.states_explored:
            summary[alg]["total_states_explored"] += item.states_explored
        if item.states_pruned:
            summary[alg]["total_states_pruned"] += item.states_pruned

    for alg, s in summary.items():
        if s["count"] > 0:
            s["avg_runtime_ms"] = round(s["avg_runtime_ms"] / s["count"], 3)
            s["avg_makespan"] = round(s["avg_makespan"] / s["count"], 2)

    return BenchmarkResponse(
        results=results,
        total_runs=len(results),
        total_runtime_ms=round(total_time_ms, 3),
        summary=summary
    )
