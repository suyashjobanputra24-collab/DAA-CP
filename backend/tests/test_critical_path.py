"""
test_critical_path.py - Pytest unit tests for Dynamic Programming Critical Path Analysis & Slack.
"""

from backend.models import Task
from backend.graph.dag import DAG
from backend.algorithms.critical_path import calculate_critical_path


def test_research_agent_critical_path():
    """
    Test 6: Critical path on Research Agent workflow.
    Tasks:
    - T1: Search Web (duration 5)
    - T2: Read Papers (duration 8)
    - T3: Analyze (duration 10, deps: [T1, T2])
    - T4: Generate Report (duration 7, deps: [T3])
    - T5: Review (duration 5, deps: [T4])

    Expected:
    - Project duration = 30.0
    - Critical tasks = ["T2", "T3", "T4", "T5"]
    - Critical path sequence = ["T2", "T3", "T4", "T5"]
    """
    tasks = [
        Task(task_id="T1", name="Search Web", duration=5.0, dependencies=[]),
        Task(task_id="T2", name="Read Papers", duration=8.0, dependencies=[]),
        Task(task_id="T3", name="Analyze", duration=10.0, dependencies=["T1", "T2"]),
        Task(task_id="T4", name="Generate Report", duration=7.0, dependencies=["T3"]),
        Task(task_id="T5", name="Review", duration=5.0, dependencies=["T4"]),
    ]
    dag = DAG(tasks)
    result = calculate_critical_path(dag)

    assert result.valid is True
    assert result.project_duration == 30.0

    # Critical tasks verification
    assert set(result.critical_tasks) == {"T2", "T3", "T4", "T5"}
    assert result.critical_path == ["T2", "T3", "T4", "T5"]


def test_slack_analysis():
    """
    Test 7: Verify slack calculations.
    - Critical tasks (T2, T3, T4, T5) must have slack == 0.
    - Search Web (T1) must have positive slack == 3.0.
    """
    tasks = [
        Task(task_id="T1", name="Search Web", duration=5.0, dependencies=[]),
        Task(task_id="T2", name="Read Papers", duration=8.0, dependencies=[]),
        Task(task_id="T3", name="Analyze", duration=10.0, dependencies=["T1", "T2"]),
        Task(task_id="T4", name="Generate Report", duration=7.0, dependencies=["T3"]),
        Task(task_id="T5", name="Review", duration=5.0, dependencies=["T4"]),
    ]
    dag = DAG(tasks)
    result = calculate_critical_path(dag)

    metrics = result.task_metrics

    # T1 Slack check
    assert metrics["T1"].slack == 3.0
    assert metrics["T1"].is_critical is False
    assert metrics["T1"].ES == 0.0
    assert metrics["T1"].EF == 5.0
    assert metrics["T1"].LS == 3.0
    assert metrics["T1"].LF == 8.0

    # Critical Tasks Slack check
    for crit_id in ["T2", "T3", "T4", "T5"]:
        assert metrics[crit_id].slack == 0.0
        assert metrics[crit_id].is_critical is True
