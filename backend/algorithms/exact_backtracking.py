"""
exact_backtracking.py - Exact Backtracking Scheduler for Workflow DAGs

Solves the identical parallel machine scheduling problem with precedence constraints
(P | prec | C_max) to mathematical optimality for small-to-medium workflows.

Theoretical Foundation:
- Explores the space of active and semi-active schedules.
- By allowing ready task assignments to available workers as well as non-delay wait branches,
  the search space is guaranteed to contain the global minimum makespan C_max.
- Symmetric worker permutations are eliminated by assigning to the canonical lowest-indexed idle worker.
- Search limits (max_states, time_limit_sec) guard against combinatorial explosion.
- Optimality is ONLY claimed if the search completes exhaustively without hitting limits.
"""

import time
from typing import Dict, List, Optional, Set, Tuple, FrozenSet

from backend.graph.dag import DAG
from backend.models import (
    Workflow,
    ScheduleResult,
    ScheduledTask,
    WorkerUtilization
)
from backend.algorithms.critical_path import calculate_critical_path


def schedule_backtrack(
    workflow: Workflow,
    max_states: int = 50000,
    time_limit_sec: float = 5.0,
    dag: Optional[DAG] = None
) -> ScheduleResult:
    """
    Finds the exact optimal makespan using exhaustive state-space backtracking.

    Args:
        workflow: Workflow model containing tasks and worker count.
        max_states: Maximum number of recursive state evaluations before stopping.
        time_limit_sec: Maximum wall-clock time in seconds before stopping.
        dag: Pre-constructed DAG (optional).

    Returns:
        ScheduleResult with the best feasible schedule found and proof status.
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
            algorithm="Exact Backtracking",
            number_of_workers=num_workers,
            makespan=0.0,
            precedence_lower_bound=0.0,
            worker_utilization=0.0,
            worker_idle_time=0.0,
            per_worker_utilization={},
            tasks=[],
            execution_order=[],
            states_explored=0,
            optimality_proven=True,
            status="OPTIMAL",
            runtime_ms=0.0
        )

    # 1. Critical Path and Precedence Lower Bound
    cp_res = calculate_critical_path(dag)
    precedence_lower_bound = cp_res.project_duration if cp_res.valid else 0.0
    critical_task_set = set(cp_res.critical_tasks) if cp_res.valid else set()

    # Pre-index predecessors for O(1) checks
    predecessors: Dict[str, Set[str]] = {
        tid: set(dag.get_predecessors(tid)) for tid in all_nodes
    }

    # Tracking search progress
    best_makespan = float("inf")
    best_schedule: List[ScheduledTask] = []
    states_explored = 0
    limit_reached = False
    limit_reason = ""

    def search(
        current_time: float,
        running_tasks: Tuple[Tuple[float, int, str], ...],
        completed: FrozenSet[str],
        scheduled_tasks: Tuple[ScheduledTask, ...]
    ):
        nonlocal best_makespan, best_schedule, states_explored, limit_reached, limit_reason

        states_explored += 1

        # Check search limits
        if states_explored >= max_states:
            limit_reached = True
            limit_reason = "SEARCH_LIMIT_REACHED"
            return
        if (time.perf_counter() - start_wall_time) >= time_limit_sec:
            limit_reached = True
            limit_reason = "TIME_LIMIT_REACHED"
            return

        # Base case: all tasks scheduled and running tasks completed
        if len(completed) == tasks_count:
            if current_time < best_makespan:
                best_makespan = current_time
                best_schedule = list(scheduled_tasks)
            return

        # If all tasks are already scheduled but some are still running, fast-forward to the end
        if len(scheduled_tasks) == tasks_count:
            final_time = max((t.finish_time for t in scheduled_tasks), default=current_time)
            if final_time < best_makespan:
                best_makespan = final_time
                best_schedule = list(scheduled_tasks)
            return

        # Identify busy workers and idle workers
        busy_workers = {w_idx for _, w_idx, _ in running_tasks}
        idle_workers = [w for w in range(1, num_workers + 1) if w not in busy_workers]

        # Scheduled task IDs so far
        scheduled_ids = {st.task_id for st in scheduled_tasks}

        # Identify READY tasks (all predecessors completed, not yet scheduled)
        ready_tasks = [
            tid for tid in all_nodes
            if tid not in scheduled_ids and predecessors[tid].issubset(completed)
        ]
        # Sort ready tasks deterministically by ID
        ready_tasks.sort()

        # Branching Strategy:
        if idle_workers and ready_tasks:
            # Symmetrical machine reduction: use lowest idle worker
            w_idx = min(idle_workers)
            wid = f"W{w_idx}"

            # Branch A: Assign one of the ready tasks to w_idx at current_time
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

            # Branch B: Non-delay wait branch (if there are running tasks)
            # Intentionally leave w_idx idle until the earliest running task completes
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
            # No idle workers or no ready tasks: must advance time to next completion
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
            algorithm="Exact Backtracking",
            number_of_workers=num_workers,
            makespan=round(makespan, 4),
            precedence_lower_bound=round(precedence_lower_bound, 4),
            worker_utilization=round(overall_utilization, 4),
            worker_idle_time=round(total_idle, 4),
            per_worker_utilization=per_worker_util,
            tasks=best_schedule,
            execution_order=execution_order,
            states_explored=states_explored,
            optimality_proven=optimality_proven,
            status=status,
            runtime_ms=round(elapsed_ms, 3)
        )
    else:
        # Search failed to find any feasible schedule before limit
        return ScheduleResult(
            workflow_id=workflow.workflow_id,
            algorithm="Exact Backtracking",
            number_of_workers=num_workers,
            makespan=0.0,
            precedence_lower_bound=round(precedence_lower_bound, 4),
            worker_utilization=0.0,
            worker_idle_time=0.0,
            per_worker_utilization={},
            tasks=[],
            execution_order=[],
            states_explored=states_explored,
            optimality_proven=False,
            status=limit_reason if limit_reason else "FAILED_NO_SOLUTION",
            runtime_ms=round(elapsed_ms, 3),
            error="No feasible schedule found within the designated search limit."
        )
