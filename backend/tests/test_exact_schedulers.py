"""
test_exact_schedulers.py - Tests for Exact Backtracking and Branch & Bound Schedulers

Validates:
- Exact Backtracking produces mathematically valid non-preemptive schedules
- Branch & Bound yields identical optimal makespans to exhaustive Backtracking
- Lower-bound pruning effectively reduces state evaluations
- Search limits are enforced and optimality is not falsely claimed when interrupted
- Suboptimal Greedy instance where BnB strictly beats Greedy
"""

import pytest
from backend.models import Task, Workflow
from backend.algorithms.greedy_scheduler import schedule_greedy
from backend.algorithms.exact_backtracking import schedule_backtrack
from backend.algorithms.branch_and_bound import schedule_branch_and_bound


def test_backtracking_and_bnb_match_on_small_instance():
    """Branch & Bound and Backtracking must agree on the optimal makespan."""
    tasks = [
        Task(task_id="T1", name="Task 1", duration=3.0, dependencies=[]),
        Task(task_id="T2", name="Task 2", duration=5.0, dependencies=[]),
        Task(task_id="T3", name="Task 3", duration=4.0, dependencies=["T1"]),
    ]
    wf = Workflow(workflow_id="small_01", name="Small Test", tasks=tasks, number_of_workers=2)

    res_bt = schedule_backtrack(wf)
    res_bnb = schedule_branch_and_bound(wf)

    assert res_bt.optimality_proven is True
    assert res_bnb.optimality_proven is True
    assert res_bt.makespan == res_bnb.makespan
    assert res_bt.makespan == 7.0  # T1(3)+T3(4)=7 on W1; T2(5) on W2


def test_branch_and_bound_pruning_effectiveness():
    """Branch & Bound should explore fewer or equal states compared to Backtracking."""
    tasks = [
        Task(task_id="A", name="Task A", duration=4.0, dependencies=[]),
        Task(task_id="B", name="Task B", duration=3.0, dependencies=[]),
        Task(task_id="C", name="Task C", duration=2.0, dependencies=[]),
        Task(task_id="D", name="Task D", duration=5.0, dependencies=["A"]),
        Task(task_id="E", name="Task E", duration=3.0, dependencies=["B", "C"]),
    ]
    wf = Workflow(workflow_id="prune_test", name="Prune Test", tasks=tasks, number_of_workers=2)

    res_bt = schedule_backtrack(wf)
    res_bnb = schedule_branch_and_bound(wf)

    assert res_bt.makespan == res_bnb.makespan
    assert res_bnb.states_explored <= res_bt.states_explored


def test_greedy_suboptimal_case_proven():
    """
    Classic Graham's List Scheduling anomaly:
    Greedy CP yields makespan 10.0, but Branch & Bound discovers optimal makespan 9.0!
    """
    tasks = [
        Task(task_id="A1", name="Fast Prep A", duration=3.0, dependencies=[]),
        Task(task_id="A2", name="Deep Task A", duration=3.0, dependencies=["A1"]),
        Task(task_id="B1", name="Quick Init B", duration=2.0, dependencies=[]),
        Task(task_id="B2", name="Heavy Compute B", duration=4.0, dependencies=["B1"]),
        Task(task_id="C1", name="Quick Init C", duration=2.0, dependencies=[]),
        Task(task_id="C2", name="Heavy Compute C", duration=4.0, dependencies=["C1"]),
    ]
    wf = Workflow(workflow_id="anomaly_check", name="Anomaly Check", tasks=tasks, number_of_workers=2)

    res_greedy = schedule_greedy(wf, priority_policy="CRITICAL_PATH")
    res_bnb = schedule_branch_and_bound(wf)

    assert res_greedy.makespan == 10.0
    assert res_bnb.makespan == 9.0
    assert res_bnb.optimality_proven is True
    assert res_bnb.makespan < res_greedy.makespan


def test_search_limit_and_unproven_optimality():
    """When state limit is exceeded, optimality must NOT be claimed."""
    tasks = [
        Task(task_id=f"T{i}", name=f"Task {i}", duration=2.0 + i, dependencies=[])
        for i in range(1, 9)
    ]
    wf = Workflow(workflow_id="limit_wf", name="Limit Test", tasks=tasks, number_of_workers=2)

    # Artificially tiny limit of 5 states
    res_bt = schedule_backtrack(wf, max_states=5)
    assert res_bt.optimality_proven is False
    assert res_bt.status == "SEARCH_LIMIT_REACHED"
