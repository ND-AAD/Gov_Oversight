import { VercelRequest, VercelResponse } from '@vercel/node';

interface SiteSubmission {
  name: string;
  base_url: string;
  main_rfp_page_url: string;
  sample_rfp_url?: string;
  description?: string;
  field_mappings?: Array<{
    alias: string;
    sample_value: string;
    data_type: string;
  }>;
}

function formatGitHubIssueBody(siteData: SiteSubmission): string {
  const fieldMappingsText = siteData.field_mappings && siteData.field_mappings.length > 0
    ? siteData.field_mappings
        .map(fm => `- ${fm.alias.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())} → "${fm.sample_value}" (${fm.data_type})`)
        .join('\n')
    : '- Status → "Active" (text)\n- Posted Date → "2024-12-20" (date)\n- Contract Value → "$50,000" (currency)';

  return `**Site Information:**
- Name: ${siteData.name}
- Base URL: ${siteData.base_url}
- Main RFP Page: ${siteData.main_rfp_page_url}
- Sample RFP URL: ${siteData.sample_rfp_url || 'N/A'}

**Field Mappings:**
${fieldMappingsText}

**Description:**
${siteData.description || 'Added via web form submission'}

---
*Submitted via LA 2028 RFP Monitor web interface*`;
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
    const siteData = req.body as SiteSubmission;

    // Basic validation
    if (!siteData.name || !siteData.base_url) {
      return res.status(400).json({ 
        error: 'Missing required fields: name and base_url are required' 
      });
    }

    // Validate URLs
    try {
      new URL(siteData.base_url);
      if (siteData.main_rfp_page_url) {
        new URL(siteData.main_rfp_page_url);
      }
      if (siteData.sample_rfp_url) {
        new URL(siteData.sample_rfp_url);
      }
    } catch (error) {
      return res.status(400).json({ 
        error: 'Invalid URL format provided' 
      });
    }

    // Create GitHub issue via API
    const githubToken = process.env.GITHUB_TOKEN;
    const githubRepo = process.env.GITHUB_REPOSITORY || 'your-username/Gov_Oversight';

    if (!githubToken) {
      return res.status(500).json({ 
        error: 'Server configuration error: GitHub token not available' 
      });
    }

    const issueTitle = `Add Site: ${siteData.name}`;
    const issueBody = formatGitHubIssueBody(siteData);

    const githubResponse = await fetch(`https://api.github.com/repos/${githubRepo}/issues`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${githubToken}`,
        'Content-Type': 'application/json',
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'LA-2028-RFP-Monitor/1.0'
      },
      body: JSON.stringify({
        title: issueTitle,
        body: issueBody,
        labels: ['site-addition']
      })
    });

    if (!githubResponse.ok) {
      const errorData = await githubResponse.text();
      console.error('GitHub API error:', errorData);
      return res.status(500).json({ 
        error: 'Failed to create GitHub issue',
        details: errorData
      });
    }

    const issue = await githubResponse.json();

    // Success response
    return res.status(200).json({
      success: true,
      message: `Site "${siteData.name}" has been submitted for processing`,
      github_issue_url: issue.html_url,
      github_issue_number: issue.number,
      estimated_processing_time: '5-10 minutes'
    });

  } catch (error) {
    console.error('Add site error:', error);
    return res.status(500).json({ 
      error: 'Internal server error',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
}