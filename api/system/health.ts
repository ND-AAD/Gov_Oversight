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

  try {
    const githubToken = process.env.GITHUB_TOKEN;
    const githubRepo = process.env.GITHUB_REPOSITORY || 'your-username/Gov_Oversight';

    const health = {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      version: '2.0.0-vercel',
      api_mode: 'direct_file_updates',
      environment: process.env.NODE_ENV || 'production',
      checks: {
        github_token: !!githubToken,
        github_repo: !!githubRepo,
        vercel_functions: true
      }
    };

    // Test GitHub API connectivity if token is available
    if (githubToken && githubRepo) {
      try {
        const testResponse = await fetch(`https://api.github.com/repos/${githubRepo}`, {
          headers: {
            'Authorization': `Bearer ${githubToken}`,
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'LA-2028-RFP-Monitor/1.0'
          }
        });

        health.checks.github_api = testResponse.ok;
        
        if (testResponse.ok) {
          const repoData = await testResponse.json();
          health.repository = {
            name: repoData.full_name,
            private: repoData.private,
            updated_at: repoData.updated_at
          };
        }
      } catch (error) {
        health.checks.github_api = false;
        health.github_error = error instanceof Error ? error.message : 'Unknown error';
      }
    }

    // Check if all systems are healthy
    const allHealthy = Object.values(health.checks).every(check => check === true);
    if (!allHealthy) {
      health.status = 'degraded';
    }

    const statusCode = health.status === 'healthy' ? 200 : 503;
    
    return res.status(statusCode).json(health);

  } catch (error) {
    console.error('Health check error:', error);
    return res.status(503).json({
      status: 'unhealthy',
      timestamp: new Date().toISOString(),
      error: error instanceof Error ? error.message : 'Unknown error',
      checks: {
        github_token: !!process.env.GITHUB_TOKEN,
        github_repo: !!process.env.GITHUB_REPOSITORY,
        vercel_functions: false
      }
    });
  }
}