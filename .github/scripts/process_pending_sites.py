#!/usr/bin/env python3
"""
Process pending site additions from GitHub issues.

This script reads GitHub issues labeled 'site-addition', parses the site configuration,
validates it, and adds it to the sites.json file.
"""

import json
import os
import re
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any
import requests

def get_github_issues() -> List[Dict]:
    """Fetch open issues with 'site-addition' label."""
    token = os.environ.get('GITHUB_TOKEN')
    repo = os.environ.get('GITHUB_REPOSITORY')
    
    if not token or not repo:
        print("❌ Missing GitHub token or repository")
        return []
    
    url = f"https://api.github.com/repos/{repo}/issues"
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    params = {
        'labels': 'site-addition',
        'state': 'open'
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Failed to fetch issues: {e}")
        return []

def parse_site_config_from_issue(issue_body: str) -> Optional[Dict]:
    """Parse site configuration from issue body."""
    if not issue_body:
        return None
    
    # Look for site configuration in various formats
    config = {}
    
    # Extract site name
    name_match = re.search(r'(?:Site Name|Name):\s*(.+)', issue_body, re.IGNORECASE)
    if name_match:
        config['name'] = name_match.group(1).strip()
    
    # Extract URLs
    url_patterns = [
        (r'(?:Base URL|Main URL):\s*(https?://[^\s]+)', 'base_url'),
        (r'(?:RFP Page URL|RFP URL):\s*(https?://[^\s]+)', 'main_rfp_page_url'),
        (r'(?:Sample RFP URL|Sample URL):\s*(https?://[^\s]+)', 'sample_rfp_url'),
    ]
    
    for pattern, key in url_patterns:
        match = re.search(pattern, issue_body, re.IGNORECASE)
        if match:
            config[key] = match.group(1).strip()
    
    # Extract description
    desc_match = re.search(r'(?:Description):\s*(.+?)(?:\n\n|\n[A-Z]|$)', issue_body, re.IGNORECASE | re.DOTALL)
    if desc_match:
        config['description'] = desc_match.group(1).strip()
    
    # Check if we have minimum required fields
    required_fields = ['name', 'base_url']
    if not all(field in config for field in required_fields):
        return None
    
    # Set defaults for missing optional fields
    if 'main_rfp_page_url' not in config:
        config['main_rfp_page_url'] = config['base_url']
    if 'sample_rfp_url' not in config:
        config['sample_rfp_url'] = config['main_rfp_page_url']
    if 'description' not in config:
        config['description'] = f"Site configuration for {config['name']}"
    
    return config

def generate_site_id(name: str, existing_ids: List[str]) -> str:
    """Generate a unique site ID."""
    # Create base ID from name
    base_id = re.sub(r'[^a-z0-9_]', '_', name.lower())
    base_id = re.sub(r'_+', '_', base_id).strip('_')
    
    # Ensure uniqueness
    site_id = base_id
    counter = 1
    while site_id in existing_ids:
        site_id = f"{base_id}_{counter}"
        counter += 1
    
    return site_id

def validate_site_config(config: Dict) -> List[str]:
    """Validate site configuration and return any errors."""
    errors = []
    
    # Required fields
    required = ['name', 'base_url', 'main_rfp_page_url', 'sample_rfp_url']
    for field in required:
        if not config.get(field):
            errors.append(f"Missing required field: {field}")
    
    # URL validation
    url_fields = ['base_url', 'main_rfp_page_url', 'sample_rfp_url']
    for field in url_fields:
        if config.get(field) and not config[field].startswith(('http://', 'https://')):
            errors.append(f"Invalid URL format for {field}: {config[field]}")
    
    return errors

def load_current_sites() -> Dict:
    """Load current sites.json file."""
    sites_file = 'data/sites.json'
    
    if os.path.exists(sites_file):
        try:
            with open(sites_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Error reading sites.json: {e}")
    
    # Return default structure if file doesn't exist or is invalid
    return {
        "metadata": {
            "last_updated": datetime.now().isoformat() + "Z",
            "total_sites": 0,
            "version": "1.0"
        },
        "sites": []
    }

def save_sites_file(sites_data: Dict):
    """Save updated sites.json file."""
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    
    # Update metadata
    sites_data['metadata']['last_updated'] = datetime.now().isoformat() + "Z"
    sites_data['metadata']['total_sites'] = len(sites_data['sites'])
    
    with open('data/sites.json', 'w') as f:
        json.dump(sites_data, f, indent=2)

def close_issue(issue_number: int, comment: str):
    """Close a processed issue with a comment."""
    token = os.environ.get('GITHUB_TOKEN')
    repo = os.environ.get('GITHUB_REPOSITORY')
    
    if not token or not repo:
        return
    
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # Add comment
    comment_url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"
    try:
        requests.post(comment_url, headers=headers, json={'body': comment})
    except Exception as e:
        print(f"⚠️ Failed to add comment to issue #{issue_number}: {e}")
    
    # Close issue
    close_url = f"https://api.github.com/repos/{repo}/issues/{issue_number}"
    try:
        requests.patch(close_url, headers=headers, json={'state': 'closed'})
        print(f"✅ Closed issue #{issue_number}")
    except Exception as e:
        print(f"⚠️ Failed to close issue #{issue_number}: {e}")

def create_site_from_config(config: Dict, existing_ids: List[str]) -> Dict:
    """Create a complete site configuration."""
    site_id = generate_site_id(config['name'], existing_ids)
    
    return {
        "id": site_id,
        "name": config['name'],
        "base_url": config['base_url'],
        "main_rfp_page_url": config['main_rfp_page_url'],
        "sample_rfp_url": config['sample_rfp_url'],
        "description": config.get('description', f"Site configuration for {config['name']}"),
        "field_mappings": [],  # Will be configured via location-binding
        "status": "active",
        "last_scrape": None,
        "rfp_count": 0,
        "last_tested": datetime.now().isoformat() + "Z",
        "test_results": {
            "success": False,
            "errors": [],
            "warnings": ["Site needs to be tested and configured"],
            "tested_at": datetime.now().isoformat() + "Z"
        }
    }

def main():
    """Main processing function."""
    print("🏛️ Processing pending site additions...")
    
    # Fetch pending issues
    issues = get_github_issues()
    if not issues:
        print("ℹ️ No pending site addition issues found")
        return
    
    print(f"📋 Found {len(issues)} pending site addition issues")
    
    # Load current sites
    sites_data = load_current_sites()
    existing_ids = [site['id'] for site in sites_data['sites']]
    
    processed_count = 0
    
    for issue in issues:
        issue_number = issue['number']
        issue_title = issue['title']
        issue_body = issue['body'] or ''
        
        print(f"\n📄 Processing issue #{issue_number}: {issue_title}")
        
        # Parse site configuration
        config = parse_site_config_from_issue(issue_body)
        if not config:
            comment = f"""❌ **Site Addition Failed**

Unable to parse site configuration from this issue. Please ensure your issue includes:

- **Site Name**: Name of the government site
- **Base URL**: Main website URL (e.g., https://agency.gov)
- **RFP Page URL**: URL of the RFP listing page (optional, will use base URL)
- **Sample RFP URL**: URL of a specific RFP for testing (optional)
- **Description**: Brief description of the site (optional)

Example format:
```
Site Name: LA County Procurement
Base URL: https://lacounty.gov
RFP Page URL: https://lacounty.gov/bids
Sample RFP URL: https://lacounty.gov/rfp/sample-123
Description: Los Angeles County procurement portal
```

Please update this issue with the correct format and we'll process it automatically."""
            
            close_issue(issue_number, comment)
            continue
        
        # Validate configuration
        errors = validate_site_config(config)
        if errors:
            error_list = '\n'.join(f"- {error}" for error in errors)
            comment = f"""❌ **Site Addition Failed**

The site configuration has validation errors:

{error_list}

Please update the issue with corrected information."""
            
            close_issue(issue_number, comment)
            continue
        
        # Check for duplicate names/URLs
        existing_names = [site['name'].lower() for site in sites_data['sites']]
        existing_urls = [site['base_url'].lower() for site in sites_data['sites']]
        
        if config['name'].lower() in existing_names:
            comment = f"""⚠️ **Site Addition Skipped**

A site with the name "{config['name']}" already exists. Please check the existing sites or use a different name."""
            close_issue(issue_number, comment)
            continue
        
        if config['base_url'].lower() in existing_urls:
            comment = f"""⚠️ **Site Addition Skipped**

A site with the URL "{config['base_url']}" already exists. This site may already be configured."""
            close_issue(issue_number, comment)
            continue
        
        # Create site configuration
        new_site = create_site_from_config(config, existing_ids)
        sites_data['sites'].append(new_site)
        existing_ids.append(new_site['id'])
        
        print(f"✅ Added site: {new_site['name']} (ID: {new_site['id']})")
        
        # Close issue with success message
        comment = f"""✅ **Site Added Successfully**

Your site has been added to the RFP monitoring system!

**Site Details:**
- **Name**: {new_site['name']}
- **ID**: `{new_site['id']}`
- **Base URL**: {new_site['base_url']}
- **RFP Page**: {new_site['main_rfp_page_url']}

**Next Steps:**
1. The site will be included in the next scraping run
2. Use the dashboard to configure field mappings for better data extraction
3. Test the site configuration to ensure it's working properly

The site is now active and will be monitored for new RFPs. Thank you for contributing to government transparency! 🎉"""
        
        close_issue(issue_number, comment)
        processed_count += 1
    
    if processed_count > 0:
        # Save updated sites file
        save_sites_file(sites_data)
        print(f"\n✅ Successfully processed {processed_count} site additions")
        print(f"📁 Updated sites.json with {len(sites_data['sites'])} total sites")
    else:
        print("\nℹ️ No sites were added this run")

if __name__ == '__main__':
    main()
