"""Site configuration models for managing scraper targets."""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum


class DataType(Enum):
    """Supported data types for field extraction."""
    TEXT = "text"
    DATE = "date"
    CURRENCY = "currency"
    NUMBER = "number"
    URL = "url"
    EMAIL = "email"


class SiteStatus(Enum):
    """Site operational status."""
    ACTIVE = "active"
    ERROR = "error"
    TESTING = "testing"
    DISABLED = "disabled"


@dataclass
class FieldMapping:
    """
    Maps a user-friendly alias to a specific location on a website.
    
    The core innovation: users provide sample values, we find the location,
    then extract whatever current value is at that location.
    """
    
    alias: str                    # User-friendly name (e.g., "Status", "Contract Value")
    selector: str                 # CSS selector for the element
    data_type: DataType           # Expected data type for validation
    training_value: str           # Original value used to find this location
    confidence_score: float = 1.0 # How confident we are in this mapping (0-1)
    
    # Optional advanced settings
    xpath: Optional[str] = None   # XPath alternative to CSS selector
    regex_pattern: Optional[str] = None  # Pattern to extract specific part of text
    fallback_selectors: Optional[List[str]] = None  # Backup selectors if primary fails
    
    # Validation and testing
    last_validated: Optional[datetime] = None
    validation_errors: Optional[List[str]] = None
    expected_format: Optional[str] = None  # For dates, currencies, etc.
    
    def __post_init__(self):
        """Validate field mapping after initialization."""
        if self.fallback_selectors is None:
            self.fallback_selectors = []
        
        if self.validation_errors is None:
            self.validation_errors = []
        
        # Ensure data_type is enum
        if isinstance(self.data_type, str):
            self.data_type = DataType(self.data_type)
    
    def is_valid(self) -> bool:
        """Check if this field mapping appears to be working."""
        return (
            self.confidence_score > 0.5 and
            len(self.validation_errors) == 0 and
            self.selector is not None
        )
    
    def add_validation_error(self, error: str) -> None:
        """Record a validation error for this field mapping."""
        if self.validation_errors is None:
            self.validation_errors = []
        
        self.validation_errors.append(error)
        self.confidence_score = max(0.0, self.confidence_score - 0.2)
    
    def clear_validation_errors(self) -> None:
        """Clear validation errors and restore confidence."""
        self.validation_errors = []
        self.confidence_score = min(1.0, self.confidence_score + 0.3)
        self.last_validated = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        
        # Convert enums to strings
        data['data_type'] = self.data_type.value
        
        # Convert datetime to ISO string
        if self.last_validated:
            data['last_validated'] = self.last_validated.isoformat()
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FieldMapping':
        """Create FieldMapping from dictionary."""
        # Convert string back to enum
        if 'data_type' in data:
            data['data_type'] = DataType(data['data_type'])
        
        # Convert ISO string back to datetime
        if data.get('last_validated'):
            data['last_validated'] = datetime.fromisoformat(data['last_validated'])
        
        return cls(**data)


