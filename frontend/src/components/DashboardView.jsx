import React from 'react';
import {
  Layers,
  GitFork,
  Cpu,
  Clock,
  Zap,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  TrendingUp,
} from 'lucide-react';

export default function DashboardView({
  workflow,
  validation,
  criticalPath,
  greedySchedule,
  exactSchedule,
  comparison,
  setActiveTab,
  onRunGreedy,
  onRunExact,
  onRunCompare,
  loading,
}) {
  const totalTasks = workflow?.tasks?.length || 0;
  const totalDeps = workflow?.tasks?.reduce((acc, t) => acc + (t.dependencies?.length || 0), 0) || 0;
  const numWorkers = workflow?.number_of_workers || 1;
  const cpDuration = criticalPath?.project_duration || 0;
  const greedyMakespan = greedySchedule?.makespan || null;
  const exactMakespan = exactSchedule?.makespan || null;
  const isOptimal = exactSchedule?.optimality_proven || (greedySchedule?.optimality_proven && greedyMakespan === cpDuration);

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Hero Welcome & Quick Execution Bar */}
      <div
        className="card"
        style={{
          background: 'linear-gradient(135deg, rgba(26, 35, 58, 0.75) 0%, rgba(16, 22, 34, 0.95) 100%)',
          borderColor: 'var(--border-medium)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.4rem' }}>
              <span className="badge badge-neutral" style={{ fontSize: '0.7rem' }}>
                ACTIVE WORKFLOW: {workflow?.workflow_id || 'N/A'}
              </span>
              {validation?.valid ? (
                <span className="badge badge-optimal">DAG VALIDATED</span>
              ) : (
                <span className="badge badge-critical">INVALID DAG</span>
              )}
            </div>
            <h1 style={{ fontSize: '1.75rem', fontWeight: 800 }}>{workflow?.name || 'Workflow Scheduler Dashboard'}</h1>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginTop: '0.25rem' }}>
              Real-time multi-agent workflow scheduling under precedence and worker constraints (P | prec | Cmax).
            </p>
          </div>

          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            <button className="btn btn-secondary" onClick={() => setActiveTab('builder')}>
              <Layers size={15} /> Edit Workflow
            </button>
            <button className="btn btn-secondary" onClick={onRunGreedy} disabled={loading}>
              <Zap size={15} /> Run Greedy
            </button>
            <button className="btn btn-primary" onClick={onRunExact} disabled={loading}>
              <ShieldCheck size={15} /> Run Branch & Bound
            </button>
            <button className="btn btn-accent" onClick={onRunCompare} disabled={loading}>
              <TrendingUp size={15} /> Compare All
            </button>
          </div>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-header">
            <span>Workflow Tasks</span>
            <Layers size={16} />
          </div>
          <div className="kpi-value">{totalTasks}</div>
          <div className="kpi-subtext">Total vertices in DAG</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-header">
            <span>Precedence Edges</span>
            <GitFork size={16} />
          </div>
          <div className="kpi-value">{totalDeps}</div>
          <div className="kpi-subtext">Directed dependencies (E)</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-header">
            <span>Execution Workers</span>
            <Cpu size={16} />
          </div>
          <div className="kpi-value">{numWorkers}</div>
          <div className="kpi-subtext">Parallel capacity (m)</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-header">
            <span>Critical Path Duration</span>
            <Clock size={16} />
          </div>
          <div className="kpi-value" style={{ color: 'var(--amber)' }}>
            {cpDuration > 0 ? `${cpDuration}s` : '—'}
          </div>
          <div className="kpi-subtext">Precedence lower bound Cmax</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-header">
            <span>Greedy Makespan</span>
            <Zap size={16} />
          </div>
          <div className="kpi-value" style={{ color: 'var(--cyan)' }}>
            {greedyMakespan !== null ? `${greedyMakespan}s` : '—'}
          </div>
          <div className="kpi-subtext">
            {greedySchedule?.worker_utilization ? `${(greedySchedule.worker_utilization * 100).toFixed(1)}% utilization` : 'Heuristic schedule'}
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-header">
            <span>Exact Optimum</span>
            <ShieldCheck size={16} />
          </div>
          <div className="kpi-value" style={{ color: 'var(--emerald)' }}>
            {exactMakespan !== null ? `${exactMakespan}s` : '—'}
          </div>
          <div className="kpi-subtext">
            {exactSchedule ? (
              <span className={`badge ${exactSchedule.optimality_proven ? 'badge-optimal' : 'badge-heuristic'}`}>
                {exactSchedule.status}
              </span>
            ) : (
              'Branch & Bound proof'
            )}
          </div>
        </div>
      </div>

      {/* Two-Column Middle Section */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))', gap: '1.5rem' }}>
        {/* Critical Bottleneck Card */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">
              <Clock size={18} style={{ color: 'var(--amber)' }} /> Critical Path Sequence
            </h3>
            <button className="btn btn-secondary btn-sm" onClick={() => setActiveTab('critical-path')}>
              View DP Table <ArrowRight size={13} />
            </button>
          </div>

          {criticalPath?.critical_path?.length > 0 ? (
            <div>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
                Longest precedence chain with zero slack ($Slack = 0$). Represents the absolute minimum theoretical duration under unlimited workers.
              </p>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                {criticalPath.critical_path.map((tid, idx) => (
                  <React.Fragment key={tid}>
                    <div
                      style={{
                        padding: '0.5rem 0.85rem',
                        borderRadius: 'var(--radius-md)',
                        background: 'rgba(239, 68, 68, 0.15)',
                        border: '1px solid rgba(239, 68, 68, 0.4)',
                        color: '#fca5a5',
                        fontWeight: 600,
                        fontSize: '0.85rem',
                      }}
                    >
                      <span style={{ fontFamily: 'var(--font-mono)' }}>[{tid}]</span>{' '}
                      {workflow?.tasks?.find((t) => t.task_id === tid)?.name || tid}
                    </div>
                    {idx < criticalPath.critical_path.length - 1 && (
                      <ArrowRight size={15} style={{ color: 'var(--text-muted)' }} />
                    )}
                  </React.Fragment>
                ))}
              </div>
            </div>
          ) : (
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Run Critical Path analysis to inspect bottlenecks.</p>
          )}
        </div>

        {/* Algorithm Comparison Quick Summary */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">
              <TrendingUp size={18} style={{ color: 'var(--violet)' }} /> Algorithmic Performance
            </h3>
            <button className="btn btn-secondary btn-sm" onClick={() => setActiveTab('comparison')}>
              Full Details <ArrowRight size={13} />
            </button>
          </div>

          {comparison ? (
            <div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginBottom: '1rem' }}>
                {Object.entries(comparison.algorithms || {}).map(([name, res]) => (
                  <div
                    key={name}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '0.6rem 0.85rem',
                      borderRadius: 'var(--radius-md)',
                      background: 'rgba(255, 255, 255, 0.03)',
                      border: '1px solid var(--border-subtle)',
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>{name}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        {res.runtime_ms} ms &bull; {res.states_explored || 0} states
                      </div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontWeight: 700, fontFamily: 'var(--font-mono)', fontSize: '0.95rem' }}>
                        {res.makespan}s
                      </div>
                      <span className={`badge ${res.optimality_proven ? 'badge-optimal' : 'badge-neutral'}`} style={{ fontSize: '0.65rem' }}>
                        {res.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
              <p style={{ fontSize: '0.775rem', color: 'var(--text-secondary)', fontStyle: 'italic' }}>
                {comparison.analysis}
              </p>
            </div>
          ) : (
            <div>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '1rem' }}>
                Click below to run a side-by-side benchmark comparing Greedy heuristics, Exact Backtracking, and Branch & Bound lower-bound pruning on this workflow.
              </p>
              <button className="btn btn-primary" onClick={onRunCompare} disabled={loading}>
                Compare Solvers Now
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
