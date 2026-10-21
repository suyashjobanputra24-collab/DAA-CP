"""
test_cycle_detection.py - Pytest unit tests for DFS 3-state cycle detection and cycle handling.
"""

from backend.models import Task
from backend.graph.dag import DAG
from backend.algorithms.cycle_detection import detect_cycle_dfs
from backend.algorithms.topological_sort import kahn_topological_sort


def test_cycle_detection_3_node_cycle():
    """
    Test 3: Cyclic graph A -> B -> C -> A
    Expected:
    1. DFS cycle detector detects cycle and returns (True, cycle_path).
    2. Kahn's topological sort detects cycle and returns valid=False.
    """
    tasks = [
        Task(task_id="A", name="Task A", duration=1.0, dependencies=["C"]),
        Task(task_id="B", name="Task B", duration=2.0, dependencies=["A"]),
        Task(task_id="C", name="Task C", duration=3.0, dependencies=["B"]),
    ]
    dag = DAG(tasks)

    # 1. Test DFS
    has_cycle, cycle_path = detect_cycle_dfs(dag)
    assert has_cycle is True
    assert cycle_path is not None
    assert len(cycle_path) >= 3

    # 2. Test Kahn's algo handling
    topo_res = kahn_topological_sort(dag)
    assert topo_res.valid is False
    assert "cycle" in topo_res.error.lower()


def test_no_cycle_in_acyclic_graph():
    """
    Test acyclic graph (no cycle).
    """
    tasks = [
        Task(task_id="A", name="Task A", duration=1.0, dependencies=[]),
        Task(task_id="B", name="Task B", duration=2.0, dependencies=["A"]),
        Task(task_id="C", name="Task C", duration=3.0, dependencies=["A", "B"]),
    ]
    dag = DAG(tasks)
    has_cycle, cycle_path = detect_cycle_dfs(dag)

    assert has_cycle is False
    assert cycle_path is None
