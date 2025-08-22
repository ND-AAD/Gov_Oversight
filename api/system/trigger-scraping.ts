import { VercelRequest, VercelResponse } from '@vercel/node';

interface ScrapingTriggerRequest {
  force_full_scan?: boolean;
  specific_sites?: string[]; // Array of site IDs to scrape specifically
  reason?: string;
}

export default async function handler(req: VercelRequest, res: VercelResponse) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { 
      force_full_scan = false, 
      specific_sites = [], 
      reason = 'Manual trigger via Vercel API' 
    } = req.body as ScrapingTriggerRequest;

    const githubToken = process.env.GITHUB_TOKEN;
    const githubRepo = process.env.GITHUB_REPOSITORY || 'your-username/Gov_Oversight';

    if (!githubToken) {
      return res.status(500).json({ 
        error: 'Server configuration error: GitHub token not available' 
      });
    }

    // Trigger GitHub Actions workflow
    const workflowUrl = `https://api.github.com/repos/${githubRepo}/actions/workflows/scrape.yml/dispatches`;
    
    const workflowInputs: Record<string, string> = {
      force_full_scan: force_full_scan.toString(),
      reason: reason,
      triggered_by: 'vercel_api',
      timestamp: new Date().toISOString()
    };

    // Add specific sites if provided
    if (specific_sites.length > 0) {
      workflowInputs.specific_sites = specific_sites.join(',');
    }

    const response = await fetch(workflowUrl, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${githubToken}`,
        'Content-Type': 'application/json',
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'LA-2028-RFP-Monitor/1.0'
      },
      body: JSON.stringify({
        ref: 'main', // or your default branch
        inputs: workflowInputs
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      return res.status(500).json({ 
        error: 'Failed to trigger scraping workflow',
        details: errorText,
        status: response.status
      });
    }

    // Get recent workflow runs to provide run URL
    const runsUrl = `https://api.github.com/repos/${githubRepo}/actions/workflows/scrape.yml/runs?per_page=1`;
    let runUrl = undefined;
    
    try {
      const runsResponse = await fetch(runsUrl, {
        headers: {
          'Authorization': `Bearer ${githubToken}`,
          'Accept': 'application/vnd.github.v3+json',
          'User-Agent': 'LA-2028-RFP-Monitor/1.0'
        }
      });
      
      if (runsResponse.ok) {
        const runsData = await runsResponse.json();
        if (runsData.workflow_runs && runsData.workflow_runs.length > 0) {
          runUrl = runsData.workflow_runs[0].html_url;
        }
      }
    } catch (error) {
      // Don't fail the whole request if we can't get the run URL
      console.warn('Failed to get workflow run URL:', error);
    }

    return res.status(200).json({
      success: true,
      message: 'Scraping workflow triggered successfully',
      details: {
        force_full_scan,
        specific_sites: specific_sites.length > 0 ? specific_sites : 'all',
        reason,
        estimated_duration: force_full_scan ? '10-15 minutes' : '3-5 minutes'
      },
      workflow_run_url: runUrl,
      monitoring_tip: 'Check the GitHub Actions tab to monitor progress'
    });

  } catch (error) {
    console.error('Trigger scraping error:', error);
    return res.status(500).json({ 
      error: 'Internal server error',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
}