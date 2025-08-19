"""
Web scraping infrastructure for LA 2028 RFP Monitor.

This package provides the location-binding engine and scraping infrastructure
for resilient extraction of RFP data from government websites.
"""

from .location_binder import LocationBinder, ElementCandidate, SelectorStrategy
from .base_scraper import BaseScraper, ScrapingSession

__all__ = [
    'LocationBinder',
    'ElementCandidate', 
    'SelectorStrategy',
    'BaseScraper',
    'ScrapingSession'
]
