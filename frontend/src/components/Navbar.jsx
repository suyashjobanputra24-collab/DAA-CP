import React from 'react';
import {
  Activity,
  Layers,
  GitFork,
  Clock,
  Calendar,
  BarChart3,
  FlaskConical,
  BookOpen,
  Wifi,
  WifiOff,
} from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, isBackendOnline, currentWorkflow }) {
  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: Activity },
    { id: 'builder', label: 'Workflow Builder', icon: Layers },
    { id: 'dag', label: 'DAG Explorer', icon: GitFork },
    { id: 'critical-path', label: 'Critical Path', icon: Clock },
    { id: 'gantt', label: 'Gantt / Schedule', icon: Calendar },
    { id: 'comparison', label: 'Comparison', icon: BarChart3 },
    { id: 'benchmark', label: 'Benchmark Lab', icon: FlaskConical },
    { id: 'about', label: 'DAA Algorithms', icon: BookOpen },
  ];

  return (
    <header className="navbar">
      <div className="nav-brand">
        <div className="brand-icon-wrapper">
          <GitFork size={20} />
        </div>
        <div>
          <span style={{ color: 'var(--text-primary)' }}>AI Agent</span>{' '}
          <span style={{ color: 'var(--primary)' }}>Scheduler</span>
          <span style={{ fontSize: '0.65rem', marginLeft: '0.5rem', color: 'var(--text-muted)', fontWeight: 500 }}>
            DAA LAB
          </span>
        </div>
      </div>

      <nav className="nav-tabs">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              className={`nav-tab-btn ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              <Icon size={15} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="nav-status">
        <div className="status-badge">
          <div className={`status-dot ${isBackendOnline ? '' : 'offline'}`} />
          <span>{isBackendOnline ? 'FastAPI 2.0.0 Online' : 'Connecting...'}</span>
        </div>
        <div className="status-badge" style={{ color: 'var(--cyan)' }}>
          <span>{currentWorkflow?.number_of_workers || 2} Workers</span>
        </div>
      </div>
    </header>
  );
}
