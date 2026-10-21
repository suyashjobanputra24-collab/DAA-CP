# DAA Algorithms & Mathematical Reference

## 1. Problem Classification & Complexity

Modern AI agent architectures (e.g. multi-step research pipelines, iterative code synthesis, review workflows) execute complex workflows structured as Directed Acyclic Graphs (DAGs). Scheduling these tasks across limited agent workers is formalized in Graham's scheduling taxonomy as:

$$\mathbf{P \mid prec \mid C_{\max}}$$

- **$P$**: $m$ identical parallel processors / agent workers ($W_1, W_2, \dots, W_m$).
- **$prec$**: General precedence constraints defined by a Directed Acyclic Graph $G = (V, E)$.
- **$C_{\max}$**: Makespan minimization, where $C_{\max} = \max_{v \in V} C(v)$ and $C(v) = S(v) + d(v)$.

### NP-Hardness Proof (Ullman 1975)
J.D. Ullman (1975) proved that $P \mid prec \mid C_{\max}$ is **NP-hard in the strong sense**, even when restricted to:
1. $m = 2$ workers and all durations $d(v) \in \{1, 2\}$, or
2. Arbitrary $m$ workers with unit execution times ($p_j = 1$).

Consequently, no polynomial-time exact algorithm exists unless $\mathcal{P} = \mathcal{NP}$.

---

## 2. Dynamic Programming Critical Path Method (CPM)

### Mathematical Formulation
The precedence lower bound ($C_{\max}^* \ge CP$) assumes an unconstrained worker pool ($m \to \infty$).
Computed via two Dynamic Programming sweeps over a valid topological ordering:

#### A. Forward Pass — Earliest Start (ES) and Earliest Finish (EF)
$$\text{ES}(u) = \begin{cases} 0 & \text{if } \text{preds}(u) = \emptyset \\ \max_{p \in \text{preds}(u)} \text{EF}(p) & \text{otherwise} \end{cases}$$
$$\text{EF}(u) = \text{ES}(u) + d(u)$$
$$\text{Project Duration } C_{\max}^{\text{prec}} = \max_{u \in V} \text{EF}(u)$$

#### B. Reverse Pass — Latest Finish (LF) and Latest Start (LS)
$$\text{LF}(u) = \begin{cases} C_{\max}^{\text{prec}} & \text{if } \text{succs}(u) = \emptyset \\ \min_{s \in \text{succs}(u)} \text{LS}(s) & \text{otherwise} \end{cases}$$
$$\text{LS}(u) = \text{LF}(u) - d(u)$$
$$\text{Total Slack / Float } \text{Slack}(u) = \text{LS}(u) - \text{ES}(u) = \text{LF}(u) - \text{EF}(u)$$

#### C. Critical Path Identification
A task $u$ is **critical** iff $\text{Slack}(u) = 0$.
The **Critical Path** is the longest directed path from a source to a sink along zero-slack edges:
$$\sum_{v \in \text{Critical Path}} d(v) = C_{\max}^{\text{prec}}$$

- **Time Complexity:** $O(V + E)$
- **Space Complexity:** $O(V)$

---

## 3. Event-Driven Greedy List Scheduler

### Algorithm Description
At each simulation epoch $t$, when workers are idle and tasks are ready (all predecessors completed):
1. Ready tasks are placed into a Priority Queue (Python `heapq`).
2. Highest priority tasks are popped and assigned to canonical lowest-index idle workers.
3. Clock jumps directly to the earliest task completion event rather than incrementing $t$ unit-by-unit.
4. Simultaneous completions at the exact same timestamp are processed in batch.

### Supported Priority Policies
1. **`CRITICAL_PATH` (Bottom-Level)**:
   $$b(u) = d(u) + \max(\{b(v) : v \in \text{succs}(u)\} \cup \{0\})$$
   Tasks with greatest remaining path to sink are dispatched first. Secondary tie-breaker is minimum slack; tertiary tie-breaker is deterministic `task_id` ascending.
2. **`LPT` (Longest Processing Time)**: Prioritizes heavier tasks.
3. **`SPT` (Shortest Processing Time)**: Prioritizes smaller tasks.
4. **`FIFO` (Topological Order)**: Dispatches in topological sequence.

