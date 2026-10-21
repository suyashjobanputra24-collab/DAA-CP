"""
random_dag.py - Synthetic Directed Acyclic Graph (DAG) Generator

Generates random, reproducible, structurally valid workflow DAGs for benchmarking.
Acyclicity is mathematically guaranteed by only generating forward edges i -> j where i < j.
Supports:
- Controlled task counts (V)
- Configurable dependency density (edge probability between valid pairs)
- Random seed initialization for exact scientific reproducibility
- Configurable duration intervals
"""

import random
from typing import List, Optional
from backend.models import Task, Workflow


def generate_random_dag(
    num_tasks: int = 8,
    dependency_density: float = 0.3,
    min_duration: float = 1.0,
    max_duration: float = 15.0,
    seed: Optional[int] = None,
    number_of_workers: int = 2,
    workflow_id: Optional[str] = None,
    name: Optional[str] = None
) -> Workflow:
    """
    Generates a valid synthetic Workflow DAG.

    Args:
        num_tasks: Number of tasks (V).
        dependency_density: Edge probability p in [0.0, 1.0].
        min_duration: Minimum duration for tasks.
        max_duration: Maximum duration for tasks.
        seed: Random seed for reproducibility.
        number_of_workers: Assigned worker capacity.
        workflow_id: Optional ID string.
        name: Optional workflow name.

    Returns:
        Workflow instance guaranteed to be an acyclic valid DAG.
    """
    if seed is not None:
        rng = random.Random(seed)
    else:
        rng = random.Random()

    task_roles = ["research", "preprocess", "compute", "analysis", "review", "deploy", "aggregate"]

    tasks: List[Task] = []
    task_ids = [f"T{i+1}" for i in range(num_tasks)]

    # Adjacency list: predecessors for each task
    predecessors_map = {tid: [] for tid in task_ids}

    # Generate forward edges (i < j ensures no cycles)
    for j in range(1, num_tasks):
        # We can connect j to previous tasks i < j
        for i in range(j):
            if rng.random() < dependency_density:
                predecessors_map[task_ids[j]].append(task_ids[i])

    # To avoid completely isolated disconnected graphs when density > 0,
    # ensure each non-source task has at least one dependency if density is high,
    # or keep pure random. Let's make sure the root T1 has no dependencies and at least some tasks depend on something.
    for i, tid in enumerate(task_ids):
        dur = round(rng.uniform(min_duration, max_duration), 1)
        role = rng.choice(task_roles)
        prio = rng.randint(1, 5)

        tasks.append(
            Task(
                task_id=tid,
                name=f"Agent Step {i+1} ({role.capitalize()})",
                duration=dur,
                dependencies=sorted(predecessors_map[tid]),
                task_type=role,
                priority=prio
            )
        )

    wf_id = workflow_id or f"synthetic_dag_{num_tasks}t_{seed if seed is not None else 'rand'}"
    wf_name = name or f"Synthetic Workflow ({num_tasks} Tasks, Density {dependency_density:.2f})"

    return Workflow(
        workflow_id=wf_id,
        name=wf_name,
        tasks=tasks,
        number_of_workers=number_of_workers
    )
