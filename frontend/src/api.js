/**
 * api.js - Backend REST API Client for AI Agent Workflow Scheduler
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

async function handleResponse(response) {
  if (!response.ok) {
    let errorDetail = 'API Request Failed';
    try {
      const errorJson = await response.json();
      if (errorJson.detail) {
        if (typeof errorJson.detail === 'string') {
          errorDetail = errorJson.detail;
        } else if (errorJson.detail.message) {
          errorDetail = `${errorJson.detail.message}: ${errorJson.detail.errors?.join(', ') || ''}`;
        } else {
          errorDetail = JSON.stringify(errorJson.detail);
        }
      }
    } catch {
      errorDetail = `HTTP ${response.status}: ${response.statusText}`;
    }
    throw new Error(errorDetail);
  }
  return response.json();
}

export const api = {
  async getHealth() {
    const res = await fetch(`${API_BASE}/`);
    return handleResponse(res);
  },

  async validateWorkflow(workflow) {
    const res = await fetch(`${API_BASE}/workflow/validate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(workflow),
    });
    return handleResponse(res);
  },

  async getTopologicalSort(workflow) {
    const res = await fetch(`${API_BASE}/workflow/topological-sort`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(workflow),
    });
    return handleResponse(res);
  },

  async getCriticalPath(workflow) {
    const res = await fetch(`${API_BASE}/workflow/critical-path`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(workflow),
    });
    return handleResponse(res);
  },

  async scheduleGreedy(workflow, priorityPolicy = 'CRITICAL_PATH') {
    const res = await fetch(`${API_BASE}/schedule/greedy`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        workflow,
        priority_policy: priorityPolicy,
      }),
    });
    return handleResponse(res);
  },

  async scheduleBacktrack(workflow, maxStates = 20000, timeLimit = 3.0) {
    const res = await fetch(`${API_BASE}/schedule/backtrack`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        workflow,
        max_states: maxStates,
        time_limit_sec: timeLimit,
      }),
    });
    return handleResponse(res);
  },

  async scheduleBranchAndBound(workflow, maxStates = 20000, timeLimit = 3.0) {
    const res = await fetch(`${API_BASE}/schedule/branch-and-bound`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        workflow,
        max_states: maxStates,
        time_limit_sec: timeLimit,
      }),
    });
    return handleResponse(res);
  },

  async compareAlgorithms(workflow, maxStates = 20000, timeLimit = 3.0) {
    const res = await fetch(`${API_BASE}/schedule/compare`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        workflow,
        max_states: maxStates,
        time_limit_sec: timeLimit,
      }),
    });
    return handleResponse(res);
  },

  async generateRandomDag(params) {
    const res = await fetch(`${API_BASE}/workflow/random`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    return handleResponse(res);
  },

  async runBenchmark(params) {
    const res = await fetch(`${API_BASE}/benchmark/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    return handleResponse(res);
  },

  async getSampleWorkflows() {
    const res = await fetch(`${API_BASE}/sample-workflows`);
    return handleResponse(res);
  },

  async getSampleWorkflow(filename) {
    const res = await fetch(`${API_BASE}/sample-workflows/${filename}`);
    return handleResponse(res);
  },
};