### Graham's List Scheduling Bound & Anomaly
Graham (1966) proved that any list schedule satisfies:
$$\frac{C_{\text{list}}}{C_{\text{opt}}} \le 2 - \frac{1}{m}$$
**Graham's Anomaly:** Greedy local decisions can lead to suboptimal global schedules.
Example instance in `sample_data/greedy_suboptimal.json`:
- Greedy (CP) Makespan: **10.0 time units**
- Branch & Bound Optimal: **9.0 time units** (11.1% improvement).

---

## 4. Exact Backtracking & Active Schedule Space

### Theoretical Justification
Giffler & Thompson (1960) established that the set of **active schedules** constitutes a dominant set for any regular measure of performance, including $C_{\max}$. An active schedule is one in which no task can be started earlier without delaying another task.

Our state-space search explores:
1. Assigning available ready tasks to idle workers at time $t$.
2. Intentionally waiting (advancing time to the next task completion event without assigning a currently available task).

This guarantees that the global optimum $C_{\max}^*$ is never pruned by greedy heuristics.
To avoid exploring symmetrical permutations of identical workers, assignments are fixed to the lowest-indexed idle worker.

---

## 5. Branch and Bound with Lower-Bound Pruning

### Mathematical Lower Bound Derivations

At partial schedule state $S$ at timestamp $t$, with running tasks $\mathcal{R}$ and unstarted tasks $\mathcal{U}$:

#### 1. Precedence Lower Bound ($LB_{\text{prec}}$)
For each running task $u \in \mathcal{R}$ with completion time $F(u)$, and each unstarted task $v \in \mathcal{U}$:
$$LB_{\text{prec}} = \max \left( \max_{u \in \mathcal{R}} [F(u) + b(u) - d(u)], \max_{v \in \mathcal{U}} [ES_{\text{est}}(v) + b(v)] \right)$$
where $ES_{\text{est}}(v) = \max(\{t\} \cup \{F(p) : p \in \text{preds}(v) \cap \mathcal{R}\})$.

#### 2. Workload / Capacity Lower Bound ($LB_{\text{workload}}$)
Let $A(w)$ be the earliest availability time of worker $w \in \{1, \dots, m\}$ ($A(w) = t$ if idle, or $F(u)$ if running task $u$).
The total remaining computational work distributed across $m$ identical workers yields:
$$LB_{\text{workload}} = \frac{\sum_{w=1}^m A(w) + \sum_{u \in \mathcal{U}} d(u)}{m}$$

#### 3. Pruning Rule
$$LB(S) = \max \left( LB_{\text{prec}}, LB_{\text{workload}}, \max_{u \in \mathcal{R}} F(u) \right)$$
$$\text{If } LB(S) \ge \text{Incumbent} - 10^{-9} \implies \text{PRUNE BRANCH}$$

The incumbent is initialized with the Greedy schedule makespan, providing a strong initial upper bound that immediately prunes uncompetitive search subtrees.

---

## 6. Asymptotic Complexity Summary

| Algorithm | Paradigm | Time Complexity | Space Complexity | Optimality Guarantee |
| :--- | :--- | :--- | :--- | :--- |
| **Kahn's Topological Sort** | Graph Traversal | $O(V + E)$ | $O(V)$ | Linear Ordering |
| **DFS Cycle Detection** | DFS 3-State | $O(V + E)$ | $O(V)$ | Exact Cycle Flag |
| **Critical Path (CPM)** | Dynamic Programming | $O(V + E)$ | $O(V)$ | Precedence LB ($m \to \infty$) |
| **Greedy List Scheduler** | Priority Heap / Event Simulation | $O(E + V \log V)$ | $O(V + m)$ | Heuristic ($\le 2 - 1/m$) |
| **Exact Backtracking** | State-Space DFS | $O(m^V)$ worst-case | $O(V + m)$ recursion depth | Guaranteed Global Optimum |
| **Branch and Bound** | Pruned State-Space | $O(m^V)$ worst, $O(V \log V)$ best | $O(V + m)$ recursion depth | Guaranteed Global Optimum |
