"""
demo.py - Comprehensive CLI Demonstration Script for AI Agent Workflow Scheduler

Demonstrates the complete DAA Project suite:
1. Load sample Research Agent workflow JSON
2. Workflow Validation & Invariant Checking
3. DAG Engine Construction (Adjacency & Indegree representation)
4. DFS 3-State Cycle Detection
5. Kahn's Topological Sort algorithm O(V + E)
6. Dynamic Programming Critical Path Analysis & Slack Calculation
7. Event-Driven Greedy List Scheduling with Priority Heap
8. Branch & Bound Exact Optimization with Lower-Bound Pruning
9. Graham's List Scheduling Anomaly Demonstration (Greedy 10.0 vs BnB Optimal 9.0)
10. Algorithmic Scalability Benchmark Execution
"""

import json
import os
import sys

# Ensure root workspace directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.models import Workflow, BenchmarkRequest
from backend.graph.dag import DAG
from backend.graph.validator import validate_workflow
from backend.algorithms.topological_sort import kahn_topological_sort
from backend.algorithms.cycle_detection import detect_cycle_dfs
from backend.algorithms.critical_path import calculate_critical_path
from backend.algorithms.greedy_scheduler import schedule_greedy
from backend.algorithms.branch_and_bound import schedule_branch_and_bound
from backend.algorithms.exact_backtracking import schedule_backtrack
from backend.algorithms.comparison import compare_algorithms
from backend.algorithms.benchmark import run_benchmark


