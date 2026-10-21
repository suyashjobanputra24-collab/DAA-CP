# Professor Demonstration Guide & Viva Questions

This document provides a guided walkthrough for demonstrating the **AI Agent Workflow Scheduler** in an academic evaluation or viva presentation, followed by 10 common viva questions with rigorous technical answers.

---

## 1. Quick Demonstration Commands

### Option A: Complete Terminal CLI Demonstration (Recommended for instant viva demo)
```bash
python backend/demo.py
```
This runs the automated 10-step walkthrough covering:
1. Sample Workflow Loading (`sample_data/research_workflow.json`)
2. DAG Validation & Invariant Checks
3. Graph Engine Construction (Adjacency & Indegrees)
4. DFS 3-State Cycle Detection
5. Kahn's Topological Sort $O(V + E)$
6. Dynamic Programming Forward & Reverse Passes (ES, EF, LS, LF, Slack)
7. Event-Driven Greedy List Scheduling
8. Branch & Bound Exact Optimization
9. Graham's List Scheduling Anomaly Demonstration (Greedy 10.0 vs BnB Optimal 9.0)
10. Scalability Benchmark Suite

### Option B: Interactive Full-Stack Web GUI
```bash
# Terminal 1: Start FastAPI REST Backend
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

# Terminal 2: Start React Frontend
cd frontend
npm run dev
```
Open **`http://localhost:5173/`** in your browser to interact with the 8 tabs:
- **Dashboard**: KPI summary cards.
- **Workflow Builder**: Live task editor, sample loader, and worker capacity adjuster.
- **DAG Explorer**: Interactive SVG DAG with topological rank layering and glowing critical path.
- **Critical Path**: Dynamic Programming table (ES, EF, LS, LF, Slack).
- **Gantt / Schedule**: Real visual timeline showing worker lanes ($W_1, W_2$) and task intervals.
- **Comparison**: Side-by-side metrics and makespan bars comparing Greedy, Backtracking, and Branch & Bound.
- **Benchmark Lab**: Real-time scalability tests with CSV/JSON export.
- **DAA Algorithms**: Academic reference and complexity proofs.

---

## 2. Walkthrough Script for Evaluators

### Step 1: Explain the DAA Formulation
> "In multi-agent systems, agents execute tasks with dependencies. In DAA, this is modeled as **$P \mid prec \mid C_{\max}$** — scheduling $V$ tasks with precedence constraints $E$ on $m$ identical workers to minimize makespan $C_{\max}$."

### Step 2: Demonstrate the Research Agent Workflow
Show `sample_data/research_workflow.json` with 2 workers:
- **$T_1$ (Search Web, 5s)**
- **$T_2$ (Read Papers, 8s)**
- **$T_3$ (Analyze, 10s, depends on $T_1, T_2$)**
- **$T_4$ (Generate Report, 7s, depends on $T_3$)**
- **$T_5$ (Review, 5s, depends on $T_4$)**

Point out the DP Critical Path results:
- **Precedence Lower Bound:** $30.0$ time units.
- **Critical Path:** $T_2 \to T_3 \to T_4 \to T_5$ ($8 + 10 + 7 + 5 = 30$).
- **$T_1$ Slack:** $3.0$ units ($ES = 0, EF = 5, LS = 3, LF = 8$).

### Step 3: Demonstrate Graham's List Scheduling Anomaly
Load `sample_data/greedy_suboptimal.json` and run Algorithm Comparison:
- **Greedy List Scheduling (Critical Path priority)** yields $C_{\max} = 10.0$.
- **Branch & Bound** discovers the provable global optimum $C_{\max}^* = 9.0$ with 100% worker utilization.
- Explain: *"This demonstrates Graham's List Scheduling anomaly: a greedy local choice (choosing task $C_1$ with bottom-level 6 over $B_2$ with bottom-level 4 at $t = 2.0$) delays worker $W_1$ and causes a suboptimal schedule."*

### Step 4: Demonstrate Branch & Bound Pruning
Compare states explored:
- On small workflows, exhaustive Backtracking explores hundreds or thousands of states.
- Branch & Bound, armed with the combined lower bound $LB = \max(LB_{\text{prec}}, LB_{\text{workload}})$, prunes large subtrees and discovers the optimum in a fraction of the states and time.

---

## 3. Likely Viva Questions & Technical Answers

### Q1: What is the difference between Critical Path duration and the makespan of a schedule with limited workers?
**Answer:**  
The **Critical Path duration** is a purely structural property of the DAG, representing the longest dependency chain from any source to any sink. It is the absolute theoretical lower bound assuming an **unlimited worker pool** ($m \to \infty$).  
In contrast, the **makespan ($C_{\max}$)** of a schedule accounts for both precedence constraints AND worker capacity ($m$). When $m < |V|$, tasks that are ready in parallel must queue for available workers (resource contention). Therefore:
$$C_{\max}^* \ge \max \left( \text{Critical\_Path\_Duration}, \left\lceil \frac{\sum_{v \in V} d(v)}{m} \right\rceil \right)$$

---

