"""
models.py - Data Models for AI Agent Workflow Scheduler

Defines Pydantic schemas for tasks, workflows, and algorithm output structures.
Enforces validation rules such as positive duration and minimum worker counts.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class Task(BaseModel):
    """
    Represents an individual task (node) within an AI Agent Workflow DAG.
    """
    task_id: str = Field(..., description="Unique identifier for the task", min_length=1)
    name: str = Field(..., description="Human-readable name of the task")
    duration: float = Field(..., description="Estimated duration of execution (must be > 0)")
    dependencies: List[str] = Field(default_factory=list, description="List of task_ids that must complete before this task starts")
    cost: Optional[float] = Field(default=None, description="Optional execution cost")
    priority: Optional[int] = Field(default=None, description="Optional priority level for scheduling")
    task_type: Optional[str] = Field(default=None, description="Optional agent role/type (e.g., 'research', 'code', 'review')")

    @field_validator("duration")
    @classmethod
    def validate_duration(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Task duration must be greater than zero")
        return v


class Workflow(BaseModel):
    """
    Represents the complete workflow DAG payload containing all tasks and metadata.
    """
    workflow_id: str = Field(..., description="Unique identifier for the workflow", min_length=1)
    name: str = Field(..., description="Name of the workflow")
    tasks: List[Task] = Field(..., description="List of tasks comprising the workflow")
    number_of_workers: int = Field(default=1, description="Number of parallel execution workers available (must be >= 1)")
    deadline: Optional[float] = Field(default=None, description="Optional target deadline for completion")
    optimization_mode: Optional[str] = Field(default=None, description="Optional optimization criteria (e.g. 'makespan', 'cost')")

    @field_validator("number_of_workers")
    @classmethod
    def validate_workers(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Number of workers must be at least 1")
        return v


class ValidationResult(BaseModel):
    """
    API Response model for workflow validation checks.
    """
    valid: bool
    message: str
    errors: List[str] = Field(default_factory=list)


class TopologicalSortResult(BaseModel):
    """
    API Response model for topological sorting algorithms.
    """
    valid: bool
    topological_order: List[str] = Field(default_factory=list)
    error: Optional[str] = None


class TaskMetrics(BaseModel):
    """
    Calculated Dynamic Programming timing metrics for a single task.
    """
    task_id: str
    name: str
    duration: float
    ES: float = Field(..., description="Earliest Start time")
    EF: float = Field(..., description="Earliest Finish time")
    LS: float = Field(..., description="Latest Start time")
    LF: float = Field(..., description="Latest Finish time")
    slack: float = Field(..., description="Total Float / Slack time (LS - ES)")
    is_critical: bool = Field(..., description="True if task lies on the critical path (slack == 0)")


class CriticalPathResult(BaseModel):
    """
    API Response model containing complete Critical Path and Dynamic Programming analysis.
    """
    valid: bool
    topological_order: List[str] = Field(default_factory=list)
    project_duration: float = Field(default=0.0, description="Minimum completion time under unlimited workers (precedence lower bound)")
    critical_tasks: List[str] = Field(default_factory=list, description="List of task IDs with zero slack")
    critical_path: List[str] = Field(default_factory=list, description="Sequence of tasks forming the longest precedence path")
    task_metrics: Dict[str, TaskMetrics] = Field(default_factory=dict, description="Detailed DP timing metrics per task")
    error: Optional[str] = None


class ScheduledTask(BaseModel):
    """
    Represents an assigned task execution within a computed schedule.
    """
    task_id: str
    name: str
    worker_id: str
    start_time: float
    finish_time: float
    duration: float
    execution_order: int
    is_critical: bool = False


class WorkerUtilization(BaseModel):
    """
    Utilization metrics for an individual worker.
    """
    worker_id: str
    busy_time: float
    idle_time: float
    utilization_rate: float


class ScheduleResult(BaseModel):
    """
    Complete output of a scheduling algorithm (Greedy, Backtracking, Branch & Bound).
    """
    workflow_id: str
    algorithm: str
    priority_policy: Optional[str] = None
    number_of_workers: int
    makespan: float
    precedence_lower_bound: float
    worker_utilization: float
    worker_idle_time: float
    per_worker_utilization: Dict[str, WorkerUtilization] = Field(default_factory=dict)
    tasks: List[ScheduledTask] = Field(default_factory=list)
    execution_order: List[str] = Field(default_factory=list)
    states_explored: Optional[int] = None
    states_pruned: Optional[int] = None
    optimality_proven: bool = False
    status: str
    runtime_ms: float = 0.0
    error: Optional[str] = None


class ScheduleRequest(BaseModel):
    """
    Configuration payload for executing a scheduling algorithm.
    """
    workflow: Workflow
    priority_policy: Optional[str] = "CRITICAL_PATH"  # CRITICAL_PATH, LPT, SPT, FIFO, PRIORITY
    max_states: Optional[int] = 50000
    time_limit_sec: Optional[float] = 5.0


class ComparisonResult(BaseModel):
    """
    Comparative evaluation of multiple algorithms on the same workflow and worker count.
    """
    workflow_id: str
    number_of_workers: int
    precedence_lower_bound: float
    workload_lower_bound: float
    theoretical_lower_bound: float
    algorithms: Dict[str, ScheduleResult] = Field(default_factory=dict)
    best_makespan: float
    best_algorithm: str
    analysis: str


class RandomWorkflowRequest(BaseModel):
    """
    Parameters for generating a synthetic acyclic workflow DAG.
    """
    workflow_id: Optional[str] = None
    name: Optional[str] = None
    num_tasks: int = Field(default=8, ge=2, le=50)
    dependency_density: float = Field(default=0.3, ge=0.0, le=1.0)
    min_duration: float = Field(default=1.0, ge=0.1)
    max_duration: float = Field(default=15.0, ge=0.1)
    seed: Optional[int] = None
    number_of_workers: int = Field(default=2, ge=1, le=16)


class BenchmarkRequest(BaseModel):
    """
    Request configuration for running systematic scalability benchmarks.
    """
    task_counts: List[int] = Field(default=[5, 8, 12])
    worker_counts: List[int] = Field(default=[2, 3])
    dependency_densities: List[float] = Field(default=[0.25, 0.5])
    algorithms: List[str] = Field(default=["greedy_critical_path", "greedy_lpt", "branch_and_bound"])
    repetitions: int = Field(default=1, ge=1, le=5)
    seed: Optional[int] = 42
    backtrack_state_limit: int = Field(default=10000, le=50000)


class BenchmarkItem(BaseModel):
    """
    Metrics recorded for a single benchmark run configuration.
    """
    num_tasks: int
    num_workers: int
    density: float
    seed: int
    algorithm: str
    makespan: float
    runtime_ms: float
    states_explored: Optional[int] = None
    states_pruned: Optional[int] = None
    optimality_status: str
    lower_bound: float


class BenchmarkResponse(BaseModel):
    """
    Benchmark suite response containing tabular items and aggregate analytics.
    """
    results: List[BenchmarkItem]
    total_runs: int
    total_runtime_ms: float
    summary: Dict[str, Any] = Field(default_factory=dict)

