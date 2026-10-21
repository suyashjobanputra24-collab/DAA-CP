"""
greedy_scheduler.py - Event-Driven Greedy List Scheduler for Workflow DAGs

Implements non-preemptive list scheduling on identical parallel workers (P | prec | C_max).
Features:
- Event-driven clock advancement (skips idle gaps directly to task completions)
- Handles simultaneous task completions at the same timestamp
- Configurable priority queues implemented via Python's heapq:
    1. CRITICAL_PATH: Bottom-level (longest path to sink) descending, then slack ascending
    2. LPT: Longest Processing Time first
    3. SPT: Shortest Processing Time first
    4. FIFO: Topological order
    5. TASK_PRIORITY: Custom task.priority field descending
- Deterministic tie-breaking by task_id ascending
- Full worker utilization, idle time, and Gantt-ready scheduling metadata
- Deadlock detection for unexecutable graphs
"""

import heapq
import time
from typing import Dict, List, Optional, Set, Tuple

from backend.graph.dag import DAG
from backend.models import (
    Workflow,
    ScheduleResult,
    ScheduledTask,
    WorkerUtilization
)
from backend.algorithms.critical_path import calculate_critical_path


def compute_bottom_levels(dag: DAG) -> Dict[str, float]:
    """
    Computes bottom-level b(u) for each task u in the DAG:
    b(u) = duration(u) + max({b(v) for v in successors(u)} union {0})
    Computed via reverse topological order in O(V + E).
    """
    cp_res = calculate_critical_path(dag)
    topo_order = cp_res.topological_order
    bottom_level: Dict[str, float] = {}

    for u in reversed(topo_order):
        task = dag.get_task(u)
        succs = dag.get_successors(u)
        if not succs:
            bottom_level[u] = task.duration
        else:
            bottom_level[u] = task.duration + max(bottom_level[s] for s in succs)

    return bottom_level


