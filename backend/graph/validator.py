"""
validator.py - Workflow DAG Validator

Performs static analysis and graph structure validation on Workflow inputs prior to running scheduling algorithms.
Checks:
1. Non-empty workflow
2. Worker count >= 1
3. Duplicate task IDs
4. Valid positive task durations
5. Missing dependency references
6. Self-dependencies
7. Cycle detection via DFS graph traversal
"""

from typing import List, Set
from backend.models import Workflow, ValidationResult


def validate_workflow(workflow: Workflow) -> ValidationResult:
    """
    Validates a Workflow object for schema compliance and DAG invariants.

    Args:
        workflow: Workflow model instance.

    Returns:
        ValidationResult object containing boolean status and detailed error list if invalid.
    """
    errors: List[str] = []

    # 1. Empty workflow check
    if not workflow.tasks:
        errors.append("Workflow cannot be empty; it must contain at least one task.")
        return ValidationResult(valid=False, message="Validation failed", errors=errors)

    # 2. Worker count check
    if workflow.number_of_workers < 1:
        errors.append(f"Invalid worker count ({workflow.number_of_workers}). Must be at least 1.")

    # 3. Duplicate task IDs check
    seen_ids: Set[str] = set()
    duplicate_ids: Set[str] = set()
    for task in workflow.tasks:
        if task.task_id in seen_ids:
            duplicate_ids.add(task.task_id)
        seen_ids.add(task.task_id)

    if duplicate_ids:
        errors.append(f"Duplicate task IDs found: {sorted(list(duplicate_ids))}")

    all_task_ids = set(t.task_id for t in workflow.tasks)

    # 4 & 5 & 6. Task-level validation (durations, missing dependencies, self dependencies)
    for task in workflow.tasks:
        # Duration check
        if task.duration <= 0:
            errors.append(f"Task '{task.task_id}' has invalid duration ({task.duration}). Duration must be positive.")

        # Dependencies check
        for dep in task.dependencies:
            # Self-dependency check
            if dep == task.task_id:
                errors.append(f"Task '{task.task_id}' cannot depend on itself.")
            # Missing dependency check
            elif dep not in all_task_ids:
                errors.append(f"Task '{task.task_id}' depends on missing task '{dep}'.")

    # If static structural errors exist, return early before graph cycle detection
    if errors:
        return ValidationResult(valid=False, message="Workflow contains structural validation errors", errors=errors)

    # 7. Cycle Detection via DFS graph traversal
    # Build adjacency list for cycle detection
    adj: dict[str, list[str]] = {t.task_id: [] for t in workflow.tasks}
    for task in workflow.tasks:
        for dep in task.dependencies:
            # edge is dep -> task
            adj[dep].append(task.task_id)

    # DFS state: 0 = UNVISITED (WHITE), 1 = VISITING (GRAY), 2 = VISITED (BLACK)
    state: dict[str, int] = {t.task_id: 0 for t in workflow.tasks}
    cycle_nodes: list[str] = []

    def dfs(node: str, path: list[str]) -> bool:
        state[node] = 1  # GRAY
        path.append(node)

        for neighbor in adj[node]:
            if state[neighbor] == 1:  # GRAY node found -> Cycle!
                cycle_start_idx = path.index(neighbor)
                cycle_nodes.extend(path[cycle_start_idx:] + [neighbor])
                return True
            elif state[neighbor] == 0:  # WHITE node
                if dfs(neighbor, path):
                    return True

        path.pop()
        state[node] = 2  # BLACK
        return False

    has_cycle = False
    for task_id in all_task_ids:
        if state[task_id] == 0:
            if dfs(task_id, []):
                has_cycle = True
                break

    if has_cycle:
        cycle_str = " -> ".join(cycle_nodes) if cycle_nodes else "unknown"
        errors.append(f"Workflow graph contains a cycle: {cycle_str}")
        return ValidationResult(valid=False, message="Workflow contains cyclic dependencies", errors=errors)

    return ValidationResult(valid=True, message="Workflow is a valid DAG", errors=[])
