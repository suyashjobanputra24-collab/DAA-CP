"""
critical_path.py - Dynamic Programming Critical Path Analysis (CPM)

Algorithm Overview:
-------------------
Computes the Critical Path and float/slack metrics for tasks in a Directed Acyclic Graph (DAG)
using Dynamic Programming (Forward and Reverse Passes over Topological Order).

Mathematical Formulas:
----------------------
1. Forward Pass (Earliest Start / Finish):
   - ES(u) = 0 if u has no predecessors, else max { EF(p) for all p in predecessors(u) }
   - EF(u) = ES(u) + duration(u)
   - Project Completion Time T = max { EF(u) for all u in V }

2. Reverse Pass (Latest Start / Finish):
   - LF(u) = T if u has no successors, else min { LS(s) for all s in successors(u) }
   - LS(u) = LF(u) - duration(u)
   - Total Float / Slack(u) = LS(u) - ES(u)

3. Critical Task Identification:
   - A task u is CRITICAL if Slack(u) == 0 (within floating-point tolerance 1e-9).

DAA Academic Specifications:
1. Purpose: Calculate precedence lower bound (unlimited-worker minimal makespan) and critical bottleneck chain.
2. Time Complexity: O(V + E)
   - Topological sorting: O(V + E)
   - Forward DP pass: O(V + E)
   - Reverse DP pass: O(V + E)
   - Critical path reconstruction: O(V + E)
3. Space Complexity: O(V) for DP tables (ES, EF, LS, LF, Slack).
4. Academic Note:
   - Cmax >= CP (Critical Path duration represents the precedence lower bound).
   - Under worker constraints, optimal makespan may exceed CP duration.
"""

from typing import Dict, List
from backend.graph.dag import DAG
from backend.algorithms.topological_sort import kahn_topological_sort
from backend.models import CriticalPathResult, TaskMetrics

FLOAT_TOLERANCE = 1e-9


def calculate_critical_path(dag: DAG) -> CriticalPathResult:
    """
    Performs Dynamic Programming Critical Path Analysis on the DAG.

    Args:
        dag: Formatted DAG graph engine instance.

    Returns:
        CriticalPathResult object with project duration, critical tasks, critical path sequence,
        and per-task metrics (ES, EF, LS, LF, Slack).
    """
    nodes = dag.get_nodes()
    if not nodes:
        return CriticalPathResult(valid=True, project_duration=0.0)

    # 1. Topological Sort (Required for DP evaluation order)
    topo_res = kahn_topological_sort(dag)
    if not topo_res.valid:
        return CriticalPathResult(
            valid=False,
            error=f"Cannot compute Critical Path: {topo_res.error}"
        )

    topo_order = topo_res.topological_order

    # DP Tables
    ES: Dict[str, float] = {}
    EF: Dict[str, float] = {}
    LS: Dict[str, float] = {}
    LF: Dict[str, float] = {}
    slack: Dict[str, float] = {}

    # 2. Forward Pass: Compute Earliest Start (ES) & Earliest Finish (EF)
    for u in topo_order:
        task = dag.get_task(u)
        preds = dag.get_predecessors(u)

        if not preds:
            ES[u] = 0.0
        else:
            ES[u] = max(EF[p] for p in preds)

        EF[u] = ES[u] + task.duration

    # Project duration = maximum EF across all tasks
    project_duration = max(EF.values()) if EF else 0.0

    # 3. Reverse Pass: Compute Latest Finish (LF) & Latest Start (LS)
    for u in reversed(topo_order):
        task = dag.get_task(u)
        succs = dag.get_successors(u)

        if not succs:
            LF[u] = project_duration
        else:
            LF[u] = min(LS[s] for s in succs)

        LS[u] = LF[u] - task.duration
        slack[u] = LS[u] - ES[u]

    # 4. Critical Tasks Identification
    critical_tasks: List[str] = [
        u for u in topo_order if abs(slack[u]) < FLOAT_TOLERANCE
    ]

    # 5. Reconstruct Critical Path Sequence
    # Build actual path starting from critical source tasks to terminal tasks along zero-slack edges
    critical_set = set(critical_tasks)
    
    # Find critical sources (critical tasks with no critical predecessors)
    crit_sources = [
        u for u in critical_tasks
        if not any(p in critical_set for p in dag.get_predecessors(u))
    ]

    def get_longest_critical_chain(u: str) -> List[str]:
        best_chain: List[str] = [u]
        max_duration = 0.0

        crit_succs = [
            v for v in dag.get_successors(u)
            if v in critical_set and abs(EF[u] - ES[v]) < FLOAT_TOLERANCE
        ]

        for v in crit_succs:
            sub_chain = get_longest_critical_chain(v)
            chain_duration = sum(dag.get_task(x).duration for x in sub_chain)
            if chain_duration > max_duration:
                max_duration = chain_duration
                best_chain = [u] + sub_chain

        return best_chain

    longest_path: List[str] = []
    longest_path_duration = -1.0

    for src in crit_sources:
        chain = get_longest_critical_chain(src)
        chain_dur = sum(dag.get_task(x).duration for x in chain)
        if chain_dur > longest_path_duration:
            longest_path_duration = chain_dur
            longest_path = chain

    # If no path reconstructed (e.g. edge case), fallback to critical_tasks in topo order
    if not longest_path:
        longest_path = critical_tasks

    # Build per-task metrics map
    task_metrics: Dict[str, TaskMetrics] = {}
    for u in topo_order:
        t = dag.get_task(u)
        task_metrics[u] = TaskMetrics(
            task_id=t.task_id,
            name=t.name,
            duration=t.duration,
            ES=round(ES[u], 4),
            EF=round(EF[u], 4),
            LS=round(LS[u], 4),
            LF=round(LF[u], 4),
            slack=round(slack[u], 4),
            is_critical=(abs(slack[u]) < FLOAT_TOLERANCE)
        )

    return CriticalPathResult(
        valid=True,
        topological_order=topo_order,
        project_duration=round(project_duration, 4),
        critical_tasks=critical_tasks,
        critical_path=longest_path,
        task_metrics=task_metrics
    )
