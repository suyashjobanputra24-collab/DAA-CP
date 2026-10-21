import React from 'react';
import { BookOpen, GitFork, Clock, Zap, ShieldCheck, HelpCircle, Layers } from 'lucide-react';

export default function AboutAlgorithmsView() {
  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', maxWidth: '1100px', margin: '0 auto' }}>
      <div className="card">
        <h2 style={{ fontSize: '1.5rem', fontWeight: 800, marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <BookOpen size={22} style={{ color: 'var(--primary)' }} /> DAA Academic Algorithmic Reference
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: 1.6 }}>
          Comprehensive documentation of mathematical foundations, recurrence relations, complexity proofs, and scheduling theorems implemented in the AI Agent Workflow Scheduler project.
        </p>
      </div>

      {/* 1. DAG Engine & Graph Algorithms */}
      <div className="card">
        <h3 className="card-title" style={{ color: 'var(--cyan)', marginBottom: '0.75rem' }}>
          <GitFork size={18} /> 1. Graph Structural Algorithms (Phase 1)
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
          <div>
            <strong style={{ color: 'var(--text-primary)' }}>A. Graph Engine (Adjacency & Predecessors):</strong>
            <p>
              Workflows are modeled as a Directed Acyclic Graph $G = (V, E)$, where vertices $V$ represent tasks with positive durations $d(v) &gt; 0$, and directed edges $(u, v) \in E$ denote that task $u$ must finish before task $v$ starts.
            </p>
            <p className="mono" style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Complexity: Construction O(V + E) time, O(V + E) space.
            </p>
          </div>

          <div>
            <strong style={{ color: 'var(--text-primary)' }}>B. DFS 3-State Cycle Detection:</strong>
            <p>
              Uses vertex coloring: WHITE (0 = unvisited), GRAY (1 = currently on active recursion call stack), and BLACK (2 = fully processed). Encountering a GRAY vertex identifies a back-edge, proving a directed cycle.
            </p>
            <p className="mono" style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Complexity: O(V + E) time, O(V) recursion stack space.
            </p>
          </div>

          <div>
            <strong style={{ color: 'var(--text-primary)' }}>C. Kahn's Topological Sort:</strong>
            <p>
              Maintains an in-degree map. Initial sources (in-degree 0) are placed in a queue. Dequeuing vertex $u$ decrements in-degrees of successors $v$. When in-degree reaches 0, $v$ enters the queue. If total dequeued nodes &lt; |V|, a cycle exists.
            </p>
            <p className="mono" style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Complexity: O(V + E) time, O(V) space.
            </p>
          </div>
        </div>
      </div>

      {/* 2. Dynamic Programming Critical Path */}
      <div className="card">
        <h3 className="card-title" style={{ color: 'var(--amber)', marginBottom: '0.75rem' }}>
          <Clock size={18} /> 2. Dynamic Programming Critical Path Method (CPM)
        </h3>
        <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <p>
            Computes earliest and latest start/finish boundaries and identifies the precedence-only lower bound ($C_{max}$ under unlimited workers).
          </p>
          <div style={{ background: 'rgba(0,0,0,0.3)', padding: '1rem', borderRadius: 'var(--radius-md)', fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>
            <div>1. Forward Pass (Topological order):</div>
            <div>   ES(u) = 0 if Preds(u) is empty, else max &#123; EF(p) : p &isin; Preds(u) &#125;</div>
            <div>   EF(u) = ES(u) + d(u)</div>
            <div>   Cmax = max &#123; EF(u) : u &isin; V &#125;</div>
            <div style={{ marginTop: '0.5rem' }}>2. Reverse Pass (Reverse Topological order):</div>
            <div>   LF(u) = Cmax if Succs(u) is empty, else min &#123; LS(s) : s &isin; Succs(u) &#125;</div>
            <div>   LS(u) = LF(u) - d(u)</div>
            <div>   Total Slack(u) = LS(u) - ES(u) = LF(u) - EF(u)</div>
            <div style={{ marginTop: '0.5rem' }}>3. Critical Tasks & Path:</div>
            <div>   Task u is critical iff Slack(u) == 0. Sequence of zero-slack edges forms the Critical Path.</div>
          </div>
          <p className="mono" style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Complexity: O(V + E) time, O(V) space.
          </p>
        </div>
      </div>

      {/* 3. NP-Hardness and Graham's List Scheduling */}
      <div className="card">
        <h3 className="card-title" style={{ color: 'var(--cyan)', marginBottom: '0.75rem' }}>
          <Zap size={18} /> 3. Parallel Machine Scheduling & Graham's List Scheduling (Phase 2)
        </h3>
        <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <p>
            Under Graham's notation, our problem is denoted <strong>P | prec | Cmax</strong> (identical parallel machines with arbitrary precedence constraints to minimize makespan).
          </p>
          <p>
            <strong>NP-Hardness:</strong> J.D. Ullman (1975) proved that P | prec | Cmax is NP-hard in the strong sense, even for 2 machines with unit durations $P2 | prec, p_j = 1 | C_{max}$, or 2 machines with durations in &#123;1, 2&#125;. Hence, no polynomial-time exact algorithm exists unless P = NP.
          </p>
          <p>
            <strong>Graham's List Scheduling Heuristic (1966):</strong> Whenever a worker becomes idle, assign the highest-priority ready task. Graham proved the approximation ratio:
          </p>
          <div className="mono" style={{ background: 'rgba(0,0,0,0.3)', padding: '0.65rem 1rem', borderRadius: 'var(--radius-sm)', color: '#a5b4fc', fontSize: '0.85rem' }}>
            C_list &le; (2 - 1/m) &times; C_opt
          </div>
          <p>
            <strong>Graham's Anomaly:</strong> Increasing worker count, shortening task durations, or relaxing precedence constraints can counterintuitively <em>increase</em> the greedy list schedule length!
          </p>
        </div>
      </div>

      {/* 4. Exact Backtracking & Branch and Bound */}
      <div className="card">
        <h3 className="card-title" style={{ color: 'var(--emerald)', marginBottom: '0.75rem' }}>
          <ShieldCheck size={18} /> 4. Exact Backtracking & Branch & Bound Pruning (Phases 3 & 4)
        </h3>
        <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <p>
            <strong>Active Schedule Search Space:</strong> A schedule is active if no task can be made to start earlier without delaying another task or violating constraints. Giffler & Thompson (1960) proved that the set of active schedules is a dominant set containing at least one global optimal schedule for makespan minimization.
          </p>
          <p>
            <strong>Branch & Bound Mathematical Lower Bounds:</strong>
          </p>
          <div style={{ background: 'rgba(0,0,0,0.3)', padding: '1rem', borderRadius: 'var(--radius-md)', fontFamily: 'var(--font-mono)', fontSize: '0.8rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <div>
              <strong>1. Precedence Chain Lower Bound (LB_prec):</strong>
              <br />
              For running tasks with finish time F(u) and unstarted tasks with estimated start ES_est(u):
              <br />
              LB_prec = max( &#123; F(u) + b(u) - d(u) : u running &#125; &cup; &#123; ES_est(u) + b(u) : u unstarted &#125; )
            </div>
            <div>
              <strong>2. Workload / Capacity Lower Bound (LB_workload):</strong>
              <br />
              LB_workload = ( &sum; A(w) + &sum;_{'{'}u unstarted{'}'} d(u) ) / m
            </div>
            <div>
              <strong>3. Combined Lower Bound & Pruning Rule:</strong>
              <br />
              LB(node) = max( LB_prec, LB_workload, max_running F(u) )
              <br />
              If LB(node) &ge; Incumbent_Makespan: PRUNE SUBTREE!
            </div>
          </div>
          <p>
            By initializing the incumbent with the Greedy schedule makespan, Branch & Bound achieves orders-of-magnitude pruning compared to exhaustive Backtracking while guaranteeing mathematical optimality.
          </p>
        </div>
      </div>
    </div>
  );
}
