# LA 2028 RFP Monitor - Work Plan & Progress Tracking

## Project Overview

**Mission**: Build a transparent web scraper to monitor government RFPs related to the 2028 Olympics, enabling public oversight of potentially concerning surveillance and infrastructure contracts.

**Architecture**: GitHub-hosted static site with automated scraping, using innovative user-guided field extraction for maximum reliability.

## Core Innovation: Location-Binding Extraction

Users provide sample values from government sites to "teach" the scraper where to find each field. The scraper binds aliases to DOM locations, then extracts current values from those locations during future runs.

---

## Phase 1: Foundation & Core Backend (Week 1) ⏳

### 1.1 Project Structure Setup ✅
```
la-2028-rfp-monitor/
├── .github/workflows/           # GitHub Actions
├── backend/                     # Python scraper
├── frontend/                    # React dashboard  
├── data/                        # JSON data storage
├── docs/                        # GitHub Pages site
├── .reference/                  # Original reference files
└── README.md
```

**Status**: ✅ Complete
- [x] Folder structure created
- [x] Reference folder renamed to `.reference`
- [x] README.md written
- [x] Work plan documented

### 1.2 Core Data Models ⏳
```python
@dataclass
class FieldMapping:
    alias: str
    selector: str  
    data_type: str
    training_value: str
    confidence_score: float

@dataclass  
class SiteConfig:
    id: str
    name: str
    base_url: str
    main_rfp_page_url: str
    sample_rfp_url: str
    field_mappings: List[FieldMapping]
    last_tested: datetime
    status: str

@dataclass
class RFP:
    id: str
    title: str
    url: str
    source_site: str
    extracted_fields: Dict[str, Any]
    detected_at: datetime
    content_hash: str
    categories: List[str]
```

**Status**: ⏳ In Progress
- [ ] Create `backend/models/` directory
- [ ] Implement `rfp.py` data model
- [ ] Implement `site_config.py` data model
- [ ] Add validation methods
- [ ] Create serialization helpers

### 1.3 Location-Binding Core Engine ⏳
```python
class LocationBinder:
    def find_field_location(self, target_value: str, data_type: str) -> str
    def generate_stable_selector(self, element) -> str  
    def validate_field_mapping(self, field_mapping: FieldMapping) -> bool
    def create_site_configuration(self, sample_url: str, field_specs: List[Dict]) -> SiteConfig
```

**Status**: ⏳ Pending
- [ ] Create `backend/scrapers/location_binder.py`
- [ ] Implement value-to-location discovery
- [ ] Add stable selector generation
- [ ] Create field mapping validation
- [ ] Add error handling with suggestions

### 1.4 Base Scraper Infrastructure ⏳

**Status**: ⏳ Pending  
- [ ] Create `backend/scrapers/base_scraper.py`
- [ ] Implement Playwright integration
- [ ] Add robots.txt compliance checking
- [ ] Create rate limiting system
- [ ] Add User-Agent rotation

### 1.5 Requirements & Dependencies ⏳

**Status**: ⏳ Pending
- [ ] Create `backend/requirements.txt`
- [ ] Add Playwright dependencies
- [ ] Include data processing libraries
- [ ] Add testing frameworks

---

## Phase 2: Frontend Integration (Week 2) 📋

### 2.1 Adapt React Components
**Status**: 📋 Planned
- [ ] Modify `Dashboard.tsx` for real data consumption
- [ ] Update `SiteManagement.tsx` with backend integration
- [ ] Enhance "Add Site" modal for live testing
- [ ] Add real-time feedback systems

### 2.2 API Bridge Layer  
**Status**: 📋 Planned
- [ ] Create TypeScript API client
- [ ] Implement site configuration testing
- [ ] Add field validation endpoints
- [ ] Create error handling interfaces

### 2.3 Enhanced UX
**Status**: 📋 Planned
- [ ] Real-time field validation
- [ ] Progress indicators for site testing
- [ ] Detailed error messaging
- [ ] Success confirmations with sample data

---

## Phase 3: GitHub Integration & Deployment (Week 3) 📋

### 3.1 GitHub Actions Workflows
**Status**: 📋 Planned
- [ ] Create `scrape.yml` for automated scraping
- [ ] Create `deploy.yml` for site deployment  
- [ ] Add data validation workflows
- [ ] Implement change detection alerts

### 3.2 Data Management
**Status**: 📋 Planned
- [ ] Optimize JSON file structure
- [ ] Create historical data archiving
- [ ] Add change detection system
- [ ] Generate public API endpoints

### 3.3 Security & Compliance
**Status**: 📋 Planned
- [ ] Add robots.txt compliance
- [ ] Implement respectful rate limiting
- [ ] Create error recovery systems
- [ ] Add site health monitoring

---

## Phase 4: Testing & Validation (Week 4) 📋

### 4.1 Real Site Integration
**Status**: 📋 Planned
- [ ] Test with LA County procurement site
- [ ] Test with City of LA contracts
- [ ] Validate field extraction accuracy
- [ ] Stress test error handling

### 4.2 Community Features  
**Status**: 📋 Planned
- [ ] Site configuration sharing
- [ ] Multi-user field validation
- [ ] Community error reporting
- [ ] Public audit trail

---

## Success Metrics

- [x] **Documentation**: Comprehensive README and work plan
- [ ] **Reliability**: 95%+ successful field extraction on configured sites
- [ ] **Usability**: Non-technical users can add new sites in <10 minutes  
- [ ] **Transparency**: All code, data, and configurations publicly auditable
- [ ] **Performance**: Sub-30 second site configuration testing
- [ ] **Compliance**: Zero legal/ethical issues with government site scraping

---

## Current Focus: Phase 1.2 - Core Data Models

**Next Steps**:
1. Create backend directory structure
2. Implement RFP and SiteConfig data models
3. Add validation and serialization methods
4. Begin location-binding engine development

**Blockers**: None

**Timeline**: On track for Week 1 completion

---

## Legend
- ✅ **Complete**: Task finished and tested
- ⏳ **In Progress**: Currently being worked on  
- 📋 **Planned**: Scheduled for future phases
- ⚠️ **Blocked**: Waiting on dependencies
- ❌ **Cancelled**: No longer needed

Last Updated: 2024-12-16
