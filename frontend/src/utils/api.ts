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
    // In static mode (GitHub Pages), load directly from static files
    if (API_MODE === 'static') {
      console.log('🏛️ Loading site configs from static files (GitHub Pages mode)');
      const response = await axios.get(`${STATIC_DATA_BASE}/sites.json`);
      return response.data.sites || [];
    }
    
    // In development mode, try API first, fallback to static
    try {
      const response = await api.get<ApiResponse<SiteConfig[]>>('/api/sites');
      return response.data.data || [];
    } catch (apiError) {
      // If API server is not available, try to load from static files
      console.warn('API server not available, loading site configs from static files');
      const staticPath = window.location.hostname.includes('github.io') ? '/Gov_Oversight/data/sites.json' : '/data/sites.json';
      const response = await axios.get(staticPath);
      return response.data.sites || [];
    }
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
  const response = await api.post<ApiResponse<SiteConfig>>('/api/sites', siteData);
  if (!response.data.data) {
    throw new Error('Failed to create site');
  }
  return response.data.data;
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

export const deleteSite = async (siteId: string): Promise<void> => {
  await api.delete(`/api/sites/${siteId}`);
};

// Scraping endpoints
export const startScraping = async (forceFullScan: boolean = false): Promise<void> => {
  await api.post('/api/scrape', { force_full_scan: forceFullScan });
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
