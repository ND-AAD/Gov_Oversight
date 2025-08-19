"""
Location-binding engine for resilient web scraping.

The core innovation: users provide sample values from government sites to "teach" 
the scraper where to find each field. The scraper binds aliases to DOM locations, 
then extracts current values from those locations during future runs.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import (
    SiteConfig, FieldMapping, DataType, FieldMappingStatus,
    ValidationResult, LocationBindingError, ScrapingError
)
from models.validation import validate_css_selector

logger = logging.getLogger(__name__)


@dataclass
class ElementCandidate:
    """Represents a potential DOM element for field extraction."""
    element: Any  # Will be Playwright element when implemented
    selector: str
    text_content: str
    confidence_score: float
    extraction_method: str  # 'text', 'attribute', 'html'
    attribute_name: Optional[str] = None
    

@dataclass
class SelectorStrategy:
    """Strategy for generating CSS selectors."""
    name: str
    selector: str
    confidence: float
    fragility_score: float  # 0 = very stable, 1 = very fragile
    description: str


class LocationBinder:
    """
    Core engine for binding user-friendly field aliases to DOM locations.
    
    This class implements the location-binding approach where users provide
    sample values and the system learns where to extract data from.
    """
    
    def __init__(self):
        """Initialize the LocationBinder with default settings."""
        self.extraction_timeout = 30  # seconds
        self.max_candidates = 50  # limit candidate search
        self.min_confidence_threshold = 0.3
        
        # Common patterns for different data types
        self.data_type_patterns = {
            DataType.DATE: [
                r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
                r'\d{4}-\d{2}-\d{2}',
                r'[A-Za-z]+ \d{1,2}, \d{4}'
            ],
            DataType.CURRENCY: [
                r'\$[\d,]+(?:\.\d{2})?',
                r'USD?\s*[\d,]+(?:\.\d{2})?',
                r'[\d,]+(?:\.\d{2})?\s*dollars?'
            ],
            DataType.NUMBER: [
                r'\d+(?:,\d{3})*(?:\.\d+)?'
            ],
            DataType.EMAIL: [
                r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            ],
            DataType.URL: [
                r'https?://[^\s<>"]+',
                r'www\.[^\s<>"]+\.[a-zA-Z]{2,}'
            ]
        }
    
    def find_field_location(self, page_content: str, target_value: str, 
                           data_type: DataType, page_url: str = "") -> List[ElementCandidate]:
        """
        Find potential DOM locations containing the target value.
        
        Args:
            page_content: HTML content of the page
            target_value: The sample value to find (e.g., "Active", "$50,000")
            data_type: Expected data type for validation
            page_url: URL of the page being analyzed
            
        Returns:
            List of ElementCandidate objects ranked by confidence
            
        Raises:
            LocationBindingError: If no suitable locations found
        """
        logger.info(f"Finding location for target value: '{target_value}' (type: {data_type.value})")
        
        candidates = []
        
        try:
            # This is a simplified implementation - in the real system, this would
            # use Playwright to parse the DOM and find elements
            candidates = self._find_candidates_in_html(page_content, target_value, data_type)
            
            # Filter and rank candidates
            valid_candidates = self._filter_and_rank_candidates(candidates, target_value, data_type)
            
            if not valid_candidates:
                raise LocationBindingError(
                    site_id="unknown",
                    field_alias="unknown", 
                    training_value=target_value,
                    selector="",
                    message=f"No suitable DOM locations found for value '{target_value}'"
                )
            
            logger.info(f"Found {len(valid_candidates)} candidate locations")
            return valid_candidates
            
        except Exception as e:
            logger.error(f"Error finding field location: {e}")
            raise LocationBindingError(
                site_id="unknown",
                field_alias="unknown",
                training_value=target_value, 
                selector="",
                message=f"Location discovery failed: {str(e)}"
            )
    
    def _find_candidates_in_html(self, html_content: str, target_value: str, 
                                data_type: DataType) -> List[ElementCandidate]:
        """
        Simplified HTML parsing to find candidate elements.
        
        In the real implementation, this would use Playwright's DOM API.
        """
        candidates = []
        
        # Simplified regex-based search for demonstration
        # Real implementation would parse DOM tree
        
        # Look for exact text matches
        exact_pattern = re.escape(target_value)
        for match in re.finditer(exact_pattern, html_content, re.IGNORECASE):
            # Generate a mock candidate
            candidate = ElementCandidate(
                element=None,  # Would be actual Playwright element
                selector=f".field-containing-{hash(target_value) % 1000}",
                text_content=target_value,
                confidence_score=0.9,
                extraction_method="text"
            )
            candidates.append(candidate)
        
        # Look for pattern matches based on data type
        if data_type in self.data_type_patterns:
            for pattern in self.data_type_patterns[data_type]:
                for match in re.finditer(pattern, html_content):
                    if self._values_are_similar(match.group(), target_value):
                        candidate = ElementCandidate(
                            element=None,
                            selector=f".pattern-field-{hash(match.group()) % 1000}",
                            text_content=match.group(),
                            confidence_score=0.7,
                            extraction_method="text"
                        )
                        candidates.append(candidate)
        
        return candidates
    
    def _filter_and_rank_candidates(self, candidates: List[ElementCandidate], 
                                   target_value: str, data_type: DataType) -> List[ElementCandidate]:
        """Filter and rank candidate elements by confidence score."""
        valid_candidates = []
        
        for candidate in candidates:
            # Calculate confidence based on multiple factors
            confidence = self._calculate_confidence(candidate, target_value, data_type)
            
            if confidence >= self.min_confidence_threshold:
                candidate.confidence_score = confidence
                valid_candidates.append(candidate)
        
        # Sort by confidence (highest first)
        valid_candidates.sort(key=lambda c: c.confidence_score, reverse=True)
        
        # Limit to top candidates
        return valid_candidates[:self.max_candidates]
    
    def _calculate_confidence(self, candidate: ElementCandidate, target_value: str, 
                            data_type: DataType) -> float:
        """Calculate confidence score for a candidate element."""
        confidence = 0.0
        
        # Exact text match gets high score
        if candidate.text_content.strip().lower() == target_value.strip().lower():
            confidence += 0.8
        
        # Partial match gets medium score
        elif target_value.lower() in candidate.text_content.lower():
            confidence += 0.5
        
        # Data type pattern match gets bonus
        if data_type in self.data_type_patterns:
            for pattern in self.data_type_patterns[data_type]:
                if re.search(pattern, candidate.text_content):
                    confidence += 0.2
                    break
        
        # Selector stability bonus
        if self._is_stable_selector(candidate.selector):
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _values_are_similar(self, value1: str, value2: str) -> bool:
        """Check if two values are similar enough to be the same field type."""
        # Normalize values for comparison
        v1 = re.sub(r'[^\w]', '', value1.lower())
        v2 = re.sub(r'[^\w]', '', value2.lower())
        
        # Check for significant overlap
        if len(v1) == 0 or len(v2) == 0:
            return False
        
        # Simple similarity check
        longer = max(len(v1), len(v2))
        shorter = min(len(v1), len(v2))
        
        return shorter / longer >= 0.6
    
    def _is_stable_selector(self, selector: str) -> bool:
        """Check if a CSS selector appears to be stable."""
        # Avoid selectors with auto-generated IDs
        if re.search(r'#\w*\d{3,}', selector):
            return False
        
        # Avoid overly specific nth-child selectors
        if 'nth-child' in selector and selector.count(' ') > 3:
            return False
        
        # Prefer class and attribute selectors
        if '.' in selector or '[' in selector:
            return True
        
        return True
    
    def generate_stable_selector(self, candidate: ElementCandidate, 
                               page_context: Dict[str, Any]) -> List[SelectorStrategy]:
        """
        Generate multiple selector strategies for robust extraction.
        
        Args:
            candidate: The selected element candidate
            page_context: Additional context about the page structure
            
        Returns:
            List of SelectorStrategy objects ranked by stability
        """
        strategies = []
        
        # Strategy 1: Class-based selector (most stable)
        if '.' in candidate.selector:
            strategies.append(SelectorStrategy(
                name="class_based",
                selector=candidate.selector,
                confidence=0.9,
                fragility_score=0.2,
                description="Class-based selector (most stable)"
            ))
        
        # Strategy 2: Attribute-based selector
        attribute_selector = self._generate_attribute_selector(candidate)
        if attribute_selector:
            strategies.append(SelectorStrategy(
                name="attribute_based",
                selector=attribute_selector,
                confidence=0.8,
                fragility_score=0.3,
                description="Attribute-based selector"
            ))
        
        # Strategy 3: Text content selector
        text_selector = self._generate_text_selector(candidate)
        if text_selector:
            strategies.append(SelectorStrategy(
                name="text_based",
                selector=text_selector,
                confidence=0.6,
                fragility_score=0.5,
                description="Text content-based selector"
            ))
        
        # Strategy 4: Hierarchical selector
        hier_selector = self._generate_hierarchical_selector(candidate, page_context)
        if hier_selector:
            strategies.append(SelectorStrategy(
                name="hierarchical",
                selector=hier_selector,
                confidence=0.7,
                fragility_score=0.4,
                description="Parent-child relationship selector"
            ))
        
        # Sort by stability (low fragility score first)
        strategies.sort(key=lambda s: s.fragility_score)
        
        return strategies
    
    def _generate_attribute_selector(self, candidate: ElementCandidate) -> Optional[str]:
        """Generate attribute-based selector."""
        # This would analyze actual element attributes in real implementation
        # For now, return a mock selector
        return f"[data-field*='status']"
    
    def _generate_text_selector(self, candidate: ElementCandidate) -> Optional[str]:
        """Generate text content-based selector."""
        # Escape special characters in text content
        safe_text = re.escape(candidate.text_content[:20])  # First 20 chars
        return f":contains('{safe_text}')"
    
    def _generate_hierarchical_selector(self, candidate: ElementCandidate, 
                                      page_context: Dict[str, Any]) -> Optional[str]:
        """Generate selector based on parent-child relationships."""
        # This would analyze DOM hierarchy in real implementation
        return f".rfp-details {candidate.selector}"
    
    def validate_field_mapping(self, field_mapping: FieldMapping, 
                             page_content: str, page_url: str = "") -> ValidationResult:
        """
        Validate that a field mapping still works on the current page.
        
        Args:
            field_mapping: The field mapping to validate
            page_content: Current HTML content of the page
            page_url: URL of the page
            
        Returns:
            ValidationResult with validation status and details
        """
        result = ValidationResult()
        
        try:
            # Validate the CSS selector syntax first
            selector_result = validate_css_selector(field_mapping.selector)
            result.merge(selector_result)
            
            if not result.is_valid:
                return result
            
            # Try to extract value using the current selector
            extracted_value = self._extract_value_with_selector(
                page_content, field_mapping.selector, field_mapping.data_type
            )
            
            if extracted_value is None:
                # Try fallback selectors
                for fallback_selector in field_mapping.fallback_selectors:
                    extracted_value = self._extract_value_with_selector(
                        page_content, fallback_selector, field_mapping.data_type
                    )
                    if extracted_value is not None:
                        result.add_warning(f"Primary selector failed, fallback worked: {fallback_selector}")
                        break
            
            if extracted_value is None:
                result.add_error("No value could be extracted with any selector")
                return result
            
            # Validate extracted value format
            if not self._validate_extracted_value(extracted_value, field_mapping.data_type):
                result.add_warning(f"Extracted value format may be incorrect: '{extracted_value}'")
            
            # Check if value is significantly different from training value
            if not self._values_are_similar(extracted_value, field_mapping.training_value):
                result.add_warning(f"Extracted value differs from training value. "
                                 f"Got: '{extracted_value}', Expected similar to: '{field_mapping.training_value}'")
            
            logger.info(f"Field mapping validation successful: {field_mapping.alias}")
            
        except Exception as e:
            result.add_error(f"Validation failed with error: {str(e)}")
            logger.error(f"Field mapping validation failed for {field_mapping.alias}: {e}")
        
        return result
    
    def _extract_value_with_selector(self, page_content: str, selector: str, 
                                   data_type: DataType) -> Optional[str]:
        """
        Extract value from page using the given selector.
        
        In real implementation, this would use Playwright to query the DOM.
        """
        # Simplified implementation for demonstration
        # Real version would use actual DOM querying
        
        # Mock extraction based on selector patterns
        if ".status" in selector.lower() or "status" in selector.lower():
            # Return a mock status value
            return "Active"
        elif "currency" in selector.lower() or "amount" in selector.lower():
            return "$50,000"
        elif "date" in selector.lower():
            return "2024-12-16"
        
        return None
    
    def _validate_extracted_value(self, value: str, data_type: DataType) -> bool:
        """Validate that extracted value matches expected data type."""
        if data_type == DataType.DATE:
            # Try to parse as date
            for pattern in self.data_type_patterns[DataType.DATE]:
                if re.search(pattern, value):
                    return True
        elif data_type == DataType.CURRENCY:
            for pattern in self.data_type_patterns[DataType.CURRENCY]:
                if re.search(pattern, value):
                    return True
        elif data_type == DataType.NUMBER:
            for pattern in self.data_type_patterns[DataType.NUMBER]:
                if re.search(pattern, value):
                    return True
        
        return True  # Default to valid for text fields
    
    def create_site_configuration(self, sample_url: str, field_specs: List[Dict[str, Any]], 
                                 site_info: Dict[str, str]) -> SiteConfig:
        """
        Create a complete site configuration from user-provided samples.
        
        Args:
            sample_url: URL of sample RFP page with example data
            field_specs: List of field specifications with sample values
            site_info: Basic site information (name, base_url, etc.)
            
        Returns:
            SiteConfig object ready for testing and use
            
        Example field_specs:
        [
            {
                "alias": "status",
                "sample_value": "Active", 
                "data_type": "text",
                "description": "Current status of the RFP"
            },
            {
                "alias": "contract_value",
                "sample_value": "$50,000",
                "data_type": "currency", 
                "description": "Total contract value"
            }
        ]
        """
        logger.info(f"Creating site configuration for {site_info.get('name', 'Unknown Site')}")
        
        field_mappings = []
        
        # For now, create mock field mappings
        # Real implementation would fetch the sample page and analyze it
        for spec in field_specs:
            # Create field mapping with mock selectors
            field_mapping = FieldMapping(
                alias=spec["alias"],
                selector=f".{spec['alias'].lower().replace(' ', '-')}",
                data_type=DataType(spec["data_type"]),
                training_value=spec["sample_value"],
                confidence_score=0.8,
                status=FieldMappingStatus.UNTESTED,
                fallback_selectors=[
                    f"[data-field='{spec['alias']}']",
                    f":contains('{spec['sample_value'][:10]}')"
                ]
            )
            
            field_mappings.append(field_mapping)
        
        # Create site configuration
        site_config = SiteConfig(
            id=site_info.get("id", f"site_{hash(site_info.get('name', '')) % 10000}"),
            name=site_info["name"],
            base_url=site_info["base_url"],
            main_rfp_page_url=site_info["main_rfp_page_url"],
            sample_rfp_url=sample_url,
            field_mappings=field_mappings,
            description=site_info.get("description", ""),
            robots_txt_compliant=True
        )
        
        logger.info(f"Created site configuration with {len(field_mappings)} field mappings")
        return site_config
    
    def test_site_configuration(self, site_config: SiteConfig, 
                              test_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Test a site configuration to ensure field mappings work.
        
        Args:
            site_config: Site configuration to test
            test_url: Optional specific URL to test (defaults to sample_rfp_url)
            
        Returns:
            Dictionary with test results and extracted sample data
        """
        test_url = test_url or site_config.sample_rfp_url
        logger.info(f"Testing site configuration for {site_config.name} at {test_url}")
        
        # Mock test results for demonstration
        # Real implementation would fetch the page and test each field mapping
        
        test_results = {
            "success": True,
            "timestamp": datetime.now(),
            "url_tested": test_url,
            "field_results": {},
            "sample_data": {},
            "errors": [],
            "warnings": []
        }
        
        for field_mapping in site_config.field_mappings:
            # Mock field testing
            mock_extracted_value = self._get_mock_value_for_field(field_mapping.alias)
            
            field_result = {
                "success": True,
                "extracted_value": mock_extracted_value,
                "confidence": field_mapping.confidence_score,
                "selector_used": field_mapping.selector
            }
            
            test_results["field_results"][field_mapping.alias] = field_result
            test_results["sample_data"][field_mapping.alias] = mock_extracted_value
        
        # Update field mapping statuses based on test results
        for field_mapping in site_config.field_mappings:
            if test_results["field_results"][field_mapping.alias]["success"]:
                field_mapping.status = FieldMappingStatus.WORKING
                field_mapping.last_validated = datetime.now()
            else:
                field_mapping.status = FieldMappingStatus.BROKEN
                field_mapping.add_validation_error("Field extraction failed during testing")
        
        logger.info(f"Site configuration test completed for {site_config.name}")
        return test_results
    
    def _get_mock_value_for_field(self, field_alias: str) -> str:
        """Get mock extracted value for testing purposes."""
        mock_values = {
            "status": "Active",
            "title": "Olympic Village Security Infrastructure RFP",
            "contract_value": "$15,000,000",
            "posted_date": "2024-12-16",
            "closing_date": "2025-01-15",
            "department": "Los Angeles Police Department",
            "description": "Request for proposals for comprehensive security infrastructure..."
        }
        
        return mock_values.get(field_alias.lower(), f"Sample {field_alias}")
