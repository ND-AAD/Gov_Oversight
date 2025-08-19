# Data Directory

This directory contains all scraped RFP data and site configurations.

## Structure

- `rfps.json` - Current active RFPs (main data file)
- `sites.json` - Site configurations with field mappings
- `ignored_rfps.json` - RFPs that have been marked as ignored
- `history/` - Historical snapshots of RFP data

## Files

### rfps.json
The main data file consumed by the frontend dashboard. Contains all currently active RFPs with their extracted fields and metadata.

### sites.json  
Site configurations created through the "Add Site" interface. Each configuration includes field mappings that teach the scraper where to find data on each government website.

### ignored_rfps.json
List of RFP IDs that users have marked as ignored. These RFPs are filtered out of the main dashboard but preserved for audit purposes.

### history/
Daily snapshots of all RFP data for historical analysis and change tracking. Files are named with timestamps: `YYYYMMDD_HHMMSS.json`

## Data Format

All files use JSON format for maximum transparency and accessibility. See the data models in `backend/models/` for detailed schemas.

## Public Access

This data is publicly accessible via GitHub Pages for full transparency:
- `/data/rfps.json` - Current RFPs
- `/data/sites.json` - Site configurations  
- `/data/history/` - Historical data

## Privacy & Ethics

All data in this directory consists of publicly available government procurement information. No private or sensitive data is stored.
