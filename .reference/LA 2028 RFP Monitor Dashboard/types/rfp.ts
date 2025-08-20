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
  issuer?: string;
  event_association?: string;
  procurement_type?: string;
  contract_value?: number;
  status: 'active' | 'closing_soon' | 'closed';
  isStarred?: boolean;
  changeTracking?: {
    enabled: boolean;
    lastChanged?: string;
    changes: Array<{
      field: string;
      oldValue: string;
      newValue: string;
      timestamp: string;
    }>;
  };
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
  baseUrl: string;
  lastScrape?: string;
  status: 'active' | 'error' | 'disabled';
  rfpCount: number;
  scraperConfig?: {
    mainRfpPageUrl?: string;
    sampleRfpUrl?: string;
    customParameters?: Array<{
      alias: string;
      xpath: string;
      dataType: 'text' | 'number' | 'date' | 'currency';
    }>;
  };
  testResults?: {
    lastTest?: string;
    success: boolean;
    errors?: string[];
    rfpsFound?: number;
  };
}

export interface ScraperParameter {
  id: string;
  alias: string;
  currentValue: string;
  xpath?: string;
  dataType: 'text' | 'number' | 'date' | 'currency';
}