"""
test_topological.py - Pytest unit tests for Kahn's Topological Sort algorithm.
"""

from backend.models import Task
from backend.graph.dag import DAG
from backend.algorithms.topological_sort import kahn_topological_sort


def test_simple_chain():
    """
    Test 1: Simple linear chain A -> B -> C
    Expected: A before B, B before C.
    """
    tasks = [
        Task(task_id="A", name="Task A", duration=1.0, dependencies=[]),
        Task(task_id="B", name="Task B", duration=2.0, dependencies=["A"]),
        Task(task_id="C", name="Task C", duration=3.0, dependencies=["B"]),
    ]
    dag = DAG(tasks)
    result = kahn_topological_sort(dag)

    assert result.valid is True
    order = result.topological_order
    assert len(order) == 3
    assert order.index("A") < order.index("B")
    assert order.index("B") < order.index("C")


def test_parallel_tasks():
    """
    Test 2: Parallel tasks A and B precede C (A -> C, B -> C).
    Expected: Both A and B occur before C in the topological order.
    """
    tasks = [
        Task(task_id="A", name="Task A", duration=4.0, dependencies=[]),
        Task(task_id="B", name="Task B", duration=5.0, dependencies=[]),
        Task(task_id="C", name="Task C", duration=2.0, dependencies=["A", "B"]),
    ]
    dag = DAG(tasks)
    result = kahn_topological_sort(dag)

    assert result.valid is True
    order = result.topological_order
    assert len(order) == 3
    assert order.index("A") < order.index("C")
    assert order.index("B") < order.index("C")


def test_diamond_dag():
    """
    Test diamond graph: A -> B, A -> C, B -> D, C -> D
    """
    tasks = [
        Task(task_id="A", name="Task A", duration=1.0, dependencies=[]),
        Task(task_id="B", name="Task B", duration=2.0, dependencies=["A"]),
        Task(task_id="C", name="Task C", duration=3.0, dependencies=["A"]),
        Task(task_id="D", name="Task D", duration=4.0, dependencies=["B", "C"]),
    ]
    dag = DAG(tasks)
    result = kahn_topological_sort(dag)

    assert result.valid is True
    order = result.topological_order
    assert order[0] == "A"
    assert order[-1] == "D"
    assert order.index("A") < order.index("B")
    assert order.index("A") < order.index("C")
    assert order.index("B") < order.index("D")
    assert order.index("C") < order.index("D")
