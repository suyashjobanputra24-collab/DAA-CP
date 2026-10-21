"""
test_scheduling_api.py - Integration Tests for FastAPI Scheduling Endpoints

Validates:
- /schedule/greedy (valid & invalid inputs)
- /schedule/backtrack
- /schedule/branch-and-bound
- /schedule/compare
- /workflow/random
- /benchmark/run
- /sample-workflows and /sample-workflows/{filename}
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

SAMPLE_PAYLOAD = {
    "workflow": {
        "workflow_id": "api_test_wf",
        "name": "API Test Workflow",
        "number_of_workers": 2,
        "tasks": [
            {"task_id": "T1", "name": "Task 1", "duration": 5.0, "dependencies": []},
            {"task_id": "T2", "name": "Task 2", "duration": 3.0, "dependencies": ["T1"]}
        ]
    },
    "priority_policy": "CRITICAL_PATH"
}

CYCLIC_PAYLOAD = {
    "workflow": {
        "workflow_id": "cyclic_test_wf",
        "name": "Cyclic Workflow",
        "number_of_workers": 2,
        "tasks": [
            {"task_id": "A", "name": "Task A", "duration": 2.0, "dependencies": ["B"]},
            {"task_id": "B", "name": "Task B", "duration": 2.0, "dependencies": ["A"]}
        ]
    }
}


def test_api_schedule_greedy_success():
    res = client.post("/schedule/greedy", json=SAMPLE_PAYLOAD)
    assert res.status_code == 200
    data = res.json()
    assert data["makespan"] == 8.0
    assert len(data["tasks"]) == 2


def test_api_schedule_greedy_cyclic_rejected():
    res = client.post("/schedule/greedy", json=CYCLIC_PAYLOAD)
    assert res.status_code == 400
    assert "cyclic" in res.json()["detail"]["message"].lower() or "cycle" in str(res.json()["detail"]["errors"]).lower()


def test_api_schedule_backtrack():
    res = client.post("/schedule/backtrack", json=SAMPLE_PAYLOAD)
    assert res.status_code == 200
    data = res.json()
    assert data["makespan"] == 8.0
    assert data["optimality_proven"] is True


def test_api_schedule_branch_and_bound():
    res = client.post("/schedule/branch-and-bound", json=SAMPLE_PAYLOAD)
    assert res.status_code == 200
    data = res.json()
    assert data["makespan"] == 8.0
    assert data["optimality_proven"] is True


def test_api_schedule_compare():
    res = client.post("/schedule/compare", json=SAMPLE_PAYLOAD)
    assert res.status_code == 200
    data = res.json()
    assert data["best_makespan"] == 8.0
    assert "Greedy (Critical Path)" in data["algorithms"]
    assert "Branch and Bound" in data["algorithms"]


def test_api_workflow_random():
    req = {"num_tasks": 6, "dependency_density": 0.25, "seed": 42, "number_of_workers": 2}
    res = client.post("/workflow/random", json=req)
    assert res.status_code == 200
    data = res.json()
    assert len(data["tasks"]) == 6


def test_api_benchmark_run():
    req = {
        "task_counts": [4],
        "worker_counts": [2],
        "dependency_densities": [0.2],
        "algorithms": ["greedy_cp"],
        "repetitions": 1,
        "seed": 99
    }
    res = client.post("/benchmark/run", json=req)
    assert res.status_code == 200
    data = res.json()
    assert data["total_runs"] == 1


def test_api_sample_workflows_list_and_load():
    res_list = client.get("/sample-workflows")
    assert res_list.status_code == 200
    samples = res_list.json()["samples"]
    assert len(samples) >= 5

    # Load research_workflow.json
    res_wf = client.get("/sample-workflows/research_workflow.json")
    assert res_wf.status_code == 200
    wf_data = res_wf.json()
    assert wf_data["workflow_id"] == "research_workflow_01"
    assert len(wf_data["tasks"]) == 5

    # 404 on missing workflow
    res_missing = client.get("/sample-workflows/non_existent_file.json")
    assert res_missing.status_code == 404
