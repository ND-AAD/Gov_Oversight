import { VercelRequest, VercelResponse } from '@vercel/node';

interface BatchUpdateRequest {
  operations: Array<{
    rfp_id: string;
    action: 'ignore' | 'unignore' | 'star' | 'unstar' | 'flag' | 'unflag';
    reason?: string;
  }>;
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
    const { operations } = req.body as BatchUpdateRequest;

    if (!operations || !Array.isArray(operations) || operations.length === 0) {
      return res.status(400).json({ error: 'Operations array is required' });
    }

    if (operations.length > 50) {
      return res.status(400).json({ error: 'Maximum 50 operations per batch' });
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

    const results: Array<{ rfp_id: string; success: boolean; error?: string }> = [];
    const updatedRFPs: string[] = [];

    // Process each operation
    for (const operation of operations) {
      try {
        const rfpIndex = rfpsData.rfps.findIndex((rfp: any) => rfp.id === operation.rfp_id);
        
        if (rfpIndex === -1) {
          results.push({ 
            rfp_id: operation.rfp_id, 
            success: false, 
            error: 'RFP not found' 
          });
          continue;
        }

        const existingRFP = rfpsData.rfps[rfpIndex];
        let updated = false;

        switch (operation.action) {
          case 'ignore':
            rfpsData.rfps[rfpIndex] = {
              ...existingRFP,
              manual_review_status: 'ignored',
              ignored_at: new Date().toISOString(),
              ignore_reason: operation.reason,
              last_updated: new Date().toISOString()
            };
            updated = true;
            break;

          case 'unignore':
            rfpsData.rfps[rfpIndex] = {
              ...existingRFP,
              manual_review_status: existingRFP.manual_review_status === 'ignored' ? undefined : existingRFP.manual_review_status,
              ignored_at: undefined,
              ignore_reason: undefined,
              last_updated: new Date().toISOString()
            };
            updated = true;
            break;

          case 'star':
            rfpsData.rfps[rfpIndex] = {
              ...existingRFP,
              starred: true,
              starred_at: new Date().toISOString(),
              star_reason: operation.reason,
              last_updated: new Date().toISOString()
            };
            updated = true;
            break;

          case 'unstar':
            rfpsData.rfps[rfpIndex] = {
              ...existingRFP,
              starred: false,
              starred_at: undefined,
              star_reason: undefined,
              last_updated: new Date().toISOString()
            };
            updated = true;
            break;

          case 'flag':
            rfpsData.rfps[rfpIndex] = {
              ...existingRFP,
              manual_review_status: 'flagged',
              flagged_at: new Date().toISOString(),
              flag_reason: operation.reason,
              last_updated: new Date().toISOString()
            };
            updated = true;
            break;

          case 'unflag':
            rfpsData.rfps[rfpIndex] = {
              ...existingRFP,
              manual_review_status: existingRFP.manual_review_status === 'flagged' ? undefined : existingRFP.manual_review_status,
              flagged_at: undefined,
              flag_reason: undefined,
              last_updated: new Date().toISOString()
            };
            updated = true;
            break;

          default:
            results.push({ 
              rfp_id: operation.rfp_id, 
              success: false, 
              error: `Unknown action: ${operation.action}` 
            });
            continue;
        }

        if (updated) {
          updatedRFPs.push(existingRFP.title);
          results.push({ rfp_id: operation.rfp_id, success: true });
        }

      } catch (error) {
        results.push({ 
          rfp_id: operation.rfp_id, 
          success: false, 
          error: error instanceof Error ? error.message : 'Unknown error' 
        });
      }
    }

    // Only commit if we have updates
    if (updatedRFPs.length > 0) {
      rfpsData.metadata.last_updated = new Date().toISOString();

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
          message: `Batch update ${updatedRFPs.length} RFPs (via Vercel API)`,
          content: encodedContent,
          sha: fileSha
        })
      });

      if (!putResponse.ok) {
        const errorData = await putResponse.text();
        return res.status(500).json({ 
          error: 'Failed to commit batch updates',
          details: errorData
        });
      }

      const commitResult = await putResponse.json();

      return res.status(200).json({
        success: true,
        message: `Successfully processed ${operations.length} operations, updated ${updatedRFPs.length} RFPs`,
        results,
        updated_count: updatedRFPs.length,
        commit_url: commitResult.commit.html_url
      });
    } else {
      return res.status(200).json({
        success: true,
        message: 'No updates were made',
        results,
        updated_count: 0
      });
    }

  } catch (error) {
    console.error('Batch update error:', error);
    return res.status(500).json({ 
      error: 'Internal server error',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
}