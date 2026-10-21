import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import DashboardView from './components/DashboardView';
import WorkflowBuilderView from './components/WorkflowBuilderView';
import DagExplorerView from './components/DagExplorerView';
import CriticalPathView from './components/CriticalPathView';
import GanttView from './components/GanttView';
import ComparisonView from './components/ComparisonView';
import BenchmarkView from './components/BenchmarkView';
import AboutAlgorithmsView from './components/AboutAlgorithmsView';
import { api } from './api';

const DEFAULT_WORKFLOW = {
  workflow_id: 'research_workflow_01',
  name: 'Research Agent Workflow',
  number_of_workers: 2,
  tasks: [
    { task_id: 'T1', name: 'Search Web', duration: 5.0, dependencies: [], task_type: 'research' },
    { task_id: 'T2', name: 'Read Papers', duration: 8.0, dependencies: [], task_type: 'research' },
    { task_id: 'T3', name: 'Analyze', duration: 10.0, dependencies: ['T1', 'T2'], task_type: 'analysis' },
    { task_id: 'T4', name: 'Generate Report', duration: 7.0, dependencies: ['T3'], task_type: 'document' },
    { task_id: 'T5', name: 'Review', duration: 5.0, dependencies: ['T4'], task_type: 'review' },
  ],
};

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [isBackendOnline, setIsBackendOnline] = useState(false);
  const [workflow, setWorkflow] = useState(DEFAULT_WORKFLOW);
  const [sampleList, setSampleList] = useState([]);
  const [validation, setValidation] = useState(null);
  const [criticalPath, setCriticalPath] = useState(null);
  const [topologicalOrder, setTopologicalOrder] = useState(null);
  const [greedySchedule, setGreedySchedule] = useState(null);
  const [exactSchedule, setExactSchedule] = useState(null);
  const [activeSchedule, setActiveSchedule] = useState(null);
  const [comparison, setComparison] = useState(null);
  const [loading, setLoading] = useState(false);
  const [globalError, setGlobalError] = useState(null);

  // Check health and load initial samples on mount
  useEffect(() => {
    let isMounted = true;

    async function init() {
      try {
        await api.getHealth();
        if (!isMounted) return;
        setIsBackendOnline(true);

        // Fetch sample workflow catalog
        const sampleRes = await api.getSampleWorkflows();
        if (isMounted && sampleRes.samples) {
          setSampleList(sampleRes.samples);
        }

        // Try to load default research workflow from server
        try {
          const loadedWf = await api.getSampleWorkflow('research_workflow.json');
          if (isMounted && loadedWf) {
            setWorkflow(loadedWf);
            await refreshWorkflowAlgorithms(loadedWf);
            return;
          }
        } catch {
          // Fallback to local default
        }

        await refreshWorkflowAlgorithms(DEFAULT_WORKFLOW);
      } catch (err) {
        if (!isMounted) return;
        setIsBackendOnline(false);
        setGlobalError('Could not connect to FastAPI backend at http://127.0.0.1:8000. Start the backend with: python -m uvicorn backend.main:app');
      }
    }

    init();
    return () => { isMounted = false; };
  }, []);

  // Compute validation, critical path, and initial greedy schedule for a workflow
  const refreshWorkflowAlgorithms = async (wf) => {
    setLoading(true);
    setGlobalError(null);
    try {
      // 1. Validation
      const valRes = await api.validateWorkflow(wf);
      setValidation(valRes);

      if (!valRes.valid) {
        setCriticalPath(null);
        setTopologicalOrder(null);
        setGreedySchedule(null);
        setExactSchedule(null);
        setActiveSchedule(null);
        setComparison(null);
        return;
      }

      // 2. Critical Path
      const cpRes = await api.getCriticalPath(wf);
      setCriticalPath(cpRes);
      setTopologicalOrder(cpRes.topological_order);

      // 3. Greedy Schedule
      const gRes = await api.scheduleGreedy(wf, 'CRITICAL_PATH');
      setGreedySchedule(gRes);
      setActiveSchedule(gRes);
    } catch (err) {
      setGlobalError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Handler: Validate button
  const handleValidate = async () => {
    await refreshWorkflowAlgorithms(workflow);
  };

  // Handler: Run Greedy with specific policy
  const handleRunGreedy = async (policy = 'CRITICAL_PATH') => {
    setLoading(true);
    setGlobalError(null);
    try {
      const gRes = await api.scheduleGreedy(workflow, policy);
      setGreedySchedule(gRes);
      setActiveSchedule(gRes);
    } catch (err) {
      setGlobalError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Handler: Run Branch & Bound
  const handleRunExact = async () => {
    setLoading(true);
    setGlobalError(null);
    try {
      const bnbRes = await api.scheduleBranchAndBound(workflow);
      setExactSchedule(bnbRes);
      setActiveSchedule(bnbRes);
    } catch (err) {
      setGlobalError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Handler: Run Gantt Schedule
  const handleRunSchedule = async (algorithm, policy) => {
    setLoading(true);
    setGlobalError(null);
    try {
      if (algorithm === 'greedy') {
        const res = await api.scheduleGreedy(workflow, policy);
        setActiveSchedule(res);
        setGreedySchedule(res);
      } else if (algorithm === 'branch_and_bound') {
        const res = await api.scheduleBranchAndBound(workflow);
        setActiveSchedule(res);
        setExactSchedule(res);
      } else if (algorithm === 'backtrack') {
        const res = await api.scheduleBacktrack(workflow);
        setActiveSchedule(res);
        setExactSchedule(res);
      }
    } catch (err) {
      setGlobalError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Handler: Compare All
  const handleRunCompare = async () => {
    setLoading(true);
    setGlobalError(null);
    try {
      const compRes = await api.compareAlgorithms(workflow);
      setComparison(compRes);
      if (compRes.algorithms['Branch and Bound']) {
        setExactSchedule(compRes.algorithms['Branch and Bound']);
      }
      if (compRes.algorithms['Greedy (Critical Path)']) {
        setGreedySchedule(compRes.algorithms['Greedy (Critical Path)']);
      }
    } catch (err) {
      setGlobalError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Handler: Load sample preset
  const handleLoadSample = async (filename) => {
    setLoading(true);
    setGlobalError(null);
    try {
      const loaded = await api.getSampleWorkflow(filename);
      setWorkflow(loaded);
      await refreshWorkflowAlgorithms(loaded);
    } catch (err) {
      setGlobalError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        isBackendOnline={isBackendOnline}
        currentWorkflow={workflow}
      />

      <main className="main-content">
        {globalError && (
          <div className="alert alert-danger" style={{ marginBottom: '1.5rem' }}>
            <span>{globalError}</span>
          </div>
        )}

        {activeTab === 'dashboard' && (
          <DashboardView
            workflow={workflow}
            validation={validation}
            criticalPath={criticalPath}
            greedySchedule={greedySchedule}
            exactSchedule={exactSchedule}
            comparison={comparison}
            setActiveTab={setActiveTab}
            onRunGreedy={() => handleRunGreedy('CRITICAL_PATH')}
            onRunExact={handleRunExact}
            onRunCompare={handleRunCompare}
            loading={loading}
          />
        )}

        {activeTab === 'builder' && (
          <WorkflowBuilderView
            workflow={workflow}
            setWorkflow={(newWf) => {
              setWorkflow(newWf);
              refreshWorkflowAlgorithms(newWf);
            }}
            validation={validation}
            onValidate={handleValidate}
            onLoadSample={handleLoadSample}
            sampleList={sampleList}
            loading={loading}
          />
        )}

        {activeTab === 'dag' && (
          <DagExplorerView
            workflow={workflow}
            criticalPath={criticalPath}
            topologicalOrder={topologicalOrder}
          />
        )}

        {activeTab === 'critical-path' && (
          <CriticalPathView
            workflow={workflow}
            criticalPath={criticalPath}
            topologicalOrder={topologicalOrder}
          />
        )}

        {activeTab === 'gantt' && (
          <GanttView
            workflow={workflow}
            activeSchedule={activeSchedule}
            onRunSchedule={handleRunSchedule}
            loading={loading}
          />
        )}

        {activeTab === 'comparison' && (
          <ComparisonView
            workflow={workflow}
            comparison={comparison}
            onRunCompare={handleRunCompare}
            loading={loading}
          />
        )}

        {activeTab === 'benchmark' && <BenchmarkView />}

        {activeTab === 'about' && <AboutAlgorithmsView />}
      </main>
    </div>
  );
}
