#!/usr/bin/env python3
"""
Simple script to run the scraper from Node.js backend
"""

import sys
import json
import os

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main_loop import run_scraper_main

def main():
    try:
        # Read payload from stdin
        print("-----starting scraper-----")
        payload_json = sys.stdin.read()
        if not payload_json.strip():
            print(json.dumps({
                "success": False,
                "error": "No payload received",
                "message": "No payload provided"
            }))
            return
            
        payload = json.loads(payload_json)
        
        # Run the scraper
        result = run_scraper_main(payload)
        
        # Output result as JSON
        print(json.dumps(result))
        
    except json.JSONDecodeError as e:
        print(json.dumps({
            "success": False,
            "error": f"Invalid JSON payload: {e}",
            "message": "Invalid payload format"
        }))
    except Exception as e:
        print(json.dumps({
            "success": False,
            "error": str(e),
            "message": "Unexpected error occurred"
        }))

if __name__ == "__main__":
    main()
