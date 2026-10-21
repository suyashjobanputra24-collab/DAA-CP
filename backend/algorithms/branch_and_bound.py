"""
branch_and_bound.py - Branch and Bound Exact Scheduler for Workflow DAGs

Solves the identical parallel machine scheduling problem with precedence constraints
(P | prec | C_max) to mathematical optimality using rigorous Lower-Bound Pruning.

Academic Lower Bound Derivations:
1. Precedence / Critical-Path Lower Bound (LB_prec):
   For any task currently running with finish time F(u), or any unstarted task u:
   - If u is running: completion of any chain originating at u cannot finish earlier than:
       F(u) + bottom_level(u) - duration(u)
   - If u is unstarted: earliest start is bounded by current time and running predecessors:
       ES_est(u) = max({current_time} union {F(p) for p in preds(u) if p is running})
       Chain completion cannot finish earlier than: ES_est(u) + bottom_level(u)
   LB_prec = max over all remaining tasks of their projected chain completions.

2. Workload / Capacity Lower Bound (LB_workload):
   Let A(w) be the earliest availability timestamp of worker w (current_time if idle,
   or finish time if busy). Total work remaining = sum of unstarted durations + remaining busy time.
   LB_workload = (sum_{w=1}^m A(w) + sum_{u in unstarted} duration(u)) / m.

3. Pruning Criterion:
   LB(node) = max(LB_prec, LB_workload, max_{running} F(u))
   If LB(node) >= incumbent_makespan - 1e-9:
       PRUNE branch (guaranteed cannot strictly improve the incumbent).
"""

import time
import math
from typing import Dict, List, Optional, Set, Tuple, FrozenSet

from backend.graph.dag import DAG
from backend.models import (
    Workflow,
    ScheduleResult,
    ScheduledTask,
    WorkerUtilization
)
from backend.algorithms.critical_path import calculate_critical_path
from backend.algorithms.greedy_scheduler import compute_bottom_levels, schedule_greedy


