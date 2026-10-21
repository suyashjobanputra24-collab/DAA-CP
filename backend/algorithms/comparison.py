"""
comparison.py - Multi-Algorithm Scheduling Comparison Service

Runs Greedy (Critical Path & LPT), Exact Backtracking, and Branch & Bound
on the same workflow and worker configuration.
Computes:
- Precedence lower bound
- Workload (capacity) lower bound
- Theoretical lower bound = max(precedence, workload)
- Comparative makespan and optimality gaps
- States explored and pruned
- Academic DAA analysis of heuristic vs. exact guarantees
"""

from typing import Dict, List, Optional
from backend.graph.dag import DAG
from backend.models import (
    Workflow,
    ComparisonResult,
    ScheduleResult
)
from backend.algorithms.critical_path import calculate_critical_path
from backend.algorithms.greedy_scheduler import schedule_greedy
from backend.algorithms.exact_backtracking import schedule_backtrack
from backend.algorithms.branch_and_bound import schedule_branch_and_bound


def compare_algorithms(
    workflow: Workflow,
    max_states: int = 20000,
    time_limit_sec: float = 3.0
) -> ComparisonResult:
    """
    Executes multiple scheduling algorithms on identical workflow input and compares performance.

    Args:
        workflow: Workflow model containing tasks and worker capacity.
        max_states: Max states limit for exact search algorithms.
        time_limit_sec: Max timeout in seconds for exact search algorithms.

    Returns:
        ComparisonResult with side-by-side metrics and academic summary.
    """
    dag = DAG(workflow.tasks)
    num_workers = workflow.number_of_workers

    # 1. Theoretical Lower Bounds
    cp_res = calculate_critical_path(dag)
    precedence_lb = cp_res.project_duration if cp_res.valid else 0.0
    total_duration = sum(t.duration for t in workflow.tasks)
    workload_lb = (total_duration / num_workers) if num_workers > 0 else 0.0
    theoretical_lb = max(precedence_lb, workload_lb)

    # 2. Run Greedy Heuristics
    greedy_cp = schedule_greedy(workflow, priority_policy="CRITICAL_PATH", dag=dag)
    greedy_lpt = schedule_greedy(workflow, priority_policy="LPT", dag=dag)

    # 3. Run Exact Solvers (adaptive limit based on task count)
    # If task count is large (> 18), backoff exact state limit to prevent slow responses
    effective_max_states = max_states
    effective_timeout = time_limit_sec
    if len(workflow.tasks) > 16:
        effective_max_states = min(max_states, 5000)
        effective_timeout = min(time_limit_sec, 2.0)

    bnb_res = schedule_branch_and_bound(
        workflow,
        max_states=effective_max_states,
        time_limit_sec=effective_timeout,
        dag=dag
    )

    backtrack_res = schedule_backtrack(
        workflow,
        max_states=effective_max_states,
        time_limit_sec=effective_timeout,
        dag=dag
    )

    algorithms_dict: Dict[str, ScheduleResult] = {
        "Greedy (Critical Path)": greedy_cp,
        "Greedy (LPT)": greedy_lpt,
        "Exact Backtracking": backtrack_res,
        "Branch and Bound": bnb_res
    }

    # Determine best makespan found
    valid_makespans = [
        res.makespan for res in algorithms_dict.values()
        if res.makespan > 0 and not res.error
    ]
    best_makespan = min(valid_makespans) if valid_makespans else 0.0

    # Best performing algorithm
    best_alg_name = "Branch and Bound"
    for name, res in algorithms_dict.items():
        if abs(res.makespan - best_makespan) < 1e-9 and res.optimality_proven:
            best_alg_name = name
            break
        elif abs(res.makespan - best_makespan) < 1e-9:
            best_alg_name = name

    # Generate academic analysis
    analysis_lines = []
    analysis_lines.append(
        f"Theoretical Lower Bound: {theoretical_lb:.2f} time units "
        f"(Precedence LB = {precedence_lb:.2f}, Workload LB = {workload_lb:.2f})."
    )

    if bnb_res.optimality_proven:
        analysis_lines.append(
            f"The global minimum makespan is {bnb_res.makespan:.2f}, proven by Branch and Bound."
        )
        if greedy_cp.makespan > bnb_res.makespan:
            gap = greedy_cp.makespan - bnb_res.makespan
            gap_pct = (gap / bnb_res.makespan) * 100.0
            analysis_lines.append(
                f"Greedy List Scheduling (CP) produced a suboptimal schedule of {greedy_cp.makespan:.2f} "
                f"(Optimality Gap: +{gap:.2f} units, {gap_pct:.1f}%). "
                f"This demonstrates Graham's List Scheduling anomaly where greedy local choices do not guarantee global optimality."
            )
        else:
            analysis_lines.append(
                "Greedy List Scheduling (CP) achieved the optimal makespan on this instance."
            )
    else:
        analysis_lines.append(
            f"Best feasible makespan discovered is {best_makespan:.2f} by {best_alg_name}."
        )

    if bnb_res.states_pruned is not None and bnb_res.states_pruned > 0:
        analysis_lines.append(
            f"Branch & Bound successfully pruned {bnb_res.states_pruned} subtrees using precedence and workload bounds, "
            f"evaluating {bnb_res.states_explored} states compared to {backtrack_res.states_explored} in exhaustive Backtracking."
        )

    analysis_str = " ".join(analysis_lines)

    return ComparisonResult(
        workflow_id=workflow.workflow_id,
        number_of_workers=num_workers,
        precedence_lower_bound=round(precedence_lb, 4),
        workload_lower_bound=round(workload_lb, 4),
        theoretical_lower_bound=round(theoretical_lb, 4),
        algorithms=algorithms_dict,
        best_makespan=round(best_makespan, 4),
        best_algorithm=best_alg_name,
        analysis=analysis_str
    )
