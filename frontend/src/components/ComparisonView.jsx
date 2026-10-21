import React from 'react';
import { BarChart3, TrendingUp, ShieldCheck, Zap, AlertTriangle, ArrowRight } from 'lucide-react';

export default function ComparisonView({
  workflow,
  comparison,
  onRunCompare,
  loading,
}) {
  const algMap = comparison?.algorithms || {};
  const bestMakespan = comparison?.best_makespan || 0;
  const theoreticalLb = comparison?.theoretical_lower_bound || 0;
  const precedenceLb = comparison?.precedence_lower_bound || 0;
  const workloadLb = comparison?.workload_lower_bound || 0;

  // Find max makespan to scale bars nicely
  const allMakespans = Object.values(algMap).map((a) => a.makespan || 0);
  const maxMakespan = Math.max(theoreticalLb, ...allMakespans, 1);

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Top Banner & Trigger */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <BarChart3 size={18} style={{ color: 'var(--violet)' }} /> Multi-Algorithm Scheduling Comparison
            </h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.825rem' }}>
              Evaluates heuristic Greedy List Scheduling vs. Exact Backtracking and Branch & Bound lower-bound pruning on the same DAG.
            </p>
          </div>

          <button className="btn btn-accent" onClick={onRunCompare} disabled={loading}>
            <TrendingUp size={15} /> Re-run Full Comparison
          </button>
        </div>
      </div>

      {/* Theoretical Lower Bounds Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem' }}>
        <div className="card" style={{ borderLeft: '4px solid var(--amber)' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
            Precedence Lower Bound
          </div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--amber)', margin: '0.3rem 0' }}>
            {precedenceLb}s
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
            Critical Path duration (assuming W &rarr; &infin;)
          </div>
        </div>

        <div className="card" style={{ borderLeft: '4px solid var(--cyan)' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
            Workload (Area) Lower Bound
          </div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--cyan)', margin: '0.3rem 0' }}>
            {workloadLb.toFixed(2)}s
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
            &sum; duration(v) / {workflow?.number_of_workers || 2} workers
          </div>
        </div>

        <div className="card" style={{ borderLeft: '4px solid var(--emerald)', background: 'rgba(16, 185, 129, 0.05)' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
            Combined Theoretical Lower Bound
          </div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--emerald)', margin: '0.3rem 0' }}>
            {theoreticalLb.toFixed(2)}s
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
            max( Precedence_LB, Workload_LB )
          </div>
        </div>
      </div>

      {/* Side-by-Side Metrics Table */}
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">Side-by-Side Algorithm Benchmark Metrics</h3>
        </div>

        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Algorithm</th>
                <th>Makespan (Cmax)</th>
                <th>Optimality Gap</th>
                <th>Execution Time</th>
                <th>States Explored</th>
                <th>States Pruned</th>
                <th>Worker Utilization</th>
                <th>Optimality Status</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(algMap).map(([name, res]) => {
                const isBest = Math.abs(res.makespan - bestMakespan) < 1e-4;
                const gap = res.makespan - bestMakespan;
                const gapPct = bestMakespan > 0 ? (gap / bestMakespan) * 100 : 0;

                return (
                  <tr key={name} style={isBest ? { background: 'rgba(16, 185, 129, 0.04)' } : {}}>
                    <td style={{ fontWeight: 700 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        {name.includes('Greedy') ? <Zap size={15} style={{ color: 'var(--cyan)' }} /> : <ShieldCheck size={15} style={{ color: 'var(--primary)' }} />}
                        {name}
                      </div>
                    </td>
                    <td className="mono" style={{ fontWeight: 800, fontSize: '1rem', color: isBest ? 'var(--emerald)' : 'var(--text-primary)' }}>
                      {res.makespan}s
                    </td>
                    <td>
                      {gap <= 0.001 ? (
                        <span className="badge badge-optimal">0.00s (0%)</span>
                      ) : (
                        <span className="badge badge-heuristic" style={{ color: 'var(--rose)', borderColor: 'rgba(244,63,94,0.4)' }}>
                          +{gap.toFixed(2)}s (+{gapPct.toFixed(1)}%)
                        </span>
                      )}
                    </td>
                    <td className="mono">{res.runtime_ms} ms</td>
                    <td className="mono">{res.states_explored !== null ? res.states_explored : '—'}</td>
                    <td className="mono" style={{ color: res.states_pruned ? 'var(--emerald)' : 'var(--text-muted)' }}>
                      {res.states_pruned !== null && res.states_pruned !== undefined ? res.states_pruned : 'N/A'}
                    </td>
                    <td className="mono">{(res.worker_utilization * 100).toFixed(1)}%</td>
                    <td>
                      <span className={`badge ${res.optimality_proven ? 'badge-optimal' : 'badge-neutral'}`}>
                        {res.status}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Visual Makespan Bar Comparison */}
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">Comparative Makespan Bar Chart (Lower is Better)</h3>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', padding: '0.5rem 0' }}>
          {/* Theoretical Lower Bound line */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{ width: '180px', fontSize: '0.8rem', color: 'var(--emerald)', fontWeight: 700 }}>
              Theoretical Lower Bound
            </div>
            <div style={{ flex: 1, position: 'relative', height: '24px' }}>
              <div
                style={{
                  position: 'absolute',
                  left: 0,
                  top: '2px',
                  bottom: '2px',
                  width: `${(theoreticalLb / maxMakespan) * 100}%`,
                  background: 'rgba(16, 185, 129, 0.25)',
                  borderRight: '3px solid var(--emerald)',
                  borderRadius: 'var(--radius-sm)',
                  display: 'flex',
                  alignItems: 'center',
                  paddingLeft: '0.5rem',
                  fontSize: '0.75rem',
                  fontFamily: 'var(--font-mono)',
                  color: 'var(--emerald)',
                  fontWeight: 700,
                }}
              >
                {theoreticalLb.toFixed(1)}s (Lower Bound)
              </div>
            </div>
          </div>

          {/* Algorithm Bars */}
          {Object.entries(algMap).map(([name, res]) => {
            const widthPct = (res.makespan / maxMakespan) * 100;
            const isBest = Math.abs(res.makespan - bestMakespan) < 1e-4;

            return (
              <div key={name} style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <div style={{ width: '180px', fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 600 }}>
                  {name}
                </div>
                <div style={{ flex: 1, position: 'relative', height: '28px' }}>
                  <div
                    style={{
                      position: 'absolute',
                      left: 0,
                      top: 0,
                      bottom: 0,
                      width: `${Math.max(widthPct, 2)}%`,
                      background: isBest
                        ? 'linear-gradient(90deg, #10b981, #059669)'
                        : 'linear-gradient(90deg, #6366f1, #4f46e5)',
                      borderRadius: 'var(--radius-sm)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '0 0.75rem',
                      fontSize: '0.8rem',
                      fontFamily: 'var(--font-mono)',
                      color: '#fff',
                      fontWeight: 700,
                      boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
                    }}
                  >
                    <span>{res.makespan}s</span>
                    <span style={{ fontSize: '0.7rem', opacity: 0.85 }}>{res.runtime_ms} ms</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Academic Analysis Commentary Card */}
      {comparison?.analysis && (
        <div
          className="card"
          style={{
            background: 'rgba(21, 28, 44, 0.95)',
            borderLeft: '4px solid var(--violet)',
          }}
        >
          <h3 className="card-title" style={{ color: 'var(--violet)', marginBottom: '0.5rem' }}>
            Academic DAA Evaluation & Graham Anomaly Findings
          </h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', lineHeight: 1.6 }}>
            {comparison.analysis}
          </p>
        </div>
      )}
    </div>
  );
}
