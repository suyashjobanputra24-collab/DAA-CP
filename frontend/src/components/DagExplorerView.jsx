import React, { useState, useMemo } from 'react';
import { GitFork, Info, Clock, AlertCircle } from 'lucide-react';

export default function DagExplorerView({ workflow, criticalPath, topologicalOrder }) {
  const [selectedTaskId, setSelectedTaskId] = useState(null);

  const tasks = workflow?.tasks || [];
  const criticalSet = useMemo(() => new Set(criticalPath?.critical_tasks || []), [criticalPath]);
  const metricsMap = criticalPath?.task_metrics || {};

  // Compute topological layers (ranks) for clean left-to-right DAG layout
  const { nodePositions, edgeList, layersCount, maxLayerSize } = useMemo(() => {
    if (!tasks.length) return { nodePositions: {}, edgeList: [], layersCount: 0, maxLayerSize: 0 };

    const taskMap = new Map(tasks.map((t) => [t.task_id, t]));
    const ranks = {};

    // Topological order or iterative rank calculation
    tasks.forEach((t) => { ranks[t.task_id] = 0; });

    let changed = true;
    let iterations = 0;
    while (changed && iterations < tasks.length + 2) {
      changed = false;
      iterations++;
      tasks.forEach((t) => {
        t.dependencies?.forEach((depId) => {
          if (ranks[depId] !== undefined) {
            const newRank = ranks[depId] + 1;
            if (newRank > ranks[t.task_id]) {
              ranks[t.task_id] = newRank;
              changed = true;
            }
          }
        });
      });
    }

    // Group tasks into layers
    const layerBuckets = {};
    tasks.forEach((t) => {
      const r = ranks[t.task_id] || 0;
      if (!layerBuckets[r]) layerBuckets[r] = [];
      layerBuckets[r].push(t);
    });

    const lCount = Object.keys(layerBuckets).length;
    let maxSize = 0;
    Object.values(layerBuckets).forEach((b) => {
      if (b.length > maxSize) maxSize = b.length;
    });

    // Compute coordinates
    const positions = {};
    const layerWidth = 240;
    const nodeHeight = 70;
    const gapY = 40;

    Object.entries(layerBuckets).forEach(([layerStr, bucketTasks]) => {
      const layerIdx = parseInt(layerStr, 10);
      const x = 120 + layerIdx * layerWidth;
      const totalH = bucketTasks.length * nodeHeight + (bucketTasks.length - 1) * gapY;
      const startY = Math.max(80, 260 - totalH / 2);

      bucketTasks.forEach((t, i) => {
        const y = startY + i * (nodeHeight + gapY);
        positions[t.task_id] = { x, y, task: t, rank: layerIdx };
      });
    });

    // Build directed edges
    const edges = [];
    tasks.forEach((t) => {
      t.dependencies?.forEach((depId) => {
        if (positions[depId] && positions[t.task_id]) {
          const isCriticalEdge =
            criticalSet.has(depId) &&
            criticalSet.has(t.task_id) &&
            metricsMap[depId] &&
            metricsMap[t.task_id] &&
            Math.abs(metricsMap[depId].EF - metricsMap[t.task_id].ES) < 1e-4;

          edges.push({
            from: depId,
            to: t.task_id,
            fromPos: positions[depId],
            toPos: positions[t.task_id],
            isCritical: isCriticalEdge,
          });
        }
      });
    });

    return {
      nodePositions: positions,
      edgeList: edges,
      layersCount: lCount,
      maxLayerSize: maxSize,
    };
  }, [tasks, criticalSet, metricsMap]);

  const selectedTask = selectedTaskId ? tasks.find((t) => t.task_id === selectedTaskId) : null;
  const selectedMetrics = selectedTaskId ? metricsMap[selectedTaskId] : null;

  const svgWidth = Math.max(900, 180 + layersCount * 250);
  const svgHeight = Math.max(520, 140 + maxLayerSize * 110);

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      <div className="card">
        <div className="card-header">
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <GitFork size={18} style={{ color: 'var(--primary)' }} /> Interactive DAG Graph Explorer
            </h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.825rem' }}>
              Directed Acyclic Graph layout with topological rank layering. Red glowing borders & edges indicate the zero-slack Critical Path.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', fontSize: '0.75rem' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <span style={{ width: 10, height: 10, borderRadius: 2, background: 'rgba(239,68,68,0.8)' }} /> Critical Task
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <span style={{ width: 10, height: 10, borderRadius: 2, background: 'var(--primary)' }} /> Non-Critical
            </span>
          </div>
        </div>

        {/* SVG Graph Canvas */}
        <div style={{ overflowX: 'auto', background: 'var(--bg-canvas)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
          <svg
            width={svgWidth}
            height={svgHeight}
            className="dag-svg-canvas"
            style={{ display: 'block', minWidth: '100%' }}
          >
            <defs>
              <marker id="arrow" viewBox="0 0 10 10" refX="22" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#64748b" />
              </marker>
              <marker id="arrow-critical" viewBox="0 0 10 10" refX="22" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#ef4444" />
              </marker>
              <filter id="glow-crit" x="-20%" y="-20%" width="140%" height="140%">
                <feDropShadow dx="0" dy="0" stdDeviation="4" floodColor="#ef4444" floodOpacity="0.6" />
              </filter>
            </defs>

            {/* Render Edges */}
            {edgeList.map((edge, i) => {
              const x1 = edge.fromPos.x + 85;
              const y1 = edge.fromPos.y + 28;
              const x2 = edge.toPos.x - 85;
              const y2 = edge.toPos.y + 28;
              const dx = (x2 - x1) * 0.5;
              const pathData = `M ${x1} ${y1} C ${x1 + dx} ${y1}, ${x2 - dx} ${y2}, ${x2} ${y2}`;

              return (
                <path
                  key={`edge-${i}`}
                  d={pathData}
                  fill="none"
                  stroke={edge.isCritical ? '#ef4444' : 'rgba(255,255,255,0.18)'}
                  strokeWidth={edge.isCritical ? 3 : 1.5}
                  strokeDasharray={edge.isCritical ? 'none' : 'none'}
                  markerEnd={edge.isCritical ? 'url(#arrow-critical)' : 'url(#arrow)'}
                  style={edge.isCritical ? { filter: 'url(#glow-crit)' } : {}}
                />
              );
            })}

            {/* Render Nodes */}
            {Object.entries(nodePositions).map(([tid, pos]) => {
              const isCrit = criticalSet.has(tid);
              const isSelected = selectedTaskId === tid;
              const t = pos.task;

              return (
                <g
                  key={tid}
                  transform={`translate(${pos.x - 85}, ${pos.y})`}
                  onClick={() => setSelectedTaskId(tid)}
                  style={{ cursor: 'pointer' }}
                >
                  <rect
                    width="170"
                    height="56"
                    rx="8"
                    fill={isSelected ? '#1e293b' : 'rgba(16, 22, 34, 0.95)'}
                    stroke={isSelected ? '#6366f1' : isCrit ? '#ef4444' : 'rgba(255,255,255,0.15)'}
                    strokeWidth={isSelected || isCrit ? 2 : 1}
                    style={isCrit ? { filter: 'url(#glow-crit)' } : {}}
                  />
                  {/* Task ID Tag */}
                  <rect
                    x="8"
                    y="8"
                    width="42"
                    height="18"
                    rx="4"
                    fill={isCrit ? 'rgba(239,68,68,0.25)' : 'rgba(99,102,241,0.25)'}
                  />
                  <text
                    x="29"
                    y="21"
                    textAnchor="middle"
                    fill={isCrit ? '#fca5a5' : '#a5b4fc'}
                    fontSize="10"
                    fontWeight="700"
                    fontFamily="var(--font-mono)"
                  >
                    {tid}
                  </text>
                  {/* Duration Tag */}
                  <text
                    x="155"
                    y="21"
                    textAnchor="end"
                    fill="#94a3b8"
                    fontSize="10.5"
                    fontFamily="var(--font-mono)"
                  >
                    {t.duration}s
                  </text>
                  {/* Task Name */}
                  <text
                    x="12"
                    y="42"
                    fill="#f8fafc"
                    fontSize="11.5"
                    fontWeight="600"
                    fontFamily="var(--font-sans)"
                  >
                    {t.name?.length > 18 ? t.name.slice(0, 17) + '…' : t.name}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>
      </div>

      {/* Selected Task Details Inspector */}
      {selectedTask && (
        <div className="card" style={{ background: 'rgba(21, 28, 44, 0.95)', border: '1px solid var(--primary)' }}>
          <div className="card-header">
            <h3 className="card-title" style={{ color: 'var(--text-primary)' }}>
              <Info size={18} style={{ color: 'var(--cyan)' }} /> Task Inspector: [{selectedTask.task_id}] {selectedTask.name}
            </h3>
            {criticalSet.has(selectedTask.task_id) && (
              <span className="badge badge-critical">Critical Path Task (Slack = 0)</span>
            )}
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem', fontSize: '0.85rem' }}>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Duration:</span>{' '}
              <strong className="mono">{selectedTask.duration}s</strong>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Predecessors:</span>{' '}
              <strong className="mono">{selectedTask.dependencies?.join(', ') || 'None (Source Node)'}</strong>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Role / Type:</span>{' '}
              <strong>{selectedTask.task_type || 'Generic'}</strong>
            </div>
            {selectedMetrics && (
              <>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Earliest Start (ES):</span>{' '}
                  <strong className="mono">{selectedMetrics.ES}s</strong>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Earliest Finish (EF):</span>{' '}
                  <strong className="mono">{selectedMetrics.EF}s</strong>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Latest Start (LS):</span>{' '}
                  <strong className="mono">{selectedMetrics.LS}s</strong>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Latest Finish (LF):</span>{' '}
                  <strong className="mono">{selectedMetrics.LF}s</strong>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Total Slack (Float):</span>{' '}
                  <strong className="mono" style={{ color: selectedMetrics.slack === 0 ? 'var(--rose)' : 'var(--emerald)' }}>
                    {selectedMetrics.slack}s
                  </strong>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
