"""
main.py - FastAPI Application Endpoint Definitions

AI Agent Workflow Scheduler REST API
Exposes endpoints for:
- Health and system metadata
- Workflow structural validation and cycle detection
- Kahn's topological sort O(V + E)
- Dynamic Programming Critical Path analysis (ES, EF, LS, LF, Slack)
- Event-driven Greedy List Scheduling (CRITICAL_PATH, LPT, SPT, FIFO, PRIORITY)
- Exact Backtracking Scheduler
- Branch & Bound Scheduler with Lower-Bound Pruning
- Multi-Algorithm Comparison
- Synthetic Random DAG Generation
- Benchmark Suite Execution
- Built-in Sample Workflows Repository
"""

import json
import os
from typing import Dict, List, Any
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from backend.models import (
    Workflow,
    ValidationResult,
    TopologicalSortResult,
    CriticalPathResult,
    ScheduleResult,
    ScheduleRequest,
    ComparisonResult,
    RandomWorkflowRequest,
    BenchmarkRequest,
    BenchmarkResponse
)
from backend.graph.dag import DAG
from backend.graph.validator import validate_workflow
from backend.algorithms.topological_sort import kahn_topological_sort
from backend.algorithms.critical_path import calculate_critical_path
from backend.algorithms.greedy_scheduler import schedule_greedy
from backend.algorithms.exact_backtracking import schedule_backtrack
from backend.algorithms.branch_and_bound import schedule_branch_and_bound
from backend.algorithms.comparison import compare_algorithms
from backend.algorithms.random_dag import generate_random_dag
from backend.algorithms.benchmark import run_benchmark

app = FastAPI(
    title="AI Agent Workflow Scheduler API",
    description="3rd Year DAA Subject Project: Comprehensive Workflow Scheduling Engine with Greedy, Backtracking, and Branch & Bound algorithms.",
    version="2.0.0"
)

# Enable CORS for React frontend (Vite dev server and production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SAMPLE_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sample_data"))


# ============================================================================
# 1. Health & Metadata Endpoints
# ============================================================================

@app.get("/", tags=["Health"])
def root_endpoint():
    """Root health check endpoint returning API metadata and capabilities."""
    return {
        "project": "AI Agent Workflow Scheduler",
        "phase": "COMPLETED (DAG Engine, DP Critical Path, Greedy List Scheduling, Backtracking, Branch & Bound, Benchmark Lab)",
        "version": "2.0.0",
        "status": "operational",
        "documentation": "/docs"
    }


# ============================================================================
# 2. Workflow Validation & Structural Graph Algorithms
# ============================================================================

@app.post(
    "/workflow/validate",
    response_model=ValidationResult,
    tags=["Workflow Algorithms"],
    summary="Validate Workflow Structure & Detect Cycles"
)
def api_validate_workflow(workflow: Workflow):
    """
    Validates the input workflow:
    - Checks for duplicate task IDs
    - Checks for missing dependency references
    - Checks for self-dependencies and invalid non-positive durations
    - Performs DFS 3-state cycle detection
    """
    return validate_workflow(workflow)


@app.post(
    "/workflow/topological-sort",
    response_model=TopologicalSortResult,
    tags=["Workflow Algorithms"],
    summary="Compute Kahn's Topological Sort"
)
def api_topological_sort(workflow: Workflow):
    """
    Computes a valid linear execution order for the workflow tasks using Kahn's Algorithm O(V + E).
    """
    val_res = validate_workflow(workflow)
    if not val_res.valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": val_res.message,
                "errors": val_res.errors
            }
        )

    dag = DAG(workflow.tasks)
    return kahn_topological_sort(dag)


@app.post(
    "/workflow/critical-path",
    response_model=CriticalPathResult,
    tags=["Workflow Algorithms"],
    summary="Compute Dynamic Programming Critical Path & Task Slack"
)
def api_critical_path(workflow: Workflow):
    """
    Calculates Earliest Start (ES), Earliest Finish (EF), Latest Start (LS), Latest Finish (LF),
    Slack (Total Float), Critical Tasks, and Critical Path Sequence using Dynamic Programming.
    """
    val_res = validate_workflow(workflow)
    if not val_res.valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": val_res.message,
                "errors": val_res.errors
            }
        )

    dag = DAG(workflow.tasks)
    return calculate_critical_path(dag)


# ============================================================================
# 3. Scheduling Algorithms (Greedy, Backtracking, Branch & Bound)
# ============================================================================

@app.post(
    "/schedule/greedy",
    response_model=ScheduleResult,
    tags=["Scheduling Engine"],
    summary="Execute Event-Driven Greedy List Scheduling"
)
def api_schedule_greedy(request: ScheduleRequest):
    """
    Executes Greedy List Scheduling with event-driven clock advancement and priority heap:
    - Priority policies: CRITICAL_PATH, LPT, SPT, FIFO, TASK_PRIORITY
    - Deterministic tie-breaking by task_id ascending
    - Handles simultaneous completions and computes worker utilization
    """
    val_res = validate_workflow(request.workflow)
    if not val_res.valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": val_res.message,
                "errors": val_res.errors
            }
        )

    policy = request.priority_policy or "CRITICAL_PATH"
    return schedule_greedy(request.workflow, priority_policy=policy)