def schedule_greedy(
    workflow: Workflow,
    priority_policy: str = "CRITICAL_PATH",
    dag: Optional[DAG] = None
) -> ScheduleResult:
    """
    Executes event-driven Greedy List Scheduling on the provided workflow.

    Args:
        workflow: Workflow model containing tasks and worker count.
        priority_policy: 'CRITICAL_PATH', 'LPT', 'SPT', 'FIFO', or 'TASK_PRIORITY'.
        dag: Pre-constructed DAG (optional; constructed if None).

    Returns:
        ScheduleResult containing scheduled tasks, makespan, and utilization metrics.
    """
    start_wall_time = time.perf_counter()

    if dag is None:
        dag = DAG(workflow.tasks)

    num_workers = workflow.number_of_workers
    tasks_count = len(workflow.tasks)

    if tasks_count == 0:
        return ScheduleResult(
            workflow_id=workflow.workflow_id,
            algorithm="Greedy List Scheduler",
            priority_policy=priority_policy,
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

    # 1. Critical path and bottom-levels for priority calculation & lower bound
    cp_res = calculate_critical_path(dag)
    precedence_lower_bound = cp_res.project_duration if cp_res.valid else 0.0
    critical_task_set = set(cp_res.critical_tasks) if cp_res.valid else set()
    bottom_levels = compute_bottom_levels(dag) if cp_res.valid else {t.task_id: t.duration for t in workflow.tasks}

    # Map topological index for FIFO
    topo_idx = {tid: i for i, tid in enumerate(cp_res.topological_order)} if cp_res.valid else {}

    # 2. Worker representation: worker IDs "W1", "W2", ..., "Wn"
    # Idle workers stored in a min-heap of integer indices [1..num_workers] for deterministic assignment
    idle_workers: List[int] = list(range(1, num_workers + 1))
    heapq.heapify(idle_workers)

    # 3. Track dependency completion counts
    remaining_predecessors: Dict[str, int] = {
        tid: len(dag.get_predecessors(tid)) for tid in dag.get_nodes()
    }

    # 4. Priority Queue for Ready Tasks
    # Heap stores: (priority_tuple, task_id)
    policy = priority_policy.upper()

    def get_priority_key(task_id: str) -> Tuple:
        task = dag.get_task(task_id)
        if policy == "CRITICAL_PATH":
            # Priority: Largest bottom-level first, then smallest slack, then task_id
            slack = cp_res.task_metrics[task_id].slack if cp_res.valid and task_id in cp_res.task_metrics else 0.0
            return (-bottom_levels.get(task_id, 0.0), slack, task_id)
        elif policy == "LPT":
            # Longest Processing Time first
            return (-task.duration, task_id)
        elif policy == "SPT":
            # Shortest Processing Time first
            return (task.duration, task_id)
        elif policy == "TASK_PRIORITY":
            p = task.priority if task.priority is not None else 0
            return (-p, task_id)
        elif policy == "FIFO":
            return (topo_idx.get(task_id, 0), task_id)
        else:
            # Default to Critical Path
            slack = cp_res.task_metrics[task_id].slack if cp_res.valid and task_id in cp_res.task_metrics else 0.0
            return (-bottom_levels.get(task_id, 0.0), slack, task_id)

    ready_queue: List[Tuple[Tuple, str]] = []

    # Enqueue initial source tasks (indegree == 0)
    for tid, rem_preds in remaining_predecessors.items():
        if rem_preds == 0:
            heapq.heappush(ready_queue, (get_priority_key(tid), tid))

    # 5. Event Queue for Running Tasks
    # Event tuple: (finish_time, worker_idx, task_id)
    event_queue: List[Tuple[float, int, str]] = []

    current_time: float = 0.0
    scheduled_tasks: List[ScheduledTask] = []
    execution_order: List[str] = []
    worker_busy_time: Dict[str, float] = {f"W{i}": 0.0 for i in range(1, num_workers + 1)}

    sequence_counter = 0

    # 6. Event-Driven Simulation Loop
    while ready_queue or event_queue:
        # A. Assign ready tasks to idle workers while both exist
        while idle_workers and ready_queue:
            _, task_id = heapq.heappop(ready_queue)
            worker_idx = heapq.heappop(idle_workers)
            worker_id = f"W{worker_idx}"

            task = dag.get_task(task_id)
            start_time = current_time
            finish_time = current_time + task.duration

            sequence_counter += 1
            is_crit = task_id in critical_task_set

            scheduled_tasks.append(
                ScheduledTask(
                    task_id=task_id,
                    name=task.name,
                    worker_id=worker_id,
                    start_time=round(start_time, 4),
                    finish_time=round(finish_time, 4),
                    duration=task.duration,
                    execution_order=sequence_counter,
                    is_critical=is_crit
                )
            )
            execution_order.append(task_id)
            worker_busy_time[worker_id] += task.duration

            # Register completion event
            heapq.heappush(event_queue, (finish_time, worker_idx, task_id))

        # B. Advance simulation clock to next completion event
        if event_queue:
            # Advance clock directly to the next event time
            next_time = event_queue[0][0]
            current_time = next_time

            # Handle ALL events completing at current_time (simultaneous completions)
            while event_queue and abs(event_queue[0][0] - current_time) < 1e-9:
                f_time, w_idx, comp_task_id = heapq.heappop(event_queue)
                # Worker becomes idle
                heapq.heappush(idle_workers, w_idx)

                # Update successors of completed task
                for succ in dag.get_successors(comp_task_id):
                    remaining_predecessors[succ] -= 1
                    if remaining_predecessors[succ] == 0:
                        heapq.heappush(ready_queue, (get_priority_key(succ), succ))

    # 7. Check for Deadlock / Unscheduled Tasks
    if len(scheduled_tasks) < tasks_count:
        unscheduled = set(dag.get_nodes()) - set(execution_order)
        elapsed_ms = (time.perf_counter() - start_wall_time) * 1000.0
        return ScheduleResult(
            workflow_id=workflow.workflow_id,
            algorithm="Greedy List Scheduler",
            priority_policy=policy,
            number_of_workers=num_workers,
            makespan=0.0,
            precedence_lower_bound=precedence_lower_bound,
            worker_utilization=0.0,
            worker_idle_time=0.0,
            per_worker_utilization={},
            tasks=[],
            execution_order=[],
            states_explored=len(scheduled_tasks),
            optimality_proven=False,
            status="DEADLOCK_DETECTED",
            runtime_ms=round(elapsed_ms, 3),
            error=f"Deadlock detected: could not schedule remaining tasks {sorted(list(unscheduled))} due to unmet dependencies or cycle."
        )

    # 8. Compute Makespan and Worker Utilization Metrics
    makespan = max((t.finish_time for t in scheduled_tasks), default=0.0)
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

    elapsed_ms = (time.perf_counter() - start_wall_time) * 1000.0

    # Note: Greedy schedule achieves the precedence lower bound iff makespan == precedence_lower_bound
    # In general, Greedy is a heuristic (optimality is not guaranteed)
    is_provably_optimal = abs(makespan - precedence_lower_bound) < 1e-9

    return ScheduleResult(
        workflow_id=workflow.workflow_id,
        algorithm="Greedy List Scheduler",
        priority_policy=policy,
        number_of_workers=num_workers,
        makespan=round(makespan, 4),
        precedence_lower_bound=round(precedence_lower_bound, 4),
        worker_utilization=round(overall_utilization, 4),
        worker_idle_time=round(total_idle, 4),
        per_worker_utilization=per_worker_util,
        tasks=scheduled_tasks,
        execution_order=execution_order,
        states_explored=len(scheduled_tasks),
        optimality_proven=is_provably_optimal,
        status="PROVEN_OPTIMAL" if is_provably_optimal else "HEURISTIC",
        runtime_ms=round(elapsed_ms, 3)
    )