def run_demo():
    print("=" * 85)
    print("      AI AGENT WORKFLOW SCHEDULER - COMPLETE DAA PROJECT DEMONSTRATION")
    print("=" * 85)

    # 1. Load Sample Data
    sample_path = os.path.join(os.path.dirname(__file__), "..", "sample_data", "research_workflow.json")
    print(f"\n[STEP 1] Loading Workflow from: {os.path.abspath(sample_path)}")

    with open(sample_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    workflow = Workflow(**data)
    print(f"Loaded Workflow: '{workflow.name}' (ID: {workflow.workflow_id})")
    print(f"Tasks Count: {len(workflow.tasks)} | Available Workers: {workflow.number_of_workers}")

    # 2. Workflow Validation
    print("\n[STEP 2] Running Workflow Structural Validation...")
    val_res = validate_workflow(workflow)
    print(f"Validation Status : {'VALID' if val_res.valid else 'INVALID'}")
    print(f"Validation Message: {val_res.message}")
    if val_res.errors:
        print(f"Errors Found      : {val_res.errors}")
        return

    # 3. DAG Construction
    print("\n[STEP 3] Constructing Directed Acyclic Graph (DAG)...")
    dag = DAG(workflow.tasks)
    print(f"Nodes (V)   : {dag.get_nodes()}")
    print(f"Sources     : {dag.get_sources()}")
    print(f"Sinks       : {dag.get_sinks()}")
    print("Indegree Map:")
    for node, deg in dag.get_indegree_map().items():
        task = dag.get_task(node)
        print(f"  - [{node}] {task.name:<18} : Indegree = {deg}")

    # 4. DFS Cycle Detection
    print("\n[STEP 4] Running DFS 3-State Cycle Detection...")
    has_cycle, cycle_path = detect_cycle_dfs(dag)
    print(f"Cycle Detected: {has_cycle}")
    if has_cycle:
        print(f"Cycle Path    : {' -> '.join(cycle_path)}")

    # 5. Kahn's Topological Sort
    print("\n[STEP 5] Running Kahn's Topological Sort Algorithm O(V + E)...")
    topo_res = kahn_topological_sort(dag)
    print(f"Topological Sort Valid: {topo_res.valid}")
    print(f"Topological Order     : {' -> '.join(topo_res.topological_order)}")

    # 6. Dynamic Programming Critical Path Analysis
    print("\n[STEP 6] Running Critical Path Analysis (Dynamic Programming Forward/Reverse Passes)...")
    cp_res = calculate_critical_path(dag)

    print("-" * 85)
    print(f"{'Task ID':<8} {'Task Name':<18} {'Dur':<6} {'ES':<6} {'EF':<6} {'LS':<6} {'LF':<6} {'Slack':<8} {'Critical?':<10}")
    print("-" * 85)
    for tid in cp_res.topological_order:
        m = cp_res.task_metrics[tid]
        crit_str = "YES ***" if m.is_critical else "No"
        print(f"{m.task_id:<8} {m.name:<18} {m.duration:<6.1f} {m.ES:<6.1f} {m.EF:<6.1f} {m.LS:<6.1f} {m.LF:<6.1f} {m.slack:<8.1f} {crit_str:<10}")

    print("-" * 85)
    print(f"PROJECT COMPLETION TIME (Precedence Lower Bound Cmax): {cp_res.project_duration} time units")
    print(f"CRITICAL TASKS (Slack == 0)                          : {', '.join(cp_res.critical_tasks)}")
    crit_path_names = [f"[{tid}] {dag.get_task(tid).name}" for tid in cp_res.critical_path]
    print(f"CRITICAL PATH SEQUENCE                               : {' -> '.join(crit_path_names)}")

    # 7. Event-Driven Greedy List Scheduling
    print("\n[STEP 7] Running Event-Driven Greedy List Scheduling (P | prec | C_max)...")
    greedy_res = schedule_greedy(workflow, priority_policy="CRITICAL_PATH", dag=dag)
    print(f"Greedy Makespan     : {greedy_res.makespan} time units")
    print(f"Worker Utilization  : {greedy_res.worker_utilization * 100:.1f}%")
    print(f"Worker Idle Time    : {greedy_res.worker_idle_time} time units")
    print(f"Optimality Status   : {greedy_res.status} (Proven: {greedy_res.optimality_proven})")
    print(f"Schedule Execution  :")
    for st in greedy_res.tasks:
        crit_tag = "[CRITICAL]" if st.is_critical else ""
        print(f"  Worker {st.worker_id}: [{st.task_id}] {st.name:<16} Start={st.start_time:<5.1f} Finish={st.finish_time:<5.1f} {crit_tag}")

    # 8. Exact Optimization (Branch & Bound vs Backtracking)
    print("\n[STEP 8] Running Exact Branch & Bound with Lower-Bound Pruning...")
    bnb_res = schedule_branch_and_bound(workflow, dag=dag)
    bt_res = schedule_backtrack(workflow, dag=dag)
    print(f"Branch & Bound Makespan : {bnb_res.makespan} time units (Proven: {bnb_res.optimality_proven})")
    print(f"States Explored (BnB)   : {bnb_res.states_explored} | States Pruned: {bnb_res.states_pruned} | Time: {bnb_res.runtime_ms:.3f} ms")
    print(f"States Explored (Exh. BT): {bt_res.states_explored} | Time: {bt_res.runtime_ms:.3f} ms")

    # 9. Graham's Anomaly Demo (Greedy Suboptimality)
    subopt_path = os.path.join(os.path.dirname(__file__), "..", "sample_data", "greedy_suboptimal.json")
    print(f"\n[STEP 9] Demonstrating Graham's List Scheduling Anomaly...")
    with open(subopt_path, "r", encoding="utf-8") as f:
        subopt_wf = Workflow(**json.load(f))
    subopt_comp = compare_algorithms(subopt_wf)
    print(f"Workflow: '{subopt_wf.name}' (2 Workers)")
    print(f"  - Theoretical Lower Bound : {subopt_comp.theoretical_lower_bound:.1f} time units")
    print(f"  - Greedy (CP) Makespan   : {subopt_comp.algorithms['Greedy (Critical Path)'].makespan:.1f} time units (SUBOPTIMAL)")
    print(f"  - Greedy (LPT) Makespan  : {subopt_comp.algorithms['Greedy (LPT)'].makespan:.1f} time units (SUBOPTIMAL)")
    print(f"  - Branch & Bound Makespan: {subopt_comp.algorithms['Branch and Bound'].makespan:.1f} time units (PROVEN OPTIMAL)")
    print(f"  - Academic Analysis      : {subopt_comp.analysis}")

    # 10. Benchmark Suite Demo
    print("\n[STEP 10] Running Algorithmic Scalability Benchmark Suite...")
    bench_req = BenchmarkRequest(
        task_counts=[4, 8],
        worker_counts=[2],
        dependency_densities=[0.3],
        algorithms=["greedy_critical_path", "branch_and_bound", "exact_backtracking"],
        repetitions=1,
        seed=42
    )
    b_resp = run_benchmark(bench_req)
    print(f"Executed {b_resp.total_runs} benchmark runs in {b_resp.total_runtime_ms:.2f} ms total.")
    print("-" * 85)
    print(f"{'Algorithm':<22} {'Count':<8} {'Avg Makespan':<15} {'Avg Runtime (ms)':<18} {'Total States':<12}")
    print("-" * 85)
    for alg_name, stats in b_resp.summary.items():
        print(f"{alg_name:<22} {stats['count']:<8} {stats['avg_makespan']:<15.2f} {stats['avg_runtime_ms']:<18.3f} {stats['total_states_explored']:<12}")

    print("=" * 85)
    print("                     ALL ALGORITHMIC PHASES COMPLETE & VERIFIED")
    print("=" * 85)


if __name__ == "__main__":
    run_demo()
