from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import subprocess
import json
import os
import sys
from pathlib import Path

# Import scraper functions directly from current directory
from main_loop import run_scraper_main

app = FastAPI(title="Amazon Automation API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Frontend URLs
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

@app.post("/api/submissions", response_model=SubmissionResponse)
async def create_submission(request: SubmissionRequest):
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
    uvicorn.run(app, host="0.0.0.0", port=4000)
