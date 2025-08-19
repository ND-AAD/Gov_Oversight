"""
RFP monitoring data models.

This package contains the core data models for the LA 2028 RFP Monitor:
- RFP: Individual procurement opportunities  
- SiteConfig: Configuration for scraping government websites
- FieldMapping: Maps user-friendly aliases to DOM locations
- Validation: Data validation functions
- Serialization: JSON file management
- Errors: Custom exception classes
"""

from .rfp import RFP
from .site_config import (
    SiteConfig, 
    FieldMapping, 
    TestResult,
    DataType, 
    SiteStatus, 
    FieldMappingStatus
)
from .validation import (
    ValidationError as ValidationErrorClass,
    ValidationResult,
    validate_url,
    validate_date_string, 
    validate_currency_string,
    validate_css_selector,
    validate_olympic_relevance,
    validate_rfp_data,
    validate_site_config_data
)
from .serialization import DataManager
from .errors import (
    RFPMonitorError,
    ValidationError,
    ScrapingError, 
    FieldMappingError,
    ConfigurationError,
    DataIntegrityError,
    NetworkError,
    LocationBindingError
)

__all__ = [
    # Core models
    'RFP',
    'SiteConfig', 
    'FieldMapping',
    'TestResult',
    
    # Enums
    'DataType',
    'SiteStatus', 
    'FieldMappingStatus',
    
    # Validation
    'ValidationErrorClass',
    'ValidationResult',
    'validate_url',
    'validate_date_string',
    'validate_currency_string', 
    'validate_css_selector',
    'validate_olympic_relevance',
    'validate_rfp_data',
    'validate_site_config_data',
    
    # Data management
    'DataManager',
    
    # Errors
    'RFPMonitorError',
    'ValidationError',
    'ScrapingError',
    'FieldMappingError', 
    'ConfigurationError',
    'DataIntegrityError',
    'NetworkError',
    'LocationBindingError'
]