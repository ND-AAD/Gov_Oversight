import { VercelRequest, VercelResponse } from '@vercel/node';

interface IgnoreRequest {
  ignored: boolean; // true to ignore, false to unignore
  reason?: string;
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
    const rfpId = req.query.id as string;
    const { ignored, reason } = req.body as IgnoreRequest;

    if (!rfpId) {
      return res.status(400).json({ error: 'RFP ID is required' });
    }

    if (typeof ignored !== 'boolean') {
      return res.status(400).json({ error: 'ignored field is required and must be boolean' });
    }

    const githubToken = process.env.GITHUB_TOKEN;
    const githubRepo = process.env.GITHUB_REPOSITORY || 'your-username/Gov_Oversight';

    if (!githubToken) {
      return res.status(500).json({ 
        error: 'Server configuration error: GitHub token not available' 
      });
    }

    // Get current rfps.json
    const rfpsUrl = `https://api.github.com/repos/${githubRepo}/contents/data/rfps.json`;
    const getResponse = await fetch(rfpsUrl, {
      headers: {
        'Authorization': `Bearer ${githubToken}`,
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'LA-2028-RFP-Monitor/1.0'
      }
    });

    if (!getResponse.ok) {
      return res.status(404).json({ error: 'RFPs data not found' });
    }

    const fileData = await getResponse.json();
    const fileSha = fileData.sha;
    const content = Buffer.from(fileData.content, 'base64').toString('utf-8');
    const rfpsData = JSON.parse(content);

    // Find RFP to update
    const rfpIndex = rfpsData.rfps.findIndex((rfp: any) => rfp.id === rfpId);
    if (rfpIndex === -1) {
      return res.status(404).json({ error: 'RFP not found' });
    }

    // Update RFP with ignore status
    const existingRFP = rfpsData.rfps[rfpIndex];
    rfpsData.rfps[rfpIndex] = {
      ...existingRFP,
      manual_review_status: ignored ? 'ignored' : undefined,
      ignored_at: ignored ? new Date().toISOString() : undefined,
      ignore_reason: ignored ? reason : undefined,
      last_updated: new Date().toISOString()
    };

    rfpsData.metadata.last_updated = new Date().toISOString();

    // Commit updated file
    const updatedContent = JSON.stringify(rfpsData, null, 2);
    const encodedContent = Buffer.from(updatedContent).toString('base64');

    const putResponse = await fetch(rfpsUrl, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${githubToken}`,
        'Content-Type': 'application/json',
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'LA-2028-RFP-Monitor/1.0'
      },
      body: JSON.stringify({
        message: `${ignored ? 'Ignore' : 'Unignore'} RFP: ${existingRFP.title} (via Vercel API)`,
        content: encodedContent,
        sha: fileSha
      })
    });

    if (!putResponse.ok) {
      const errorData = await putResponse.text();
      return res.status(500).json({ 
        error: 'Failed to update RFP ignore status',
        details: errorData
      });
    }

    const commitResult = await putResponse.json();

    return res.status(200).json({
      success: true,
      message: ignored 
        ? `RFP "${existingRFP.title}" has been ignored`
        : `RFP "${existingRFP.title}" has been restored`,
      rfp_id: rfpId,
      ignored,
      commit_url: commitResult.commit.html_url
    });

  } catch (error) {
    console.error('Update RFP ignore status error:', error);
    return res.status(500).json({ 
      error: 'Internal server error',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
}