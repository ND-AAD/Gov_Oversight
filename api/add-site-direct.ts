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

interface SiteConfig {
  id: string;
  name: string;
  base_url: string;
  main_rfp_page_url: string;
  sample_rfp_url?: string;
  field_mappings: Array<{
    alias: string;
    selector: string;
    data_type: string;
    training_value: string;
    confidence_score: number;
    xpath?: string;
    regex_pattern?: string;
    fallback_selectors: string[];
    last_validated?: string;
    validation_errors: string[];
    expected_format?: string;
    status: string;
    consecutive_failures: number;
  }>;
  status: string;
  last_scrape?: string;
  last_test?: string;
  rfp_count: number;
  test_results?: any;
  description?: string;
  contact_info?: any;
  terms_of_service_url?: string;
  robots_txt_compliant: boolean;
  scraper_settings: {
    delay_between_requests: number;
    timeout: number;
    max_retries: number;
    respect_robots_txt: boolean;
  };
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

    const githubToken = process.env.GITHUB_TOKEN;
    const githubRepo = process.env.GITHUB_REPOSITORY || 'your-username/Gov_Oversight';

    if (!githubToken) {
      return res.status(500).json({ 
        error: 'Server configuration error: GitHub token not available' 
      });
    }

    // Step 1: Get current sites.json file
    const sitesUrl = `https://api.github.com/repos/${githubRepo}/contents/data/sites.json`;
    const getResponse = await fetch(sitesUrl, {
      headers: {
        'Authorization': `Bearer ${githubToken}`,
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'LA-2028-RFP-Monitor/1.0'
      }
    });

    let currentSites: any = { sites: [], metadata: {} };
    let fileSha: string | undefined;

    if (getResponse.ok) {
      const fileData = await getResponse.json();
      fileSha = fileData.sha;
      
      // Decode existing content
      const content = Buffer.from(fileData.content, 'base64').toString('utf-8');
      currentSites = JSON.parse(content);
    } else if (getResponse.status === 404) {
      // File doesn't exist, create initial structure
      currentSites = {
        metadata: {
          last_updated: new Date().toISOString(),
          total_sites: 0,
          version: '1.0'
        },
        sites: []
      };
    } else {
      throw new Error(`Failed to fetch sites.json: ${getResponse.status} ${getResponse.statusText}`);
    }

    // Step 2: Create new site configuration
    const siteId = siteData.name.toLowerCase()
      .replace(/[^a-z0-9\s]/g, '')
      .replace(/\s+/g, '_')
      .substring(0, 50);

    // Check for duplicate IDs
    const existingIds = currentSites.sites.map((site: any) => site.id);
    if (existingIds.includes(siteId)) {
      return res.status(400).json({ 
        error: `Site with ID "${siteId}" already exists` 
      });
    }

    const newSite: SiteConfig = {
      id: siteId,
      name: siteData.name,
      base_url: siteData.base_url,
      main_rfp_page_url: siteData.main_rfp_page_url || siteData.base_url,
      sample_rfp_url: siteData.sample_rfp_url || '',
      field_mappings: siteData.field_mappings?.map(fm => ({
        alias: fm.alias,
        selector: `[data-field="${fm.alias}"]`, // Placeholder selector
        data_type: fm.data_type,
        training_value: fm.sample_value,
        confidence_score: 0.0,
        xpath: undefined,
        regex_pattern: undefined,
        fallback_selectors: [],
        last_validated: undefined,
        validation_errors: [],
        expected_format: undefined,
        status: 'untested',
        consecutive_failures: 0
      })) || [],
      status: 'testing',
      last_scrape: undefined,
      last_test: undefined,
      rfp_count: 0,
      test_results: undefined,
      description: siteData.description || `Added via Vercel API on ${new Date().toISOString()}`,
      contact_info: undefined,
      terms_of_service_url: undefined,
      robots_txt_compliant: true,
      scraper_settings: {
        delay_between_requests: 2.0,
        timeout: 30,
        max_retries: 3,
        respect_robots_txt: true
      }
    };

    // Step 3: Add new site to array
    currentSites.sites.push(newSite);
    
    // Update metadata
    currentSites.metadata.last_updated = new Date().toISOString();
    currentSites.metadata.total_sites = currentSites.sites.length;

    // Step 4: Commit updated file back to GitHub
    const updatedContent = JSON.stringify(currentSites, null, 2);
    const encodedContent = Buffer.from(updatedContent).toString('base64');

    const commitData = {
      message: `Add site: ${siteData.name} (via Vercel API)`,
      content: encodedContent,
      ...(fileSha && { sha: fileSha }) // Include SHA if file exists
    };

    const putResponse = await fetch(sitesUrl, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${githubToken}`,
        'Content-Type': 'application/json',
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'LA-2028-RFP-Monitor/1.0'
      },
      body: JSON.stringify(commitData)
    });

    if (!putResponse.ok) {
      const errorData = await putResponse.text();
      console.error('GitHub API error:', errorData);
      return res.status(500).json({ 
        error: 'Failed to update sites.json',
        details: errorData
      });
    }

    const commitResult = await putResponse.json();

    // Step 5: Trigger GitHub Actions workflow (optional)
    try {
      await triggerScrapingWorkflow(githubToken, githubRepo);
    } catch (error) {
      console.warn('Failed to trigger scraping workflow:', error);
      // Don't fail the request if workflow trigger fails
    }

    // Success response
    return res.status(200).json({
      success: true,
      message: `Site "${siteData.name}" has been added successfully and scraping will begin shortly`,
      site_id: siteId,
      commit_url: commitResult.commit.html_url,
      estimated_processing_time: '2-5 minutes'
    });

  } catch (error) {
    console.error('Add site error:', error);
    return res.status(500).json({ 
      error: 'Internal server error',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
}

async function triggerScrapingWorkflow(token: string, repo: string): Promise<void> {
  try {
    // Trigger the scraping workflow
    const workflowUrl = `https://api.github.com/repos/${repo}/actions/workflows/scrape.yml/dispatches`;
    
    const response = await fetch(workflowUrl, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'LA-2028-RFP-Monitor/1.0'
      },
      body: JSON.stringify({
        ref: 'main', // or your default branch
        inputs: {
          force_full_scan: 'false',
          reason: 'New site added via Vercel API'
        }
      })
    });

    if (!response.ok) {
      throw new Error(`Workflow trigger failed: ${response.status} ${response.statusText}`);
    }

    console.log('Successfully triggered scraping workflow');
  } catch (error) {
    console.error('Failed to trigger workflow:', error);
    throw error;
  }
}