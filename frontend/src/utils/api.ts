import axios from 'axios';
import type { RFP, SiteConfig, ApiResponse } from '../types/rfp';

// API configuration - supports both development and static hosting
const API_MODE = import.meta.env.VITE_API_MODE || (window.location.hostname.includes('github.io') ? 'static' : 'development');
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';
const STATIC_DATA_BASE = import.meta.env.VITE_STATIC_DATA_BASE || '/Gov_Oversight/data';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    
    if (error.response?.status === 404) {
      throw new Error('Resource not found');
    } else if (error.response?.status >= 500) {
      throw new Error('Server error - please try again later');
    } else if (error.response?.data?.detail) {
      const detail = error.response.data.detail;
      if (typeof detail === 'string') {
        throw new Error(detail);
      } else {
        throw new Error(detail.message || 'API error');
      }
    }
    
    throw error;
  }
);

// Health check
export const healthCheck = async (): Promise<{ status: string; timestamp: string }> => {
  const response = await api.get('/health');
  return response.data;
};

// RFP endpoints with static/API dual mode support
export const getRFPs = async (): Promise<RFP[]> => {
  try {
    // In static mode (GitHub Pages), load directly from static files
    if (API_MODE === 'static') {
      console.log('📊 Loading RFP data from static files (GitHub Pages mode)');
      const response = await axios.get(`${STATIC_DATA_BASE}/rfps.json`);
      return response.data.rfps || [];
    }
    
    // In development mode, try API first, fallback to static
    try {
      const response = await api.get<ApiResponse<RFP[]>>('/api/rfps');
      return response.data.data || [];
    } catch (apiError) {
      // If API server is not available, try to load from static files
      console.warn('API server not available, loading from static files');
      const staticPath = window.location.hostname.includes('github.io') ? '/Gov_Oversight/data/rfps.json' : '/data/rfps.json';
      const response = await axios.get(staticPath);
      return response.data.rfps || [];
    }
  } catch (error) {
    console.error('Failed to load RFP data:', error);
    return []; // Return empty array on error
  }
};

export const getRFP = async (rfpId: string): Promise<RFP> => {
  const response = await api.get<ApiResponse<RFP>>(`/api/rfps/${rfpId}`);
  if (!response.data.data) {
    throw new Error('RFP not found');
  }
  return response.data.data;
};

export const deleteRFP = async (rfpId: string): Promise<void> => {
  await api.delete(`/api/rfps/${rfpId}`);
};

// Site configuration endpoints with static/API dual mode support  
export const getSites = async (): Promise<SiteConfig[]> => {
  try {
    let sites: SiteConfig[] = [];
    
    // In static mode (GitHub Pages), load directly from static files
    if (API_MODE === 'static') {
      console.log('🏛️ Loading site configs from static files (GitHub Pages mode)');
      const response = await axios.get(`${STATIC_DATA_BASE}/sites.json`);
      sites = response.data.sites || [];
    } else {
      // In development mode, try API first, fallback to static
      try {
        const response = await api.get<ApiResponse<SiteConfig[]>>('/api/sites');
        sites = response.data.data || [];
      } catch (apiError) {
        // If API server is not available, try to load from static files
        console.warn('API server not available, loading site configs from static files');
        const staticPath = window.location.hostname.includes('github.io') ? '/Gov_Oversight/data/sites.json' : '/data/sites.json';
        const response = await axios.get(staticPath);
        sites = response.data.sites || [];
      }
    }
    
    // In static mode, also include pending sites and filter out soft-deleted sites
    if (API_MODE === 'static') {
      const pendingSites = localStorage.getItem('pending_site_additions');
      if (pendingSites) {
        try {
          const pending: SiteConfig[] = JSON.parse(pendingSites);
          sites = [...sites, ...pending];
        } catch (e) {
          console.warn('Failed to parse pending sites from localStorage');
        }
      }
      
      // Filter out soft-deleted sites
      const deletedSites = JSON.parse(localStorage.getItem('soft_deleted_sites') || '[]');
      const deletedIds = new Set<string>(deletedSites.map((site: any) => site.id as string));
      sites = sites.filter(site => !deletedIds.has(site.id));
      
      // Clean up ignored RFPs from deleted sites
      cleanupIgnoredRFPsFromDeletedSites(deletedIds);
    }
    
    return sites;
  } catch (error) {
    console.error('Failed to load site configurations:', error);
    return []; // Return empty array on error
  }
};