### Q2: Why is scheduling on identical parallel machines with precedence constraints ($P \mid prec \mid C_{\max}$) NP-hard?
**Answer:**  
J.D. Ullman (1975) showed that $P \mid prec \mid C_{\max}$ is NP-hard in the strong sense by reduction from 3-Partition and Clique. Even for $m = 2$ workers with task durations in $\{1, 2\}$, or for general $m$ with unit durations ($p_j = 1$), determining whether a schedule of length $\le K$ exists is NP-complete.

---

### Q3: How does Kahn's algorithm detect directed cycles?
**Answer:**  
Kahn's algorithm maintains an in-degree map for all vertices. Vertices with in-degree 0 are placed in a queue. In each step, a vertex $u$ is removed from the queue and added to the topological ordering, and the in-degrees of all its successors $v$ are decremented. If a cycle exists, the vertices within the cycle always have an in-degree of at least 1 and can never enter the queue. If the total number of vertices in the final topological ordering is strictly less than $|V|$, a cycle is definitively detected.

---

### Q4: What lower bounds are used in your Branch and Bound implementation?
**Answer:**  
We implement two mathematically sound lower bounds at any search state $S$ at timestamp $t$:
1. **Precedence Lower Bound ($LB_{\text{prec}}$):** Computes the maximum projected chain completion time across all running tasks ($F(u) + b(u) - d(u)$) and unstarted tasks ($ES_{\text{est}}(v) + b(v)$) using their bottom-levels $b(v)$.
2. **Workload / Capacity Lower Bound ($LB_{\text{workload}}$):** Sums the committed worker availability timestamps $A(w)$ and remaining unstarted task durations, divided by $m$:
   $$LB_{\text{workload}} = \frac{\sum_{w=1}^m A(w) + \sum_{u \in \text{unstarted}} d(u)}{m}$$
3. **Pruning Condition:** If $\max(LB_{\text{prec}}, LB_{\text{workload}}) \ge \text{Incumbent}$, the entire subtree is pruned.

---

### Q5: What is Graham's List Scheduling anomaly? Can adding more workers increase makespan?
**Answer:**  
Yes! Graham (1966) discovered that for list scheduling heuristics on parallel processors with precedence constraints, counterintuitive anomalies occur:
- Adding more processors,
- Shortening individual task durations, or
- Removing dependency edges  
can all lead to an **increase** in the resulting schedule makespan. This occurs because greedy local dispatching changes the relative completion timing of predecessors, which can delay the start of a critical bottleneck task.

---

### Q6: Why is event-driven simulation preferred over fixed time-step discretization?
**Answer:**  
In fixed time-step discretization (e.g. stepping $\Delta t = 0.1$ or $1.0$), simulation runtime scales with the magnitude of task durations ($O(C_{\max} / \Delta t)$), introducing rounding errors or missing optimal non-integer transition points.  
**Event-driven simulation** advances the clock directly to the next scheduled task completion event ($t_{\text{next}} = \min_{u \in \text{running}} F(u)$). This guarantees exact floating-point precision, correctly handles arbitrary task durations, processes simultaneous completions in $O(1)$ batch updates, and executes in $O(V \log V)$ time regardless of the makespan scale.

---

### Q7: Why are active schedules sufficient to guarantee global optimality in exact search?
**Answer:**  
Giffler & Thompson (1960) proved that for any regular performance measure (including makespan $C_{\max}$), the set of **active schedules** is a dominant set. An active schedule is one where no operation can be started earlier without delaying another operation or violating precedence. Because at least one active schedule is guaranteed to be optimal, our state-space search explores all valid assignments of ready tasks to idle workers and intentional waiting branches, guaranteeing an exact global optimum without exploring arbitrary, non-dominant infinite schedules.

---

### Q8: What is the role of the incumbent in Branch and Bound?
**Answer:**  
The incumbent represents the best feasible makespan found so far. In our implementation, we warm-start the incumbent using the makespan produced by the Greedy List Scheduler. If the Greedy solution happens to equal the root theoretical lower bound, optimality is proven instantly in 1 state ($O(1)$ search). Otherwise, a tight upper bound enables immediate aggressive pruning of suboptimal branches right from the root of the search tree.

---

### Q9: What priority queue policies did you implement for Greedy List Scheduling?
**Answer:**  
We implemented four configurable policies using Python's `heapq`:
1. **Critical Path (Bottom-Level):** Prioritizes tasks with the longest directed path to a terminal node ($b(u) = d(u) + \max_{v \in \text{succs}} b(v)$), with minimum slack as secondary key.
2. **LPT (Longest Processing Time):** Heavier tasks first.
3. **SPT (Shortest Processing Time):** Lighter tasks first.
4. **FIFO / Topological:** Strict topological rank order.  
All policies break ties deterministically by `task_id` ascending, ensuring scientific reproducibility.

---

### Q10: How do you prevent exponential explosion during automated benchmarking?
**Answer:**  
Because exact backtracking has worst-case time complexity $O(m^V)$, running exact solvers on large random DAGs ($V > 14$) could take prohibitive time. Our Benchmark Engine implements:
1. **Adaptive State Bounds:** For $V > 14$, exact solvers are capped at 3,000 to 5,000 states.
2. **Wall-Clock Timeouts:** Search terminates after 1.5s to 2.0s per instance.
3. **Honest Status Reporting:** The engine records `SEARCH_LIMIT_REACHED` and sets `optimality_proven = False`, never claiming unproven optimality.
