"""
topological_sort.py - Kahn's Algorithm for Topological Sorting

Algorithm Overview:
-------------------
Kahn's algorithm produces a linear ordering of vertices in a Directed Acyclic Graph (DAG)
such that for every directed edge u -> v, task u appears before task v in the ordering.

DAA Academic Specifications:
1. Purpose: Generate a valid task execution sequence satisfying all precedence constraints.
2. Input: A DAG object representing tasks and dependencies.
3. Output: TopologicalSortResult containing the topological ordering list or an error if a cycle exists.
4. Algorithm Steps:
   a. Compute the in-degree (number of incoming edges / dependencies) for each node.
   b. Enqueue all zero-indegree nodes into a queue (these are source tasks with no prerequisites).
   c. While queue is non-empty:
      i. Dequeue a vertex u and append it to the topological_order list.
      ii. For each successor v of u, decrement in-degree(v) by 1.
      iii. If in-degree(v) becomes 0, enqueue v.
   d. If length of topological_order == total number of vertices, return ordering.
      Otherwise, the graph contains at least one directed cycle.
5. Time Complexity: O(V + E)
   - Every vertex is enqueued and dequeued exactly once: O(V).
   - Every edge is traversed once to decrement in-degrees: O(E).
6. Space Complexity: O(V)
   - Queue: O(V) space.
   - In-degree dictionary: O(V) space.
   - Output list: O(V) space.
7. Correctness Reasoning:
   - Zero in-degree nodes have all prerequisites satisfied, so placing them first is valid.
   - Removing u and decrementing successors' in-degrees simulates completing task u and freeing dependent tasks.
   - If a cycle exists, nodes in the cycle will never reach an in-degree of 0, leaving processed count < V.
"""

from collections import deque
from typing import List
from backend.graph.dag import DAG
from backend.models import TopologicalSortResult


def kahn_topological_sort(dag: DAG) -> TopologicalSortResult:
    """
    Executes Kahn's Topological Sort algorithm on the given DAG.

    Args:
        dag: Formatted DAG graph engine instance.

    Returns:
        TopologicalSortResult with sorted task_ids if successful, or error if graph contains a cycle.
    """
    nodes = dag.get_nodes()
    if not nodes:
        return TopologicalSortResult(valid=True, topological_order=[])

    # 1. Obtain working copy of in-degree for each vertex
    indegree = dag.get_indegree_map()

    # 2. Enqueue all source nodes (indegree == 0)
    # Using collections.deque for O(1) pops
    queue = deque([node for node in nodes if indegree[node] == 0])

    topological_order: List[str] = []

    # 3. Process queue
    while queue:
        u = queue.popleft()
        topological_order.append(u)

        # For each successor task dependent on u
        for v in dag.get_successors(u):
            indegree[v] -= 1
            if indegree[v] == 0:
                queue.append(v)

    # 4. Cycle verification
    if len(topological_order) == len(nodes):
        return TopologicalSortResult(valid=True, topological_order=topological_order)
    else:
        return TopologicalSortResult(
            valid=False,
            topological_order=[],
            error=f"Graph contains a cycle! Only {len(topological_order)} of {len(nodes)} tasks could be ordered."
        )
