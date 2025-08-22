import { VercelRequest, VercelResponse } from '@vercel/node';

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

interface SitesResponse {
  metadata: {
    last_updated: string;
    total_sites: number;
    version: string;
  };
  sites: SiteConfig[];
}

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
    const githubRepo = process.env.GITHUB_REPOSITORY || 'your-username/Gov_Oversight';
    const githubToken = process.env.GITHUB_TOKEN;

    // Fetch sites data from GitHub repository
    const dataUrl = `https://api.github.com/repos/${githubRepo}/contents/data/sites.json`;
    
    const headers: Record<string, string> = {
      'Accept': 'application/vnd.github.v3+json',
      'User-Agent': 'LA-2028-RFP-Monitor/1.0'
    };

    if (githubToken) {
      headers['Authorization'] = `Bearer ${githubToken}`;
    }

    const response = await fetch(dataUrl, { headers });

    if (!response.ok) {
      if (response.status === 404) {
        // Return empty data structure if file doesn't exist yet
        return res.status(200).json({
          metadata: {
            last_updated: new Date().toISOString(),
            total_sites: 0,
            version: '1.0'
          },
          sites: []
        });
      }
      throw new Error(`GitHub API error: ${response.status} ${response.statusText}`);
    }

    const fileData = await response.json();
    
    // Decode base64 content
    const content = Buffer.from(fileData.content, 'base64').toString('utf-8');
    const sitesData: SitesResponse = JSON.parse(content);

    // Optional: Filter based on query parameters
    const { status, limit, include_inactive } = req.query;

    let filteredSites = sitesData.sites;

    if (status && typeof status === 'string') {
      filteredSites = filteredSites.filter(site => 
        site.status.toLowerCase() === status.toLowerCase()
      );
    }

    if (include_inactive !== 'true') {
      filteredSites = filteredSites.filter(site => 
        site.status !== 'inactive' && site.status !== 'disabled' && site.status !== 'deleted'
      );
    }

    if (limit && typeof limit === 'string') {
      const limitNum = parseInt(limit, 10);
      if (!isNaN(limitNum) && limitNum > 0) {
        filteredSites = filteredSites.slice(0, limitNum);
      }
    }

    return res.status(200).json({
      metadata: {
        ...sitesData.metadata,
        filtered_count: filteredSites.length,
        total_count: sitesData.sites.length
      },
      sites: filteredSites
    });

  } catch (error) {
    console.error('Error fetching sites:', error);
    return res.status(500).json({ 
      error: 'Failed to fetch sites data',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
}