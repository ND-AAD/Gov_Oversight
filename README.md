# LA 2028 RFP Monitor

🔍 **Public oversight tool for tracking 2028 Olympics procurement contracts**

A transparent web scraper that monitors government Request for Proposals (RFPs) related to the LA 2028 Olympics, with special focus on identifying potentially concerning surveillance and infrastructure contracts.

## 🚀 **Live Application**: https://la-2028-rfp-monitor.vercel.app

## 🎯 Mission

The 2028 Olympics present opportunities for government overreach through surveillance infrastructure procurement. This tool provides public transparency by automatically tracking RFPs across government websites, enabling activists and citizens to monitor concerning contracts before they're awarded.

## ✨ Key Features

- **🕸️ Intelligent Web Scraping**: User-guided field extraction that learns from examples
- **📊 Beautiful Dashboard**: React-based interface for browsing and filtering RFPs
- **🔍 Smart Categorization**: Automatic flagging of surveillance and security contracts
- **📱 Mobile Responsive**: Works on all devices for maximum accessibility
- **🔓 Fully Transparent**: All code, data, and configurations are public
- **⚡ Instant Site Addition**: Add new sites via web form in 2-3 seconds
- **🔄 Real-time Updates**: Automated scraping every 6 hours with manual triggers

## 🚀 How It Works

### Revolutionary Approach: Direct File Updates

Users can now add sites and manage data through a professional web interface:

1. **Simple Web Form**: Fill out site details in the dashboard
2. **Instant Processing**: Vercel API updates GitHub files directly in 2-3 seconds
3. **Automatic Scraping**: GitHub Actions begins monitoring immediately
4. **Real-time Feedback**: See changes and commit URLs instantly

No GitHub account or technical knowledge required!

### Location-Binding Extraction

Instead of fragile CSS selectors, our scraper learns from user examples:

1. **User provides sample**: "Status: Active" from a real government RFP
2. **Scraper finds location**: Identifies where "Active" appears on the page
3. **Binds alias to location**: Maps "Status" to that DOM position  
4. **Future extractions**: Reads whatever value appears in that location ("Active", "Closed", etc.)

This makes the scraper incredibly resilient to website changes while requiring zero technical knowledge from users.

## 🏗️ Architecture

### Unified Vercel + GitHub Architecture
- **Frontend + API**: React + TypeScript dashboard with Vercel serverless functions
- **Backend**: Python with Playwright for robust web scraping
- **Storage**: JSON files for simplicity and transparency  
- **Hosting**: Vercel for frontend + API, GitHub for data storage
- **Automation**: GitHub Actions for scraping, Vercel for user operations
- **Data**: Real-time access via Vercel API endpoints

## 📋 Current Status

**🚀 Production Ready with Unified Architecture** *(August 2025)*

**Live System:**
- ✅ **Frontend Dashboard**: https://la-2028-rfp-monitor.vercel.app
- ✅ **Vercel API Integration**: Direct file updates in 2-3 seconds
- ✅ **Site Addition**: Simple web form, no GitHub account needed
- ✅ **RFP Scraping**: Active monitoring with GitHub Actions
- ✅ **Real-time Data**: Live RFP data from government sites

**Recent Achievements:**
- ✅ **Eliminated Brittleness**: No more manual GitHub issue creation
- ✅ **Professional UX**: Instant feedback and error handling
- ✅ **Zero Configuration**: Users can add sites immediately
- ✅ **Full Automation**: End-to-end pipeline working smoothly

**Currently Deployed:**
1. **Web Dashboard**: Browse RFPs, add sites, manage data
2. **Vercel API**: Instant site addition and data management
3. **GitHub Actions**: Automated scraping every 6 hours
4. **Real-time Updates**: Direct file commits with full transparency

See `WORK_PLAN.md` for detailed progress tracking.

## 🛠️ Development Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- Git

### Quick Start
```bash
# Frontend development
npm run dev

# Backend development
cd backend
pip install -r requirements.txt
playwright install
python main.py --test
```

### Frontend Setup  
```bash
cd frontend
npm install
npm run dev
```

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
playwright install
python main.py --test
```

## 📊 Data Structure

### RFP Data Format
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
    "contract_value": "$15,000,000",
    "issuer": "Los Angeles Police Department"
  },
  "categories": ["Security", "Technology", "Olympics"],
  "detected_at": "2024-12-16T10:00:00Z"
}
```

### Site Configuration Format
```json
{
  "id": "la_county",
  "name": "LA County Procurement", 
  "main_rfp_page_url": "https://lacounty.gov/bids",
  "sample_rfp_url": "https://lacounty.gov/rfp/sample",
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

## 🤝 Contributing

This project welcomes contributions from activists, developers, and concerned citizens:

### Adding New Sites
**Simple Web Interface:**
1. Visit https://la-2028-rfp-monitor.vercel.app
2. Click "Sites" → "Add Site" 
3. Fill out the simple form:
   - **Site Name**: "LA County Procurement"
   - **Base URL**: "https://lacounty.gov"
   - **RFP Page**: "https://lacounty.gov/bids"
   - **Sample RFP** (optional): Example RFP URL
4. Click "Submit" - site added in 2-3 seconds!
5. Scraping begins automatically within minutes

**Advanced Configuration** (optional):
- Add custom field mappings for better data extraction
- Specify training values for location-binding
- Configure scraping parameters

### Improving Categorization
1. Review `backend/utils/categorizer.py`
2. Add new surveillance/security keywords
3. Test against existing RFP database
4. Submit PR with evidence of improvement

### Bug Reports & Features
- Open issues with detailed descriptions
- Include URLs of problematic sites
- Provide screenshots when possible

## ⚖️ Legal & Ethics

- **Compliance**: Respects robots.txt and rate limits
- **Transparency**: All scraping is logged and auditable  
- **Public Data**: Only scrapes publicly available information
- **Non-commercial**: Tool is for public benefit, not profit

## 📞 Contact

- **Issues**: Use GitHub Issues for bugs and features
- **Security**: Email security concerns privately
- **Press**: Contact through repository maintainers

## 📜 License

MIT License - See `LICENSE` file for details.

---

