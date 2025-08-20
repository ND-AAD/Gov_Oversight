import { RFP, SiteConfig } from '../types/rfp';

export const mockRFPs: RFP[] = [
  {
    id: 'rfp-001',
    title: 'Olympic Village Security Infrastructure and Surveillance Systems',
    url: 'https://example.gov/rfp/olympic-security-001',
    posted_date: '2024-12-15',
    closing_date: '2025-01-15',
    description: 'Comprehensive security infrastructure including CCTV networks, access control systems, and perimeter monitoring for the LA 2028 Olympic Village. Requirements include AI-powered surveillance capabilities, facial recognition systems, and integrated threat detection.',
    source_site: 'LA City Portal',
    content_hash: 'hash001',
    detected_at: '2024-12-15T10:00:00Z',
    categories: ['Security', 'Technology', 'Olympics'],
    issuer: 'Los Angeles Police Department',
    event_association: 'Olympics 2028',
    procurement_type: 'Technology',
    contract_value: 15000000,
    status: 'active'
  },
  {
    id: 'rfp-002',
    title: 'Transportation Hub Digital Signage and Information Systems',
    url: 'https://example.gov/rfp/transport-digital-002',
    posted_date: '2024-12-10',
    closing_date: '2024-12-30',
    description: 'Design, installation, and maintenance of digital signage networks across major transportation hubs including LAX, Union Station, and metro stations. System must support real-time updates, multilingual content, and emergency broadcasts.',
    source_site: 'Metro LA Procurement',
    content_hash: 'hash002',
    detected_at: '2024-12-10T14:30:00Z',
    categories: ['Transportation', 'Digital Infrastructure'],
    issuer: 'Los Angeles Metro',
    event_association: 'Olympics 2028',
    procurement_type: 'Technology',
    contract_value: 8500000,
    status: 'closing_soon'
  },
  {
    id: 'rfp-003',
    title: 'Olympic Stadium Construction and Infrastructure Development',
    url: 'https://example.gov/rfp/stadium-construction-003',
    posted_date: '2024-12-01',
    closing_date: '2025-02-28',
    description: 'Major construction project for Olympic stadium infrastructure including seating, accessibility features, technology integration, and sustainable building practices. Must meet IOC requirements and LEED certification standards.',
    source_site: 'CA State Contracts',
    content_hash: 'hash003',
    detected_at: '2024-12-01T09:15:00Z',
    categories: ['Construction', 'Infrastructure'],
    issuer: 'California Department of General Services',
    event_association: 'Olympics 2028',
    procurement_type: 'Construction',
    contract_value: 125000000,
    status: 'active'
  },
  {
    id: 'rfp-004',
    title: 'Emergency Response Communication Network Upgrade',
    url: 'https://example.gov/rfp/emergency-comms-004',
    posted_date: '2024-11-28',
    closing_date: '2024-12-28',
    description: 'Modernization of emergency response communication networks to support increased capacity during Olympic events. Includes radio systems, dispatch software, and interoperability with federal agencies.',
    source_site: 'LA County Procurement',
    content_hash: 'hash004',
    detected_at: '2024-11-28T16:45:00Z',
    categories: ['Emergency Services', 'Communications'],
    issuer: 'LA County Fire Department',
    event_association: 'Olympics 2028',
    procurement_type: 'Technology',
    contract_value: 12000000,
    status: 'closing_soon'
  },
  {
    id: 'rfp-005',
    title: 'Venue Crowd Management and Analytics Platform',
    url: 'https://example.gov/rfp/crowd-analytics-005',
    posted_date: '2024-12-12',
    closing_date: '2025-01-20',
    description: 'AI-powered crowd management system utilizing computer vision and predictive analytics to monitor crowd density, flow patterns, and potential safety issues across Olympic venues. Must integrate with existing security infrastructure.',
    source_site: 'LA City Portal',
    content_hash: 'hash005',
    detected_at: '2024-12-12T11:20:00Z',
    categories: ['AI/ML', 'Safety', 'Analytics'],
    issuer: 'LA Emergency Management Department',
    event_association: 'Olympics 2028',
    procurement_type: 'Technology',
    contract_value: 6800000,
    status: 'active'
  },
  {
    id: 'rfp-006',
    title: 'FIFA World Cup 2026 Stadium Security Assessment',
    url: 'https://example.gov/rfp/fifa-security-006',
    posted_date: '2024-12-08',
    closing_date: '2025-01-10',
    description: 'Comprehensive security assessment and planning for FIFA World Cup 2026 venues in Los Angeles area. Includes threat analysis, security protocol development, and coordination with international security agencies.',
    source_site: 'CA State Contracts',
    content_hash: 'hash006',
    detected_at: '2024-12-08T13:10:00Z',
    categories: ['Security', 'Assessment'],
    issuer: 'California Highway Patrol',
    event_association: 'World Cup 2026',
    procurement_type: 'Services',
    contract_value: 2500000,
    status: 'active'
  },
  {
    id: 'rfp-007',
    title: 'Public Wi-Fi Infrastructure Expansion',
    url: 'https://example.gov/rfp/wifi-expansion-007',
    posted_date: '2024-11-25',
    closing_date: '2025-01-05',
    description: 'Expansion of public Wi-Fi infrastructure throughout Los Angeles to support increased connectivity demands during major sporting events. Includes network security, capacity planning, and user analytics.',
    source_site: 'LA City Portal',
    content_hash: 'hash007',
    detected_at: '2024-11-25T08:30:00Z',
    categories: ['Infrastructure', 'Connectivity'],
    issuer: 'LA Department of Technology',
    event_association: 'Olympics 2028',
    procurement_type: 'Technology',
    contract_value: 18000000,
    status: 'active'
  },
  {
    id: 'rfp-008',
    title: 'Environmental Monitoring and Air Quality Systems',
    url: 'https://example.gov/rfp/environmental-008',
    posted_date: '2024-12-03',
    closing_date: '2024-12-23',
    description: 'Installation and maintenance of environmental monitoring stations to track air quality, noise levels, and other environmental factors during Olympic events. Data must be publicly accessible and real-time.',
    source_site: 'EPA Region 9',
    content_hash: 'hash008',
    detected_at: '2024-12-03T15:45:00Z',
    categories: ['Environmental', 'Monitoring'],
    issuer: 'South Coast Air Quality Management District',
    event_association: 'Olympics 2028',
    procurement_type: 'Equipment',
    contract_value: 4200000,
    status: 'closing_soon'
  }
];

