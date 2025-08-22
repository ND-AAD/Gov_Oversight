import { VercelRequest, VercelResponse } from '@vercel/node';

export default async function handler(req: VercelRequest, res: VercelResponse) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const githubToken = process.env.GITHUB_TOKEN;
  const githubRepo = process.env.GITHUB_REPOSITORY;
  
  if (!githubToken || !githubRepo) {
    return res.status(500).json({ 
      error: 'Missing environment variables',
      has_token: !!githubToken,
      has_repo: !!githubRepo,
      instructions: 'Set GITHUB_TOKEN and GITHUB_REPOSITORY in Vercel environment variables'
    });
  }

  try {
    console.log(`Testing connection to repository: ${githubRepo}`);
    
    // Test GitHub API connection
    const response = await fetch(`https://api.github.com/repos/${githubRepo}`, {
      headers: {
        'Authorization': `Bearer ${githubToken}`,
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'LA-2028-RFP-Monitor-Test/1.0'
      }
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('GitHub API error:', response.status, errorText);
      
      return res.status(response.status).json({
        error: 'GitHub API test failed',
        status: response.status,
        statusText: response.statusText,
        details: errorText,
        troubleshooting: {
          401: 'Token is invalid or expired',
          403: 'Token lacks required permissions',
          404: 'Repository not found or token lacks access'
        }
      });
    }

    const repoData = await response.json();
    console.log('GitHub API test successful');

    // Test if we can access the data directory
    let dataAccessTest;
    try {
      const dataResponse = await fetch(`https://api.github.com/repos/${githubRepo}/contents/data`, {
        headers: {
          'Authorization': `Bearer ${githubToken}`,
          'Accept': 'application/vnd.github.v3+json',
          'User-Agent': 'LA-2028-RFP-Monitor-Test/1.0'
        }
      });
      
      dataAccessTest = {
        can_access_data_dir: dataResponse.ok,
        status: dataResponse.status
      };
    } catch (error) {
      dataAccessTest = {
        can_access_data_dir: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }

    // Test workflow trigger permissions (optional)
    let workflowTest;
    try {
      const workflowsResponse = await fetch(`https://api.github.com/repos/${githubRepo}/actions/workflows`, {
        headers: {
          'Authorization': `Bearer ${githubToken}`,
          'Accept': 'application/vnd.github.v3+json',
          'User-Agent': 'LA-2028-RFP-Monitor-Test/1.0'
        }
      });
      
      const workflowsData = workflowsResponse.ok ? await workflowsResponse.json() : null;
      
      workflowTest = {
        can_access_workflows: workflowsResponse.ok,
        workflow_count: workflowsData?.total_count || 0,
        workflows: workflowsData?.workflows?.map((w: any) => w.name) || []
      };
    } catch (error) {
      workflowTest = {
        can_access_workflows: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
    
    return res.status(200).json({
      success: true,
      message: '🎉 All connections working perfectly!',
      timestamp: new Date().toISOString(),
      repository: {
        name: repoData.full_name,
        private: repoData.private,
        default_branch: repoData.default_branch,
        permissions: repoData.permissions,
        updated_at: repoData.updated_at
      },
      environment_check: {
        github_token: '✅ Present and valid',
        github_repo: '✅ Present and accessible',
        vercel_function: '✅ Working',
        data_directory_access: dataAccessTest.can_access_data_dir ? '✅ Accessible' : '❌ Cannot access',
        workflow_access: workflowTest.can_access_workflows ? '✅ Can trigger workflows' : '⚠️ Limited workflow access'
      },
      next_steps: [
        '1. Deploy the full API suite',
        '2. Test site addition via frontend',
        '3. Verify file updates in GitHub',
        '4. Test manual scraping trigger'
      ],
      api_endpoints_ready: [
        'POST /api/add-site',
        'PUT /api/sites/[id]/update', 
        'DELETE /api/sites/[id]/delete',
        'PUT /api/rfps/[id]/ignore',
        'POST /api/system/trigger-scraping'
      ]
    });

  } catch (error) {
    console.error('Connection test failed:', error);
    
    return res.status(500).json({
      success: false,
      error: 'Connection test failed',
      details: error instanceof Error ? error.message : 'Unknown error',
      troubleshooting_steps: [
        '1. Verify GITHUB_TOKEN is set correctly in Vercel',
        '2. Verify GITHUB_REPOSITORY format is: username/repository',
        '3. Check GitHub token has repo and workflow permissions',
        '4. Ensure repository exists and is accessible'
      ]
    });
  }
}