/**
 * GitHub Actions status checking utilities
 */

interface GitHubWorkflowRun {
  id: number;
  status: 'queued' | 'in_progress' | 'completed';
  conclusion: 'success' | 'failure' | 'cancelled' | 'skipped' | null;
  created_at: string;
  updated_at: string;
  workflow_id: number;
}

interface GitHubWorkflowRunsResponse {
  total_count: number;
  workflow_runs: GitHubWorkflowRun[];
}

/**
 * Check if GitHub Actions are currently running for site processing
 */
export const checkGitHubActionsStatus = async (): Promise<{
  isProcessing: boolean;
  lastRun?: string;
  nextScheduled?: string;
}> => {
  try {
    // Check the process-pending-sites workflow
    const response = await fetch(
      'https://api.github.com/repos/ND-AAD/Gov_Oversight/actions/workflows/process-pending-sites.yml/runs?per_page=5'
    );
    
    if (!response.ok) {
      throw new Error('Failed to fetch workflow status');
    }
    
    const data: GitHubWorkflowRunsResponse = await response.json();
    
    // Check if any runs are currently in progress
    const isProcessing = data.workflow_runs.some(
      run => run.status === 'queued' || run.status === 'in_progress'
    );
    
    // Get last completed run
    const lastCompleted = data.workflow_runs
      .filter(run => run.status === 'completed')
      .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())[0];
    
    // Calculate next scheduled run (every hour)
    let nextScheduled: string | undefined;
    if (lastCompleted) {
      const lastRun = new Date(lastCompleted.updated_at);
      const nextRun = new Date(lastRun.getTime() + 60 * 60 * 1000); // Add 1 hour
      nextScheduled = nextRun.toISOString();
    }
    
    return {
      isProcessing,
      lastRun: lastCompleted?.updated_at,
      nextScheduled
    };
    
  } catch (error) {
    console.warn('Failed to check GitHub Actions status:', error);
    return {
      isProcessing: false
    };
  }
};

/**
 * Get human-readable status message
 */
export const getProcessingStatusMessage = (status: {
  isProcessing: boolean;
  lastRun?: string;
  nextScheduled?: string;
}): string => {
  if (status.isProcessing) {
    return 'Site processing is currently running...';
  }
  
  if (status.nextScheduled) {
    const nextRun = new Date(status.nextScheduled);
    const now = new Date();
    const minutesUntil = Math.ceil((nextRun.getTime() - now.getTime()) / (1000 * 60));
    
    if (minutesUntil <= 0) {
      return 'Site processing should start any moment...';
    } else if (minutesUntil < 60) {
      return `Next site processing in ~${minutesUntil} minutes`;
    } else {
      return `Next site processing in ~${Math.ceil(minutesUntil / 60)} hours`;
    }
  }
  
  return 'Site processing runs every hour';
};
