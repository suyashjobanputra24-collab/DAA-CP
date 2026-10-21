import React, { useState } from 'react';
import { Calendar, Play, Clock, Cpu, Zap, ShieldCheck } from 'lucide-react';

export default function GanttView({
  workflow,
  activeSchedule,
  onRunSchedule,
  loading,
}) {
  const [selectedAlgorithm, setSelectedAlgorithm] = useState('greedy');
  const [selectedPolicy, setSelectedPolicy] = useState('CRITICAL_PATH');

  const tasks = activeSchedule?.tasks || [];
  const makespan = activeSchedule?.makespan || 0;
  const numWorkers = activeSchedule?.number_of_workers || workflow?.number_of_workers || 2;
  const workerList = Array.from({ length: numWorkers }, (_, i) => `W${i + 1}`);

  const handleExecute = () => {
    onRunSchedule(selectedAlgorithm, selectedPolicy);
  };

  // Group tasks by worker
  const workerTasks = {};
  workerList.forEach((wid) => { workerTasks[wid] = []; });
  tasks.forEach((t) => {
    if (!workerTasks[t.worker_id]) workerTasks[t.worker_id] = [];
    workerTasks[t.worker_id].push(t);
  });

  // Calculate ticks along the makespan time axis
  const timeStep = Math.max(1, Math.ceil(makespan / 10));
  const timeTicks = [];
  for (let t = 0; t <= makespan + 0.1; t += timeStep) {
    timeTicks.push(t);
  }

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Top Configuration & Algorithm Run Controls */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Calendar size={18} style={{ color: 'var(--cyan)' }} /> Worker Gantt Timeline Schedule
            </h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.825rem' }}>
              Non-preemptive parallel machine execution under precedence constraints. Shows worker assignments, idle gaps, and critical path bottlenecks.
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <label style={{ fontSize: '0.8rem', fontWeight: 600 }}>Algorithm:</label>
              <select
                className="form-select"
                value={selectedAlgorithm}
                onChange={(e) => setSelectedAlgorithm(e.target.value)}
              >
                <option value="greedy">Greedy List Scheduler</option>
                <option value="branch_and_bound">Branch & Bound (Exact)</option>
                <option value="backtrack">Exact Backtracking</option>
              </select>
            </div>

            {selectedAlgorithm === 'greedy' && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                <label style={{ fontSize: '0.8rem', fontWeight: 600 }}>Priority:</label>
                <select
                  className="form-select"
                  value={selectedPolicy}
                  onChange={(e) => setSelectedPolicy(e.target.value)}
                >
                  <option value="CRITICAL_PATH">Critical Path (Bottom-Level)</option>
                  <option value="LPT">LPT (Longest Processing Time)</option>
                  <option value="SPT">SPT (Shortest Processing Time)</option>
                  <option value="FIFO">FIFO (Topological Order)</option>
                </select>
              </div>
            )}

            <button className="btn btn-primary" onClick={handleExecute} disabled={loading}>
              <Play size={15} /> Recompute Schedule
            </button>
          </div>
        </div>
      </div>

      {/* Gantt Overview & Metrics Banner */}
      {activeSchedule && (
        <div className="card" style={{ padding: '1rem 1.5rem', background: 'rgba(16, 22, 34, 0.95)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
            <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'center' }}>
              <div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Active Solver</span>
                <div style={{ fontWeight: 700, fontSize: '1rem', color: 'var(--text-primary)' }}>
                  {activeSchedule.algorithm} {activeSchedule.priority_policy ? `(${activeSchedule.priority_policy})` : ''}
                </div>
              </div>
              <div style={{ borderLeft: '1px solid var(--border-subtle)', paddingLeft: '1.5rem' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Total Makespan (Cmax)</span>
                <div style={{ fontWeight: 800, fontSize: '1.25rem', fontFamily: 'var(--font-mono)', color: 'var(--amber)' }}>
                  {makespan}s
                </div>
              </div>
              <div style={{ borderLeft: '1px solid var(--border-subtle)', paddingLeft: '1.5rem' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Worker Utilization</span>
                <div style={{ fontWeight: 800, fontSize: '1.25rem', fontFamily: 'var(--font-mono)', color: 'var(--emerald)' }}>
                  {(activeSchedule.worker_utilization * 100).toFixed(1)}%
                </div>
              </div>
              <div style={{ borderLeft: '1px solid var(--border-subtle)', paddingLeft: '1.5rem' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Idle Capacity</span>
                <div style={{ fontWeight: 800, fontSize: '1.25rem', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>
                  {activeSchedule.worker_idle_time}s
                </div>
              </div>
            </div>

            <div>
              <span className={`badge ${activeSchedule.optimality_proven ? 'badge-optimal' : 'badge-heuristic'}`}>
                {activeSchedule.status}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Real Gantt Chart Canvas */}
      <div className="card">
        {makespan > 0 ? (
          <div className="gantt-container">
            {/* Time Axis Header */}
            <div style={{ display: 'flex', alignItems: 'center', height: '24px' }}>
              <div style={{ width: '90px', flexShrink: 0 }} />
              <div style={{ flex: 1, position: 'relative', height: '100%' }}>
                {timeTicks.map((t) => {
                  const leftPct = (t / makespan) * 100;
                  return (
                    <div
                      key={t}
                      style={{
                        position: 'absolute',
                        left: `${leftPct}%`,
                        transform: 'translateX(-50%)',
                        fontSize: '0.75rem',
                        fontFamily: 'var(--font-mono)',
                        color: 'var(--text-muted)',
                      }}
                    >
                      {t}s
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Worker Lanes */}
            {workerList.map((wid) => {
              const laneTasks = workerTasks[wid] || [];
              const utilInfo = activeSchedule?.per_worker_utilization?.[wid];

              return (
                <div key={wid} className="gantt-lane">
                  <div className="gantt-lane-label">
                    <span>{wid}</span>
                    {utilInfo && (
                      <span style={{ fontSize: '0.65rem', marginLeft: '0.35rem', color: 'var(--text-muted)', fontWeight: 400 }}>
                        {(utilInfo.utilization_rate * 100).toFixed(0)}%
                      </span>
                    )}
                  </div>
                  <div className="gantt-timeline-area">
                    {/* Time Grid Guidelines */}
                    {timeTicks.map((t) => (
                      <div
                        key={t}
                        style={{
                          position: 'absolute',
                          left: `${(t / makespan) * 100}%`,
                          top: 0,
                          bottom: 0,
                          width: '1px',
                          background: 'rgba(255,255,255,0.05)',
                        }}
                      />
                    ))}

                    {/* Task Blocks */}
                    {laneTasks.map((t) => {
                      const leftPct = (t.start_time / makespan) * 100;
                      const widthPct = (t.duration / makespan) * 100;
                      const isCrit = t.is_critical;

                      return (
                        <div
                          key={t.task_id}
                          className={`gantt-block ${isCrit ? 'critical' : 'normal'}`}
                          style={{
                            left: `${leftPct}%`,
                            width: `${Math.max(widthPct, 2)}%`,
                          }}
                          title={`[${t.task_id}] ${t.name}: ${t.start_time}s -> ${t.finish_time}s (dur ${t.duration}s)`}
                        >
                          <span style={{ fontFamily: 'var(--font-mono)' }}>[{t.task_id}]</span>
                          <span style={{ opacity: 0.85, fontSize: '0.7rem' }}>{t.duration}s</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
            No schedule computed yet. Select an algorithm and click 'Recompute Schedule'.
          </div>
        )}
      </div>

      {/* Per-Worker Utilization Breakdown */}
      {activeSchedule?.per_worker_utilization && Object.keys(activeSchedule.per_worker_utilization).length > 0 && (
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">
              <Cpu size={16} style={{ color: 'var(--primary)' }} /> Worker Utilization & Idle Time Breakdown
            </h3>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1rem' }}>
            {Object.entries(activeSchedule.per_worker_utilization).map(([wid, u]) => (
              <div
                key={wid}
                style={{
                  background: 'rgba(255,255,255,0.02)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-md)',
                  padding: '1rem',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                  <strong className="mono" style={{ color: 'var(--cyan)' }}>Worker {wid}</strong>
                  <span className="mono" style={{ fontWeight: 700, color: 'var(--emerald)' }}>
                    {(u.utilization_rate * 100).toFixed(1)}%
                  </span>
                </div>
                {/* Progress Bar */}
                <div style={{ height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px', overflow: 'hidden', marginBottom: '0.5rem' }}>
                  <div
                    style={{
                      height: '100%',
                      width: `${u.utilization_rate * 100}%`,
                      background: 'linear-gradient(90deg, var(--primary), var(--emerald))',
                    }}
                  />
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  <span>Busy: <strong className="mono" style={{ color: 'var(--text-primary)' }}>{u.busy_time}s</strong></span>
                  <span>Idle: <strong className="mono" style={{ color: 'var(--text-secondary)' }}>{u.idle_time}s</strong></span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
