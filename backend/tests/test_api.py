"""
test_api.py - Integration tests for FastAPI endpoints.
"""

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

SAMPLE_WORKFLOW_PAYLOAD = {
    "workflow_id": "research_workflow_01",
    "name": "Research Agent Workflow",
    "number_of_workers": 2,
    "tasks": [
        {
            "task_id": "T1",
            "name": "Search Web",
            "duration": 5.0,
            "dependencies": []
        },
        {
            "task_id": "T2",
            "name": "Read Papers",
            "duration": 8.0,
            "dependencies": []
        },
        {
            "task_id": "T3",
            "name": "Analyze",
            "duration": 10.0,
            "dependencies": ["T1", "T2"]
        },
        {
            "task_id": "T4",
            "name": "Generate Report",
            "duration": 7.0,
            "dependencies": ["T3"]
        },
        {
            "task_id": "T5",
            "name": "Review",
            "duration": 5.0,
            "dependencies": ["T4"]
        }
    ]
}


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "project" in data
    assert data["status"] == "operational"


def test_api_validate_workflow():
    response = client.post("/workflow/validate", json=SAMPLE_WORKFLOW_PAYLOAD)
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["message"] == "Workflow is a valid DAG"


def test_api_topological_sort():
    response = client.post("/workflow/topological-sort", json=SAMPLE_WORKFLOW_PAYLOAD)
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    order = data["topological_order"]
    assert len(order) == 5
    assert order.index("T1") < order.index("T3")
    assert order.index("T2") < order.index("T3")
    assert order.index("T3") < order.index("T4")
    assert order.index("T4") < order.index("T5")


def test_api_critical_path():
    response = client.post("/workflow/critical-path", json=SAMPLE_WORKFLOW_PAYLOAD)
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["project_duration"] == 30.0
    assert set(data["critical_tasks"]) == {"T2", "T3", "T4", "T5"}
    assert data["critical_path"] == ["T2", "T3", "T4", "T5"]
    assert "T1" in data["task_metrics"]
    assert data["task_metrics"]["T1"]["slack"] == 3.0
