"""
cycle_detection.py - Three-State Depth-First Search (DFS) Cycle Detector

Algorithm Overview:
-------------------
Detects directed cycles in a graph using classic 3-state Depth-First Search (DFS) vertex coloring.

States:
- WHITE (0): Unvisited vertex.
- GRAY (1): Vertex currently being explored (on the current DFS call stack).
- BLACK (2): Vertex completely explored along all outbound branches.

DAA Academic Specifications:
1. Purpose: Independently verify directed acyclic graph invariants and isolate cycle paths.
2. Input: A DAG object representing tasks and precedence edges.
3. Output: Tuple (has_cycle: bool, cycle_path: Optional[List[str]]).
4. Algorithm Steps:
   a. Initialize state[v] = WHITE for all vertices v in V.
   b. For each vertex u in V:
      If state[u] == WHITE, invoke DFS(u).
   c. In DFS(u):
      i. Set state[u] = GRAY, push u onto recursion path stack.
      ii. For each successor v of u:
          - If state[v] == GRAY: Cycle detected! Extract cycle from path stack from v to u.
          - If state[v] == WHITE: Recursively call DFS(v). If it returns True, propagate cycle.
      iii. Set state[u] = BLACK, pop u from path stack.
      iv. Return False.
5. Time Complexity: O(V + E)
   - Each node is visited once per state transition WHITE -> GRAY -> BLACK: O(V).
   - Each directed edge is checked once: O(E).
6. Space Complexity: O(V)
   - Recursion stack depth: O(V) worst case (linear graph).
   - State dictionary: O(V).
7. Correctness Reasoning:
   - A GRAY node represents an active ancestor on the current DFS call stack.
   - Encountering an edge u -> v where v is GRAY implies a back-edge from descendant to ancestor, forming a directed cycle.
"""

from typing import Tuple, List, Optional, Dict
from backend.graph.dag import DAG

# State Constants
WHITE = 0  # Unvisited
GRAY = 1   # Visiting (on call stack)
BLACK = 2  # Visited


def detect_cycle_dfs(dag: DAG) -> Tuple[bool, Optional[List[str]]]:
    """
    Performs DFS 3-State cycle detection on the given DAG graph engine.

    Args:
        dag: Formatted DAG graph engine instance.

    Returns:
        Tuple (has_cycle: bool, cycle_path: Optional[List[str]]).
        If a cycle is found, returns True and the sequence of task IDs forming the cycle.
        If no cycle exists, returns (False, None).
    """
    nodes = dag.get_nodes()
    state: Dict[str, int] = {node: WHITE for node in nodes}
    path_stack: List[str] = []
    cycle_result: List[str] = []

    def dfs(u: str) -> bool:
        state[u] = GRAY
        path_stack.append(u)

        for v in dag.get_successors(u):
            if state[v] == GRAY:
                # Cycle found! Extract subpath from first occurrence of v in call stack up to u, plus v to close
                cycle_start_idx = path_stack.index(v)
                nonlocal cycle_result
                cycle_result = path_stack[cycle_start_idx:] + [v]
                return True
            elif state[v] == WHITE:
                if dfs(v):
                    return True

        path_stack.pop()
        state[u] = BLACK
        return False

    for node in nodes:
        if state[node] == WHITE:
            if dfs(node):
                return True, cycle_result

    return False, None