@app.post(
    "/schedule/backtrack",
    response_model=ScheduleResult,
    tags=["Scheduling Engine"],
    summary="Execute Exact Backtracking Scheduler"
)
def api_schedule_backtrack(request: ScheduleRequest):
    """
    Executes exhaustive state-space backtracking to determine the exact optimal makespan.
    Configurable search limit guards against combinatorial explosion.
    """
    val_res = validate_workflow(request.workflow)
    if not val_res.valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": val_res.message,
                "errors": val_res.errors
            }
        )

    max_st = request.max_states or 50000
    timeout = request.time_limit_sec or 5.0
    return schedule_backtrack(request.workflow, max_states=max_st, time_limit_sec=timeout)


@app.post(
    "/schedule/branch-and-bound",
    response_model=ScheduleResult,
    tags=["Scheduling Engine"],
    summary="Execute Branch and Bound Scheduler with Lower-Bound Pruning"
)
def api_schedule_branch_and_bound(request: ScheduleRequest):
    """
    Executes Branch and Bound using:
    - Warm-start Greedy incumbent (Upper Bound)
    - Precedence chain lower bounds (LB_prec)
    - Worker capacity workload bounds (LB_workload)
    - Valid branch pruning
    """
    val_res = validate_workflow(request.workflow)
    if not val_res.valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": val_res.message,
                "errors": val_res.errors
            }
        )

    max_st = request.max_states or 50000
    timeout = request.time_limit_sec or 5.0
    return schedule_branch_and_bound(request.workflow, max_states=max_st, time_limit_sec=timeout)


@app.post(
    "/schedule/compare",
    response_model=ComparisonResult,
    tags=["Scheduling Engine"],
    summary="Comparative Evaluation of Multiple Algorithms"
)
def api_compare_algorithms(request: ScheduleRequest):
    """
    Runs Greedy (Critical Path & LPT), Backtracking, and Branch & Bound on the same workflow,
    comparing makespan, runtime, explored states, and optimality gaps.
    """
    val_res = validate_workflow(request.workflow)
    if not val_res.valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": val_res.message,
                "errors": val_res.errors
            }
        )

    max_st = request.max_states or 20000
    timeout = request.time_limit_sec or 3.0
    return compare_algorithms(request.workflow, max_states=max_st, time_limit_sec=timeout)


# ============================================================================
# 4. Workflow Generator & Benchmark Lab
# ============================================================================

@app.post(
    "/workflow/random",
    response_model=Workflow,
    tags=["Workflow Tools"],
    summary="Generate Synthetic Random Valid DAG"
)
def api_generate_random_workflow(request: RandomWorkflowRequest):
    """
    Generates a reproducible, structurally valid acyclic DAG based on task count,
    dependency density, and optional seed.
    """
    return generate_random_dag(
        num_tasks=request.num_tasks,
        dependency_density=request.dependency_density,
        min_duration=request.min_duration,
        max_duration=request.max_duration,
        seed=request.seed,
        number_of_workers=request.number_of_workers,
        workflow_id=request.workflow_id,
        name=request.name
    )


@app.post(
    "/benchmark/run",
    response_model=BenchmarkResponse,
    tags=["Benchmark Lab"],
    summary="Run Systematic Algorithmic Benchmark Suite"
)
def api_run_benchmark(request: BenchmarkRequest):
    """
    Runs automated scalability experiments measuring wall-clock runtime,
    makespan, states explored, and lower-bound gaps across configurations.
    """
    return run_benchmark(request)


# ============================================================================
# 5. Built-in Sample Workflows
# ============================================================================

@app.get(
    "/sample-workflows",
    tags=["Sample Workflows"],
    summary="List All Built-in Sample Workflows"
)
def api_list_sample_workflows():
    """
    Lists all available sample workflows stored in sample_data/.
    """
    samples = []
    if os.path.exists(SAMPLE_DATA_DIR):
        for fname in sorted(os.listdir(SAMPLE_DATA_DIR)):
            if fname.endswith(".json"):
                fpath = os.path.join(SAMPLE_DATA_DIR, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    samples.append({
                        "filename": fname,
                        "workflow_id": data.get("workflow_id", fname),
                        "name": data.get("name", fname),
                        "tasks_count": len(data.get("tasks", [])),
                        "number_of_workers": data.get("number_of_workers", 2)
                    })
                except Exception:
                    pass
    return {"samples": samples}


@app.get(
    "/sample-workflows/{filename}",
    response_model=Workflow,
    tags=["Sample Workflows"],
    summary="Load Specific Sample Workflow by Filename"
)
def api_get_sample_workflow(filename: str):
    """
    Loads and parses a sample workflow JSON by filename.
    """
    # Sanitize filename
    safe_name = os.path.basename(filename)
    if not safe_name.endswith(".json"):
        safe_name += ".json"

    fpath = os.path.join(SAMPLE_DATA_DIR, safe_name)
    if not os.path.exists(fpath):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sample workflow '{filename}' not found."
        )

    try:
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return Workflow(**data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error parsing sample workflow: {str(e)}"
        )