def schedule_branch_and_bound(
    workflow: Workflow,
    max_states: int = 50000,
    time_limit_sec: float = 5.0,
    dag: Optional[DAG] = None
) -> ScheduleResult:
    """
    Finds the exact optimal makespan using Branch & Bound with mathematically valid lower bounds.

    Args:
        workflow: Workflow model containing tasks and worker count.
        max_states: Maximum number of recursive states to evaluate before terminating.
        time_limit_sec: Maximum wall-clock time in seconds.
        dag: Pre-constructed DAG (optional).

    Returns:
        ScheduleResult containing the proven optimal schedule, explored/pruned states count.
    """
    start_wall_time = time.perf_counter()

    if dag is None:
        dag = DAG(workflow.tasks)

    num_workers = workflow.number_of_workers
    tasks_count = len(workflow.tasks)
    all_nodes = set(dag.get_nodes())

    if tasks_count == 0:
        return ScheduleResult(
            workflow_id=workflow.workflow_id,
            algorithm="Branch and Bound",
            number_of_workers=num_workers,
            makespan=0.0,
            precedence_lower_bound=0.0,
            worker_utilization=0.0,
            worker_idle_time=0.0,
            per_worker_utilization={},
            tasks=[],
            execution_order=[],
            states_explored=0,
            states_pruned=0,
            optimality_proven=True,
            status="OPTIMAL",
            runtime_ms=0.0
        )

    # 1. Precedence analysis and bottom levels
    cp_res = calculate_critical_path(dag)
    precedence_lower_bound = cp_res.project_duration if cp_res.valid else 0.0
    critical_task_set = set(cp_res.critical_tasks) if cp_res.valid else set()
    bottom_levels = compute_bottom_levels(dag) if cp_res.valid else {t.task_id: t.duration for t in workflow.tasks}

    # Pre-index predecessors for O(1) checks
    predecessors: Dict[str, Set[str]] = {
        tid: set(dag.get_predecessors(tid)) for tid in all_nodes
    }

    # Total duration of all tasks
    total_work_all = sum(t.duration for t in workflow.tasks)
    workload_lower_bound = total_work_all / num_workers
    root_lower_bound = max(precedence_lower_bound, workload_lower_bound)

    # 2. Warm-start incumbent with Greedy (Upper Bound)
    greedy_sol = schedule_greedy(workflow, priority_policy="CRITICAL_PATH", dag=dag)
    best_makespan = greedy_sol.makespan if (greedy_sol.status in ("HEURISTIC", "PROVEN_OPTIMAL") and greedy_sol.tasks) else float("inf")
    best_schedule = list(greedy_sol.tasks) if best_makespan < float("inf") else []

    # If greedy already matches root lower bound, it is instantly proven optimal!
    if best_makespan < float("inf") and abs(best_makespan - root_lower_bound) < 1e-9:
        elapsed_ms = (time.perf_counter() - start_wall_time) * 1000.0
        return ScheduleResult(
            workflow_id=workflow.workflow_id,
            algorithm="Branch and Bound",
            number_of_workers=num_workers,
            makespan=round(best_makespan, 4),
            precedence_lower_bound=round(precedence_lower_bound, 4),
            worker_utilization=greedy_sol.worker_utilization,
            worker_idle_time=greedy_sol.worker_idle_time,
            per_worker_utilization=greedy_sol.per_worker_utilization,
            tasks=best_schedule,
            execution_order=greedy_sol.execution_order,
            states_explored=1,
            states_pruned=0,
            optimality_proven=True,
            status="OPTIMAL",
            runtime_ms=round(elapsed_ms, 3)
        )

    states_explored = 0
    states_pruned = 0
    limit_reached = False
    limit_reason = ""

    def calculate_lower_bound(
        current_time: float,
        running_tasks: Tuple[Tuple[float, int, str], ...],
        scheduled_ids: Set[str]
    ) -> float:
        """Computes combined max(LB_prec, LB_workload, max_running_finish)."""
        running_map: Dict[str, float] = {tid: f_t for f_t, _, tid in running_tasks}
        unstarted = all_nodes - scheduled_ids

        # Running max finish
        max_running = max(running_map.values(), default=current_time)

        # A. Precedence bound
        lb_prec = max_running
        # Running tasks chain projection
        for tid, f_t in running_map.items():
            chain_proj = f_t + bottom_levels.get(tid, 0.0) - dag.get_task(tid).duration
            if chain_proj > lb_prec:
                lb_prec = chain_proj

        # Unstarted tasks chain projection
        for tid in unstarted:
            preds = predecessors[tid]
            es_est = current_time
            for p in preds:
                if p in running_map and running_map[p] > es_est:
                    es_est = running_map[p]
            chain_proj = es_est + bottom_levels.get(tid, 0.0)
            if chain_proj > lb_prec:
                lb_prec = chain_proj

        # B. Workload bound
        # Worker availability times
        worker_avail: Dict[int, float] = {w: current_time for w in range(1, num_workers + 1)}
        for f_t, w, _ in running_tasks:
            worker_avail[w] = f_t

        unstarted_work = sum(dag.get_task(u).duration for u in unstarted)
        total_committed_work = sum(worker_avail.values()) + unstarted_work
        lb_workload = total_committed_work / num_workers

        return max(lb_prec, lb_workload, max_running)

    def search(
        current_time: float,
        running_tasks: Tuple[Tuple[float, int, str], ...],
        completed: FrozenSet[str],
        scheduled_tasks: Tuple[ScheduledTask, ...]
    ):
        nonlocal best_makespan, best_schedule, states_explored, states_pruned, limit_reached, limit_reason

        states_explored += 1

        # Check limits
        if states_explored >= max_states:
            limit_reached = True
            limit_reason = "SEARCH_LIMIT_REACHED"
            return
        if (time.perf_counter() - start_wall_time) >= time_limit_sec:
            limit_reached = True
            limit_reason = "TIME_LIMIT_REACHED"
            return

        scheduled_ids = {st.task_id for st in scheduled_tasks}

        # Base case: all tasks scheduled
        if len(scheduled_tasks) == tasks_count:
            final_time = max((t.finish_time for t in scheduled_tasks), default=current_time)
            if final_time < best_makespan:
                best_makespan = final_time
                best_schedule = list(scheduled_tasks)
            return

        # Lower bound check for pruning
        lb = calculate_lower_bound(current_time, running_tasks, scheduled_ids)
        if lb >= best_makespan - 1e-9:
            states_pruned += 1
            return

        # Busy and idle workers
        busy_workers = {w_idx for _, w_idx, _ in running_tasks}
        idle_workers = [w for w in range(1, num_workers + 1) if w not in busy_workers]

        # Identify READY tasks
        ready_tasks = [
            tid for tid in all_nodes
            if tid not in scheduled_ids and predecessors[tid].issubset(completed)
        ]

        # Sort ready tasks by descending bottom-level (most critical first for fast bounds)
        ready_tasks.sort(key=lambda tid: (-bottom_levels.get(tid, 0.0), tid))

        if idle_workers and ready_tasks:
            w_idx = min(idle_workers)
            wid = f"W{w_idx}"

            # Branch A: Assign one of the ready tasks
            for task_id in ready_tasks:
                task = dag.get_task(task_id)
                start_t = current_time
                finish_t = current_time + task.duration

                new_record = ScheduledTask(
                    task_id=task_id,
                    name=task.name,
                    worker_id=wid,
                    start_time=round(start_t, 4),
                    finish_time=round(finish_t, 4),
                    duration=task.duration,
                    execution_order=len(scheduled_tasks) + 1,
                    is_critical=(task_id in critical_task_set)
                )

                new_running = tuple(sorted(running_tasks + ((finish_t, w_idx, task_id),)))
                new_scheduled = scheduled_tasks + (new_record,)

                search(current_time, new_running, completed, new_scheduled)
                if limit_reached:
                    return

            # Branch B: Non-delay wait branch (if tasks are running)
            if running_tasks:
                next_event_time = running_tasks[0][0]
                newly_completed = set()
                remaining_running = []

                for f_t, w, tid in running_tasks:
                    if abs(f_t - next_event_time) < 1e-9:
                        newly_completed.add(tid)
                    else:
                        remaining_running.append((f_t, w, tid))

                new_completed = completed.union(newly_completed)
                search(
                    next_event_time,
                    tuple(remaining_running),
                    new_completed,
                    scheduled_tasks
                )

        elif running_tasks:
            next_event_time = running_tasks[0][0]
            newly_completed = set()
            remaining_running = []

            for f_t, w, tid in running_tasks:
                if abs(f_t - next_event_time) < 1e-9:
                    newly_completed.add(tid)
                else:
                    remaining_running.append((f_t, w, tid))

            new_completed = completed.union(newly_completed)
            search(
                next_event_time,
                tuple(remaining_running),
                new_completed,
                scheduled_tasks
            )

    # Launch recursive search from t=0
    search(0.0, (), frozenset(), ())

    elapsed_ms = (time.perf_counter() - start_wall_time) * 1000.0

    if best_schedule:
        makespan = max((t.finish_time for t in best_schedule), default=0.0)
        execution_order = [t.task_id for t in sorted(best_schedule, key=lambda x: (x.start_time, x.execution_order))]

        worker_busy_time = {f"W{i}": 0.0 for i in range(1, num_workers + 1)}
        for st in best_schedule:
            worker_busy_time[st.worker_id] += st.duration

        total_capacity = num_workers * makespan
        total_busy = sum(worker_busy_time.values())
        total_idle = max(0.0, total_capacity - total_busy)
        overall_utilization = (total_busy / total_capacity) if total_capacity > 0 else 0.0

        per_worker_util: Dict[str, WorkerUtilization] = {}
        for i in range(1, num_workers + 1):
            wid = f"W{i}"
            busy = worker_busy_time[wid]
            idle = max(0.0, makespan - busy)
            rate = (busy / makespan) if makespan > 0 else 0.0
            per_worker_util[wid] = WorkerUtilization(
                worker_id=wid,
                busy_time=round(busy, 4),
                idle_time=round(idle, 4),
                utilization_rate=round(rate, 4)
            )

        optimality_proven = not limit_reached
        status = "OPTIMAL" if optimality_proven else limit_reason

        return ScheduleResult(
            workflow_id=workflow.workflow_id,
            algorithm="Branch and Bound",
            number_of_workers=num_workers,
            makespan=round(makespan, 4),
            precedence_lower_bound=round(precedence_lower_bound, 4),
            worker_utilization=round(overall_utilization, 4),
            worker_idle_time=round(total_idle, 4),
            per_worker_utilization=per_worker_util,
            tasks=best_schedule,
            execution_order=execution_order,
            states_explored=states_explored,
            states_pruned=states_pruned,
            optimality_proven=optimality_proven,
            status=status,
            runtime_ms=round(elapsed_ms, 3)
        )
    else:
        return ScheduleResult(
            workflow_id=workflow.workflow_id,
            algorithm="Branch and Bound",
            number_of_workers=num_workers,
            makespan=0.0,
            precedence_lower_bound=round(precedence_lower_bound, 4),
            worker_utilization=0.0,
            worker_idle_time=0.0,
            per_worker_utilization={},
            tasks=[],
            execution_order=[],
            states_explored=states_explored,
            states_pruned=states_pruned,
            optimality_proven=False,
            status=limit_reason if limit_reason else "FAILED_NO_SOLUTION",
            runtime_ms=round(elapsed_ms, 3),
            error="No feasible schedule found within the designated search limit."
        )
