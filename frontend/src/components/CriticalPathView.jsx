import React from 'react';
import { Clock, ArrowRight, ShieldAlert, BookOpen, Layers } from 'lucide-react';

export default function CriticalPathView({ workflow, criticalPath, topologicalOrder }) {
  const metrics = criticalPath?.task_metrics || {};
  const order = criticalPath?.topological_order || Object.keys(metrics);
  const cpTasks = criticalPath?.critical_path || [];
  const projectDuration = criticalPath?.project_duration || 0;

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Theoretical Distinction Card */}
      <div
        className="card"
        style={{
          background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.08) 0%, rgba(16, 22, 34, 0.9) 100%)',
          borderColor: 'rgba(245, 158, 11, 0.3)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '1rem' }}>
          <div
            style={{
              padding: '0.65rem',
              borderRadius: 'var(--radius-md)',
              background: 'rgba(245, 158, 11, 0.15)',
              color: 'var(--amber)',
            }}
          >
            <ShieldAlert size={24} />
          </div>
          <div>
            <h2 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--amber)' }}>
              Fundamental DAA Distinction: Precedence Lower Bound vs Limited-Worker Makespan
            </h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '0.35rem' }}>
              The <strong>Critical Path duration ({projectDuration}s)</strong> represents the absolute theoretical lower bound assuming an <em>unlimited supply of workers</em> ($W \to \infty$).
              When workers are restricted to $W = {workflow?.number_of_workers || 2}$, the optimal schedule length may be strictly greater due to machine contention:
            </p>
            <div
              className="mono"
              style={{
                marginTop: '0.5rem',
                padding: '0.4rem 0.85rem',
                background: 'rgba(0,0,0,0.3)',
                borderRadius: 'var(--radius-sm)',
                display: 'inline-block',
                fontSize: '0.85rem',
                color: '#fef3c7',
              }}
            >
              Cmax(optimal) &ge; max( Critical_Path_Duration, &lceil; &sum; duration(v) / W &rceil; )
            </div>
          </div>
        </div>
      </div>

      {/* Critical Path Reconstructed Sequence */}
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">
            <Clock size={18} style={{ color: 'var(--rose)' }} /> Critical Path Bottleneck Sequence
          </h3>
          <span className="badge badge-critical">Zero Total Float (Slack = 0)</span>
        </div>

        {cpTasks.length > 0 ? (
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', flexWrap: 'wrap' }}>
              {cpTasks.map((tid, idx) => {
                const t = workflow?.tasks?.find((x) => x.task_id === tid);
                return (
                  <React.Fragment key={tid}>
                    <div
                      style={{
                        padding: '0.75rem 1rem',
                        borderRadius: 'var(--radius-md)',
                        background: 'rgba(244, 63, 94, 0.15)',
                        border: '1px solid rgba(244, 63, 94, 0.4)',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '0.2rem',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem', fontSize: '0.75rem' }}>
                        <span className="mono" style={{ fontWeight: 700, color: '#fca5a5' }}>
                          [{tid}]
                        </span>
                        <span className="mono" style={{ color: 'var(--text-muted)' }}>
                          {t?.duration || 0}s
                        </span>
                      </div>
                      <div style={{ fontWeight: 600, fontSize: '0.9rem', color: '#fff' }}>{t?.name || tid}</div>
                    </div>
                    {idx < cpTasks.length - 1 && (
                      <ArrowRight size={18} style={{ color: 'var(--rose)', opacity: 0.8 }} />
                    )}
                  </React.Fragment>
                );
              })}
            </div>
            <div style={{ marginTop: '1.25rem', fontSize: '0.825rem', color: 'var(--text-secondary)' }}>
              Any delay in tasks on this sequence directly extends the overall project completion time.
            </div>
          </div>
        ) : (
          <p style={{ color: 'var(--text-muted)' }}>No critical path calculated.</p>
        )}
      </div>

      {/* Dynamic Programming Metrics Table */}
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">
            <Layers size={18} style={{ color: 'var(--primary)' }} /> Dynamic Programming Pass Results (ES, EF, LS, LF, Slack)
          </h3>
        </div>

        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th style={{ width: '90px' }}>Task ID</th>
                <th>Task Name</th>
                <th style={{ width: '100px' }}>Duration</th>
                <th style={{ width: '110px' }}>Earliest Start (ES)</th>
                <th style={{ width: '110px' }}>Earliest Finish (EF)</th>
                <th style={{ width: '110px' }}>Latest Start (LS)</th>
                <th style={{ width: '110px' }}>Latest Finish (LF)</th>
                <th style={{ width: '100px' }}>Slack (Float)</th>
                <th style={{ width: '120px', textAlign: 'center' }}>Critical?</th>
              </tr>
            </thead>
            <tbody>
              {order.map((tid) => {
                const m = metrics[tid];
                if (!m) return null;
                const isCrit = m.is_critical;

                return (
                  <tr
                    key={tid}
                    style={isCrit ? { background: 'rgba(239, 68, 68, 0.05)' } : {}}
                  >
                    <td className="mono" style={{ fontWeight: 700, color: isCrit ? '#f87171' : 'var(--primary)' }}>
                      {m.task_id}
                    </td>
                    <td style={{ fontWeight: 600 }}>{m.name}</td>
                    <td className="mono">{m.duration}s</td>
                    <td className="mono">{m.ES}s</td>
                    <td className="mono">{m.EF}s</td>
                    <td className="mono">{m.LS}s</td>
                    <td className="mono">{m.LF}s</td>
                    <td className="mono" style={{ fontWeight: 700, color: isCrit ? 'var(--rose)' : 'var(--emerald)' }}>
                      {m.slack}s
                    </td>
                    <td style={{ textAlign: 'center' }}>
                      <span className={`badge ${isCrit ? 'badge-critical' : 'badge-neutral'}`}>
                        {isCrit ? 'CRITICAL' : 'Flexible'}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Dynamic Programming Formulation Reference */}
      <div className="card">
        <h3 className="card-title" style={{ marginBottom: '0.75rem' }}>
          <BookOpen size={16} /> Dynamic Programming Recurrence Relations
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1rem', fontSize: '0.825rem', color: 'var(--text-secondary)' }}>
          <div style={{ background: 'rgba(0,0,0,0.25)', padding: '0.85rem', borderRadius: 'var(--radius-md)' }}>
            <strong style={{ color: 'var(--cyan)' }}>1. Forward Pass (Topological Order):</strong>
            <p style={{ marginTop: '0.35rem' }}>
              ES(u) = 0 if Preds(u) is empty, else max &#123; EF(p) : p &isin; Preds(u) &#125;
            </p>
            <p>EF(u) = ES(u) + Duration(u)</p>
            <p>Cmax = max &#123; EF(u) : u &isin; V &#125;</p>
          </div>

          <div style={{ background: 'rgba(0,0,0,0.25)', padding: '0.85rem', borderRadius: 'var(--radius-md)' }}>
            <strong style={{ color: 'var(--violet)' }}>2. Reverse Pass (Reverse Topological Order):</strong>
            <p style={{ marginTop: '0.35rem' }}>
              LF(u) = Cmax if Succs(u) is empty, else min &#123; LS(s) : s &isin; Succs(u) &#125;
            </p>
            <p>LS(u) = LF(u) - Duration(u)</p>
            <p>Total Slack(u) = LS(u) - ES(u) = LF(u) - EF(u)</p>
          </div>
        </div>
      </div>
    </div>
  );
}
