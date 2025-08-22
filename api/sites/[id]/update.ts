import { VercelRequest, VercelResponse } from '@vercel/node';

interface SiteUpdateRequest {
  name?: string;
  base_url?: string;
  main_rfp_page_url?: string;
  sample_rfp_url?: string;
  description?: string;
  field_mappings?: Array<{
    alias: string;
    sample_value: string;
    data_type: string;
  }>;
  status?: 'active' | 'testing' | 'disabled' | 'error';
}

export default async function handler(req: VercelRequest, res: VercelResponse) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'PUT, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'PUT') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const siteId = req.query.id as string;
    const updateData = req.body as SiteUpdateRequest;

    if (!siteId) {
      return res.status(400).json({ error: 'Site ID is required' });
    }

    const githubToken = process.env.GITHUB_TOKEN;
    const githubRepo = process.env.GITHUB_REPOSITORY || 'your-username/Gov_Oversight';

    if (!githubToken) {
      return res.status(500).json({ 
        error: 'Server configuration error: GitHub token not available' 
      });
    }

    // Get current sites.json
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

    // Find site to update
    const siteIndex = sitesData.sites.findIndex((site: any) => site.id === siteId);
    if (siteIndex === -1) {
      return res.status(404).json({ error: 'Site not found' });
    }

    // Update site with provided data
    const existingSite = sitesData.sites[siteIndex];
    const updatedSite = {
      ...existingSite,
      ...(updateData.name && { name: updateData.name }),
      ...(updateData.base_url && { base_url: updateData.base_url }),
      ...(updateData.main_rfp_page_url && { main_rfp_page_url: updateData.main_rfp_page_url }),
      ...(updateData.sample_rfp_url !== undefined && { sample_rfp_url: updateData.sample_rfp_url }),
      ...(updateData.description !== undefined && { description: updateData.description }),
      ...(updateData.status && { status: updateData.status }),
      ...(updateData.field_mappings && {
        field_mappings: updateData.field_mappings.map(fm => ({
          alias: fm.alias,
          selector: `[data-field="${fm.alias}"]`,
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
        }))
      }),
      last_updated: new Date().toISOString()
    };

    sitesData.sites[siteIndex] = updatedSite;
    sitesData.metadata.last_updated = new Date().toISOString();

    // Commit updated file
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
        message: `Update site: ${updatedSite.name} (via Vercel API)`,
        content: encodedContent,
        sha: fileSha
      })
    });

    if (!putResponse.ok) {
      const errorData = await putResponse.text();
      return res.status(500).json({ 
        error: 'Failed to update site',
        details: errorData
      });
    }

    const commitResult = await putResponse.json();

    return res.status(200).json({
      success: true,
      message: `Site "${updatedSite.name}" updated successfully`,
      site: updatedSite,
      commit_url: commitResult.commit.html_url
    });

  } catch (error) {
    console.error('Update site error:', error);
    return res.status(500).json({ 
      error: 'Internal server error',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
}