@dataclass
class TestResult:
    """Results from testing a site configuration."""
    
    success: bool
    timestamp: datetime
    rfps_found: int = 0
    errors: Optional[List[str]] = None
    field_results: Optional[Dict[str, Any]] = None  # Results for each field tested
    sample_data: Optional[Dict[str, Any]] = None    # Sample extracted data
    
    def __post_init__(self):
        """Initialize optional fields."""
        if self.errors is None:
            self.errors = []
        
        if self.field_results is None:
            self.field_results = {}
        
        if self.sample_data is None:
            self.sample_data = {}
    
    def add_field_result(self, field_alias: str, success: bool, 
                        extracted_value: Any = None, error: str = None) -> None:
        """Record the result of testing a specific field."""
        self.field_results[field_alias] = {
            'success': success,
            'extracted_value': extracted_value,
            'error': error
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class SiteConfig:
    """
    Complete configuration for scraping a government website.
    
    Contains all the information needed to extract RFP data from a specific site,
    including user-configured field mappings and testing results.
    """
    
    # Basic site information
    id: str
    name: str
    base_url: str
    main_rfp_page_url: str
    sample_rfp_url: str
    
    # Field extraction configuration
    field_mappings: List[FieldMapping]
    
    # Site status and health
    status: SiteStatus = SiteStatus.TESTING
    last_scrape: Optional[datetime] = None
    last_test: Optional[datetime] = None
    rfp_count: int = 0
    
    # Testing and validation results
    test_results: Optional[TestResult] = None
    
    # Optional metadata
    description: Optional[str] = None
    contact_info: Optional[str] = None
    terms_of_service_url: Optional[str] = None
    robots_txt_compliant: bool = True
    
    # Advanced scraper settings
    scraper_settings: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Validate and process site configuration."""
        # Ensure status is enum
        if isinstance(self.status, str):
            self.status = SiteStatus(self.status)
        
        # Initialize optional fields
        if self.scraper_settings is None:
            self.scraper_settings = {
                'delay_between_requests': 2.0,
                'timeout': 30,
                'max_retries': 3,
                'respect_robots_txt': True
            }
    
    def add_field_mapping(self, field_mapping: FieldMapping) -> None:
        """Add a new field mapping to this site configuration."""
        # Check for duplicate aliases
        existing_aliases = [fm.alias for fm in self.field_mappings]
        if field_mapping.alias in existing_aliases:
            raise ValueError(f"Field mapping with alias '{field_mapping.alias}' already exists")
        
        self.field_mappings.append(field_mapping)
    
    def remove_field_mapping(self, alias: str) -> bool:
        """Remove a field mapping by alias. Returns True if found and removed."""
        original_count = len(self.field_mappings)
        self.field_mappings = [fm for fm in self.field_mappings if fm.alias != alias]
        return len(self.field_mappings) < original_count
    
    def get_field_mapping(self, alias: str) -> Optional[FieldMapping]:
        """Get a field mapping by alias."""
        for field_mapping in self.field_mappings:
            if field_mapping.alias == alias:
                return field_mapping
        return None
    
    def update_test_results(self, test_result: TestResult) -> None:
        """Update the site's test results."""
        self.test_results = test_result
        self.last_test = test_result.timestamp
        
        # Update status based on test results
        if test_result.success:
            if self.status == SiteStatus.TESTING:
                self.status = SiteStatus.ACTIVE
        else:
            self.status = SiteStatus.ERROR
    
    def is_healthy(self) -> bool:
        """Check if the site configuration is working properly."""
        if self.status != SiteStatus.ACTIVE:
            return False
        
        # Check if field mappings are valid
        valid_mappings = sum(1 for fm in self.field_mappings if fm.is_valid())
        return valid_mappings >= len(self.field_mappings) * 0.8  # 80% success rate
    
    def get_required_fields(self) -> List[str]:
        """Get list of field aliases that are considered required."""
        # These are the minimum fields we need for a useful RFP
        required = ['title', 'status']
        return [alias for alias in required 
                if any(fm.alias.lower() == alias for fm in self.field_mappings)]
    
    def get_missing_required_fields(self) -> List[str]:
        """Get list of required fields that are not configured."""
        required = ['title', 'status', 'posted_date']
        configured = [fm.alias.lower() for fm in self.field_mappings]
        return [field for field in required if field not in configured]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        
        # Convert enums to strings
        data['status'] = self.status.value
        
        # Convert datetime objects to ISO strings
        if self.last_scrape:
            data['last_scrape'] = self.last_scrape.isoformat()
        if self.last_test:
            data['last_test'] = self.last_test.isoformat()
        
        # Convert field mappings
        data['field_mappings'] = [fm.to_dict() for fm in self.field_mappings]
        
        # Convert test results
        if self.test_results:
            data['test_results'] = self.test_results.to_dict()
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SiteConfig':
        """Create SiteConfig from dictionary."""
        # Convert strings back to enums/datetime
        if 'status' in data:
            data['status'] = SiteStatus(data['status'])
        
        if data.get('last_scrape'):
            data['last_scrape'] = datetime.fromisoformat(data['last_scrape'])
        
        if data.get('last_test'):
            data['last_test'] = datetime.fromisoformat(data['last_test'])
        
        # Convert field mappings
        if 'field_mappings' in data:
            data['field_mappings'] = [
                FieldMapping.from_dict(fm_data) for fm_data in data['field_mappings']
            ]
        
        # Convert test results
        if data.get('test_results'):
            test_data = data['test_results']
            test_data['timestamp'] = datetime.fromisoformat(test_data['timestamp'])
            data['test_results'] = TestResult(**test_data)
        
        return cls(**data)
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"SiteConfig({self.name}): {len(self.field_mappings)} fields, status={self.status.value}"
    
    def __repr__(self) -> str:
        """Developer-friendly string representation."""
        return (f"SiteConfig(id='{self.id}', name='{self.name}', "
                f"status={self.status.value}, fields={len(self.field_mappings)})")