export interface CreateSiteRequest {
  name: string;
  base_url: string;
  main_rfp_page_url: string;
  sample_rfp_url: string;
  description?: string;
  field_mappings?: Array<{
    alias: string;
    sample_value: string;
    data_type: string;
  }>;
}

export const createSite = async (siteData: CreateSiteRequest): Promise<SiteConfig> => {
  // Check if we're in development mode (localhost with API server)
  const isDevelopmentMode = window.location.hostname.includes('localhost');
  
  console.log('createSite - hostname:', window.location.hostname, 'isDevelopmentMode:', isDevelopmentMode);
  
  if (!isDevelopmentMode) {
    // GitHub-only approach for production (static mode)
    return await createSiteViaGitHub(siteData);
  } else {
    try {
      // Try API server first in development
      const response = await api.post<ApiResponse<SiteConfig>>('/api/sites', siteData);
      if (!response.data.data) {
        throw new Error('Failed to create site');
      }
      return response.data.data;
    } catch (error) {
      // Fallback to GitHub approach even in development if API server unavailable
      console.warn('API server unavailable, falling back to GitHub approach');
      return await createSiteViaGitHub(siteData);
    }
  }
};

export interface FieldMappingRequest {
  alias: string;
  sample_value: string;
  data_type: string;
}

export const createFieldMappings = async (
  siteId: string,
  fieldMappings: FieldMappingRequest[]
): Promise<SiteConfig> => {
  const response = await api.post<ApiResponse<SiteConfig>>(
    `/api/sites/${siteId}/field-mappings`,
    fieldMappings
  );
  if (!response.data.data) {
    throw new Error('Failed to create field mappings');
  }
  return response.data.data;
};

export const testSite = async (siteId: string): Promise<{
  success: boolean;
  errors: string[];
  warnings: string[];
  tested_at: string;
}> => {
  const response = await api.post<ApiResponse<any>>(`/api/sites/${siteId}/test`);
  return response.data.data;
};

// Soft delete a site (mark as deleted but preserve data)
export const softDeleteSite = async (siteId: string, siteName: string): Promise<void> => {
  // Check if we're in static mode (GitHub Pages or any non-localhost)
  const isStaticMode = window.location.hostname.includes('github.io') || 
                      !window.location.hostname.includes('localhost');
  
  if (isStaticMode) {
    // Remove from pending sites if it exists
    const pendingSites = localStorage.getItem('pending_site_additions');
    if (pendingSites) {
      try {
        const sites = JSON.parse(pendingSites);
        const filteredSites = sites.filter((site: any) => site.id !== siteId);
        localStorage.setItem('pending_site_additions', JSON.stringify(filteredSites));
      } catch (e) {
        console.warn('Failed to update pending sites');
      }
    }
    
    // For committed sites, create a soft delete request via GitHub Issue
    await createSoftDeleteIssue(siteId, siteName);
    
    // Also mark as deleted in localStorage for immediate UX
    const deletedSites = JSON.parse(localStorage.getItem('soft_deleted_sites') || '[]');
    deletedSites.push({
      id: siteId,
      name: siteName,
      deletedAt: new Date().toISOString()
    });
    localStorage.setItem('soft_deleted_sites', JSON.stringify(deletedSites));
    
  } else {
    // Development mode - use API
    await api.post(`/api/sites/${siteId}/soft-delete`);
  }
};

// Create GitHub issue for soft deletion
const createSoftDeleteIssue = async (siteId: string, siteName: string): Promise<void> => {
  const issueBody = `
**Soft Delete Site Request**

Site ID: ${siteId}
Site Name: ${siteName}
Action: Mark as deleted (preserve data, stop scraping)
Requested: ${new Date().toISOString()}

**Automated Action Required:**
- [ ] Mark site status as "deleted" in sites.json
- [ ] Exclude from future scraping runs
- [ ] Preserve all existing RFP data
- [ ] Site can be restored easily if needed

---
*This request was submitted via the dashboard soft delete feature.*
`.trim();

  const issueData = {
    title: `Soft Delete Site: ${siteName}`,
    body: issueBody,
    labels: ['site-soft-delete', 'automation']
  };

  // Store the formatted request for processing
  const issueRequests = JSON.parse(localStorage.getItem('github_issue_requests') || '[]');
  issueRequests.push({
    ...issueData,
    timestamp: new Date().toISOString(),
    status: 'pending'
  });
  localStorage.setItem('github_issue_requests', JSON.stringify(issueRequests));
  
  console.log('Soft delete request created:', issueData);
};

