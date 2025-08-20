#!/usr/bin/env python3
"""Script to count RFPs in the data file for GitHub Actions."""

import json
import sys
from pathlib import Path

def count_rfps():
    """Count the number of RFPs in the data file."""
    try:
        data_file = Path('../data/rfps.json')
        if not data_file.exists():
            print("0")
            return
            
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            count = len(data)
        elif isinstance(data, dict) and 'rfps' in data:
            count = len(data['rfps'])
        else:
            count = 0
            
        print(count)
        
    except Exception as e:
        print("0")
        sys.stderr.write(f"Error counting RFPs: {e}\n")

if __name__ == "__main__":
    count_rfps()
