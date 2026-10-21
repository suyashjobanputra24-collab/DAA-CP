import React, { useState } from 'react';
import { FlaskConical, Play, Download, AlertTriangle, RefreshCw, Layers, Cpu, Clock } from 'lucide-react';
import { api } from '../api';

export default function BenchmarkView() {
  const [taskCounts, setTaskCounts] = useState('4, 8, 12');
  const [workerCounts, setWorkerCounts] = useState('2, 3');
  const [densities, setDensities] = useState('0.3');
  const [selectedAlgorithms, setSelectedAlgorithms] = useState([
    'greedy_critical_path',
    'greedy_lpt',
    'branch_and_bound',
  ]);
  const [seed, setSeed] = useState(42);
  const [repetitions, setRepetitions] = useState(1);
  const [loading, setLoading] = useState(false);
  const [benchmarkResult, setBenchmarkResult] = useState(null);
  const [error, setError] = useState(null);

  const availableAlgs = [
    { id: 'greedy_critical_path', label: 'Greedy (Critical Path)' },
    { id: 'greedy_lpt', label: 'Greedy (LPT)' },
    { id: 'branch_and_bound', label: 'Branch and Bound' },
    { id: 'exact_backtracking', label: 'Exact Backtracking' },
  ];

  const handleToggleAlg = (id) => {
    setSelectedAlgorithms((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const parseNumberList = (str, isFloat = false) => {
    return str
      .split(',')
      .map((s) => (isFloat ? parseFloat(s.trim()) : parseInt(s.trim(), 10)))
      .filter((n) => !isNaN(n));
  };

  const handleRunBenchmark = async () => {
    setLoading(true);
    setError(null);
    try {
      const parsedTasks = parseNumberList(taskCounts);
      const parsedWorkers = parseNumberList(workerCounts);
      const parsedDensities = parseNumberList(densities, true);

      if (!parsedTasks.length || !parsedWorkers.length || !selectedAlgorithms.length) {
        throw new Error('Please select at least one task count, worker count, and algorithm.');
      }

      const req = {
        task_counts: parsedTasks,
        worker_counts: parsedWorkers,
        dependency_densities: parsedDensities.length ? parsedDensities : [0.3],
        algorithms: selectedAlgorithms,
        repetitions: parseInt(repetitions, 10) || 1,
        seed: parseInt(seed, 10) || 42,
        backtrack_state_limit: 10000,
      };

      const res = await api.runBenchmark(req);
      setBenchmarkResult(res);
    } catch (err) {
      setError(err.message || 'Benchmark execution failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleExportJson = () => {
    if (!benchmarkResult) return;
    const blob = new Blob([JSON.stringify(benchmarkResult, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `benchmark_results_seed${seed}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleExportCsv = () => {
    if (!benchmarkResult || !benchmarkResult.results) return;
    const headers = ['Tasks', 'Workers', 'Density', 'Seed', 'Algorithm', 'Makespan', 'Runtime_ms', 'States_Explored', 'States_Pruned', 'Status', 'Lower_Bound'];
    const rows = benchmarkResult.results.map((r) => [
      r.num_tasks,
      r.num_workers,
      r.density,
      r.seed,
      `"${r.algorithm}"`,
      r.makespan,
      r.runtime_ms,
      r.states_explored ?? '',
      r.states_pruned ?? '',
      `"${r.optimality_status}"`,
      r.lower_bound,
    ]);

    const csvContent = [headers.join(','), ...rows.map((row) => row.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `benchmark_results_seed${seed}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Check if user entered large task sizes with exact solvers
  const hasExact = selectedAlgorithms.includes('branch_and_bound') || selectedAlgorithms.includes('exact_backtracking');
  const maxEnteredTask = Math.max(...parseNumberList(taskCounts), 0);
  const showExponentialWarning = hasExact && maxEnteredTask > 14;

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Configuration Header Card */}
      <div className="card">
        <div className="card-header">
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <FlaskConical size={18} style={{ color: 'var(--cyan)' }} /> Empirical Algorithmic Benchmark Lab
            </h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.825rem' }}>
              Perform reproducible scalability experiments across DAG task counts, edge densities, worker capacities, and random seeds.
            </p>
          </div>
        </div>

        {/* Form Inputs Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1.25rem', marginBottom: '1.25rem' }}>
          <div className="form-group">
            <label className="form-label">Task Counts (|V| separated by comma)</label>
            <input
              type="text"
              className="form-input mono"
              value={taskCounts}
              onChange={(e) => setTaskCounts(e.target.value)}
              placeholder="e.g. 4, 8, 12, 16"
            />
          </div>

          <div className="form-group">
            <label className="form-label">Worker Capacities (W)</label>
            <input
              type="text"
              className="form-input mono"
              value={workerCounts}
              onChange={(e) => setWorkerCounts(e.target.value)}
              placeholder="e.g. 2, 3"
            />
          </div>

          <div className="form-group">
            <label className="form-label">Edge Densities (0.0 to 1.0)</label>
            <input
              type="text"
              className="form-input mono"
              value={densities}
              onChange={(e) => setDensities(e.target.value)}
              placeholder="e.g. 0.25, 0.5"
            />
          </div>

          <div className="form-group">
            <label className="form-label">Random Seed</label>
            <input
              type="number"
              className="form-input mono"
              value={seed}
              onChange={(e) => setSeed(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Repetitions (Trials)</label>
            <input
              type="number"
              min="1"
              max="5"
              className="form-input mono"
              value={repetitions}
              onChange={(e) => setRepetitions(e.target.value)}
            />
          </div>
        </div>

        {/* Algorithm Checkboxes */}
        <div style={{ marginBottom: '1.25rem' }}>
          <label className="form-label" style={{ display: 'block', marginBottom: '0.5rem' }}>
            Algorithms to Benchmark:
          </label>
          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
            {availableAlgs.map((alg) => (
              <label
                key={alg.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.4rem',
                  fontSize: '0.825rem',
                  cursor: 'pointer',
                  background: 'rgba(255,255,255,0.03)',
                  padding: '0.4rem 0.75rem',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <input
                  type="checkbox"
                  checked={selectedAlgorithms.includes(alg.id)}
                  onChange={() => handleToggleAlg(alg.id)}
                />
                <span>{alg.label}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Complexity Warning Banner if N > 14 */}
        {showExponentialWarning && (
          <div className="alert alert-warning">
            <AlertTriangle size={18} />
            <div>
              <strong>Exponential Search Warning:</strong>
              <p style={{ marginTop: '0.2rem' }}>
                Task sizes &gt; 14 with Exact Backtracking or Branch & Bound may have massive state spaces ($O(W^V)$).
                The engine safely applies adaptive state caps (3,000 to 5,000 states) and timeouts (1.5s to 2.0s) to keep benchmark responses fast.
              </p>
            </div>
          </div>
        )}

        {error && (
          <div className="alert alert-danger">
            <AlertTriangle size={18} />
            <div>{error}</div>
          </div>
        )}

        {/* Action Buttons */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
          <button className="btn btn-primary" onClick={handleRunBenchmark} disabled={loading}>
            {loading ? <RefreshCw size={15} className="spin" /> : <Play size={15} />}
            {loading ? 'Running Suite...' : 'Run Benchmark Suite'}
          </button>
        </div>
      </div>

      {/* Benchmark Results */}
      {benchmarkResult && (
        <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Summary Cards */}
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">
                <Clock size={16} /> Aggregate Benchmark Summary ({benchmarkResult.total_runs} Executions in {benchmarkResult.total_runtime_ms} ms)
              </h3>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button className="btn btn-secondary btn-sm" onClick={handleExportCsv}>
                  <Download size={13} /> Export CSV
                </button>
                <button className="btn btn-secondary btn-sm" onClick={handleExportJson}>
                  <Download size={13} /> Export JSON
                </button>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
              {Object.entries(benchmarkResult.summary || {}).map(([alg, s]) => (
                <div
                  key={alg}
                  style={{
                    background: 'rgba(255,255,255,0.03)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-md)',
                    padding: '1rem',
                  }}
                >
                  <strong style={{ color: 'var(--primary)', fontSize: '0.9rem' }}>{alg}</strong>
                  <div style={{ marginTop: '0.5rem', fontSize: '0.8rem', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                    <div>Avg Runtime: <strong className="mono">{s.avg_runtime_ms} ms</strong></div>
                    <div>Avg Makespan: <strong className="mono">{s.avg_makespan}s</strong></div>
                    <div>Optimal Proven: <strong className="mono">{s.optimal_count} / {s.count}</strong></div>
                    {s.total_states_explored > 0 && (
                      <div>Total States: <strong className="mono">{s.total_states_explored}</strong></div>
                    )}
                    {s.total_states_pruned > 0 && (
                      <div style={{ color: 'var(--emerald)' }}>Pruned States: <strong className="mono">{s.total_states_pruned}</strong></div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Granular Execution Results Table */}
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">Granular Benchmark Records</h3>
            </div>

            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Tasks (|V|)</th>
                    <th>Workers (W)</th>
                    <th>Density</th>
                    <th>Algorithm</th>
                    <th>Makespan</th>
                    <th>Lower Bound</th>
                    <th>Runtime</th>
                    <th>States Explored</th>
                    <th>States Pruned</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {benchmarkResult.results.map((r, i) => (
                    <tr key={i}>
                      <td className="mono" style={{ fontWeight: 700 }}>{r.num_tasks}</td>
                      <td className="mono">{r.num_workers}</td>
                      <td className="mono">{r.density}</td>
                      <td style={{ fontWeight: 600 }}>{r.algorithm}</td>
                      <td className="mono" style={{ fontWeight: 700, color: 'var(--cyan)' }}>{r.makespan}s</td>
                      <td className="mono">{r.lower_bound}s</td>
                      <td className="mono">{r.runtime_ms} ms</td>
                      <td className="mono">{r.states_explored !== null ? r.states_explored : '—'}</td>
                      <td className="mono" style={{ color: r.states_pruned ? 'var(--emerald)' : 'var(--text-muted)' }}>
                        {r.states_pruned !== null ? r.states_pruned : '—'}
                      </td>
                      <td>
                        <span className={`badge ${r.optimality_status.includes('OPTIMAL') ? 'badge-optimal' : 'badge-neutral'}`}>
                          {r.optimality_status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
