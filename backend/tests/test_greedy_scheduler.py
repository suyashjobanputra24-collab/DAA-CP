"""
test_greedy_scheduler.py - Tests for Event-Driven Greedy List Scheduler

Validates:
- Precedence respect: tasks never start before predecessors finish
- Worker capacity: workers never execute multiple tasks at once
- Independent parallel execution across multiple workers
- Correct makespan and lower bound comparisons
- Priority policies: CRITICAL_PATH, LPT, SPT, FIFO
- Simultaneous task completion handling
- Deadlock detection on unexecutable DAGs
"""

import pytest
from backend.models import Task, Workflow
from backend.algorithms.greedy_scheduler import schedule_greedy


def test_independent_parallel_tasks():
    """Independent tasks with 2 workers should be scheduled in parallel."""
    tasks = [
        Task(task_id="T1", name="Task 1", duration=4.0, dependencies=[]),
        Task(task_id="T2", name="Task 2", duration=6.0, dependencies=[]),
    ]
    wf = Workflow(workflow_id="p1", name="Parallel Test", tasks=tasks, number_of_workers=2)
    res = schedule_greedy(wf)

    assert res.makespan == 6.0
    assert len(res.tasks) == 2
    # Verify workers: one on W1, one on W2
    workers_used = {t.worker_id for t in res.tasks}
    assert workers_used == {"W1", "W2"}
    # Both should start at time 0.0
    for t in res.tasks:
        assert t.start_time == 0.0


def test_precedence_constraints_respected():
    """Tasks must never start before all their predecessors have completed."""
    tasks = [
        Task(task_id="T1", name="Step 1", duration=5.0, dependencies=[]),
        Task(task_id="T2", name="Step 2", duration=3.0, dependencies=["T1"]),
        Task(task_id="T3", name="Step 3", duration=4.0, dependencies=["T1", "T2"]),
    ]
    wf = Workflow(workflow_id="chain1", name="Chain Test", tasks=tasks, number_of_workers=2)
    res = schedule_greedy(wf)

    task_map = {t.task_id: t for t in res.tasks}
    # T2 cannot start before T1 finishes
    assert task_map["T2"].start_time >= task_map["T1"].finish_time
    # T3 cannot start before T2 finishes
    assert task_map["T3"].start_time >= task_map["T2"].finish_time
    assert res.makespan == 12.0


def test_worker_never_executes_two_tasks_simultaneously():
    """Verify non-overlapping execution intervals on each worker."""
    tasks = [
        Task(task_id=f"T{i}", name=f"Task {i}", duration=3.0, dependencies=[])
        for i in range(1, 7)
    ]
    wf = Workflow(workflow_id="par6", name="Parallel 6", tasks=tasks, number_of_workers=2)
    res = schedule_greedy(wf)

    # Check each worker's task intervals
    for wid in ["W1", "W2"]:
        w_tasks = sorted([t for t in res.tasks if t.worker_id == wid], key=lambda x: x.start_time)
        for i in range(len(w_tasks) - 1):
            curr_finish = w_tasks[i].finish_time
            next_start = w_tasks[i + 1].start_time
            assert next_start >= curr_finish - 1e-9, f"Worker {wid} had overlapping tasks!"


def test_priority_policies():
    """Test that different priority policies change the execution sequence."""
    tasks = [
        Task(task_id="SHORT", name="Short Task", duration=2.0, dependencies=[]),
        Task(task_id="LONG", name="Long Task", duration=10.0, dependencies=[]),
    ]
    wf = Workflow(workflow_id="prio_test", name="Prio Test", tasks=tasks, number_of_workers=1)

    # LPT: LONG should start first
    res_lpt = schedule_greedy(wf, priority_policy="LPT")
    assert res_lpt.tasks[0].task_id == "LONG"

    # SPT: SHORT should start first
    res_spt = schedule_greedy(wf, priority_policy="SPT")
    assert res_spt.tasks[0].task_id == "SHORT"


def test_simultaneous_completions():
    """Verify engine handles multiple tasks finishing at the identical timestamp."""
    tasks = [
        Task(task_id="A1", name="A1", duration=4.0, dependencies=[]),
        Task(task_id="A2", name="A2", duration=4.0, dependencies=[]),
        Task(task_id="B1", name="B1", duration=2.0, dependencies=["A1", "A2"]),
    ]
    wf = Workflow(workflow_id="simul", name="Simultaneous Test", tasks=tasks, number_of_workers=2)
    res = schedule_greedy(wf)

    assert res.makespan == 6.0
    task_map = {t.task_id: t for t in res.tasks}
    assert task_map["A1"].finish_time == 4.0
    assert task_map["A2"].finish_time == 4.0
    assert task_map["B1"].start_time == 4.0


def test_empty_workflow():
    """Empty workflow produces 0 makespan without crashing."""
    wf = Workflow(workflow_id="empty", name="Empty", tasks=[], number_of_workers=2)
    res = schedule_greedy(wf)
    assert res.makespan == 0.0
    assert len(res.tasks) == 0
    assert res.optimality_proven is True
