# LA 2028 RFP Monitor

🔍 **Public oversight tool for tracking 2028 Olympics procurement contracts**

A transparent web scraper that monitors government Request for Proposals (RFPs) related to the LA 2028 Olympics, with special focus on identifying potentially concerning surveillance and infrastructure contracts.

## 🎯 Mission

The 2028 Olympics present opportunities for government overreach through surveillance infrastructure procurement. This tool provides public transparency by automatically tracking RFPs across government websites, enabling activists and citizens to monitor concerning contracts before they're awarded.

## ✨ Key Features

- **🕸️ Intelligent Web Scraping**: User-guided field extraction that learns from examples
- **📊 Beautiful Dashboard**: React-based interface for browsing and filtering RFPs
- **🔍 Smart Categorization**: Automatic flagging of surveillance and security contracts
- **📱 Mobile Responsive**: Works on all devices for maximum accessibility
- **🔓 Fully Transparent**: All code, data, and configurations are public
- **⚡ Real-time Updates**: Automated scraping every 6 hours with GitHub Actions

## 🚀 How It Works

### Revolutionary Approach: Location-Binding Extraction

Instead of fragile CSS selectors, our scraper learns from user examples:

1. **User provides sample**: "Status: Active" from a real government RFP
2. **Scraper finds location**: Identifies where "Active" appears on the page
3. **Binds alias to location**: Maps "Status" to that DOM position  
4. **Future extractions**: Reads whatever value appears in that location ("Active", "Closed", etc.)

This makes the scraper incredibly resilient to website changes while requiring zero technical knowledge from users.

## 🏗️ Architecture

- **Frontend**: React + TypeScript with shadcn/ui components
- **Backend**: Python with Playwright for robust web scraping
- **Storage**: JSON files for simplicity and transparency
- **Hosting**: GitHub Pages for free, reliable hosting
- **Automation**: GitHub Actions for scheduled scraping
- **Data**: Publicly accessible at `/data/rfps.json`

## 📋 Current Status

**Phase 1: Foundation & Core Backend** ⏳ *In Progress*
- [x] Technical specification complete
- [x] Project structure created
- [ ] Core scraper engine
- [ ] Location-binding system
- [ ] Data models

**Upcoming Phases:**
- Phase 2: Frontend Integration
- Phase 3: GitHub Deployment  
- Phase 4: Real-world Testing

See `WORK_PLAN.md` for detailed progress tracking.

## 🛠️ Development Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- Git

### Backend Setup
```bash
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
1. Use the "Add Site" feature in the dashboard
2. Provide sample RFP URL and field examples
3. Test configuration before submitting
4. Submit pull request with site configuration

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

**🔥 Built by activists, for activists. Transparency is our superpower.**
