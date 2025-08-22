import { VercelRequest, VercelResponse } from '@vercel/node';

interface StatsResponse {
  overview: {
    total_rfps: number;
    total_sites: number;
    active_sites: number;
    high_priority_rfps: number;
    rfps_this_week: number;
    last_update: string;
  };
  categories: Record<string, number>;
  sites_status: Record<string, number>;
  recent_activity: Array<{
    type: 'rfp_added' | 'rfp_updated' | 'site_added' | 'site_tested';
    item_id: string;
    item_name: string;
    timestamp: string;
  }>;
  surveillance_alerts: {
    total_surveillance_rfps: number;
    new_this_week: number;
    high_value_contracts: number;
  };
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

    const headers: Record<string, string> = {
      'Accept': 'application/vnd.github.v3+json',
      'User-Agent': 'LA-2028-RFP-Monitor/1.0'
    };

    if (githubToken) {
      headers['Authorization'] = `Bearer ${githubToken}`;
    }

    // Fetch both RFPs and sites data
    const [rfpsResponse, sitesResponse] = await Promise.all([
      fetch(`https://api.github.com/repos/${githubRepo}/contents/data/rfps.json`, { headers }),
      fetch(`https://api.github.com/repos/${githubRepo}/contents/data/sites.json`, { headers })
    ]);

    // Handle empty data gracefully
    let rfpsData: any = { rfps: [] };
    let sitesData: any = { sites: [] };

    if (rfpsResponse.ok) {
      const rfpsFileData = await rfpsResponse.json();
      const rfpsContent = Buffer.from(rfpsFileData.content, 'base64').toString('utf-8');
      rfpsData = JSON.parse(rfpsContent);
    }

    if (sitesResponse.ok) {
      const sitesFileData = await sitesResponse.json();
      const sitesContent = Buffer.from(sitesFileData.content, 'base64').toString('utf-8');
      sitesData = JSON.parse(sitesContent);
    }

    const rfps = rfpsData.rfps || [];
    const sites = sitesData.sites || [];

    // Calculate statistics
    const oneWeekAgo = new Date();
    oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);

    // Count categories
    const categories: Record<string, number> = {};
    rfps.forEach((rfp: any) => {
      rfp.categories?.forEach((category: string) => {
        categories[category] = (categories[category] || 0) + 1;
      });
    });

    // Count site statuses
    const sitesStatus: Record<string, number> = {};
    sites.forEach((site: any) => {
      const status = site.status || 'unknown';
      sitesStatus[status] = (sitesStatus[status] || 0) + 1;
    });

    // Recent RFPs (this week)
    const rfpsThisWeek = rfps.filter((rfp: any) => {
      try {
        const detectedAt = new Date(rfp.detected_at);
        return detectedAt >= oneWeekAgo;
      } catch {
        return false;
      }
    }).length;

    // High priority RFPs (surveillance, security, etc.)
    const highPriorityCategories = ['surveillance', 'security', 'high priority', 'biometric'];
    const highPriorityRfps = rfps.filter((rfp: any) => 
      rfp.categories?.some((cat: string) => 
        highPriorityCategories.some(priority => 
          cat.toLowerCase().includes(priority.toLowerCase())
        )
      )
    ).length;

    // Surveillance-specific statistics
    const surveillanceKeywords = ['surveillance', 'facial recognition', 'biometric', 'monitoring'];
    const surveillanceRfps = rfps.filter((rfp: any) => {
      const text = `${rfp.title} ${rfp.description || ''}`.toLowerCase();
      return surveillanceKeywords.some(keyword => text.includes(keyword)) ||
             rfp.categories?.some((cat: string) => cat.toLowerCase().includes('surveillance'));
    });

    const newSurveillanceThisWeek = surveillanceRfps.filter((rfp: any) => {
      try {
        const detectedAt = new Date(rfp.detected_at);
        return detectedAt >= oneWeekAgo;
      } catch {
        return false;
      }
    }).length;

    // High value contracts (>$1M)
    const highValueContracts = rfps.filter((rfp: any) => {
      const contractValue = rfp.extracted_fields?.contract_value || rfp.extracted_fields?.value || '';
      const valueStr = String(contractValue).replace(/[$,]/g, '');
      const value = parseFloat(valueStr);
      return !isNaN(value) && value >= 1000000;
    }).length;

    // Recent activity (simplified)
    const recentActivity = rfps
      .slice(-10) // Last 10 RFPs
      .map((rfp: any) => ({
        type: 'rfp_added' as const,
        item_id: rfp.id,
        item_name: rfp.title,
        timestamp: rfp.detected_at
      }))
      .sort((a: any, b: any) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

    const stats: StatsResponse = {
      overview: {
        total_rfps: rfps.length,
        total_sites: sites.length,
        active_sites: sites.filter((site: any) => site.status === 'active' || site.status === 'testing').length,
        high_priority_rfps: highPriorityRfps,
        rfps_this_week: rfpsThisWeek,
        last_update: new Date().toISOString()
      },
      categories,
      sites_status: sitesStatus,
      recent_activity: recentActivity.slice(0, 5), // Top 5 recent activities
      surveillance_alerts: {
        total_surveillance_rfps: surveillanceRfps.length,
        new_this_week: newSurveillanceThisWeek,
        high_value_contracts: highValueContracts
      }
    };

    return res.status(200).json(stats);

  } catch (error) {
    console.error('Error generating stats:', error);
    return res.status(500).json({ 
      error: 'Failed to generate statistics',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
}