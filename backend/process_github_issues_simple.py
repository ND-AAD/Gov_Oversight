#!/usr/bin/env python3
"""
Simplified GitHub Issue Processor for Site Additions

This is a lightweight standalone script that processes GitHub issues
and adds sites to sites.json without complex dependencies.

Used by GitHub Actions workflow for automated site processing.
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any


def parse_site_data_from_issue(issue_body: str) -> Optional[Dict[str, Any]]:
    """
    Parse site configuration data from GitHub issue body.
    
    Expected format:
    **Site Information:**
    - Name: Example Government Site
    - Base URL: https://example.gov
    - RFP Page URL: https://example.gov/rfps
    - Sample RFP URL: https://example.gov/rfp/123
    
    **Field Mappings:**
    - Status → "Active" (text)
    - Posted Date → "2024-12-20" (date)
    - Contract Value → "$50,000" (currency)
    """
    
    site_data = {}
    field_mappings = []
    
    lines = issue_body.split('\n')
    current_section = None
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Section headers
        if '**Site Information:**' in line:
            current_section = 'site_info'
            continue
        elif '**Field Mappings:**' in line:
            current_section = 'field_mappings'
            continue
        
        # Parse site information
        if current_section == 'site_info' and line.startswith('- '):
            # Handle both single-line and multi-line values
            match = re.match(r'- ([^:]+):\s*(.*)', line)
            if match:
                key, value = match.groups()
                original_key = key.strip()
                key = key.strip().lower().replace(' ', '_')
                value = value.strip()
                
                # If value is empty, it might be on the next line(s)
                if not value:
                    # Look ahead for the value on subsequent lines
                    for j in range(i + 1, len(lines)):
                        next_line = lines[j].strip()
                        # Stop if we hit another field or section
                        if next_line.startswith('- ') or next_line.startswith('**'):
                            break
                        # Add this line to the value
                        if next_line:
                            value = next_line
                            break
                
                print(f"DEBUG: Parsing site info - original_key='{original_key}', normalized_key='{key}', value='{value}'")
                
                if key == 'name':
                    site_data['name'] = value
                elif key in ['base_url', 'base url']:
                    site_data['base_url'] = value
                    print(f"DEBUG: Set base_url = '{value}'")
                elif key in ['rfp_page_url', 'rfp page url', 'main_rfp_page', 'main rfp page', 'main_rfp_page_url']:
                    site_data['main_rfp_page_url'] = value
                    print(f"DEBUG: Set main_rfp_page_url = '{value}'")
                elif key in ['sample_rfp_url', 'sample rfp url', 'sample_rfp_url']:
                    site_data['sample_rfp_url'] = value
                else:
                    print(f"DEBUG: Unrecognized field key: '{key}'")
        
        # Parse field mappings
        elif current_section == 'field_mappings' and line.startswith('- '):
            # Format: - Field Name → "Example Value" (data_type)
            match = re.match(r'- ([^→]+)→\s*"([^"]+)"\s*\(([^)]+)\)', line)
            if match:
                field_name, example_value, data_type = match.groups()
                field_name = field_name.strip()
                example_value = example_value.strip()
                data_type = data_type.strip()
                
                # Convert field name to alias
                alias = field_name.lower().replace(' ', '_')
                
                field_mapping = {
                    'alias': alias,
                    'selector': f'[data-field="{alias}"]',  # Placeholder selector
                    'data_type': data_type,
                    'training_value': example_value,
                    'confidence_score': 0.0,
                    'xpath': None,
                    'regex_pattern': None,
                    'fallback_selectors': [],
                    'last_validated': None,
                    'validation_errors': [],
                    'expected_format': None,
                    'status': 'untested',
                    'consecutive_failures': 0
                }
                
                field_mappings.append(field_mapping)
    
    # Generate site ID
    if 'name' in site_data:
        site_id = site_data['name'].lower().replace(' ', '_').replace('.', '_')
        site_id = re.sub(r'[^a-z0-9_]', '', site_id)
        site_data['id'] = site_id
    
    # Add field mappings and metadata
    site_data['field_mappings'] = field_mappings
    site_data['description'] = f"Added via GitHub issue on {datetime.now().strftime('%Y-%m-%d')}"
    
    # Debug output
    if site_data:
        print(f"DEBUG: Parsed site data: name='{site_data.get('name')}', base_url='{site_data.get('base_url')}', main_rfp_page_url='{site_data.get('main_rfp_page_url')}'")
        print(f"DEBUG: Found {len(field_mappings)} field mappings")
    
    return site_data if site_data else None


def validate_site_data(site_data: Dict[str, Any]) -> List[str]:
    """Basic validation of site data."""
    errors = []
    
    required_fields = ['id', 'name', 'base_url', 'main_rfp_page_url']
    for field in required_fields:
        if not site_data.get(field):
            errors.append(f"Missing required field: {field}")
    
    # Validate URLs
    for url_field in ['base_url', 'main_rfp_page_url', 'sample_rfp_url']:
        url = site_data.get(url_field)
        if url and not url.startswith(('http://', 'https://')):
            errors.append(f"Invalid URL format for {url_field}: {url}")
    
    return errors


def create_site_config_dict(site_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a complete site configuration dictionary."""
    
    return {
        'id': site_data['id'],
        'name': site_data['name'],
        'base_url': site_data['base_url'],
        'main_rfp_page_url': site_data['main_rfp_page_url'],
        'sample_rfp_url': site_data.get('sample_rfp_url', ''),
        'field_mappings': site_data.get('field_mappings', []),
        'status': 'testing',
        'last_scrape': None,
        'last_test': None,
        'rfp_count': 0,
        'test_results': None,
        'description': site_data.get('description', ''),
        'contact_info': None,
        'terms_of_service_url': None,
        'robots_txt_compliant': True,
        'scraper_settings': {
            'delay_between_requests': 2.0,
            'timeout': 30,
            'max_retries': 3,
            'respect_robots_txt': True
        }
    }


