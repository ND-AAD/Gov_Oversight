#!/usr/bin/env python3
"""Script to generate RFP statistics for GitHub Actions."""

import json
import sys
from datetime import datetime
from pathlib import Path

def generate_stats():
    """Generate statistics from RFP data."""
    try:
        data_file = Path('data/rfps.json')
        if not data_file.exists():
            create_empty_stats()
            return
            
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle both list format and structured format
        if isinstance(data, list):
            rfps = data
        elif isinstance(data, dict) and 'rfps' in data:
            rfps = data['rfps']
        else:
            rfps = []
        
        stats = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'total_rfps': len(rfps),
            'active_rfps': len([r for r in rfps if r.get('extracted_fields', {}).get('status', '').lower() == 'active']),
            'olympic_related': len([r for r in rfps if 'olympic' in r.get('categories', [])]),
            'surveillance_flagged': len([r for r in rfps if any(cat in ['surveillance', 'security', 'monitoring'] for cat in r.get('categories', []))]),
            'last_updated': datetime.utcnow().isoformat() + 'Z'
        }
        
        with open('data/stats.json', 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)
        
        print(f"📊 Updated statistics: {stats['total_rfps']} total RFPs, {stats['olympic_related']} Olympic-related")
        
    except Exception as e:
        print(f"Warning: Could not generate stats: {e}")
        create_empty_stats()

def create_empty_stats():
    """Create empty stats file on error."""
    try:
        empty_stats = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'total_rfps': 0,
            'active_rfps': 0,
            'olympic_related': 0,
            'surveillance_flagged': 0,
            'last_updated': datetime.utcnow().isoformat() + 'Z',
            'error': 'No data available'
        }
        
        with open('data/stats.json', 'w', encoding='utf-8') as f:
            json.dump(empty_stats, f, indent=2)
            
    except Exception as e:
        sys.stderr.write(f"Failed to create empty stats: {e}\n")

if __name__ == "__main__":
    generate_stats()
