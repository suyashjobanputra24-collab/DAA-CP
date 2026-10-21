"""
test_validation.py - Pytest unit tests for Workflow validation rules.
"""

from backend.models import Workflow, Task
from backend.graph.validator import validate_workflow


def test_missing_dependency():
    """
    Test 4: Task A depends on non-existent task X.
    Expected: Validation fails with error mentioning missing dependency X.
    """
    wf = Workflow(
        workflow_id="wf_missing_dep",
        name="Missing Dependency Test",
        number_of_workers=2,
        tasks=[
            Task(task_id="A", name="Task A", duration=5.0, dependencies=["X"])
        ]
    )
    result = validate_workflow(wf)
    assert result.valid is False
    assert any("missing task 'X'" in err for err in result.errors)


def test_duplicate_task_ids():
    """
    Test 5: Two tasks have the exact same task_id ("T1").
    Expected: Validation fails with duplicate ID error.
    """
    wf = Workflow(
        workflow_id="wf_dup",
        name="Duplicate ID Test",
        number_of_workers=2,
        tasks=[
            Task(task_id="T1", name="Task T1 First", duration=3.0, dependencies=[]),
            Task(task_id="T1", name="Task T1 Second", duration=4.0, dependencies=[])
        ]
    )
    result = validate_workflow(wf)
    assert result.valid is False
    assert any("Duplicate task IDs" in err for err in result.errors)


def test_self_dependency():
    """
    Test self-dependency: Task T1 depends on T1.
    Expected: Validation fails with self-dependency error.
    """
    wf = Workflow(
        workflow_id="wf_self_dep",
        name="Self Dependency Test",
        number_of_workers=2,
        tasks=[
            Task(task_id="T1", name="Task T1", duration=2.0, dependencies=["T1"])
        ]
    )
    result = validate_workflow(wf)
    assert result.valid is False
    assert any("cannot depend on itself" in err for err in result.errors)
