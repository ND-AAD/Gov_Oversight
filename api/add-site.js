/**
 * Serverless Function: Add Site Request Handler
 * 
 * Receives site addition requests from the frontend and creates GitHub issues
 * for automated processing. Maintains exact same UX while enabling GitHub-native backend.
 * 
 * Deployment: Vercel Functions (recommended) or Netlify Functions
 * Endpoint: /api/add-site
 */

module.exports = async function handler(req, res) {
  // Enable CORS for frontend
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }
  
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const siteData = req.body;
    
    // Validate required fields (same as frontend validation)
    if (!siteData.name || !siteData.base_url) {
      return res.status(400).json({ 
        error: 'Missing required fields: name and base_url' 
      });
    }

    // Create GitHub issue for site addition
    const issueData = await createSiteAdditionIssue(siteData);
    
    // Return success response (matches existing frontend expectations)
    res.status(201).json({
      id: `pending_${Date.now()}`,
      name: siteData.name,
      status: 'queued',
      github_issue: issueData.number,
      message: 'Site addition request created successfully'
    });

  } catch (error) {
    console.error('Site addition failed:', error);
    res.status(500).json({ 
      error: 'Failed to process site addition request',
      details: error.message 
    });
  }
}

/**
 * Create GitHub issue for site addition using GitHub API
 */
async function createSiteAdditionIssue(siteData) {
  const { Octokit } = require('@octokit/rest');
  
  const octokit = new Octokit({
    auth: process.env.GITHUB_TOKEN
  });

  // Format field mappings for GitHub issue
  const fieldMappingsText = siteData.field_mappings?.map(mapping => 
    `- **${mapping.alias}:** "${mapping.sample_value}" (${mapping.data_type || 'text'})`
  ).join('\n') || 'No field mappings provided (basic configuration)';

  // Create structured GitHub issue
  const issueBody = `## Site Addition Request

**Site Name:** ${siteData.name}
**Base URL:** ${siteData.base_url}
**Main RFP Page:** ${siteData.main_rfp_page_url || siteData.base_url}
**Sample RFP URL:** ${siteData.sample_rfp_url || 'Not provided'}

### Description
${siteData.description || 'No description provided'}

### Field Mappings
${fieldMappingsText}

### Metadata
- **Submitted:** ${new Date().toISOString()}
- **User Agent:** ${process.env.VERCEL_REGION || 'serverless'}
- **Processing Status:** Pending

---
*This issue was created automatically by the LA 2028 RFP Monitor frontend.*
*The site addition workflow will process this request and update the status.*`;

  const issue = await octokit.rest.issues.create({
    owner: process.env.GITHUB_OWNER || 'ND-AAD',
    repo: process.env.GITHUB_REPO || 'Gov_Oversight',
    title: `Add Site: ${siteData.name}`,
    body: issueBody,
    labels: ['site-addition', 'automated']
  });

  return issue.data;
}
