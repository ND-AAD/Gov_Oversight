# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LA 2028 RFP Monitor - A public oversight tool for tracking 2028 Olympics procurement contracts. This tool provides transparency by automatically scraping government RFPs, with special focus on identifying potentially concerning surveillance and infrastructure contracts.

## Development Commands

### Backend (Python)
```bash
cd backend
pip install -r requirements.txt
playwright install
python main.py --help                # CLI help
python test_runner.py               # Run all tests
python main.py scrape               # Scrape RFPs
python main.py list-sites           # List configured sites
python main.py stats                # Show statistics
```

### Frontend (React + TypeScript)
```bash
cd frontend
npm install
npm run dev                         # Development server
npm run build                       # Production build
npm run lint                        # ESLint
```


## Architecture

### GitHub-Only Architecture
- **Backend**: Python scraper with CLI interface (`backend/`)
- **Frontend**: React dashboard with TypeScript (`frontend/`)
- **GitHub Actions**: All processing (scraping, site management, deployment)
- **Data Storage**: JSON files in `/data/` directory
- **Hosting**: GitHub Pages for free, transparent hosting
- **Documentation**: Markdown guides in root directory

### Core Innovation: Location-Binding Extraction
The scraper uses a revolutionary approach instead of fragile CSS selectors:
1. User provides sample: "Status: Active" from a real RFP
2. Scraper finds DOM location of "Active"
3. Maps "Status" alias to that position
4. Future extractions read whatever appears there

This makes scraping resilient to website changes while requiring zero technical knowledge.

### Key Components

#### Backend Architecture (`backend/`)
- **Models**: Core data structures (`models/rfp.py`, `models/site_config.py`)
  - `RFP`: Represents procurement opportunities with change tracking
  - `SiteConfig`: Website configurations with field mappings
  - `FieldMapping`: Location-binding configuration for data extraction
- **Scrapers**: Web scraping infrastructure (`scrapers/`)
  - `BaseScraper`: Playwright-based scraper with rate limiting
  - `LocationBinder`: Core location-binding extraction engine
  - `RFPScraper`: RFP-specific scraping logic
- **Utils**: Supporting tools (`utils/`)
  - `ChangeDetector`: Tracks changes in RFP data over time
  - `DataArchiver`: Creates timestamped data archives
  - `SiteMonitor`: Health monitoring for configured sites

#### Frontend Architecture (`frontend/src/`)
- **Components**: React components with shadcn/ui
  - `Dashboard.tsx`: Main RFP browsing interface
  - `SiteManagement.tsx`: Add/configure RFP sites
  - `RFPDetailModal.tsx`: Detailed RFP information
  - `FilterBar.tsx`: Search and filter functionality
- **Types**: TypeScript definitions (`types/rfp.ts`)
- **Utils**: API and utility functions (`utils/`)

### Data Flow
1. Sites configured via frontend (localStorage → GitHub Actions)
2. GitHub Actions processes site additions and scraping
3. Data stored in JSON files (`/data/rfps.json`, `/data/sites.json`)
4. Frontend reads data from GitHub Pages static files
5. Changes tracked via git history and archival system

## Testing

### Backend Testing
```bash
cd backend
python test_runner.py               # All tests
python test_runner.py --unit-only   # Unit tests only
python -m pytest tests/test_models.py -v  # Specific test file
```

Test coverage includes:
- Data models and validation (95%+ coverage)
- Location-binding engine (90%+ coverage) 
- CLI interface (all commands)
- Integration workflows (end-to-end)

Success criteria: 90%+ test pass rate before proceeding to frontend work.

## Olympic Surveillance Detection

The system automatically categorizes RFPs for surveillance-related contracts:

**High Priority Keywords**: facial recognition, biometric, surveillance, monitoring, intelligence, predictive policing, social media monitoring, cell site simulator, stingray, IMSI catcher, mass surveillance

**Categories**: Security, Technology, Olympics, Surveillance, Data Collection

Use `validate_olympic_relevance()` function to test surveillance detection.

## Data Formats

### RFP Structure
```json
{
  "id": "la_county_rfp_001",
  "title": "Olympic Village Security Infrastructure",
  "url": "https://example.gov/rfp/001",
  "source_site": "LA County Procurement", 
  "extracted_fields": {
    "status": "Active",
    "posted_date": "2024-12-16",
    "closing_date": "2025-01-15",
    "contract_value": "$15,000,000"
  },
  "categories": ["Security", "Technology", "Olympics"],
  "detected_at": "2024-12-16T10:00:00Z"
}
```

### Site Configuration
```json
{
  "id": "la_county",
  "name": "LA County Procurement",
  "base_url": "https://lacounty.gov",
  "main_rfp_page_url": "https://lacounty.gov/bids",
  "field_mappings": [
    {
      "alias": "status", 
      "selector": ".rfp-status",
      "data_type": "text",
      "training_value": "Active"
    }
  ]
}
```

## Development Notes

- Always run backend tests before frontend work
- Use location-binding instead of CSS selectors for extraction
- Respect robots.txt and implement rate limiting
- Olympic surveillance detection is a core feature
- All scraping is logged for transparency
- Data files are publicly accessible for transparency

## File Organization

- `/backend/` - Python scraper and CLI
- `/frontend/` - React dashboard  
- `/api/` - Vercel serverless functions
- `/data/` - JSON data files (RFPs, sites, archives)
- `/docs/` - Documentation
- `WORK_PLAN.md` - Development progress tracking
- `DEPLOYMENT_GUIDE.md` - Deployment instructions