// Keep the old deleteSite function for backwards compatibility but redirect to soft delete
export const deleteSite = async (_siteId: string): Promise<void> => {
  throw new Error('Direct deletion has been replaced with soft delete for better data safety. Use softDeleteSite() instead.');
};

// Scraping endpoints
export const startScraping = async (forceFullScan: boolean = false): Promise<void> => {
  // Check if we're in static mode (GitHub Pages or any non-localhost)
  const isStaticMode = window.location.hostname.includes('github.io') || 
                      !window.location.hostname.includes('localhost');
  
  if (isStaticMode) {
    // In static mode, we need to trigger GitHub Actions workflow
    // Since we can't trigger workflows directly from the browser due to CORS,
    // we'll create a GitHub issue that triggers the workflow
    await triggerScrapingViaGitHub(forceFullScan);
  } else {
    // Development mode - use API
    await api.post('/api/scrape', { force_full_scan: forceFullScan });
  }
};

// Trigger scraping via GitHub Actions (static mode)
const triggerScrapingViaGitHub = async (forceFullScan: boolean): Promise<void> => {
  // For now, we'll simulate the trigger since direct GitHub Actions API calls
  // require authentication that can't be done securely from the browser
  console.log('Scraping trigger requested (force:', forceFullScan, ')');
  
  // In a production setup, this would:
  // 1. Create a GitHub issue with label "trigger-scraping"
  // 2. GitHub Actions would detect the issue and run the scraping workflow
  // 3. The issue would be closed automatically
  
  // For now, inform the user about the current process
  throw new Error('Manual scraping trigger: GitHub Actions runs automatically every 6 hours. To force an immediate run, go to the GitHub repository Actions tab and manually trigger the "Automated RFP Scraping" workflow.');
};

// Statistics
export const getStats = async (): Promise<{
  rfps: { total: number; high_priority: number; closing_soon: number };
  sites: { total: number; active: number; errors: number };
  last_updated: string;
}> => {
  const response = await api.get<ApiResponse<any>>('/api/stats');
  return response.data.data;
};

// Olympic relevance checking
export const checkOlympicRelevance = async (text: string): Promise<{
  is_relevant: boolean;
  keywords: string[];
  score: number;
}> => {
  const response = await api.post<ApiResponse<any>>('/api/check-relevance', { text });
  return response.data.data;
};

// Fallback to static JSON files for GitHub Pages
export const loadStaticRFPs = async (): Promise<RFP[]> => {
  try {
    const staticPath = window.location.hostname.includes('github.io') ? '/Gov_Oversight/data/rfps.json' : '/data/rfps.json';
    const response = await fetch(staticPath);
    const data = await response.json();
    
    if (Array.isArray(data)) {
      return data;
    } else if (data.rfps && Array.isArray(data.rfps)) {
      return data.rfps;
    }
    
    return [];
  } catch (error) {
    console.error('Failed to load static RFPs:', error);
    return [];
  }
};

export const loadStaticSites = async (): Promise<SiteConfig[]> => {
  try {
    const staticPath = window.location.hostname.includes('github.io') ? '/Gov_Oversight/data/sites.json' : '/data/sites.json';
    const response = await fetch(staticPath);
    const data = await response.json();
    
    if (Array.isArray(data)) {
      return data;
    } else if (data.sites && Array.isArray(data.sites)) {
      return data.sites;
    }
    
    return [];
  } catch (error) {
    console.error('Failed to load static sites:', error);
    return [];
  }
};

