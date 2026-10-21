# AI Agent Workflow Scheduler

> **3rd Year Design and Analysis of Algorithms (DAA) Capstone Project**  
> **Comprehensive Multi-Worker Scheduling Engine: Graph DAG Engine, Kahn's Topological Sort, Dynamic Programming Critical Path Analysis, Event-Driven Greedy List Scheduling, Exact Backtracking, and Branch & Bound with Lower-Bound Pruning.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-2.0.0-emerald.svg)](https://fastapi.tiangolo.com)
[![Pytest](https://img.shields.io/badge/Tests-36%20Passing-brightgreen.svg)](https://pytest.org)
[![React](https://img.shields.io/badge/React-19%20%7C%20Vite-indigo.svg)](https://vitejs.dev)
[![License](https://img.shields.io/badge/License-Academic%20DAA-violet.svg)](#)

---

## 1. Project Overview & Problem Statement

Modern autonomous multi-agent pipelines (such as web research agents, code generation assistants, data preprocessors, and review bots) execute interconnected task DAGs. Determining an optimal execution schedule across a finite pool of agent workers is a fundamental problem in the **Design and Analysis of Algorithms (DAA)**.

In Graham's scheduling taxonomy, this problem is classified as:

$$\mathbf{P \mid prec \mid C_{\max}}$$

Given:
1. A set of tasks $V$ with strictly positive execution durations $d(v) > 0$.
2. Precedence dependencies $E$ represented as a Directed Acyclic Graph (DAG) $G = (V, E)$.
3. A finite number of identical parallel execution workers $W \ge 1$.

**Project Objective:**
- Validate graph structure and detect directed cycles in $O(V + E)$ time.
- Compute topological execution orders using Kahn's algorithm in $O(V + E)$ time.
- Calculate the precedence lower bound (Earliest/Latest Start/Finish, Slack, Critical Path) using Dynamic Programming forward/reverse passes.
- Schedule tasks across $W$ workers using an event-driven Greedy List Scheduler with priority min-heaps.
- Solve small-to-medium workflows to mathematical optimality using Exact Backtracking over the active schedule space.
- Accelerate exact search using Branch & Bound with mathematically valid precedence and workload lower-bound pruning.
- Empirically demonstrate Graham's List Scheduling Anomaly (where Greedy produces suboptimal makespans compared to Branch & Bound).
- Provide an interactive, responsive React + Vite web dashboard and automated scalability benchmark lab.

---

## 2. Key Algorithmic Implementations

### A. Graph Invariant Validation & Cycle Detection
- **Adjacency & Indegree Engine:** Maintains forward and reverse edge lists for $O(1)$ queries.
- **DFS 3-State Cycle Detection:** Uses vertex coloring (`WHITE = 0`, `GRAY = 1`, `BLACK = 2`) to identify back-edges in $O(V + E)$ time and $O(V)$ stack space.
- **Kahn's Topological Sort:** Queue-based in-degree reduction algorithm in $O(V + E)$ time.

### B. Dynamic Programming Critical Path Method (CPM)
- **Forward Pass:** Computes Earliest Start ($\text{ES}$) and Earliest Finish ($\text{EF}$):
  $$\text{ES}(u) = \max_{p \in \text{preds}(u)} \text{EF}(p), \quad \text{EF}(u) = \text{ES}(u) + d(u)$$
- **Reverse Pass:** Computes Latest Finish ($\text{LF}$) and Latest Start ($\text{LS}$):
  $$\text{LF}(u) = \min_{s \in \text{succs}(u)} \text{LS}(s), \quad \text{LS}(u) = \text{LF}(u) - d(u)$$
- **Slack & Bottleneck Identification:** $\text{Slack}(u) = \text{LS}(u) - \text{ES}(u)$. Tasks with zero slack lie on the Critical Path.
- **Precedence Lower Bound:** Minimal completion time assuming unlimited workers ($W \to \infty$).

### C. Event-Driven Greedy List Scheduler
- Clock advances directly to the next earliest task completion event ($t_{\text{next}}$) rather than arbitrary discretization steps.
- Handles simultaneous task completions in batch.
- Priority queue implemented using Python's `heapq` supporting:
  - `CRITICAL_PATH`: Bottom-level $b(u) = d(u) + \max_{v \in \text{succs}} b(v)$ descending, then slack ascending.
  - `LPT`: Longest Processing Time first.
  - `SPT`: Shortest Processing Time first.
  - `FIFO`: Strict topological order.
  - Deterministic tie-breaking by `task_id` ascending.
- Records per-worker busy time, idle intervals, and utilization rate $\frac{\sum d(v)}{W \cdot C_{\max}}$.

### D. Exact Backtracking Scheduler
- Explores the space of active schedules (Giffler & Thompson 1960).
- Branches over valid task-to-worker assignments and non-delay wait decisions.
- Eliminates identical worker permutations by assigning to the canonical lowest-indexed idle worker.
- Enforces strict search limits (`max_states`, `time_limit_sec`) and reports proof status honestly.

### E. Branch & Bound with Lower-Bound Pruning
- Warm-starts incumbent feasible solution using Greedy List Scheduling.
- Implements two mathematically valid lower bounds at each state:
  1. **Precedence Lower Bound ($LB_{\text{prec}}$):** Chain projection of running and unstarted tasks via bottom-levels.
  2. **Workload / Capacity Lower Bound ($LB_{\text{workload}}$):** Total committed and remaining duration divided by $W$.
- Prunes any branch where $\max(LB_{\text{prec}}, LB_{\text{workload}}) \ge \text{Incumbent}$.

---

## 3. Important Theoretical Distinction

> [!IMPORTANT]
> **Precedence Lower Bound vs Limited-Worker Makespan:**  
> The Critical Path duration represents the theoretical completion time under **unlimited workers** ($W \to \infty$).  
> Under finite workers $W$, optimal makespan is bounded by:  
> $$C_{\max}^* \ge \max \left( \text{Critical\_Path\_Duration}, \left\lceil \frac{\sum_{v \in V} d(v)}{W} \right\rceil \right)$$

---

## 4. Graham's List Scheduling Anomaly Demonstration

In `sample_data/greedy_suboptimal.json` ($W = 2$ workers):
- **Greedy List Scheduler (Critical Path Priority):** Produces makespan **$10.0$ time units**.
- **Greedy List Scheduler (LPT Priority):** Produces makespan **$12.0$ time units**.
- **Branch & Bound / Exact Backtracking:** Discovers the global optimal makespan **$9.0$ time units** (100% worker utilization, 0 idle time).

This mathematically demonstrates Graham's List Scheduling anomaly: greedy local heuristic decisions do not guarantee global optimality. Branch & Bound pruned 25 subtrees, evaluating only 56 states compared to 4,603 states in exhaustive Backtracking (an 82x reduction).

---

## 5. System Architecture & Folder Structure

```
AI_Agent_Workflow_Scheduler/
├── backend/
│   ├── main.py                         # FastAPI REST API application & endpoints
│   ├── models.py                       # Pydantic schemas (Tasks, Workflows, Schedules, Benchmarks)
│   ├── demo.py                         # 10-Step comprehensive terminal demonstration script
│   ├── requirements.txt                # Python backend dependencies
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── dag.py                      # Core DAG representation (adj list, pred list, indegrees)
│   │   └── validator.py                # Structural validator & 3-state DFS cycle detector
│   ├── algorithms/
│   │   ├── __init__.py
│   │   ├── topological_sort.py         # Kahn's Topological Sort O(V + E)
│   │   ├── cycle_detection.py          # DFS 3-State Cycle Detection O(V + E)
│   │   ├── critical_path.py            # DP Critical Path & Slack Analysis O(V + E)
│   │   ├── greedy_scheduler.py         # Event-driven Greedy List Scheduler with priority heap
│   │   ├── exact_backtracking.py       # Exhaustive active-schedule Backtracking solver
│   │   ├── branch_and_bound.py         # Branch & Bound with precedence & workload lower bounds
│   │   ├── comparison.py               # Multi-algorithm comparison service
│   │   ├── random_dag.py               # Synthetic acyclic DAG generator with seed control
│   │   └── benchmark.py                # Automated scalability benchmark runner
│   └── tests/
│       ├── __init__.py
│       ├── test_validation.py          # Pytest: Duplicate IDs, missing deps, self-deps
│       ├── test_cycle_detection.py     # Pytest: DFS cycle detection
│       ├── test_topological.py         # Pytest: Kahn's algorithm
│       ├── test_critical_path.py       # Pytest: DP forward/reverse passes & slack
│       ├── test_greedy_scheduler.py    # Pytest: Greedy simulation & priority policies
│       ├── test_exact_schedulers.py    # Pytest: Backtrack vs BnB, pruning, Graham anomaly
│       ├── test_comparison_and_benchmarks.py # Pytest: Comparison, random DAGs, benchmarks
│       ├── test_api.py                 # Pytest: Phase 1 REST endpoints
│       └── test_scheduling_api.py      # Pytest: Scheduling, comparison, benchmark REST endpoints
├── frontend/                           # React + Vite Interactive Web Application
│   ├── src/
│   │   ├── main.jsx                    # React entry point
│   │   ├── App.jsx                     # Root application container & tab router
│   │   ├── api.js                      # Backend REST API client
│   │   ├── index.css                   # Obsidian dark theme & design system
│   │   └── components/
│   │       ├── Navbar.jsx              # Navigation header with backend status indicator
│   │       ├── DashboardView.jsx       # KPI cards & execution summary
│   │       ├── WorkflowBuilderView.jsx # Visual task editor, preset loader, JSON modal
│   │       ├── DagExplorerView.jsx     # Interactive SVG DAG graph with rank layering
│   │       ├── CriticalPathView.jsx    # DP table, slack analysis, mathematical formulas
│   │       ├── GanttView.jsx           # Real worker timeline lanes (W1, W2) & task intervals
│   │       ├── ComparisonView.jsx      # Side-by-side metrics table & makespan bars
│   │       ├── BenchmarkView.jsx       # Empirical scalability lab with CSV/JSON export
│   │       └── AboutAlgorithmsView.jsx # Academic reference, theorems & complexity proofs
│   ├── package.json
│   └── vite.config.js
├── sample_data/
│   ├── research_workflow.json          # Primary 5-task Research Agent workflow (CP = 30s)
│   ├── chain_workflow.json             # Sequential pipeline chain
│   ├── parallel_workflow.json          # Independent batch parallel tasks
│   ├── diamond_workflow.json           # Classic diamond DAG
│   ├── contention_workflow.json        # High worker contention fan-out
│   ├── multiple_critical_paths.json    # DAG with multiple zero-slack paths
│   ├── greedy_suboptimal.json          # Verified Graham anomaly instance (Greedy 10s vs BnB 9s)
│   └── cyclic_workflow.json            # Cyclic graph for testing rejection
├── docs/
│   ├── ALGORITHMS.md                   # Full mathematical formulations & proofs
│   ├── TESTING.md                      # Comprehensive test suite breakdown
│   └── DEMO_GUIDE.md                   # Step-by-step evaluator demo & 10 viva Q&As
└── README.md
```

---

## 6. Installation & Setup Instructions

### Prerequisites
- Python 3.10+ installed
- Node.js 18+ and npm installed

### Step 1: Install Backend Dependencies
```bash
pip install -r backend/requirements.txt
```

### Step 2: Install Frontend Dependencies
```bash
cd frontend
npm install
cd ..
```

---

## 7. Running the Project

### Option A: Run the Complete Terminal CLI Demonstration
```bash
python backend/demo.py
```

### Option B: Run Automated Pytest Suite (36 Tests)
```bash
python -m pytest backend/tests -v
```

### Option C: Start the Full-Stack Application
1. **Start FastAPI Backend (Port 8000):**
   ```bash
   python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
   ```
   Interactive Swagger documentation: 👉 **`http://127.0.0.1:8000/docs`**

2. **Start React Frontend (Port 5173):**
   ```bash
   cd frontend
   npm run dev
   ```
   Open in your browser: 👉 **`http://localhost:5173/`**

---

## 8. REST API Reference

| Method | Endpoint | Description | Request / Query |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | System health check & metadata | None |
| `POST` | `/workflow/validate` | Validates DAG invariants & checks cycles | `Workflow` |
| `POST` | `/workflow/topological-sort` | Computes Kahn's topological sort | `Workflow` |
| `POST` | `/workflow/critical-path` | Dynamic Programming Critical Path & Slack | `Workflow` |
| `POST` | `/schedule/greedy` | Event-driven Greedy List Scheduling | `ScheduleRequest` |
| `POST` | `/schedule/backtrack` | Exact Backtracking Scheduler | `ScheduleRequest` |
| `POST` | `/schedule/branch-and-bound` | Branch & Bound with Lower-Bound Pruning | `ScheduleRequest` |
| `POST` | `/schedule/compare` | Multi-algorithm comparative evaluation | `ScheduleRequest` |
| `POST` | `/workflow/random` | Generates synthetic reproducible DAG | `RandomWorkflowRequest` |
| `POST` | `/benchmark/run` | Executes automated benchmark suite | `BenchmarkRequest` |
| `GET` | `/sample-workflows` | Lists available sample workflow files | None |
| `GET` | `/sample-workflows/{name}` | Loads specific sample workflow JSON | Filename path param |

---

## 9. Primary Demonstration Instance (Research Agent Workflow)

Given `sample_data/research_workflow.json` with $W = 2$ workers:

| Task ID | Task Name | Duration | ES | EF | LS | LF | Slack | Critical? |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **T1** | Search Web | 5.0 | 0.0 | 5.0 | 3.0 | 8.0 | 3.0 | No |
| **T2** | Read Papers | 8.0 | 0.0 | 8.0 | 0.0 | 8.0 | 0.0 | **YES** |
| **T3** | Analyze | 10.0 | 8.0 | 18.0 | 8.0 | 18.0 | 0.0 | **YES** |
| **T4** | Generate Report | 7.0 | 18.0 | 25.0 | 18.0 | 25.0 | 0.0 | **YES** |
| **T5** | Review | 5.0 | 25.0 | 30.0 | 25.0 | 30.0 | 0.0 | **YES** |

- **Precedence Lower Bound:** `30.0` time units
- **Critical Path:** `T2 (8s) -> T3 (10s) -> T4 (7s) -> T5 (5s)`
- **Greedy Schedule:** $W_1: [T_2: 0 \to 8, T_3: 8 \to 18, T_4: 18 \to 25, T_5: 25 \to 30]$, $W_2: [T_1: 0 \to 5]$.
- **Makespan:** `30.0` time units (Matches precedence lower bound, proven optimal).

---

## 10. Completed Features Checklist

- [x] **Phase A — Audit & Invariant Verification:** Verified all Phase 1 algorithms; fixed duplicate IDs, self-dependencies, durations, and cycle detection.
- [x] **Phase B — Event-Driven Greedy List Scheduler:** Configurable priority queue (Critical Path, LPT, SPT, FIFO), non-overlapping worker execution, simultaneous completion handling, deadlock detection.
- [x] **Phase C — Exact Backtracking:** Active-schedule search space, canonical worker assignment, configurable search limits, honest proof status reporting.
- [x] **Phase D — Branch & Bound with Lower Bounds:** Precedence chain lower bound ($LB_{\text{prec}}$), workload capacity bound ($LB_{\text{workload}}$), warm-start incumbent, aggressive subtree pruning.
- [x] **Phase E — Multi-Algorithm Comparison Service:** Side-by-side metrics, makespan bars, optimality gap analysis, Graham's anomaly evaluation.
- [x] **Phase F — FastAPI REST Integration:** 12 clean REST endpoints with Pydantic schemas, validation error handling, and Swagger UI docs.
- [x] **Phase G — React + Vite Web Application:** 8 interactive views (Dashboard, Builder, DAG Explorer, Critical Path, Gantt Timeline, Comparison, Benchmark Lab, About DAA Reference).
- [x] **Phase H — Sample Workflows Catalog:** 8 sample DAGs covering chains, parallel batches, worker contention, diamonds, multiple critical paths, cyclic error tests, and verified Graham anomaly.
- [x] **Phase I — Comprehensive Test Suite:** 36 automated `pytest` tests passing with 100% verification.
- [x] **Phase J — Academic Documentation:** Complete README, `docs/ALGORITHMS.md`, `docs/TESTING.md`, `docs/DEMO_GUIDE.md` with 10 viva questions and answers.
- [x] **Phase K — Packaging & Integration:** Clean ZIP packaging script excluding virtual environments, dependencies, secrets, and caches.
