export interface RFP {
  id: string;
  title: string;
  url: string;
  posted_date: string;
  closing_date?: string;
  description: string;
  source_site: string;
  content_hash: string;
  detected_at: string;
  categories: string[];
  extracted_fields: {
    issuer?: string;
    event_association?: string;
    procurement_type?: string;
    contract_value?: number;
    status?: string;
    [key: string]: any;
  };
  change_history?: Array<{
    field: string;
    oldValue: string;
    newValue: string;
    timestamp: string;
  }>;
  manual_review_status?: string;
  notes?: string;
  isStarred?: boolean;
}

export interface FilterState {
  searchTerm: string;
  issuers: string[];
  eventAssociations: string[];
  procurementTypes: string[];
  dateRange: {
    start?: Date;
    end?: Date;
  };
  showIgnored: boolean;
  quickFilters: {
    newThisWeek: boolean;
    closingSoon: boolean;
    highValue: boolean;
  };
}

export interface SiteConfig {
  id: string;
  name: string;
  base_url: string;
  main_rfp_page_url: string;
  sample_rfp_url: string;
  field_mappings: Array<{
    alias: string;
    selector: string;
    data_type: 'text' | 'date' | 'currency' | 'number' | 'url' | 'email';
    training_value: string;
    confidence_score: number;
    xpath?: string;
    regex_pattern?: string;
    fallback_selectors: string[];
    last_validated?: string;
    validation_errors: string[];
    expected_format?: string;
    status: 'working' | 'degraded' | 'broken' | 'untested';
    consecutive_failures: number;
  }>;
  status: 'active' | 'error' | 'testing' | 'disabled' | 'deleted';
  last_scrape?: string;
  last_test?: string;
  rfp_count: number;
  test_results?: {
    is_valid: boolean;
    errors: string[];
    warnings: string[];
    timestamp: string;
  };
  description?: string;
  contact_info?: string;
  terms_of_service_url?: string;
  robots_txt_compliant: boolean;
  scraper_settings?: {
    delay_between_requests: number;
    timeout: number;
    max_retries: number;
    respect_robots_txt: boolean;
  };
}

export interface ScraperParameter {
  id: string;
  alias: string;
  currentValue: string;
  xpath?: string;
  dataType: 'text' | 'number' | 'date' | 'currency';
}

// API Response types
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
  count?: number;
}

// Error handling interface
export interface ApiError {
  detail: string | { message: string; errors: string[] };
}

// Re-export for compatibility
export type { ApiError as APIError };
