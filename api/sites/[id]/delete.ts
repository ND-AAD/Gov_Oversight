import { VercelRequest, VercelResponse } from '@vercel/node';

interface SiteDeleteRequest {
  soft_delete?: boolean; // true for soft delete, false for hard delete
  reason?: string;
}

export default async function handler(req: VercelRequest, res: VercelResponse) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'DELETE') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const siteId = req.query.id as string;
    const { soft_delete = true, reason = 'User requested deletion' } = req.body as SiteDeleteRequest || {};

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

    // Find site to delete
    const siteIndex = sitesData.sites.findIndex((site: any) => site.id === siteId);
    if (siteIndex === -1) {
      return res.status(404).json({ error: 'Site not found' });
    }

    const siteToDelete = sitesData.sites[siteIndex];

    if (soft_delete) {
      // Soft delete: mark as deleted but preserve data
      sitesData.sites[siteIndex] = {
        ...siteToDelete,
        status: 'deleted',
        deleted_at: new Date().toISOString(),
        deletion_reason: reason,
        last_updated: new Date().toISOString()
      };
    } else {
      // Hard delete: remove completely
      sitesData.sites.splice(siteIndex, 1);
    }

    sitesData.metadata.last_updated = new Date().toISOString();
    sitesData.metadata.total_sites = sitesData.sites.filter((site: any) => site.status !== 'deleted').length;

    // Commit updated file
    const updatedContent = JSON.stringify(sitesData, null, 2);
    const encodedContent = Buffer.from(updatedContent).toString('base64');

    const deleteAction = soft_delete ? 'Soft delete' : 'Delete';
    const putResponse = await fetch(sitesUrl, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${githubToken}`,
        'Content-Type': 'application/json',
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'LA-2028-RFP-Monitor/1.0'
      },
      body: JSON.stringify({
        message: `${deleteAction} site: ${siteToDelete.name} (via Vercel API)`,
        content: encodedContent,
        sha: fileSha
      })
    });

    if (!putResponse.ok) {
      const errorData = await putResponse.text();
      return res.status(500).json({ 
        error: 'Failed to delete site',
        details: errorData
      });
    }

    const commitResult = await putResponse.json();

    return res.status(200).json({
      success: true,
      message: soft_delete 
        ? `Site "${siteToDelete.name}" has been soft deleted (data preserved)`
        : `Site "${siteToDelete.name}" has been permanently deleted`,
      deleted_site: siteToDelete,
      soft_delete,
      commit_url: commitResult.commit.html_url
    });

  } catch (error) {
    console.error('Delete site error:', error);
    return res.status(500).json({ 
      error: 'Internal server error',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
}