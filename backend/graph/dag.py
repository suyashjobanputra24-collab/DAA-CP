"""
dag.py - Directed Acyclic Graph Engine for Workflow Representation

This module implements the core DAG data structure for AI Agent Workflows.
Graph representation:
- Vertices (V): Tasks
- Directed Edges (E): Precedence dependencies (u -> v indicates u must complete before v starts)

Complexity:
- Graph Construction: O(V + E)
- Queries (successors, predecessors, indegree): O(1) lookup
- Space Complexity: O(V + E)
"""

from typing import List, Dict, Set
from backend.models import Task


class DAG:
    """
    Core Directed Acyclic Graph data structure for workflow scheduling algorithms.
    """

    def __init__(self, tasks: List[Task]):
        """
        Constructs the DAG from a list of Task objects.
        
        Args:
            tasks: List of Task objects.
        """
        self.task_map: Dict[str, Task] = {}
        self.adj_list: Dict[str, List[str]] = {}   # u -> list of successor task_ids
        self.pred_list: Dict[str, List[str]] = {}  # v -> list of predecessor task_ids
        self.indegree: Dict[str, int] = {}         # task_id -> number of incoming edges

        # Initialize structures for all tasks
        for task in tasks:
            self.task_map[task.task_id] = task
            self.adj_list[task.task_id] = []
            self.pred_list[task.task_id] = []
            self.indegree[task.task_id] = 0

        # Populate edges based on dependencies
        # If task V has dependency U, then edge is U -> V
        for task in tasks:
            v = task.task_id
            for u in task.dependencies:
                if u in self.task_map:
                    self.adj_list[u].append(v)
                    self.pred_list[v].append(u)
                    self.indegree[v] += 1

    def get_nodes(self) -> List[str]:
        """Returns all task IDs in the DAG."""
        return list(self.task_map.keys())

    def get_task(self, task_id: str) -> Task:
        """Retrieves task details by task ID."""
        if task_id not in self.task_map:
            raise KeyError(f"Task ID '{task_id}' not found in DAG.")
        return self.task_map[task_id]

    def get_sources(self) -> List[str]:
        """Returns all source tasks (tasks with indegree 0, i.e., no dependencies)."""
        return [task_id for task_id, deg in self.indegree.items() if deg == 0]

    def get_sinks(self) -> List[str]:
        """Returns all terminal tasks (tasks with outdegree 0, i.e., no successors)."""
        return [task_id for task_id, succs in self.adj_list.items() if len(succs) == 0]

    def get_successors(self, task_id: str) -> List[str]:
        """Returns list of tasks that directly depend on the given task."""
        return self.adj_list.get(task_id, [])

    def get_predecessors(self, task_id: str) -> List[str]:
        """Returns list of tasks that the given task directly depends on."""
        return self.pred_list.get(task_id, [])

    def get_indegree(self, task_id: str) -> int:
        """Returns the in-degree of a task."""
        return self.indegree.get(task_id, 0)

    def get_indegree_map(self) -> Dict[str, int]:
        """Returns a copy of the indegree mapping for all nodes."""
        return dict(self.indegree)
