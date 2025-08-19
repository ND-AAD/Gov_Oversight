"""
Base scraper infrastructure with Playwright integration.

Provides the foundation for reliable, respectful web scraping of government websites
with built-in rate limiting, robots.txt compliance, and error handling.
"""

import asyncio
import logging
import time
import random
from typing import Dict, Any, Optional, List
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
from dataclasses import dataclass
from datetime import datetime, timedelta

from ..models import SiteConfig, NetworkError, ScrapingError

logger = logging.getLogger(__name__)


@dataclass
class ScrapingSession:
    """Represents a scraping session with rate limiting and state."""
    site_id: str
    last_request_time: float
    request_count: int
    session_start: datetime
    user_agent: str
    respect_robots_txt: bool = True


class BaseScraper:
    """
    Base scraper class with Playwright integration and ethical scraping practices.
    
    Features:
    - Playwright browser automation
    - Robots.txt compliance checking
    - Rate limiting and respectful delays
    - User-Agent rotation
    - Retry logic with exponential backoff
    - Request/response logging for transparency
    """
    
    def __init__(self):
        """Initialize the base scraper with default settings."""
        self.browser = None
        self.context = None
        self.page = None
        
        # Rate limiting settings
        self.default_delay = 2.0  # seconds between requests
        self.max_requests_per_minute = 20
        self.respect_robots_txt = True
        
        # Retry settings
        self.max_retries = 3
        self.retry_delay_base = 1.0  # exponential backoff base
        
        # Session tracking
        self.sessions: Dict[str, ScrapingSession] = {}
        
        # User-Agent rotation for transparency
        self.user_agents = [
            "LA2028-RFP-Monitor/1.0 (+https://github.com/ND-AAD/Gov_Oversight) - Public Oversight Tool",
            "Mozilla/5.0 (compatible; LA2028-RFP-Monitor/1.0; +https://github.com/ND-AAD/Gov_Oversight)",
            "LA2028-RFP-Monitor/1.0 (Government Transparency Tool; Contact: github.com/ND-AAD/Gov_Oversight)"
        ]
        
        # Robots.txt cache
        self.robots_cache: Dict[str, RobotFileParser] = {}
        self.robots_cache_ttl = timedelta(hours=24)
        self.robots_last_checked: Dict[str, datetime] = {}
    
    async def initialize_browser(self, headless: bool = True) -> None:
        """
        Initialize Playwright browser instance.
        
        Args:
            headless: Whether to run browser in headless mode
        """
        try:
            # This would import and use Playwright in the real implementation
            # from playwright.async_api import async_playwright
            
            logger.info("Initializing browser for web scraping")
            
            # Mock browser initialization for now
            # In real implementation:
            # self.playwright = await async_playwright().start()
            # self.browser = await self.playwright.chromium.launch(headless=headless)
            # self.context = await self.browser.new_context()
            # self.page = await self.context.new_page()
            
            logger.info("Browser initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            raise ScrapingError("browser", "", f"Browser initialization failed: {str(e)}")
    
    async def close_browser(self) -> None:
        """Clean up browser resources."""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            
            logger.info("Browser closed successfully")
            
        except Exception as e:
            logger.warning(f"Error closing browser: {e}")
    
    def check_robots_txt(self, url: str, user_agent: str = "*") -> bool:
        """
        Check if URL is allowed by robots.txt.
        
        Args:
            url: URL to check
            user_agent: User agent to check for (defaults to "*")
            
        Returns:
            True if allowed, False if disallowed
        """
        if not self.respect_robots_txt:
            return True
        
        try:
            parsed_url = urlparse(url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            robots_url = urljoin(base_url, "/robots.txt")
            
            # Check cache first
            now = datetime.now()
            if (base_url in self.robots_cache and 
                base_url in self.robots_last_checked and
                now - self.robots_last_checked[base_url] < self.robots_cache_ttl):
                
                rp = self.robots_cache[base_url]
                return rp.can_fetch(user_agent, url)
            
            # Fetch and parse robots.txt
            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            
            # Cache the result
            self.robots_cache[base_url] = rp
            self.robots_last_checked[base_url] = now
            
            allowed = rp.can_fetch(user_agent, url)
            logger.debug(f"Robots.txt check for {url}: {'allowed' if allowed else 'disallowed'}")
            
            return allowed
            
        except Exception as e:
            logger.warning(f"Error checking robots.txt for {url}: {e}")
            # Default to allowed if we can't check
            return True
    
    def get_session(self, site_id: str) -> ScrapingSession:
        """Get or create scraping session for a site."""
        if site_id not in self.sessions:
            self.sessions[site_id] = ScrapingSession(
                site_id=site_id,
                last_request_time=0,
                request_count=0,
                session_start=datetime.now(),
                user_agent=random.choice(self.user_agents)
            )
        
        return self.sessions[site_id]
    
    def enforce_rate_limit(self, site_id: str, custom_delay: Optional[float] = None) -> None:
        """
        Enforce rate limiting for respectful scraping.
        
        Args:
            site_id: Identifier for the site being scraped
            custom_delay: Override default delay between requests
        """
        session = self.get_session(site_id)
        delay = custom_delay or self.default_delay
        
        # Calculate time since last request
        current_time = time.time()
        time_since_last = current_time - session.last_request_time
        
        # Check requests per minute limit
        session_duration = (datetime.now() - session.session_start).total_seconds()
        if session_duration > 0:
            requests_per_minute = (session.request_count * 60) / session_duration
            if requests_per_minute > self.max_requests_per_minute:
                additional_delay = 60 / self.max_requests_per_minute
                delay = max(delay, additional_delay)
                logger.info(f"Rate limit exceeded, increasing delay to {delay:.2f}s")
        
        # Sleep if necessary
        if time_since_last < delay:
            sleep_time = delay - time_since_last
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        # Update session
        session.last_request_time = time.time()
        session.request_count += 1
    
    async def fetch_page(self, url: str, site_config: SiteConfig, 
                        timeout: int = 30) -> str:
        """
        Fetch a web page with error handling and retries.
        
        Args:
            url: URL to fetch
            site_config: Site configuration with scraping settings
            timeout: Request timeout in seconds
            
        Returns:
            Page content as HTML string
            
        Raises:
            ScrapingError: If page cannot be fetched after retries
            NetworkError: If network issues prevent access
        """
        # Check robots.txt compliance
        session = self.get_session(site_config.id)
        
        if not self.check_robots_txt(url, session.user_agent):
            raise ScrapingError(
                site_config.id, 
                url, 
                "Access disallowed by robots.txt"
            )
        
        # Enforce rate limiting
        custom_delay = site_config.scraper_settings.get("delay_between_requests", self.default_delay)
        self.enforce_rate_limit(site_config.id, custom_delay)
        
        # Attempt to fetch with retries
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                logger.info(f"Fetching {url} (attempt {attempt + 1}/{self.max_retries + 1})")
                
                if not self.page:
                    await self.initialize_browser()
                
                # Set user agent
                # await self.page.set_extra_http_headers({
                #     'User-Agent': session.user_agent
                # })
                
                # Navigate to page
                # response = await self.page.goto(url, timeout=timeout * 1000)
                
                # Mock response for demonstration
                content = f"<html><body>Mock content for {url}</body></html>"
                
                logger.info(f"Successfully fetched {url}")
                return content
                
            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                
                if attempt < self.max_retries:
                    # Exponential backoff
                    delay = self.retry_delay_base * (2 ** attempt)
                    logger.info(f"Retrying in {delay:.2f}s...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All retry attempts failed for {url}")
        
        # If we get here, all retries failed
        if last_error:
            if "timeout" in str(last_error).lower():
                raise NetworkError(url, "Request timeout", details={"timeout": timeout})
            elif "network" in str(last_error).lower():
                raise NetworkError(url, f"Network error: {str(last_error)}")
            else:
                raise ScrapingError(site_config.id, url, f"Fetch failed: {str(last_error)}")
        else:
            raise ScrapingError(site_config.id, url, "Unknown error during fetch")
    
    async def extract_data(self, site_config: SiteConfig, page_content: str, 
                          page_url: str) -> Dict[str, Any]:
        """
        Extract data from a page using site configuration field mappings.
        
        Args:
            site_config: Site configuration with field mappings
            page_content: HTML content of the page
            page_url: URL of the page being processed
            
        Returns:
            Dictionary with extracted field values
        """
        extracted_data = {}
        
        logger.info(f"Extracting data using {len(site_config.field_mappings)} field mappings")
        
        for field_mapping in site_config.field_mappings:
            try:
                # Try primary selector
                value = await self._extract_field_value(
                    field_mapping.selector, 
                    field_mapping.data_type,
                    page_content
                )
                
                if value is None and field_mapping.fallback_selectors:
                    # Try fallback selectors
                    for fallback_selector in field_mapping.fallback_selectors:
                        value = await self._extract_field_value(
                            fallback_selector,
                            field_mapping.data_type,
                            page_content
                        )
                        if value is not None:
                            logger.debug(f"Used fallback selector for {field_mapping.alias}")
                            break
                
                if value is not None:
                    extracted_data[field_mapping.alias] = value
                    logger.debug(f"Extracted {field_mapping.alias}: {value}")
                else:
                    logger.warning(f"No value extracted for {field_mapping.alias}")
                    
            except Exception as e:
                logger.error(f"Error extracting {field_mapping.alias}: {e}")
                # Mark field mapping as having issues
                field_mapping.add_validation_error(f"Extraction failed: {str(e)}")
        
        logger.info(f"Extracted {len(extracted_data)} fields from {page_url}")
        return extracted_data
    
    async def _extract_field_value(self, selector: str, data_type, page_content: str) -> Optional[str]:
        """
        Extract value from page using specific selector.
        
        In real implementation, this would use Playwright to query the DOM.
        """
        # Mock extraction for demonstration
        # Real implementation would use: await self.page.query_selector(selector)
        
        if "status" in selector.lower():
            return "Active"
        elif "title" in selector.lower():
            return "Olympic Security Infrastructure RFP"
        elif "amount" in selector.lower() or "value" in selector.lower():
            return "$15,000,000"
        elif "date" in selector.lower():
            return "2024-12-16"
        
        return None
    
    def get_scraping_stats(self) -> Dict[str, Any]:
        """Get statistics about current scraping sessions."""
        stats = {
            "active_sessions": len(self.sessions),
            "total_requests": sum(s.request_count for s in self.sessions.values()),
            "sessions": {}
        }
        
        for site_id, session in self.sessions.items():
            session_duration = (datetime.now() - session.session_start).total_seconds()
            stats["sessions"][site_id] = {
                "requests": session.request_count,
                "duration_seconds": session_duration,
                "requests_per_minute": (session.request_count * 60) / max(session_duration, 1),
                "user_agent": session.user_agent
            }
        
        return stats
