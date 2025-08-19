"""Custom error classes for the RFP monitoring system."""

from typing import Optional, Dict, Any


class RFPMonitorError(Exception):
    """Base exception class for RFP monitoring system."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)


class ValidationError(RFPMonitorError):
    """Raised when data validation fails."""
    
    def __init__(self, field: str, value: Any, message: str, details: Optional[Dict[str, Any]] = None):
        self.field = field
        self.value = value
        full_message = f"Validation error in '{field}': {message}"
        super().__init__(full_message, details)


class ScrapingError(RFPMonitorError):
    """Raised when web scraping operations fail."""
    
    def __init__(self, site_id: str, url: str, message: str, details: Optional[Dict[str, Any]] = None):
        self.site_id = site_id
        self.url = url
        full_message = f"Scraping error for site '{site_id}' at {url}: {message}"
        super().__init__(full_message, details)


class FieldMappingError(RFPMonitorError):
    """Raised when field mapping operations fail."""
    
    def __init__(self, site_id: str, field_alias: str, selector: str, message: str, 
                 details: Optional[Dict[str, Any]] = None):
        self.site_id = site_id
        self.field_alias = field_alias
        self.selector = selector
        full_message = f"Field mapping error for '{field_alias}' on site '{site_id}': {message}"
        super().__init__(full_message, details)


class ConfigurationError(RFPMonitorError):
    """Raised when site configuration is invalid."""
    
    def __init__(self, site_id: str, message: str, details: Optional[Dict[str, Any]] = None):
        self.site_id = site_id
        full_message = f"Configuration error for site '{site_id}': {message}"
        super().__init__(full_message, details)


class DataIntegrityError(RFPMonitorError):
    """Raised when data integrity checks fail."""
    
    def __init__(self, data_type: str, identifier: str, message: str, 
                 details: Optional[Dict[str, Any]] = None):
        self.data_type = data_type
        self.identifier = identifier
        full_message = f"Data integrity error in {data_type} '{identifier}': {message}"
        super().__init__(full_message, details)


class NetworkError(RFPMonitorError):
    """Raised when network operations fail."""
    
    def __init__(self, url: str, message: str, status_code: Optional[int] = None,
                 details: Optional[Dict[str, Any]] = None):
        self.url = url
        self.status_code = status_code
        if status_code:
            full_message = f"Network error ({status_code}) for {url}: {message}"
        else:
            full_message = f"Network error for {url}: {message}"
        super().__init__(full_message, details)


class LocationBindingError(FieldMappingError):
    """Raised when location binding fails to find or extract data."""
    
    def __init__(self, site_id: str, field_alias: str, training_value: str, 
                 selector: str, message: str, details: Optional[Dict[str, Any]] = None):
        self.training_value = training_value
        full_message = (f"Location binding failed for '{field_alias}' on site '{site_id}' "
                       f"(training value: '{training_value}'): {message}")
        
        # Add helpful details for user troubleshooting
        if details is None:
            details = {}
        details.update({
            'training_value': training_value,
            'selector': selector,
            'troubleshooting_tips': [
                "Check if the page structure has changed",
                "Verify the training value still appears on the page",
                "Try using the 'Add Site' wizard again to retrain this field"
            ]
        })
        
        super().__init__(site_id, field_alias, selector, message, details)