def load_sites_json(data_dir: str) -> Dict[str, Any]:
    """Load existing sites.json file."""
    sites_file = os.path.join(data_dir, 'sites.json')
    
    if not os.path.exists(sites_file):
        # Create empty sites file
        return {
            'metadata': {
                'last_updated': datetime.now().isoformat(),
                'total_sites': 0,
                'version': '1.0'
            },
            'sites': []
        }
    
    try:
        with open(sites_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error reading sites.json: {e}")
        # Return empty structure on error
        return {
            'metadata': {
                'last_updated': datetime.now().isoformat(),
                'total_sites': 0,
                'version': '1.0'
            },
            'sites': []
        }


def save_sites_json(data_dir: str, sites_data: Dict[str, Any]) -> None:
    """Save sites data to sites.json file."""
    sites_file = os.path.join(data_dir, 'sites.json')
    
    # Update metadata
    sites_data['metadata']['last_updated'] = datetime.now().isoformat()
    sites_data['metadata']['total_sites'] = len(sites_data['sites'])
    
    try:
        with open(sites_file, 'w', encoding='utf-8') as f:
            json.dump(sites_data, f, indent=2, ensure_ascii=False)
    except IOError as e:
        raise Exception(f"Failed to save sites.json: {e}")


def process_issue_for_site_addition(issue_number: int, issue_body: str, 
                                  data_dir: str = None) -> Dict[str, Any]:
    """
    Process a single GitHub issue for site addition.
    
    Returns:
        Dict with 'success' boolean and 'message' string
    """
    
    try:
        # Determine data directory
        if data_dir is None:
            script_dir = Path(__file__).parent
            data_dir = str(script_dir.parent / 'data')
        
        # Parse site data from issue
        site_data = parse_site_data_from_issue(issue_body)
        
        if not site_data:
            return {
                'success': False,
                'message': 'Could not parse site data from issue body'
            }
        
        # Validate site data
        validation_errors = validate_site_data(site_data)
        
        if validation_errors:
            return {
                'success': False,
                'message': f'Site validation failed: {"; ".join(validation_errors)}'
            }
        
        # Load existing sites
        sites_data = load_sites_json(data_dir)
        
        # Check for duplicate IDs
        existing_ids = [site['id'] for site in sites_data['sites']]
        if site_data['id'] in existing_ids:
            return {
                'success': False,
                'message': f'Site with ID "{site_data["id"]}" already exists'
            }
        
        # Create complete site configuration
        site_config = create_site_config_dict(site_data)
        
        # Add new site
        sites_data['sites'].append(site_config)
        
        # Save updated sites
        save_sites_json(data_dir, sites_data)
        
        return {
            'success': True,
            'message': f'Successfully added site: {site_config["name"]} ({site_config["id"]})'
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f'Error processing site addition: {str(e)}'
        }


def main():
    """
    Main entry point for GitHub Actions.
    
    Expects environment variables:
    - GITHUB_ISSUE_NUMBER: Issue number to process
    - GITHUB_ISSUE_BODY: Issue body content
    """
    
    issue_number = os.getenv('GITHUB_ISSUE_NUMBER')
    issue_body = os.getenv('GITHUB_ISSUE_BODY')
    
    if not issue_number or not issue_body:
        print("ERROR: Missing required environment variables GITHUB_ISSUE_NUMBER or GITHUB_ISSUE_BODY")
        sys.exit(1)
    
    try:
        issue_number = int(issue_number)
    except ValueError:
        print(f"ERROR: Invalid issue number: {issue_number}")
        sys.exit(1)
    
    print(f"Processing GitHub issue #{issue_number} for site addition...")
    print(f"Issue body length: {len(issue_body)} characters")
    print("DEBUG: Issue body content:")
    print("=" * 50)
    print(issue_body)
    print("=" * 50)
    
    # Process the issue
    result = process_issue_for_site_addition(issue_number, issue_body)
    
    if result['success']:
        print(f"SUCCESS: {result['message']}")
        sys.exit(0)
    else:
        print(f"FAILED: {result['message']}")
        sys.exit(1)


if __name__ == '__main__':
    main()