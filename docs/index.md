# LA 2028 RFP Monitor Documentation

Welcome to the documentation for the LA 2028 RFP Monitor - a public oversight tool for tracking Olympic-related government procurement.

## Quick Links

- [📖 Project Overview](../README.md)
- [📋 Work Plan & Progress](../WORK_PLAN.md)
- [💻 GitHub Repository](https://github.com/ND-AAD/Gov_Oversight)
- [🐛 Report Issues](https://github.com/ND-AAD/Gov_Oversight/issues)

## Project Status

**Current Phase:** Foundation & Core Backend (Phase 1)
**Progress:** Item 1.1 Complete ✅ | Working on Items 1.2-1.5

## What This Tool Does

This scraper monitors government websites for Request for Proposals (RFPs) related to the 2028 Los Angeles Olympics, with particular focus on:

- 🕵️ **Surveillance Infrastructure** - Security systems, monitoring equipment
- 🏗️ **Construction Contracts** - Olympic venues, infrastructure projects  
- 🚨 **Security Services** - Policing, crowd control, emergency response
- 📊 **Data Systems** - Databases, analytics platforms, citizen tracking

## Why This Matters

The 2028 Olympics provide cover for expanding government surveillance capabilities. By tracking RFPs in real-time, citizens can:

- Identify concerning contracts before they're awarded
- Organize public opposition to problematic procurement
- Ensure public debate about surveillance expansion
- Hold officials accountable for transparency promises

## Architecture Overview

### Location-Binding Technology
Instead of fragile CSS selectors, our scraper learns from examples:
1. User provides sample data from government sites
2. Scraper identifies where that data appears
3. Future scraping extracts current values from those locations
4. Resilient to website design changes

### Transparency by Design
- **Public Code**: All scraping logic is open source
- **Public Data**: RFP data available at `/data/rfps.json`
- **Public Operations**: GitHub Actions show every scraping run
- **Public Issues**: Community can report problems or suggest improvements

## Getting Started

### For Activists
- Browse current RFPs at [the main dashboard](#) *(coming in Phase 2)*
- Report concerning contracts via GitHub Issues
- Share findings on social media using `#Olympics2028Watch`

### For Developers
- Review the [Work Plan](../WORK_PLAN.md) for contribution opportunities
- Check [open issues](https://github.com/ND-AAD/Gov_Oversight/issues) for tasks
- Read the [technical documentation](#) *(coming in Phase 2)*

### For Government Officials
- This tool only accesses publicly available information
- We respect robots.txt and implement reasonable rate limiting
- Contact us via GitHub Issues for any concerns

## Data Format

### RFP Structure
```json
{
  "id": "unique_identifier",
  "title": "RFP Title",
  "url": "https://source.gov/rfp/link",
  "source_site": "Government Agency Name",
  "extracted_fields": {
    "status": "Active",
    "posted_date": "2024-12-16",
    "closing_date": "2025-01-15",
    "contract_value": "$15,000,000"
  },
  "categories": ["Security", "Olympics"],
  "detected_at": "2024-12-16T10:00:00Z"
}
```

### Site Configuration
```json
{
  "id": "site_identifier", 
  "name": "Human-readable name",
  "base_url": "https://agency.gov",
  "field_mappings": [
    {
      "alias": "status",
      "selector": ".rfp-status",
      "training_value": "Active"
    }
  ]
}
```

## Contributing

### Adding New Sites
1. Use the "Add Site" feature *(coming in Phase 2)*
2. Provide sample RFP with field examples
3. Test configuration with real data
4. Submit pull request

### Improving Detection
1. Review categorization logic in `backend/utils/`
2. Add Olympic-related keywords
3. Test against existing RFP database
4. Submit PR with evidence of improvement

## Legal & Ethical Guidelines

- ✅ **Compliant**: Respects robots.txt and rate limits
- ✅ **Transparent**: All activities logged and auditable
- ✅ **Public**: Only scrapes publicly available data
- ✅ **Non-commercial**: Tool serves public interest, not profit

## Contact & Support

- **Bug Reports**: [GitHub Issues](https://github.com/ND-AAD/Gov_Oversight/issues)
- **Feature Requests**: [GitHub Discussions](#) *(coming soon)*
- **Security Issues**: Email maintainers privately
- **Press Inquiries**: Contact via repository maintainers

---

**🔥 Built by activists, for activists. Transparency is our superpower.**

*Last updated: December 16, 2024*
