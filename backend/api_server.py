"""
Simple HTTP API server for LA 2028 RFP Monitor frontend integration.

This server provides endpoints for development and testing. In production,
the frontend reads directly from JSON files for GitHub Pages compatibility.
"""

import json
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import sys
sys.path.insert(0, str(Path(__file__).parent))

from models import DataManager, SiteConfig, RFP, FieldMapping, DataType, FieldMappingStatus
from models.validation import validate_site_config_data, validate_olympic_relevance
from scrapers import LocationBinder, RFPScraper

logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="LA 2028 RFP Monitor API",
    description="Backend API for government procurement oversight tool",
    version="1.0.0"
)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
data_manager = DataManager("../data")
location_binder = LocationBinder()
rfp_scraper = RFPScraper(data_manager)


# Pydantic models for API requests
class SiteConfigRequest(BaseModel):
    name: str
    base_url: str
    main_rfp_page_url: str
    sample_rfp_url: str
    description: str = ""
    field_mappings: List[Dict[str, Any]] = []


class FieldMappingRequest(BaseModel):
    alias: str
    sample_value: str
    data_type: str


class SiteTestRequest(BaseModel):
    site_config: SiteConfigRequest
    test_url: Optional[str] = None


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


# RFP endpoints
@app.get("/api/rfps")
async def get_rfps():
    """Get all RFPs."""
    try:
        rfps = data_manager.load_rfps()
        return {
            "success": True,
            "data": [rfp.to_dict() for rfp in rfps],
            "count": len(rfps)
        }
    except Exception as e:
        logger.error(f"Error loading RFPs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/rfps/{rfp_id}")
