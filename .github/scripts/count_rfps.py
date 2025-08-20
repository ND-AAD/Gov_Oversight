#!/usr/bin/env python3
"""
Count RFPs in the data file.

Simple script to count total RFPs for GitHub Actions workflow reporting.
"""

import json
import os
import sys

def count_rfps():
    """Count RFPs in the current data file."""
    rfps_file = 'data/rfps.json'
    
    if not os.path.exists(rfps_file):
        return 0
    
    try:
        with open(rfps_file, 'r') as f:
            data = json.load(f)
        
        # Handle different data formats
        if isinstance(data, list):
            return len(data)
        elif isinstance(data, dict) and 'rfps' in data:
            return len(data['rfps'])
        else:
            return 0
            
    except Exception as e:
        print(f"Error reading RFPs file: {e}", file=sys.stderr)
        return 0

if __name__ == '__main__':
    count = count_rfps()
    print(count)