export const mockSiteConfigs: SiteConfig[] = [
  {
    id: 'site-001',
    name: 'LA City Portal',
    baseUrl: 'https://losangeles.gov',
    lastScrape: '2024-12-16T10:00:00Z',
    status: 'active',
    rfpCount: 12
  },
  {
    id: 'site-002',
    name: 'CA State Contracts',
    baseUrl: 'https://caleprocure.ca.gov',
    lastScrape: '2024-12-16T09:30:00Z',
    status: 'active',
    rfpCount: 8
  },
  {
    id: 'site-003',
    name: 'Metro LA Procurement',
    baseUrl: 'https://metro.net',
    lastScrape: '2024-12-16T08:45:00Z',
    status: 'active',
    rfpCount: 5
  },
  {
    id: 'site-004',
    name: 'LA County Procurement',
    baseUrl: 'https://lacounty.gov',
    lastScrape: '2024-12-15T16:20:00Z',
    status: 'error',
    rfpCount: 3
  }
];

// Helper functions for mock data
export const getUniqueValues = (rfps: RFP[], field: keyof RFP): string[] => {
  const values = rfps.map(rfp => rfp[field]).filter(Boolean) as string[];
  return [...new Set(values)].sort();
};

export const getRecentRFPs = (rfps: RFP[], days: number = 7): RFP[] => {
  const cutoffDate = new Date();
  cutoffDate.setDate(cutoffDate.getDate() - days);
  
  return rfps.filter(rfp => new Date(rfp.posted_date) >= cutoffDate);
};

export const getClosingSoonRFPs = (rfps: RFP[], days: number = 7): RFP[] => {
  const cutoffDate = new Date();
  cutoffDate.setDate(cutoffDate.getDate() + days);
  
  return rfps.filter(rfp => 
    rfp.closing_date && new Date(rfp.closing_date) <= cutoffDate
  );
};

export const getHighValueRFPs = (rfps: RFP[], threshold: number = 1000000): RFP[] => {
  return rfps.filter(rfp => (rfp.contract_value || 0) >= threshold);
};