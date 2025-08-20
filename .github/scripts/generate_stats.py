#!/usr/bin/env python3
"""
Generate statistics file for the RFP monitoring system.

Creates stats.json with summary information about RFPs and sites.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any

def load_rfps() -> List[Dict]:
    """Load RFPs from data file."""
    rfps_file = 'data/rfps.json'
    
    if not os.path.exists(rfps_file):
        return []
    
    try:
        with open(rfps_file, 'r') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and 'rfps' in data:
            return data['rfps']
        else:
            return []
            
    except Exception as e:
        print(f"Error reading RFPs file: {e}")
        return []

def load_sites() -> List[Dict]:
    """Load sites from data file."""
    sites_file = 'data/sites.json'
    
    if not os.path.exists(sites_file):
        return []
    
    try:
        with open(sites_file, 'r') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and 'sites' in data:
            return data['sites']
        else:
            return []
            
    except Exception as e:
        print(f"Error reading sites file: {e}")
        return []

def categorize_rfp(rfp: Dict) -> List[str]:
    """Categorize an RFP based on its content."""
    categories = []
    
    # Get text to analyze
    title = rfp.get('title', '').lower()
    description = rfp.get('description', '').lower()
    text = f"{title} {description}"
    
    # Olympic-related keywords
    olympic_keywords = ['olympic', '2028', 'la28', 'olympic games', 'olympics']
    if any(keyword in text for keyword in olympic_keywords):
        categories.append('Olympics 2028')
    
    # Surveillance keywords
    surveillance_keywords = [
        'surveillance', 'monitoring', 'camera', 'cctv', 'facial recognition',
        'biometric', 'security system', 'tracking', 'intelligence',
        'predictive policing', 'data collection', 'privacy'
    ]
    if any(keyword in text for keyword in surveillance_keywords):
        categories.append('Surveillance')
    
    # Security keywords
    security_keywords = [
        'security', 'police', 'enforcement', 'patrol', 'guard',
        'access control', 'perimeter', 'screening', 'detection'
    ]
    if any(keyword in text for keyword in security_keywords):
        categories.append('Security')
    
    # Technology keywords
    tech_keywords = [
        'software', 'hardware', 'system', 'technology', 'digital',
        'database', 'platform', 'application', 'network', 'cloud'
    ]
    if any(keyword in text for keyword in tech_keywords):
        categories.append('Technology')
    
    # Construction keywords
    construction_keywords = [
        'construction', 'building', 'infrastructure', 'venue',
        'facility', 'renovation', 'installation', 'equipment'
    ]
    if any(keyword in text for keyword in construction_keywords):
        categories.append('Construction')
    
    return categories

def is_high_priority(rfp: Dict) -> bool:
    """Determine if an RFP is high priority (surveillance/security related)."""
    categories = rfp.get('categories', [])
    if isinstance(categories, str):
        categories = [categories]
    
    high_priority_categories = ['Surveillance', 'Security']
    return any(cat in categories for cat in high_priority_categories)

def is_closing_soon(rfp: Dict, days: int = 7) -> bool:
    """Check if RFP is closing within specified days."""
    closing_date = rfp.get('closing_date')
    if not closing_date:
        return False
    
    try:
        # Handle different date formats
        if 'T' in closing_date:
            closing_dt = datetime.fromisoformat(closing_date.replace('Z', '+00:00'))
        else:
            closing_dt = datetime.strptime(closing_date, '%Y-%m-%d')
        
        return (closing_dt - datetime.now()).days <= days
    except:
        return False

def calculate_contract_value(rfp: Dict) -> float:
    """Extract and calculate contract value."""
    extracted_fields = rfp.get('extracted_fields', {})
    value = extracted_fields.get('contract_value', 0)
    
    if isinstance(value, str):
        # Remove currency symbols and commas
        clean_value = value.replace('$', '').replace(',', '').replace(' ', '')
        try:
            return float(clean_value)
        except:
            return 0.0
    elif isinstance(value, (int, float)):
        return float(value)
    else:
        return 0.0

def generate_stats() -> Dict[str, Any]:
    """Generate comprehensive statistics."""
    rfps = load_rfps()
    sites = load_sites()
    
    # Basic counts
    total_rfps = len(rfps)
    total_sites = len(sites)
    
    # RFP categorization
    olympic_rfps = []
    surveillance_rfps = []
    high_priority_rfps = []
    closing_soon_rfps = []
    high_value_rfps = []
    
    total_value = 0.0
    surveillance_value = 0.0
    
    for rfp in rfps:
        # Ensure categories are set
        if 'categories' not in rfp or not rfp['categories']:
            rfp['categories'] = categorize_rfp(rfp)
        
        categories = rfp.get('categories', [])
        if isinstance(categories, str):
            categories = [categories]
        
        # Count by category
        if 'Olympics 2028' in categories:
            olympic_rfps.append(rfp)
        
        if 'Surveillance' in categories:
            surveillance_rfps.append(rfp)
        
        if is_high_priority(rfp):
            high_priority_rfps.append(rfp)
        
        if is_closing_soon(rfp):
            closing_soon_rfps.append(rfp)
        
        # Value calculations
        value = calculate_contract_value(rfp)
        total_value += value
        
        if value >= 1000000:  # $1M+
            high_value_rfps.append(rfp)
        
        if 'Surveillance' in categories:
            surveillance_value += value
    
    # Site statistics
    active_sites = [s for s in sites if s.get('status') == 'active']
    error_sites = [s for s in sites if s.get('status') == 'error']
    
    # Generate statistics
    stats = {
        "timestamp": datetime.now().isoformat() + "Z",
        "last_updated": datetime.now().isoformat() + "Z",
        
        # RFP statistics
        "rfps": {
            "total": total_rfps,
            "olympic_related": len(olympic_rfps),
            "surveillance": len(surveillance_rfps),
            "high_priority": len(high_priority_rfps),
            "closing_soon": len(closing_soon_rfps),
            "high_value": len(high_value_rfps)
        },
        
        # Site statistics
        "sites": {
            "total": total_sites,
            "active": len(active_sites),
            "errors": len(error_sites)
        },
        
        # Financial statistics
        "financials": {
            "total_contract_value": total_value,
            "surveillance_contract_value": surveillance_value,
            "average_contract_value": total_value / max(total_rfps, 1)
        },
        
        # Category breakdown
        "categories": {
            "Olympics 2028": len(olympic_rfps),
            "Surveillance": len(surveillance_rfps),
            "Security": len([r for r in rfps if 'Security' in r.get('categories', [])]),
            "Technology": len([r for r in rfps if 'Technology' in r.get('categories', [])]),
            "Construction": len([r for r in rfps if 'Construction' in r.get('categories', [])])
        },
        
        # Recent activity (last 7 days)
        "recent_activity": {
            "new_rfps_last_week": len([
                r for r in rfps 
                if (datetime.now() - datetime.fromisoformat(r.get('detected_at', '2024-01-01T00:00:00Z').replace('Z', '+00:00')).replace(tzinfo=None)).days <= 7
            ]),
            "sites_with_recent_activity": len([
                s for s in sites 
                if s.get('last_scrape') and (datetime.now() - datetime.fromisoformat(s['last_scrape'].replace('Z', '+00:00')).replace(tzinfo=None)).days <= 7
            ])
        }
    }
    
    return stats

def main():
    """Generate and save statistics."""
    print("📊 Generating RFP monitoring statistics...")
    
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    
    # Generate statistics
    stats = generate_stats()
    
    # Save statistics file
    with open('data/stats.json', 'w') as f:
        json.dump(stats, f, indent=2)
    
    print(f"✅ Statistics generated:")
    print(f"   Total RFPs: {stats['rfps']['total']}")
    print(f"   Olympic-related: {stats['rfps']['olympic_related']}")
    print(f"   Surveillance: {stats['rfps']['surveillance']}")
    print(f"   Total Sites: {stats['sites']['total']}")
    print(f"   Active Sites: {stats['sites']['active']}")

if __name__ == '__main__':
    main()