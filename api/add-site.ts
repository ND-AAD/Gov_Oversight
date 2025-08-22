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

function generateSiteId(name: string): string {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, '')
    .replace(/\s+/g, '_')
    .substring(0, 20);
}

function createSiteConfig(siteData: SiteSubmission): any {
  const siteId = generateSiteId(siteData.name);
  
  // Create default field mappings if none provided
  const defaultFieldMappings = [
    {
      alias: "status",
      selector: ".status, .rfp-status, [class*='status']",
      data_type: "text",
      training_value: "Active",
      confidence_score: 0.0,
      xpath: null,
      regex_pattern: null,
      fallback_selectors: [],
      last_validated: new Date().toISOString(),
      validation_errors: [],
      expected_format: null,
      status: "untested",
      consecutive_failures: 0
    },
    {
      alias: "posted_date",
      selector: ".posted, .date-posted, [class*='posted'], [class*='date']",
      data_type: "date",
      training_value: "2024-12-20",
      confidence_score: 0.0,
      xpath: null,
      regex_pattern: null,
      fallback_selectors: [],
      last_validated: new Date().toISOString(),
      validation_errors: [],
      expected_format: null,
      status: "untested",
      consecutive_failures: 0
    }
  ];

  // Convert user field mappings to site config format
  const fieldMappings = siteData.field_mappings && siteData.field_mappings.length > 0
    ? siteData.field_mappings.map(fm => ({
        alias: fm.alias,
        selector: `[data-field="${fm.alias}"], .${fm.alias}, #${fm.alias}`,
        data_type: fm.data_type,
        training_value: fm.sample_value,
        confidence_score: 0.0,
        xpath: null,
        regex_pattern: null,
        fallback_selectors: [],
        last_validated: new Date().toISOString(),
        validation_errors: [],
        expected_format: null,
        status: "untested",
        consecutive_failures: 0
      }))
    : defaultFieldMappings;

  return {
    id: siteId,
    name: siteData.name,
    base_url: siteData.base_url,
    main_rfp_page_url: siteData.main_rfp_page_url || siteData.base_url,
    sample_rfp_url: siteData.sample_rfp_url || "",
    field_mappings: fieldMappings,
    status: "testing",
    last_scrape: null,
    last_test: null,
    rfp_count: 0,
    test_results: null,
    description: siteData.description || "Added via Vercel API",
    contact_info: null,
    terms_of_service_url: null,
    robots_txt_compliant: true,
    scraper_settings: {
      delay_between_requests: 2.0,
      timeout: 30,
      max_retries: 3,
      respect_robots_txt: true
    }
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

    // Get current sites.json file
    const sitesUrl = `https://api.github.com/repos/${githubRepo}/contents/data/sites.json`;
    const getResponse = await fetch(sitesUrl, {
      headers: {
        'Authorization': `Bearer ${githubToken}`,
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'LA-2028-RFP-Monitor/1.0'
      }
    });

    if (!getResponse.ok) {
      return res.status(404).json({ error: 'Sites configuration not found' });
    }

    const fileData = await getResponse.json();
    const fileSha = fileData.sha;
    const content = Buffer.from(fileData.content, 'base64').toString('utf-8');
    const sitesData = JSON.parse(content);

    // Create new site configuration
    const newSite = createSiteConfig(siteData);

    // Check if site already exists
    const existingSiteIndex = sitesData.sites.findIndex((site: any) => 
      site.id === newSite.id || site.name === newSite.name || site.base_url === newSite.base_url
    );

    if (existingSiteIndex !== -1) {
      return res.status(409).json({ 
        error: 'Site already exists with this name or URL',
        existing_site: sitesData.sites[existingSiteIndex]
      });
    }

    // Add new site to the list
    sitesData.sites.push(newSite);
    sitesData.metadata.last_updated = new Date().toISOString();
    sitesData.metadata.total_sites = sitesData.sites.filter((site: any) => site.status !== 'deleted').length;

    // Commit updated file to GitHub
    const updatedContent = JSON.stringify(sitesData, null, 2);
    const encodedContent = Buffer.from(updatedContent).toString('base64');

    const putResponse = await fetch(sitesUrl, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${githubToken}`,
        'Content-Type': 'application/json',
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'LA-2028-RFP-Monitor/1.0'
      },
      body: JSON.stringify({
        message: `Add new site: ${newSite.name} (via Vercel API)`,
        content: encodedContent,
        sha: fileSha
      })
    });

    if (!putResponse.ok) {
      const errorData = await putResponse.text();
      return res.status(500).json({ 
        error: 'Failed to add site to GitHub',
        details: errorData
      });
    }

    const commitResult = await putResponse.json();

    // Success response
    return res.status(200).json({
      success: true,
      message: `Site "${newSite.name}" has been added successfully`,
      site: newSite,
      commit_url: commitResult.commit.html_url,
      next_steps: [
        "Site will be automatically scraped within 6 hours",
        "You can trigger manual scraping via the dashboard",
        "Check the site status and configure field mappings if needed"
      ]
    });

  } catch (error) {
    console.error('Add site error:', error);
    return res.status(500).json({ 
      error: 'Internal server error',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
}