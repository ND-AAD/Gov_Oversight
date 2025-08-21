#!/usr/bin/env python3
"""
GitHub Issue Processor for Site Additions

This script processes GitHub issues with 'site-addition' label,
extracts site configuration data, and adds them to sites.json.

Used by GitHub Actions workflow for automated site processing.
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add the backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from models.site_config import SiteConfig, FieldMapping, DataType, FieldMappingStatus
from models.serialization import DataManager
from models.validation import validate_site_config_data


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
    
    for line in lines:
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
            match = re.match(r'- ([^:]+):\s*(.+)', line)
            if match:
                key, value = match.groups()
                key = key.strip().lower().replace(' ', '_')
                value = value.strip()
                
                if key == 'name':
                    site_data['name'] = value
                elif key == 'base_url':
                    site_data['base_url'] = value
                elif key == 'rfp_page_url':
                    site_data['main_rfp_page_url'] = value
                elif key == 'sample_rfp_url':
                    site_data['sample_rfp_url'] = value
        
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
                
                # Map data type
                try:
                    dt = DataType(data_type)
                except ValueError:
                    dt = DataType.TEXT  # Default fallback
                
                field_mapping = {
                    'alias': alias,
                    'selector': f'[data-field="{alias}"]',  # Placeholder selector
                    'data_type': dt.value,
                    'training_value': example_value,
                    'confidence_score': 0.0,  # Will be set during validation
                    'status': FieldMappingStatus.UNTESTED.value,
                    'consecutive_failures': 0
                }
                
                field_mappings.append(field_mapping)
    
    # Generate site ID
    if 'name' in site_data:
        site_id = site_data['name'].lower().replace(' ', '_').replace('.', '_')
        site_id = re.sub(r'[^a-z0-9_]', '', site_id)
        site_data['id'] = site_id
    
    # Add field mappings
    site_data['field_mappings'] = field_mappings
    site_data['description'] = f"Added via GitHub issue on {datetime.now().strftime('%Y-%m-%d')}"
    
    return site_data if site_data else None


def create_site_config_from_data(site_data: Dict[str, Any]) -> SiteConfig:
    """Create SiteConfig object from parsed data."""
    
    # Create field mappings
    field_mappings = []
    for fm_data in site_data.get('field_mappings', []):
        field_mapping = FieldMapping(
            alias=fm_data['alias'],
            selector=fm_data['selector'],
            data_type=DataType(fm_data['data_type']),
            training_value=fm_data['training_value'],
            confidence_score=fm_data.get('confidence_score', 0.0),
            status=FieldMappingStatus(fm_data.get('status', 'untested')),
            consecutive_failures=fm_data.get('consecutive_failures', 0)
        )
        field_mappings.append(field_mapping)
    
    # Create site config
    site_config = SiteConfig(
        id=site_data['id'],
        name=site_data['name'],
        base_url=site_data['base_url'],
        main_rfp_page_url=site_data['main_rfp_page_url'],
        sample_rfp_url=site_data.get('sample_rfp_url', ''),
        field_mappings=field_mappings,
        description=site_data.get('description', '')
    )
    
    return site_config


def process_issue_for_site_addition(issue_number: int, issue_body: str, 
                                  data_dir: str = None) -> Dict[str, Any]:
    """
    Process a single GitHub issue for site addition.
    
    Returns:
        Dict with 'success' boolean and 'message' string
    """
    
    try:
        # Parse site data from issue
        site_data = parse_site_data_from_issue(issue_body)
        
        if not site_data:
            return {
                'success': False,
                'message': 'Could not parse site data from issue body'
            }
        
        # Validate required fields
        required_fields = ['name', 'base_url', 'main_rfp_page_url']
        missing_fields = [f for f in required_fields if f not in site_data]
        
        if missing_fields:
            return {
                'success': False,
                'message': f'Missing required fields: {", ".join(missing_fields)}'
            }
        
        # Create site config
        site_config = create_site_config_from_data(site_data)
        
        # Validate site configuration
        validation_result = validate_site_config_data(site_config.to_dict())
        
        if not validation_result.is_valid:
            return {
                'success': False,
                'message': f'Site configuration validation failed: {"; ".join(validation_result.errors)}'
            }
        
        # Load existing sites
        if data_dir is None:
            # Determine the correct data directory
            script_dir = Path(__file__).parent
            data_dir = script_dir.parent / 'data'
        
        data_manager = DataManager(str(data_dir))
        
        try:
            existing_sites = data_manager.load_site_configs()
        except Exception:
            # Handle case where sites.json doesn't exist or is malformed
            existing_sites = []
        
        # Check for duplicate IDs
        if any(s.id == site_config.id for s in existing_sites):
            return {
                'success': False,
                'message': f'Site with ID "{site_config.id}" already exists'
            }
        
        # Add new site
        existing_sites.append(site_config)
        
        # Save updated sites
        data_manager.save_site_configs(existing_sites)
        
        return {
            'success': True,
            'message': f'Successfully added site: {site_config.name} ({site_config.id})'
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
    
    # Process the issue
    result = process_issue_for_site_addition(issue_number, issue_body)
    
    if result['success']:
        print(f"SUCCESS: {result['message']}")
        
        # Output result for GitHub Actions
        if os.getenv('GITHUB_OUTPUT'):
            with open(os.getenv('GITHUB_OUTPUT'), 'a') as f:
                f.write(f"success=true\n")
                f.write(f"message={result['message']}\n")
        
        sys.exit(0)
    else:
        print(f"FAILED: {result['message']}")
        
        # Output result for GitHub Actions
        if os.getenv('GITHUB_OUTPUT'):
            with open(os.getenv('GITHUB_OUTPUT'), 'a') as f:
                f.write(f"success=false\n")
                f.write(f"message={result['message']}\n")
        
        sys.exit(1)


if __name__ == '__main__':
    main()