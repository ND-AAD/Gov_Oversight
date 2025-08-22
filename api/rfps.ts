import { VercelRequest, VercelResponse } from '@vercel/node';

interface RFP {
  id: string;
  title: string;
  url: string;
  source_site: string;
  posted_date: string;
  extracted_fields: Record<string, any>;
  detected_at: string;
  content_hash: string;
  categories: string[];
  closing_date?: string;
  description?: string;
  change_history?: Array<Record<string, any>>;
  manual_review_status?: string;
  notes?: string;
}

interface RFPResponse {
  metadata: {
    last_updated: string;
    total_rfps: number;
    version: string;
  };
  rfps: RFP[];
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

    // Fetch RFPs data from GitHub repository
    const dataUrl = `https://api.github.com/repos/${githubRepo}/contents/data/rfps.json`;
    
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
            total_rfps: 0,
            version: '1.0'
          },
          rfps: []
        });
      }
      throw new Error(`GitHub API error: ${response.status} ${response.statusText}`);
    }

    const fileData = await response.json();
    
    // Decode base64 content
    const content = Buffer.from(fileData.content, 'base64').toString('utf-8');
    const rfpsData: RFPResponse = JSON.parse(content);

    // Optional: Filter or transform data based on query parameters
    const { 
      category, 
      source, 
      limit, 
      search,
      high_priority_only 
    } = req.query;

    let filteredRfps = rfpsData.rfps;

    if (category && typeof category === 'string') {
      filteredRfps = filteredRfps.filter(rfp => 
        rfp.categories.some(cat => cat.toLowerCase().includes(category.toLowerCase()))
      );
    }

    if (source && typeof source === 'string') {
      filteredRfps = filteredRfps.filter(rfp => 
        rfp.source_site.toLowerCase().includes(source.toLowerCase())
      );
    }

    if (search && typeof search === 'string') {
      const searchLower = search.toLowerCase();
      filteredRfps = filteredRfps.filter(rfp => 
        rfp.title.toLowerCase().includes(searchLower) ||
        rfp.description?.toLowerCase().includes(searchLower) ||
        Object.values(rfp.extracted_fields).some(value => 
          String(value).toLowerCase().includes(searchLower)
        )
      );
    }

    if (high_priority_only === 'true') {
      filteredRfps = filteredRfps.filter(rfp => {
        const highPriorityCategories = ['surveillance', 'security', 'high priority'];
        return rfp.categories.some(cat => 
          highPriorityCategories.some(priority => 
            cat.toLowerCase().includes(priority)
          )
        );
      });
    }

    if (limit && typeof limit === 'string') {
      const limitNum = parseInt(limit, 10);
      if (!isNaN(limitNum) && limitNum > 0) {
        filteredRfps = filteredRfps.slice(0, limitNum);
      }
    }

    return res.status(200).json({
      metadata: {
        ...rfpsData.metadata,
        filtered_count: filteredRfps.length,
        total_count: rfpsData.rfps.length
      },
      rfps: filteredRfps
    });

  } catch (error) {
    console.error('Error fetching RFPs:', error);
    return res.status(500).json({ 
      error: 'Failed to fetch RFP data',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
}