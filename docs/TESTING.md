# Testing & Verification Guide

## 1. Test Suite Overview

The project features **36 automated unit and integration tests** implemented with `pytest`, covering all algorithmic modules, graph models, edge cases, scheduling constraints, and REST API endpoints.

All tests can be executed with a single command:
```bash
python -m pytest backend/tests -v
```

---

## 2. Test File Breakdown

| Test File | Tests | Focus Area |
| :--- | :---: | :--- |
| `backend/tests/test_validation.py` | 3 | Static DAG schema invariants, duplicate task IDs, missing dependencies, self-dependencies |
| `backend/tests/test_cycle_detection.py` | 2 | 3-state DFS cycle detection, acyclic graph validation |
| `backend/tests/test_topological.py` | 3 | Kahn's algorithm on chain, independent parallel, and diamond DAGs |
| `backend/tests/test_critical_path.py` | 2 | Dynamic Programming forward/reverse passes, slack calculation, critical path reconstruction |
| `backend/tests/test_greedy_scheduler.py` | 6 | Event-driven simulation, non-overlapping worker execution, precedence compliance, priority policies (CP, LPT, SPT), simultaneous completions, empty graphs |
| `backend/tests/test_exact_schedulers.py` | 4 | Backtracking vs Branch & Bound matching optimal makespans, state pruning effectiveness, Graham anomaly verification (Greedy 10.0 vs BnB 9.0), search limit termination |
| `backend/tests/test_comparison_and_benchmarks.py` | 4 | Multi-algorithm comparison service, random DAG generator validity, seed reproducibility, benchmark engine execution |
| `backend/tests/test_api.py` | 4 | FastAPI Phase 1 endpoints (`/`, `/workflow/validate`, `/workflow/topological-sort`, `/workflow/critical-path`) |
| `backend/tests/test_scheduling_api.py` | 8 | FastAPI Phase 2 & 3 endpoints (`/schedule/greedy`, `/schedule/backtrack`, `/schedule/branch-and-bound`, `/schedule/compare`, `/workflow/random`, `/benchmark/run`, `/sample-workflows`, `/sample-workflows/{filename}`) |

**Total:** 36 passing tests.

---

## 3. Key Algorithmic Invariants Verified

### A. Precedence Constraints
- $\forall (u, v) \in E: \text{Start}(v) \ge \text{Finish}(u)$.
- Verified in `test_precedence_constraints_respected`: No successor task ever begins execution before all predecessor tasks have reached their completion timestamp.

### B. Worker Capacity Constraints
- For any worker $w$ and any pair of scheduled tasks $i, j$ on $w$:
  $$[S_i, C_i) \cap [S_j, C_j) = \emptyset$$
- Verified in `test_worker_never_executes_two_tasks_simultaneously`: Confirms that each worker's assigned tasks are strictly sequential without overlapping intervals.

### C. Exact Solvers Agreement
- Exhaustive Backtracking and Branch & Bound explore different search trees due to lower-bound pruning, but **must produce identical optimal makespans**.
- Verified in `test_backtracking_and_bnb_match_on_small_instance`.

### D. Lower-Bound Pruning Efficiency
- Branch & Bound must explore $\le$ states than Backtracking on identical graphs.
- Verified in `test_branch_and_bound_pruning_effectiveness`.

### E. Graham's Anomaly (Greedy Suboptimality)
- On `sample_data/greedy_suboptimal.json` (2 workers):
  - Greedy (CP) produces $C_{\max} = 10.0$.
  - Branch & Bound achieves $C_{\max}^* = 9.0$ (100% worker utilization, 0 idle time).
- Verified in `test_greedy_suboptimal_case_proven`.

### F. Synthetic DAG Generation & Reproducibility
- Synthetic workflows generated with `generate_random_dag()` are guaranteed to be acyclic.
- Fixed random seeds produce bit-for-bit identical task sets and edge graphs.
- Verified in `test_random_dag_is_valid_dag` and `test_random_dag_seed_reproducibility`.

---

## 4. Frontend Build Verification

The React + Vite frontend was verified with:
```bash
cd frontend
npm run build
```
Result:
- **Modules transformed:** 1,939
- **Build time:** 610 ms
- **Output:** Clean bundle in `frontend/dist/` with zero errors or warnings.