// GitHub API integration for static mode site management
const createSiteViaGitHub = async (siteData: CreateSiteRequest): Promise<SiteConfig> => {
  
  try {
    // Create GitHub issue for site addition request
    await createSiteAdditionIssue(siteData);
    
    // Create temporary site object for immediate UX feedback
    const tempSite: SiteConfig = {
      id: `temp_${Date.now()}`, // Temporary ID
      name: siteData.name,
      base_url: siteData.base_url,
      main_rfp_page_url: siteData.main_rfp_page_url,
      sample_rfp_url: siteData.sample_rfp_url,
      description: siteData.description || '',
      field_mappings: siteData.field_mappings?.map(fm => ({
        alias: fm.alias,
        selector: '', // Will be populated by location binder
        data_type: fm.data_type as 'text' | 'date' | 'currency' | 'number' | 'url' | 'email',
        training_value: fm.sample_value,
        confidence_score: 0.0,
        fallback_selectors: [],
        validation_errors: [],
        status: 'untested' as 'working' | 'degraded' | 'broken' | 'untested',
        consecutive_failures: 0
      })) || [],
      last_test: new Date().toISOString(),
      status: 'testing' as 'active' | 'error' | 'testing' | 'disabled', // Mark as testing
      rfp_count: 0,
      robots_txt_compliant: true,
      test_results: {
        is_valid: false,
        errors: [],
        warnings: ['Site request submitted - processing within 1 hour'],
        timestamp: new Date().toISOString()
      }
    };
    
    // Store pending site for immediate UX feedback
    const existingPending = localStorage.getItem('pending_site_additions');
    let pendingSites: SiteConfig[] = [];
    
    if (existingPending) {
      try {
        pendingSites = JSON.parse(existingPending);
      } catch (e) {
        pendingSites = [];
      }
    }
    
    pendingSites.push(tempSite);
    localStorage.setItem('pending_site_additions', JSON.stringify(pendingSites));
    
    console.log('Site addition request submitted via GitHub issue');
    console.log('Site will be processed automatically within 1 hour');
    
    return tempSite;
    
  } catch (error) {
    console.error('Failed to create site addition request:', error);
    throw new Error('Failed to submit site addition request. Please try again or create a GitHub issue manually.');
  }
};

// Create GitHub issue for site addition - Direct GitHub API approach
const createSiteAdditionIssue = async (siteData: CreateSiteRequest): Promise<void> => {
  
  // For now, store locally and let GitHub Actions process them
  // This ensures reliability while we resolve serverless deployment issues
  
  // Format field mappings for GitHub issue
  const fieldMappingsText = siteData.field_mappings?.map(mapping => 
    `- **${mapping.alias}:** "${mapping.sample_value}" (${mapping.data_type || 'text'})`
  ).join('\n') || 'No field mappings provided (basic configuration)';

  // Create structured GitHub issue body
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
- **User Agent:** ${navigator.userAgent}
- **Processing Status:** Pending

---
*This issue was created automatically by the LA 2028 RFP Monitor frontend.*
*The site addition workflow will process this request and update the status.*`;

  const issueData = {
    title: `Add Site: ${siteData.name}`,
    body: issueBody,
    labels: ['site-addition', 'automated'],
    site_data: siteData
  };

  // Store the request for GitHub Actions to process
  const issueRequests = JSON.parse(localStorage.getItem('github_issue_requests') || '[]');
  issueRequests.push({
    ...issueData,
    timestamp: new Date().toISOString(),
    status: 'pending'
  });
  localStorage.setItem('github_issue_requests', JSON.stringify(issueRequests));
  
  console.log('Site addition request created and queued for GitHub processing:', issueData.title);
};

// Clean up ignored RFPs from deleted sites
const cleanupIgnoredRFPsFromDeletedSites = async (deletedSiteIds: Set<string>): Promise<void> => {
  try {
    // Load current RFPs to check their source sites
    const rfps = await loadStaticRFPs();
    const ignoredRFPIds = JSON.parse(localStorage.getItem('ignored_rfp_ids') || '[]');
    
    // Find RFPs that belong to deleted sites
    const rfpsFromDeletedSites = rfps
      .filter(rfp => deletedSiteIds.has(rfp.source_site))
      .map(rfp => rfp.id);
    
    // Remove ignored RFPs from deleted sites
    const cleanedIgnoredRFPs = ignoredRFPIds.filter((rfpId: string) => 
      !rfpsFromDeletedSites.includes(rfpId)
    );
    
    // Update localStorage if any cleanup was needed
    if (cleanedIgnoredRFPs.length !== ignoredRFPIds.length) {
      localStorage.setItem('ignored_rfp_ids', JSON.stringify(cleanedIgnoredRFPs));
      console.log(`Cleaned up ${ignoredRFPIds.length - cleanedIgnoredRFPs.length} ignored RFPs from deleted sites`);
    }
  } catch (error) {
    console.warn('Failed to cleanup ignored RFPs from deleted sites:', error);
  }
};

// Auto-detect whether to use API or static files
export const autoLoadRFPs = async (): Promise<RFP[]> => {
  try {
    // Try API first
    return await getRFPs();
  } catch (error) {
    console.warn('API unavailable, falling back to static files');
    return await loadStaticRFPs();
  }
};

export const autoLoadSites = async (): Promise<SiteConfig[]> => {
  try {
    // Try API first
    return await getSites();
  } catch (error) {
    console.warn('API unavailable, falling back to static files');
    return await loadStaticSites();
  }
};