async def get_rfp(rfp_id: str):
    """Get specific RFP by ID."""
    try:
        rfp = data_manager.get_rfp_by_id(rfp_id)
        if not rfp:
            raise HTTPException(status_code=404, detail="RFP not found")
        
        return {
            "success": True,
            "data": rfp.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading RFP {rfp_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/rfps/{rfp_id}")
async def delete_rfp(rfp_id: str):
    """Delete/ignore an RFP."""
    try:
        success = data_manager.ignore_rfp(rfp_id)
        if not success:
            raise HTTPException(status_code=404, detail="RFP not found")
        
        return {
            "success": True,
            "message": f"RFP {rfp_id} ignored successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ignoring RFP {rfp_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Site configuration endpoints
@app.get("/api/sites")
async def get_sites():
    """Get all site configurations."""
    try:
        sites = data_manager.load_site_configs()
        return {
            "success": True,
            "data": [site.to_dict() for site in sites],
            "count": len(sites)
        }
    except Exception as e:
        logger.error(f"Error loading sites: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sites")
async def create_site(site_request: SiteConfigRequest):
    """Create new site configuration."""
    try:
        # Generate site ID
        site_id = site_request.name.lower().replace(' ', '_').replace('.', '_')
        
        # Create basic site config
        site_config = SiteConfig(
            id=site_id,
            name=site_request.name,
            base_url=site_request.base_url,
            main_rfp_page_url=site_request.main_rfp_page_url,
            sample_rfp_url=site_request.sample_rfp_url,
            field_mappings=[],
            description=site_request.description
        )
        
        # Validate
        validation_result = validate_site_config_data(site_config.to_dict())
        if not validation_result.is_valid:
            raise HTTPException(
                status_code=400, 
                detail={
                    "message": "Site configuration validation failed",
                    "errors": validation_result.errors
                }
            )
        
        # Check for duplicates
        existing_sites = data_manager.load_site_configs()
        if any(s.id == site_id for s in existing_sites):
            raise HTTPException(
                status_code=409, 
                detail=f"Site with ID '{site_id}' already exists"
            )
        
        # Add and save
        existing_sites.append(site_config)
        data_manager.save_site_configs(existing_sites)
        
        return {
            "success": True,
            "data": site_config.to_dict(),
            "message": f"Site '{site_request.name}' created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating site: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sites/{site_id}/field-mappings")
async def create_field_mappings(site_id: str, field_requests: List[FieldMappingRequest]):
    """Create field mappings for a site using location-binding."""
    try:
        # Load site
        sites = data_manager.load_site_configs()
        site_config = next((s for s in sites if s.id == site_id), None)
        
        if not site_config:
            raise HTTPException(status_code=404, detail="Site not found")
        
        # Create field mappings using location-binding
        field_specs = []
        for field_req in field_requests:
            field_specs.append({
                "alias": field_req.alias,
                "sample_value": field_req.sample_value,
                "data_type": field_req.data_type,
                "description": f"Field mapping for {field_req.alias}"
            })
        
        # Use location binder to create field mappings
        updated_site_config = location_binder.create_site_configuration(
            site_config.sample_rfp_url,
            field_specs,
            {
                "id": site_config.id,
                "name": site_config.name,
                "base_url": site_config.base_url,
                "main_rfp_page_url": site_config.main_rfp_page_url,
                "description": site_config.description
            }
        )
        
        # Update in storage
        for i, site in enumerate(sites):
            if site.id == site_id:
                sites[i] = updated_site_config
                break
        
        data_manager.save_site_configs(sites)
        
        return {
            "success": True,
            "data": updated_site_config.to_dict(),
            "message": f"Created {len(field_specs)} field mappings for {site_config.name}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating field mappings for {site_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sites/{site_id}/test")
async def test_site(site_id: str, background_tasks: BackgroundTasks):
    """Test site configuration."""
    try:
        # Load site
        sites = data_manager.load_site_configs()
        site_config = next((s for s in sites if s.id == site_id), None)
        
        if not site_config:
            raise HTTPException(status_code=404, detail="Site not found")
        
        # Test configuration
        validation_result = await rfp_scraper.test_site_configuration(site_config)
        
        return {
            "success": validation_result.is_valid,
            "data": {
                "site_id": site_id,
                "site_name": site_config.name,
                "is_valid": validation_result.is_valid,
                "errors": validation_result.errors,
                "warnings": validation_result.warnings,
                "tested_at": datetime.now().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing site {site_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/sites/{site_id}")
async def delete_site(site_id: str):
    """Delete site configuration."""
    try:
        sites = data_manager.load_site_configs()
        original_count = len(sites)
        
        sites = [s for s in sites if s.id != site_id]
        
        if len(sites) == original_count:
            raise HTTPException(status_code=404, detail="Site not found")
        
        data_manager.save_site_configs(sites)
        
        return {
            "success": True,
            "message": f"Site {site_id} deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting site {site_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Scraping endpoints
@app.post("/api/scrape")
async def run_scraping(background_tasks: BackgroundTasks, force_full_scan: bool = False):
    """Trigger scraping process."""
    try:
        # Run scraping in background
        background_tasks.add_task(run_scraping_task, force_full_scan)
        
        return {
            "success": True,
            "message": "Scraping process started",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error starting scraping: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def run_scraping_task(force_full_scan: bool = False):
    """Background task for scraping."""
    try:
        logger.info("Starting background scraping task")
        results = await rfp_scraper.scrape_all_sites(force_full_scan)
        logger.info(f"Scraping completed: {results}")
    except Exception as e:
        logger.error(f"Background scraping failed: {e}")


# Statistics endpoints
@app.get("/api/stats")
async def get_stats():
    """Get system statistics."""
    try:
        stats = data_manager.get_data_statistics()
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Olympic relevance checking
@app.post("/api/check-relevance")
async def check_olympic_relevance(text: str):
    """Check if text is Olympic-related."""
    try:
        is_relevant, keywords, score = validate_olympic_relevance(text)
        
        return {
            "success": True,
            "data": {
                "is_relevant": is_relevant,
                "keywords": keywords,
                "score": score,
                "text_length": len(text)
            }
        }
    except Exception as e:
        logger.error(f"Error checking Olympic relevance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🚀 Starting LA 2028 RFP Monitor API Server")
    print("📊 Dashboard will be available at: http://localhost:3000")
    print("🔧 API documentation at: http://localhost:8000/docs")
    print("📋 Health check at: http://localhost:8000/health")
    
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
