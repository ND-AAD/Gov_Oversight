import type { RFP, SiteConfig } from '../types/rfp';

// Vercel-specific API client for unified architecture
const API_BASE = ''; // Relative to current domain (works for both dev and production)

export interface CreateSiteRequest {
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

export interface ApiError extends Error {
  status?: number;
  details?: string;
}

class VercelApiError extends Error implements ApiError {
  status?: number;
  details?: string;

  constructor(message: string, status?: number, details?: string) {
    super(message);
    this.name = 'VercelApiError';
    this.status = status;
    this.details = details;
  }
}

async function apiRequest<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}/api${endpoint}`;
  
  try {
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    });

    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
      let errorDetails = '';
      
      try {
        const errorData = await response.json();
        errorMessage = errorData.error || errorMessage;
        errorDetails = errorData.details || errorData.message || '';
      } catch {
        // Response is not JSON, use status text
      }
      
      throw new VercelApiError(errorMessage, response.status, errorDetails);
    }

    return await response.json();
  } catch (error) {
    if (error instanceof VercelApiError) {
      throw error;
    }
    
    // Network error or other issues
    throw new VercelApiError(
      `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`,
      0,
      'Check your internet connection and try again'
    );
  }
}

// Site Management
export async function createSite(siteData: CreateSiteRequest): Promise<{
  success: boolean;
  message: string;
  github_issue_url?: string;
  github_issue_number?: number;
  estimated_processing_time?: string;
}> {
  return apiRequest('/add-site', {
    method: 'POST',
    body: JSON.stringify(siteData),
  });
}

// Data Fetching
export async function getRFPs(filters?: {
  category?: string;
  source?: string;
  limit?: number;
  search?: string;
  high_priority_only?: boolean;
}): Promise<{
  metadata: {
    last_updated: string;
    total_rfps: number;
    filtered_count?: number;
    total_count?: number;
    version: string;
  };
  rfps: RFP[];
}> {
  const params = new URLSearchParams();
  
  if (filters) {
    if (filters.category) params.append('category', filters.category);
    if (filters.source) params.append('source', filters.source);
    if (filters.limit) params.append('limit', filters.limit.toString());
    if (filters.search) params.append('search', filters.search);
    if (filters.high_priority_only) params.append('high_priority_only', 'true');
  }

  const queryString = params.toString();
  const endpoint = queryString ? `/rfps?${queryString}` : '/rfps';
  
  return apiRequest(endpoint);
}

export async function getSites(filters?: {
  status?: string;
  limit?: number;
  include_inactive?: boolean;
}): Promise<{
  metadata: {
    last_updated: string;
    total_sites: number;
    filtered_count?: number;
    total_count?: number;
    version: string;
  };
  sites: SiteConfig[];
}> {
  const params = new URLSearchParams();
  
  if (filters) {
    if (filters.status) params.append('status', filters.status);
    if (filters.limit) params.append('limit', filters.limit.toString());
    if (filters.include_inactive) params.append('include_inactive', 'true');
  }

  const queryString = params.toString();
  const endpoint = queryString ? `/sites?${queryString}` : '/sites';
  
  return apiRequest(endpoint);
}

export async function getStats(): Promise<{
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
}> {
  return apiRequest('/stats');
}

// Utility functions for local storage (client-side state)
export function getIgnoredRFPs(): string[] {
  try {
    return JSON.parse(localStorage.getItem('ignored_rfp_ids') || '[]');
  } catch {
    return [];
  }
}

export function setIgnoredRFPs(rfpIds: string[]): void {
  localStorage.setItem('ignored_rfp_ids', JSON.stringify(rfpIds));
}

export function getStarredRFPs(): string[] {
  try {
    return JSON.parse(localStorage.getItem('starred_rfp_ids') || '[]');
  } catch {
    return [];
  }
}

export function setStarredRFPs(rfpIds: string[]): void {
  localStorage.setItem('starred_rfp_ids', JSON.stringify(rfpIds));
}


export function toggleStarRFP(rfpId: string): boolean {
  const starred = getStarredRFPs();
  const isCurrentlyStarred = starred.includes(rfpId);
  
  if (isCurrentlyStarred) {
    setStarredRFPs(starred.filter(id => id !== rfpId));
  } else {
    setStarredRFPs([...starred, rfpId]);
  }
  
  return !isCurrentlyStarred;
}

// Site Management
export async function updateSite(siteId: string, updates: {
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
}): Promise<{
  success: boolean;
  message: string;
  site: SiteConfig;
  commit_url?: string;
}> {
  return apiRequest(`/sites/${siteId}/update`, {
    method: 'PUT',
    body: JSON.stringify(updates),
  });
}

export async function deleteSite(siteId: string, softDelete = true, reason?: string): Promise<{
  success: boolean;
  message: string;
  deleted_site: SiteConfig;
  soft_delete: boolean;
  commit_url?: string;
}> {
  return apiRequest(`/sites/${siteId}/delete`, {
    method: 'DELETE',
    body: JSON.stringify({ soft_delete: softDelete, reason }),
  });
}

// RFP Management
export async function updateRFPIgnoreStatus(rfpId: string, ignored: boolean, reason?: string): Promise<{
  success: boolean;
  message: string;
  rfp_id: string;
  ignored: boolean;
  commit_url?: string;
}> {
  return apiRequest(`/rfps/${rfpId}/ignore`, {
    method: 'PUT',
    body: JSON.stringify({ ignored, reason }),
  });
}

export async function batchUpdateRFPs(operations: Array<{
  rfp_id: string;
  action: 'ignore' | 'unignore' | 'star' | 'unstar' | 'flag' | 'unflag';
  reason?: string;
}>): Promise<{
  success: boolean;
  message: string;
  results: Array<{ rfp_id: string; success: boolean; error?: string }>;
  updated_count: number;
  commit_url?: string;
}> {
  return apiRequest('/rfps/batch/update', {
    method: 'PUT',
    body: JSON.stringify({ operations }),
  });
}

// System Management
export async function triggerScraping(options?: {
  force_full_scan?: boolean;
  specific_sites?: string[];
  reason?: string;
}): Promise<{
  success: boolean;
  message: string;
  details: {
    force_full_scan: boolean;
    specific_sites: string | string[];
    reason: string;
    estimated_duration: string;
  };
  workflow_run_url?: string;
  monitoring_tip: string;
}> {
  return apiRequest('/system/trigger-scraping', {
    method: 'POST',
    body: JSON.stringify(options || {}),
  });
}

// Enhanced utility functions that sync with server
export async function ignoreRFP(rfpId: string, reason?: string): Promise<boolean> {
  try {
    await updateRFPIgnoreStatus(rfpId, true, reason);
    return true;
  } catch (error) {
    console.error('Failed to ignore RFP on server:', error);
    // Fallback to local storage
    const ignored = getIgnoredRFPs();
    if (!ignored.includes(rfpId)) {
      setIgnoredRFPs([...ignored, rfpId]);
    }
    return true;
  }
}

export async function unignoreRFP(rfpId: string): Promise<boolean> {
  try {
    await updateRFPIgnoreStatus(rfpId, false);
    return false;
  } catch (error) {
    console.error('Failed to unignore RFP on server:', error);
    // Fallback to local storage
    const ignored = getIgnoredRFPs();
    setIgnoredRFPs(ignored.filter(id => id !== rfpId));
    return false;
  }
}

// Override the existing toggle functions to use server-side updates
export function toggleIgnoreRFP(rfpId: string): boolean {
  const ignored = getIgnoredRFPs();
  const isCurrentlyIgnored = ignored.includes(rfpId);
  
  if (isCurrentlyIgnored) {
    setIgnoredRFPs(ignored.filter(id => id !== rfpId));
    // Async server update (fire and forget)
    unignoreRFP(rfpId).catch(console.error);
  } else {
    setIgnoredRFPs([...ignored, rfpId]);
    // Async server update (fire and forget)
    ignoreRFP(rfpId).catch(console.error);
  }
  
  return !isCurrentlyIgnored;
}

// Health check
export async function healthCheck(): Promise<{
  status: string;
  timestamp: string;
  version?: string;
  api_mode?: string;
  checks?: Record<string, boolean>;
  repository?: any;
}> {
  try {
    return apiRequest('/system/health');
  } catch {
    return {
      status: 'degraded', 
      timestamp: new Date().toISOString()
    };
  }
}