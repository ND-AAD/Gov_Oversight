# GitHub Workflow Guide - Site Addition System

## Overview

The LA 2028 RFP Monitor uses a GitHub-native approach for adding new government sites. This ensures transparency and allows non-technical users to easily contribute while maintaining data integrity.

## How Site Addition Works

### 1. User Experience (Dashboard)
- Users fill out the "Add Site" form in the dashboard
- Form validates required fields (Site Name, Base URL)
- Advanced mode allows custom field mapping configuration
- Submission creates a GitHub issue automatically

### 2. GitHub Issue Processing
- Issues are labeled with `site-addition` for automated processing
- GitHub Actions runs every hour to check for new site requests
- Valid configurations are automatically added to `data/sites.json`
- Issues are automatically closed with status updates

### 3. Automated Integration
- New sites are included in the next scraping run
- Dashboard shows pending sites immediately for good UX
- All changes are tracked in git history for transparency

## File Structure

```
.github/
├── ISSUE_TEMPLATE/
│   └── site-addition.yml          # Template for site addition requests
├── scripts/
│   ├── process_pending_sites.py   # Main processing script
│   ├── count_rfps.py              # Helper for RFP counting
│   └── generate_stats.py          # Statistics generation
└── workflows/
    ├── deploy.yml                 # Deploy to GitHub Pages
    ├── scrape.yml                 # Automated RFP scraping
    └── process-pending-sites.yml  # Process site addition requests
```

## For Non-Technical Users

### Adding Sites via Dashboard (Recommended)
1. Visit the live dashboard at: https://nd-aad.github.io/Gov_Oversight/
2. Click "Add Site" button
3. Fill in the required information:
   - **Site Name**: Descriptive name (e.g., "LA County Procurement")
   - **Base URL**: Main website URL (e.g., "https://lacounty.gov")
   - **RFP Page URL**: Where RFPs are listed (optional)
   - **Sample RFP URL**: Link to a specific RFP for training (optional)
4. Enable "Advanced Configuration" for custom field mapping
5. Submit - the site will be processed within 1 hour

### Adding Sites via GitHub Issues (Manual)
If the dashboard is not working, you can create a GitHub issue manually:

1. Go to: https://github.com/ND-AAD/Gov_Oversight/issues/new/choose
2. Select "Add Government Site for RFP Monitoring"
3. Fill out the template form
4. Submit the issue

## For Technical Users

### Local Development Setup
```bash
# Backend development
cd backend
pip install -r requirements.txt
python main.py --help

# Frontend development  
cd frontend
npm install
npm run dev
```

### Manual Site Addition
```bash
# Add site via command line
cd backend
python main.py add-site "Site Name" "https://example.gov" "https://example.gov/rfps" "https://example.gov/rfp/sample"

# Test site configuration
python main.py test-site site_id

# Run scraper
python main.py scrape
```

### GitHub Actions Maintenance

#### Key Environment Variables
- `GITHUB_TOKEN`: Automatically provided by GitHub Actions
- `GITHUB_REPOSITORY`: Repository in "owner/repo" format

#### Workflow Triggers
- **Scraping**: Every 6 hours + manual dispatch
- **Site Processing**: Every hour + manual dispatch  
- **Deployment**: After successful scrape + manual dispatch

#### Manual Workflow Triggers
```bash
# Trigger scraping
gh workflow run scrape.yml

# Force process pending sites
gh workflow run process-pending-sites.yml -f force_process=true

# Deploy to GitHub Pages
gh workflow run deploy.yml
```

## Data Flow Architecture

```
User Dashboard → GitHub Issue → GitHub Actions → sites.json → Scraping → rfps.json → Dashboard
```

### Key Features
1. **Immediate UX**: Sites appear in dashboard immediately via localStorage
2. **Reliable Processing**: GitHub Actions ensure sites are actually added
3. **Transparent**: All changes tracked in git history
4. **Scalable**: Can handle dozens of sites without performance issues
5. **Non-Technical Friendly**: Simple form interface with validation

## Troubleshooting

### Common Issues

#### "Site not appearing after submission"
- Check GitHub Issues tab for the site addition request
- Verify the issue has the `site-addition` label
- Check GitHub Actions for processing status

#### "GitHub Actions failing"
- Check Actions tab for error logs
- Verify `sites.json` format is valid JSON
- Ensure Python dependencies are installed correctly

#### "Scraping not finding new sites"
- Verify sites are in `data/sites.json` with `"status": "active"`
- Check scraping logs in GitHub Actions
- Test site configuration manually

### Data File Formats

#### sites.json Structure
```json
{
  "metadata": {
    "last_updated": "2024-12-16T15:30:00Z",
    "total_sites": 3,
    "version": "1.0"
  },
  "sites": [
    {
      "id": "site_id",
      "name": "Site Name",
      "base_url": "https://example.gov",
      "main_rfp_page_url": "https://example.gov/rfps",
      "sample_rfp_url": "https://example.gov/rfp/sample",
      "description": "Description",
      "field_mappings": [],
      "status": "active",
      "last_scrape": null,
      "rfp_count": 0
    }
  ]
}
```

## Security Considerations

- All site additions go through GitHub's review system
- No direct database access from frontend
- User input is validated before processing
- All changes are auditable through git history
- Rate limiting prevents spam submissions

## Contributing

### Adding Features
1. Fork the repository
2. Create feature branch
3. Test changes locally
4. Submit pull request with detailed description

### Reporting Issues
- Use GitHub Issues with appropriate labels
- Include steps to reproduce
- Provide relevant URLs and error messages

---

**For immediate help**: Create a GitHub issue or contact the repository maintainers.

**Production URL**: https://nd-aad.github.io/Gov_Oversight/
