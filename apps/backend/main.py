from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import subprocess
import json
import os
import sys
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv not installed. Install with: pip install python-dotenv")
    print("   Or set environment variables manually.")

# Import scraper functions directly from current directory
from main_loop import run_scraper_main, is_scraper_running, add_to_queue

# Load API key from environment variable
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    print("⚠️  Warning: API_KEY environment variable not set")
    print("📝 Please set API_KEY in your backend .env file")
    API_KEY = "default_key_for_development"  # Fallback for development

async def verify_api_key(x_api_key: str = Header(None)):
    """Verify the API key from request header"""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_api_key


app = FastAPI(title="Amazon Automation API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    # allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Frontend URLs
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class Product(BaseModel):
    productname: str
    url: str
    keyword: str
    categoryUrl: str

class Country(BaseModel):
    name: str
    products: List[Product]

class Brand(BaseModel):
    brand: str
    countries: List[Country]

class SubmissionRequest(BaseModel):
    brands: List[Brand]

class SubmissionResponse(BaseModel):
    ok: bool
    message: str
    payload: dict

VALID_COUNTRIES = ["US", "UK", "CAN", "AUS", "DE", "UAE"]

def normalize_country(country_name: str) -> str:
    """Normalize country name to standard format"""
    country = country_name.strip().upper()
    if country == "AU":
        return "AUS"
    return country

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"ok": True}

@app.get("/api/scraper-status")
async def get_scraper_status(api_key: str = Depends(verify_api_key)):
    """Get current scraper status"""
    from main_loop import get_queue
    queue_items = get_queue()
    return {
        "running": is_scraper_running(),
        "queue_size": len(queue_items)
    }

@app.post("/api/submissions", response_model=SubmissionResponse)
async def create_submission(request: SubmissionRequest, api_key: str = Depends(verify_api_key)):
    """Create a new submission and start the scraper"""
    try:
        # Validate input
        if not request.brands:
            raise HTTPException(status_code=400, detail="No brands provided")

        # Prepare payload for scraper
        scraper_payload = {
            "brands": []
        }

        for brand in request.brands:
            # Filter valid countries
            valid_countries = []
            for country in brand.countries:
                normalized_country = normalize_country(country.name)
                if normalized_country in VALID_COUNTRIES:
                    valid_countries.append({
                        "name": normalized_country,
                        "products": [
                            {
                                "productname": product.productname,
                                "url": product.url,
                                "keyword": product.keyword,
                                "categoryUrl": product.categoryUrl
                            }
                            for product in country.products
                        ]
                    })

            if valid_countries:
                scraper_payload["brands"].append({
                    "brand": brand.brand,
                    "countries": valid_countries
                })

        if not scraper_payload["brands"]:
            raise HTTPException(status_code=400, detail="No valid countries found")

        print("Prepared scraper payload:", json.dumps(scraper_payload, indent=2))

        # Check if scraper is already running
        if is_scraper_running():
            print("Scraper is currently running, adding to queue")
            
            # Add to queue
            if add_to_queue(scraper_payload):
                return SubmissionResponse(
                    ok=True,
                    message="Data submitted to queue, will start processing once scraper is free",
                    payload=scraper_payload
                )
            else:
                raise HTTPException(status_code=500, detail="Failed to add to queue")
        else:
            # Start scraper in background
            import threading
            
            def run_scraper_background():
                try:
                    print("Starting scraper in background...")
                    result = run_scraper_main(scraper_payload)
                    print("Scraper completed:", result)
                except Exception as e:
                    print(f"Scraper error: {e}")

            # Start scraper in background thread
            scraper_thread = threading.Thread(target=run_scraper_background)
            scraper_thread.daemon = True
            scraper_thread.start()

            print("Scraper started successfully in background")
            
            return SubmissionResponse(
                ok=True,
                message="Scraper started successfully in the background",
                payload=scraper_payload
            )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Submission processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Submission processing failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4000, access_log=True)