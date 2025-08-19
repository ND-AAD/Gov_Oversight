"""
Main RFP scraper that orchestrates the location-binding engine and base scraper.

This module brings together the location-binding technology with practical
RFP extraction workflows.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from .location_binder import LocationBinder
from .base_scraper import BaseScraper
from models import (
    SiteConfig, RFP, FieldMappingStatus, ValidationResult,
    ScrapingError, LocationBindingError, DataManager
)

logger = logging.getLogger(__name__)


class RFPScraper:
    """
    Main RFP scraper that combines location-binding with robust web scraping.
    
    This class orchestrates the entire scraping process from site configuration
    testing to RFP data extraction and storage.
    """
    
    def __init__(self, data_manager: Optional[DataManager] = None):
        """
        Initialize RFP scraper.
        
        Args:
            data_manager: Optional DataManager instance for data persistence
        """
        self.location_binder = LocationBinder()
        self.base_scraper = BaseScraper()
        self.data_manager = data_manager or DataManager()
        
        # Scraping statistics
        self.stats = {
            "sites_scraped": 0,
            "rfps_found": 0,
            "rfps_updated": 0,
            "errors": 0,
            "last_run": None
        }
    
    async def scrape_all_sites(self, force_full_scan: bool = False) -> Dict[str, Any]:
        """
        Scrape all configured sites for new RFPs.
        
        Args:
            force_full_scan: If True, scrape all RFPs regardless of last update
            
        Returns:
            Dictionary with scraping results and statistics
        """
        logger.info("Starting full site scraping process")
        start_time = datetime.now()
        
        # Reset stats
        self.stats = {
            "sites_scraped": 0,
            "rfps_found": 0,
            "rfps_updated": 0,
            "errors": 0,
            "last_run": start_time
        }
        
        results = {
            "success": True,
            "sites_processed": 0,
            "sites_failed": 0,
            "new_rfps": [],
            "updated_rfps": [],
            "errors": []
        }
        
        try:
            # Initialize browser
            await self.base_scraper.initialize_browser()
            
            # Load site configurations
            site_configs = self.data_manager.load_site_configs()
            
            if not site_configs:
                logger.warning("No site configurations found")
                return results
            
            # Process each site
            for site_config in site_configs:
                try:
                    logger.info(f"Processing site: {site_config.name}")
                    
                    site_result = await self.scrape_site(site_config, force_full_scan)
                    
                    if site_result["success"]:
                        results["sites_processed"] += 1
                        results["new_rfps"].extend(site_result.get("new_rfps", []))
                        results["updated_rfps"].extend(site_result.get("updated_rfps", []))
                    else:
                        results["sites_failed"] += 1
                        results["errors"].extend(site_result.get("errors", []))
                    
                    self.stats["sites_scraped"] += 1
                    
                except Exception as e:
                    logger.error(f"Error processing site {site_config.name}: {e}")
                    results["sites_failed"] += 1
                    results["errors"].append({
                        "site": site_config.name,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    })
                    self.stats["errors"] += 1
            
            # Update statistics
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"Scraping completed in {duration:.2f}s. "
                       f"Sites: {results['sites_processed']} success, {results['sites_failed']} failed")
            
        except Exception as e:
            logger.error(f"Critical error during scraping: {e}")
            results["success"] = False
            results["errors"].append({
                "type": "critical",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
        
        finally:
            # Clean up browser
            await self.base_scraper.close_browser()
        
        return results
    
    async def scrape_site(self, site_config: SiteConfig, 
                         force_full_scan: bool = False) -> Dict[str, Any]:
        """
        Scrape a single site for RFPs.
        
        Args:
            site_config: Site configuration to use for scraping
            force_full_scan: If True, scrape all RFPs regardless of last update
            
        Returns:
            Dictionary with site scraping results
        """
        logger.info(f"Scraping site: {site_config.name}")
        
        result = {
            "success": False,
            "site_id": site_config.id,
            "site_name": site_config.name,
            "new_rfps": [],
            "updated_rfps": [],
            "errors": [],
            "field_mapping_issues": []
        }
        
        try:
            # Check site health first
            if not site_config.is_healthy() and not force_full_scan:
                logger.warning(f"Site {site_config.name} is not healthy, skipping")
                result["errors"].append("Site configuration is not healthy")
                return result
            
            # Test field mappings if they haven't been tested recently
            if self._should_test_field_mappings(site_config):
                await self.test_site_configuration(site_config)
            
            # Get list of RFP URLs to process
            rfp_urls = await self._discover_rfp_urls(site_config)
            
            logger.info(f"Found {len(rfp_urls)} RFP URLs to process")
            
            # Process each RFP
            for rfp_url in rfp_urls:
                try:
                    rfp_result = await self._process_rfp_url(site_config, rfp_url)
                    
                    if rfp_result["is_new"]:
                        result["new_rfps"].append(rfp_result["rfp"])
                    elif rfp_result["is_updated"]:
                        result["updated_rfps"].append(rfp_result["rfp"])
                    
                except Exception as e:
                    logger.error(f"Error processing RFP {rfp_url}: {e}")
                    result["errors"].append({
                        "rfp_url": rfp_url,
                        "error": str(e)
                    })
            
            # Update site statistics
            site_config.last_scrape = datetime.now()
            site_config.rfp_count = len(result["new_rfps"]) + len(result["updated_rfps"])
            
            # Check for field mapping issues
            broken_mappings = site_config.get_broken_field_mappings()
            if broken_mappings:
                result["field_mapping_issues"] = [
                    {
                        "field": fm.alias,
                        "status": fm.status.value,
                        "errors": fm.validation_errors
                    }
                    for fm in broken_mappings
                ]
            
            result["success"] = True
            logger.info(f"Successfully scraped {site_config.name}: "
                       f"{len(result['new_rfps'])} new, {len(result['updated_rfps'])} updated")
            
        except Exception as e:
            logger.error(f"Error scraping site {site_config.name}: {e}")
            result["errors"].append(str(e))
        
        return result
    
    async def _discover_rfp_urls(self, site_config: SiteConfig) -> List[str]:
        """
        Discover RFP URLs from the site's main RFP listing page.
        
        Args:
            site_config: Site configuration
            
        Returns:
            List of RFP URLs to process
        """
        try:
            # Fetch the main RFP listing page
            page_content = await self.base_scraper.fetch_page(
                site_config.main_rfp_page_url,
                site_config
            )
            
            # For now, return mock URLs
            # Real implementation would parse the page to find RFP links
            mock_urls = [
                f"{site_config.base_url}/rfp/001",
                f"{site_config.base_url}/rfp/002",
                f"{site_config.base_url}/rfp/003"
            ]
            
            return mock_urls
            
        except Exception as e:
            logger.error(f"Error discovering RFP URLs for {site_config.name}: {e}")
            return []
    
    async def _process_rfp_url(self, site_config: SiteConfig, rfp_url: str) -> Dict[str, Any]:
        """
        Process a single RFP URL to extract data.
        
        Args:
            site_config: Site configuration
            rfp_url: URL of the RFP to process
            
        Returns:
            Dictionary with processing results
        """
        try:
            # Fetch the RFP page
            page_content = await self.base_scraper.fetch_page(rfp_url, site_config)
            
            # Extract data using location-binding
            extracted_data = await self.base_scraper.extract_data(
                site_config, page_content, rfp_url
            )
            
            # Generate RFP ID
            rfp_id = self._generate_rfp_id(rfp_url, extracted_data)
            
            # Check if RFP already exists
            existing_rfp = self.data_manager.get_rfp_by_id(rfp_id)
            
            if existing_rfp:
                # Check if data has changed
                new_content_hash = self._generate_content_hash(extracted_data)
                
                if existing_rfp.content_hash != new_content_hash:
                    # Update existing RFP
                    updated_rfp = self._update_rfp(existing_rfp, extracted_data, rfp_url)
                    self.data_manager.update_rfp(updated_rfp)
                    
                    return {
                        "is_new": False,
                        "is_updated": True,
                        "rfp": updated_rfp
                    }
                else:
                    # No changes
                    return {
                        "is_new": False,
                        "is_updated": False,
                        "rfp": existing_rfp
                    }
            else:
                # Create new RFP
                new_rfp = self._create_rfp(rfp_id, rfp_url, site_config, extracted_data)
                self.data_manager.add_rfp(new_rfp)
                
                return {
                    "is_new": True,
                    "is_updated": False,
                    "rfp": new_rfp
                }
                
        except Exception as e:
            logger.error(f"Error processing RFP {rfp_url}: {e}")
            raise
    
    def _generate_rfp_id(self, url: str, extracted_data: Dict[str, Any]) -> str:
        """Generate unique ID for an RFP."""
        # Use URL and title to generate stable ID
        title = extracted_data.get("title", "")
        content = f"{url}:{title}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def _generate_content_hash(self, extracted_data: Dict[str, Any]) -> str:
        """Generate content hash for change detection."""
        # Sort data for consistent hashing
        sorted_data = dict(sorted(extracted_data.items()))
        content = str(sorted_data)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _create_rfp(self, rfp_id: str, url: str, site_config: SiteConfig, 
                   extracted_data: Dict[str, Any]) -> RFP:
        """Create new RFP from extracted data."""
        # Determine categories based on content
        categories = self._categorize_rfp(extracted_data)
        
        rfp = RFP(
            id=rfp_id,
            title=extracted_data.get("title", "Unknown RFP"),
            url=url,
            source_site=site_config.id,
            extracted_fields=extracted_data,
            detected_at=datetime.now(),
            content_hash=self._generate_content_hash(extracted_data),
            categories=categories
        )
        
        return rfp
    
    def _update_rfp(self, existing_rfp: RFP, new_data: Dict[str, Any], url: str) -> RFP:
        """Update existing RFP with new data."""
        # Track changes
        for field, new_value in new_data.items():
            if field in existing_rfp.extracted_fields:
                old_value = existing_rfp.extracted_fields[field]
                if old_value != new_value:
                    existing_rfp.update_field(field, new_value)
        
        # Update categories
        existing_rfp.categories = self._categorize_rfp(new_data)
        
        return existing_rfp
    
    def _categorize_rfp(self, extracted_data: Dict[str, Any]) -> List[str]:
        """Categorize RFP based on extracted data."""
        categories = []
        
        # Combine title and description for analysis
        text_content = f"{extracted_data.get('title', '')} {extracted_data.get('description', '')}"
        
        # Use the Olympic relevance detection from validation module
        from models.validation import validate_olympic_relevance
        is_relevant, keywords, score = validate_olympic_relevance(text_content)
        
        if is_relevant:
            categories.append("Olympics")
            
            if score > 0.7:
                categories.append("High Priority")
            
            # Add specific categories based on keywords
            surveillance_keywords = ["surveillance", "facial recognition", "biometric", "monitoring"]
            if any(keyword in keywords for keyword in surveillance_keywords):
                categories.append("Surveillance")
            
            security_keywords = ["security", "police", "law enforcement"]
            if any(keyword in keywords for keyword in security_keywords):
                categories.append("Security")
        
        return categories if categories else ["General"]
    
    def _should_test_field_mappings(self, site_config: SiteConfig) -> bool:
        """Check if field mappings should be tested."""
        if not site_config.last_test:
            return True
        
        # Test if it's been more than 24 hours
        hours_since_test = (datetime.now() - site_config.last_test).total_seconds() / 3600
        return hours_since_test > 24
    
    async def test_site_configuration(self, site_config: SiteConfig) -> ValidationResult:
        """
        Test site configuration to ensure field mappings work.
        
        Args:
            site_config: Site configuration to test
            
        Returns:
            ValidationResult with test results
        """
        logger.info(f"Testing site configuration: {site_config.name}")
        
        try:
            # Use location binder to test the configuration
            test_results = self.location_binder.test_site_configuration(site_config)
            
            # Update site configuration with test results
            # Implementation would update field mapping statuses based on results
            
            logger.info(f"Site configuration test completed for {site_config.name}")
            
            # Save updated configuration
            site_configs = self.data_manager.load_site_configs()
            for i, config in enumerate(site_configs):
                if config.id == site_config.id:
                    site_configs[i] = site_config
                    break
            
            self.data_manager.save_site_configs(site_configs)
            
            return ValidationResult(is_valid=test_results["success"])
            
        except Exception as e:
            logger.error(f"Error testing site configuration {site_config.name}: {e}")
            return ValidationResult(is_valid=False, errors=[str(e)])
    
    def get_stats(self) -> Dict[str, Any]:
        """Get scraping statistics."""
        return {
            **self.stats,
            "scraper_stats": self.base_scraper.get_scraping_stats()
        }
