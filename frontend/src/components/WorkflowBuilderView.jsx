import React, { useState } from 'react';
import {
  Layers,
  Plus,
  Trash2,
  CheckCircle2,
  AlertTriangle,
  Play,
  RotateCcw,
  Download,
  Upload,
  FileText,
  Cpu,
} from 'lucide-react';

export default function WorkflowBuilderView({
  workflow,
  setWorkflow,
  validation,
  onValidate,
  onLoadSample,
  sampleList,
  loading,
}) {
  const [showJsonModal, setShowJsonModal] = useState(false);
  const [jsonInput, setJsonInput] = useState('');
  const [newTask, setNewTask] = useState({
    task_id: '',
    name: '',
    duration: 5.0,
    dependencies: '',
    task_type: 'compute',
  });

  const handleUpdateWorkerCount = (val) => {
    const num = Math.max(1, parseInt(val, 10) || 1);
    setWorkflow((prev) => ({ ...prev, number_of_workers: num }));
  };

  const handleUpdateTask = (index, field, value) => {
    setWorkflow((prev) => {
      const updated = [...prev.tasks];
      if (field === 'duration') {
        updated[index] = { ...updated[index], duration: Math.max(0.1, parseFloat(value) || 1.0) };
      } else if (field === 'dependencies') {
        const deps = value.split(',').map((s) => s.trim()).filter(Boolean);
        updated[index] = { ...updated[index], dependencies: deps };
      } else {
        updated[index] = { ...updated[index], [field]: value };
      }
      return { ...prev, tasks: updated };
    });
  };

  const handleDeleteTask = (index) => {
    setWorkflow((prev) => {
      const taskToDelete = prev.tasks[index].task_id;
      const updated = prev.tasks.filter((_, i) => i !== index);
      // Remove references in dependencies
      const cleaned = updated.map((t) => ({
        ...t,
        dependencies: t.dependencies.filter((d) => d !== taskToDelete),
      }));
      return { ...prev, tasks: cleaned };
    });
  };

  const handleAddTask = (e) => {
    e.preventDefault();
    if (!newTask.task_id.trim()) return;

    const deps = newTask.dependencies
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean);

    setWorkflow((prev) => ({
      ...prev,
      tasks: [
        ...prev.tasks,
        {
          task_id: newTask.task_id.trim(),
          name: newTask.name.trim() || newTask.task_id.trim(),
          duration: parseFloat(newTask.duration) || 5.0,
          dependencies: deps,
          task_type: newTask.task_type || 'compute',
        },
      ],
    }));

    setNewTask({
      task_id: '',
      name: '',
      duration: 5.0,
      dependencies: '',
      task_type: 'compute',
    });
  };

  const handleOpenJsonModal = () => {
    setJsonInput(JSON.stringify(workflow, null, 2));
    setShowJsonModal(true);
  };

  const handleApplyJson = () => {
    try {
      const parsed = JSON.parse(jsonInput);
      if (!parsed.tasks || !Array.isArray(parsed.tasks)) {
        alert("Invalid workflow schema: missing 'tasks' array.");
        return;
      }
      setWorkflow(parsed);
      setShowJsonModal(false);
    } catch (err) {
      alert(`JSON Parse Error: ${err.message}`);
    }
  };

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Validation Status Banner */}
      {validation && (
        <div className={`alert ${validation.valid ? 'alert-success' : 'alert-danger'}`}>
          {validation.valid ? <CheckCircle2 size={18} /> : <AlertTriangle size={18} />}
          <div>
            <strong>{validation.valid ? 'DAG Invariants Satisfied' : 'Validation Error Detected'}</strong>
            <p style={{ marginTop: '0.2rem' }}>{validation.message}</p>
            {validation.errors?.length > 0 && (
              <ul style={{ marginLeft: '1.25rem', marginTop: '0.4rem', fontSize: '0.8rem' }}>
                {validation.errors.map((err, i) => (
                  <li key={i}>{err}</li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}

      {/* Top Controls: Preset Loader & Worker Count */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Layers size={18} style={{ color: 'var(--primary)' }} /> Workflow Configuration
            </h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.825rem' }}>
              Define task nodes, execution durations, directed dependencies, and worker capacity.
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
            {/* Worker Capacity Input */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'rgba(255,255,255,0.04)', padding: '0.35rem 0.75rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
              <Cpu size={16} style={{ color: 'var(--cyan)' }} />
              <label style={{ fontSize: '0.8rem', fontWeight: 600 }}>Workers (m):</label>
              <input
                type="number"
                min="1"
                max="16"
                className="form-input"
                style={{ width: '60px', padding: '0.25rem 0.5rem', textAlign: 'center' }}
                value={workflow?.number_of_workers || 2}
                onChange={(e) => handleUpdateWorkerCount(e.target.value)}
              />
            </div>

            {/* Built-in Preset Dropdown */}
            <select
              className="form-select"
              onChange={(e) => e.target.value && onLoadSample(e.target.value)}
              defaultValue=""
            >
              <option value="" disabled>Load Sample Workflow...</option>
              {sampleList?.map((s) => (
                <option key={s.filename} value={s.filename}>
                  {s.name} ({s.tasks_count} tasks, {s.number_of_workers}W)
                </option>
              ))}
            </select>

            <button className="btn btn-secondary" onClick={handleOpenJsonModal}>
              <FileText size={15} /> JSON Payload
            </button>
            <button className="btn btn-primary" onClick={onValidate} disabled={loading}>
              <CheckCircle2 size={15} /> Validate DAG
            </button>
          </div>
        </div>
      </div>

      {/* Task List Table */}
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">Tasks in Workflow ({workflow?.tasks?.length || 0})</h3>
        </div>

        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th style={{ width: '120px' }}>Task ID</th>
                <th>Task Name</th>
                <th style={{ width: '120px' }}>Duration (s)</th>
                <th>Dependencies (IDs separated by comma)</th>
                <th style={{ width: '130px' }}>Role / Type</th>
                <th style={{ width: '80px', textAlign: 'center' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {workflow?.tasks?.map((task, idx) => (
                <tr key={task.task_id || idx}>
                  <td>
                    <input
                      type="text"
                      className="form-input mono"
                      style={{ width: '100%', fontWeight: 700 }}
                      value={task.task_id}
                      onChange={(e) => handleUpdateTask(idx, 'task_id', e.target.value)}
                    />
                  </td>
                  <td>
                    <input
                      type="text"
                      className="form-input"
                      style={{ width: '100%' }}
                      value={task.name}
                      onChange={(e) => handleUpdateTask(idx, 'name', e.target.value)}
                    />
                  </td>
                  <td>
                    <input
                      type="number"
                      step="0.5"
                      min="0.1"
                      className="form-input mono"
                      style={{ width: '100%' }}
                      value={task.duration}
                      onChange={(e) => handleUpdateTask(idx, 'duration', e.target.value)}
                    />
                  </td>
                  <td>
                    <input
                      type="text"
                      className="form-input mono"
                      style={{ width: '100%' }}
                      placeholder="e.g. T1, T2"
                      value={task.dependencies?.join(', ') || ''}
                      onChange={(e) => handleUpdateTask(idx, 'dependencies', e.target.value)}
                    />
                  </td>
                  <td>
                    <input
                      type="text"
                      className="form-input"
                      style={{ width: '100%' }}
                      value={task.task_type || ''}
                      onChange={(e) => handleUpdateTask(idx, 'task_type', e.target.value)}
                    />
                  </td>
                  <td style={{ textAlign: 'center' }}>
                    <button
                      className="btn btn-danger btn-sm"
                      title="Delete task"
                      onClick={() => handleDeleteTask(idx)}
                    >
                      <Trash2 size={14} />
                    </button>
                  </td>
                </tr>
              ))}
              {workflow?.tasks?.length === 0 && (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '2rem' }}>
                    No tasks currently in workflow. Add tasks below or load a preset.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Quick Add Task Form */}
        <form onSubmit={handleAddTask} style={{ marginTop: '1.25rem', display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'flex-end', background: 'rgba(255,255,255,0.02)', padding: '1rem', borderRadius: 'var(--radius-md)', border: '1px dashed var(--border-subtle)' }}>
          <div className="form-group" style={{ flex: '1 1 110px' }}>
            <label className="form-label">Task ID</label>
            <input
              type="text"
              placeholder="e.g. T6"
              className="form-input mono"
              value={newTask.task_id}
              onChange={(e) => setNewTask({ ...newTask, task_id: e.target.value })}
              required
            />
          </div>
          <div className="form-group" style={{ flex: '2 1 180px' }}>
            <label className="form-label">Task Name</label>
            <input
              type="text"
              placeholder="Human readable title"
              className="form-input"
              value={newTask.name}
              onChange={(e) => setNewTask({ ...newTask, name: e.target.value })}
            />
          </div>
          <div className="form-group" style={{ flex: '1 1 90px' }}>
            <label className="form-label">Duration</label>
            <input
              type="number"
              step="0.5"
              min="0.1"
              className="form-input mono"
              value={newTask.duration}
              onChange={(e) => setNewTask({ ...newTask, duration: e.target.value })}
              required
            />
          </div>
          <div className="form-group" style={{ flex: '2 1 160px' }}>
            <label className="form-label">Predecessors (comma-separated)</label>
            <input
              type="text"
              placeholder="e.g. T1, T2"
              className="form-input mono"
              value={newTask.dependencies}
              onChange={(e) => setNewTask({ ...newTask, dependencies: e.target.value })}
            />
          </div>
          <button type="submit" className="btn btn-primary" style={{ height: '38px' }}>
            <Plus size={16} /> Add Task
          </button>
        </form>
      </div>

      {/* JSON Editor Modal */}
      {showJsonModal && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.7)',
            backdropFilter: 'blur(8px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '1rem',
          }}
        >
          <div className="card" style={{ maxWidth: '700px', width: '100%', maxHeight: '85vh', display: 'flex', flexDirection: 'column' }}>
            <div className="card-header">
              <h3 className="card-title">
                <FileText size={18} /> Edit Workflow JSON Payload
              </h3>
            </div>
            <textarea
              className="form-input mono"
              rows={16}
              style={{ width: '100%', fontSize: '0.8rem', resize: 'vertical' }}
              value={jsonInput}
              onChange={(e) => setJsonInput(e.target.value)}
            />
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem' }}>
              <button className="btn btn-secondary" onClick={() => setShowJsonModal(false)}>
                Cancel
              </button>
              <button className="btn btn-primary" onClick={handleApplyJson}>
                Apply Workflow JSON
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
