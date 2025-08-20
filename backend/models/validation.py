"""Validation functions for RFP and SiteConfig data models."""

import re
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from urllib.parse import urlparse
import json


class ValidationError(Exception):
    """Custom exception for validation errors."""
    
    def __init__(self, field: str, value: Any, message: str):
        self.field = field
        self.value = value
        self.message = message
        super().__init__(f"Validation error in '{field}': {message}")


class ValidationResult:
    """Result of a validation check."""
    
    def __init__(self, is_valid: bool = True, errors: List[str] = None, warnings: List[str] = None):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []
    
    def add_error(self, error: str) -> None:
        """Add an error and mark as invalid."""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str) -> None:
        """Add a warning (doesn't affect validity)."""
        self.warnings.append(warning)
    
    def merge(self, other: 'ValidationResult') -> None:
        """Merge another validation result into this one."""
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        if not other.is_valid:
            self.is_valid = False


def validate_url(url: str, require_https: bool = False) -> ValidationResult:
    """
    Validate URL format and accessibility.
    
    Args:
        url: URL to validate
        require_https: Whether to require HTTPS protocol
        
    Returns:
        ValidationResult with validation status
    """
    result = ValidationResult()
    
    if not url or not isinstance(url, str):
        result.add_error("URL cannot be empty")
        return result
    
    try:
        parsed = urlparse(url)
        
        # Check basic structure
        if not parsed.scheme:
            result.add_error("URL must include protocol (http:// or https://)")
        elif parsed.scheme not in ['http', 'https']:
            result.add_error(f"Unsupported protocol: {parsed.scheme}")
        elif require_https and parsed.scheme != 'https':
            result.add_error("HTTPS required for this URL")
        
        if not parsed.netloc:
            result.add_error("URL must include domain name")
        
        # Check for suspicious patterns
        if parsed.netloc and not re.match(r'^[a-zA-Z0-9.-]+$', parsed.netloc):
            result.add_warning("Domain contains unusual characters")
        
        # Government site validation
        gov_domains = ['.gov', '.mil', '.state.', '.city.', '.county.']
        if not any(domain in parsed.netloc.lower() for domain in gov_domains):
            result.add_warning("URL does not appear to be a government domain")
            
    except Exception as e:
        result.add_error(f"Invalid URL format: {str(e)}")
    
    return result


def validate_date_string(date_str: str, field_name: str = "date") -> ValidationResult:
    """
    Validate date string format and reasonableness.
    
    Args:
        date_str: Date string to validate
        field_name: Name of the field for error reporting
        
    Returns:
        ValidationResult with validation status
    """
    result = ValidationResult()
    
    if not date_str or not isinstance(date_str, str):
        result.add_error(f"{field_name} cannot be empty")
        return result
    
    # Common date formats to try
    date_formats = [
        '%Y-%m-%d',           # 2024-12-16
        '%m/%d/%Y',           # 12/16/2024
        '%m-%d-%Y',           # 12-16-2024
        '%Y-%m-%dT%H:%M:%S',  # 2024-12-16T10:30:00
        '%Y-%m-%dT%H:%M:%SZ', # 2024-12-16T10:30:00Z
        '%B %d, %Y',          # December 16, 2024
        '%b %d, %Y',          # Dec 16, 2024
    ]
    
    parsed_date = None
    for fmt in date_formats:
        try:
            parsed_date = datetime.strptime(date_str.strip(), fmt)
            break
        except ValueError:
            continue
    
    if not parsed_date:
        result.add_error(f"Unable to parse {field_name}: '{date_str}'")
        return result
    
    # Reasonableness checks
    now = datetime.now()
    year_ago = datetime(now.year - 1, now.month, now.day)
    year_ahead = datetime(now.year + 1, now.month, now.day)
    
    if parsed_date < year_ago:
        result.add_warning(f"{field_name} is more than a year in the past")
    elif parsed_date > year_ahead:
        result.add_warning(f"{field_name} is more than a year in the future")
    
    return result


def validate_currency_string(currency_value) -> ValidationResult:
    """
    Validate currency value format (string or number).
    
    Args:
        currency_value: Currency value to validate (e.g., "$1,000,000" or 1000000)
        
    Returns:
        ValidationResult with validation status
    """
    result = ValidationResult()
    
    if currency_value is None:
        result.add_error("Currency value cannot be empty")
        return result
    
    # Handle numeric values
    if isinstance(currency_value, (int, float)):
        amount = float(currency_value)
        if amount < 0:
            result.add_warning("Negative currency amount detected")
        elif amount == 0:
            result.add_warning("Zero currency amount detected")
        return result
    
    # Handle string values
    if not isinstance(currency_value, str):
        result.add_error("Currency value must be string or number")
        return result
    
    # Remove common currency symbols and whitespace
    clean_str = re.sub(r'[$,\s]', '', currency_value.strip())
    
    # Check if remaining string is a valid number
    try:
        amount = float(clean_str)
        
        if amount < 0:
            result.add_warning("Negative currency amount detected")
        elif amount == 0:
            result.add_warning("Zero currency amount detected")
        elif amount > 1_000_000_000:  # $1 billion
            result.add_warning("Unusually large contract amount (>$1B)")
            
    except ValueError:
        result.add_error(f"Invalid currency format: '{currency_value}'")
    
    return result


def validate_css_selector(selector: str) -> ValidationResult:
    """
    Validate CSS selector syntax.
    
    Args:
        selector: CSS selector to validate
        
    Returns:
        ValidationResult with validation status
    """
    result = ValidationResult()
    
    if not selector or not isinstance(selector, str):
        result.add_error("CSS selector cannot be empty")
        return result
    
    # Basic syntax checks
    selector = selector.strip()
    
    # Check for obviously malformed selectors
    if selector.count('(') != selector.count(')'):
        result.add_error("Unmatched parentheses in selector")
    
    if selector.count('[') != selector.count(']'):
        result.add_error("Unmatched brackets in selector")
    
    # Warn about potentially fragile selectors
    if re.search(r'\d{4,}', selector):
        result.add_warning("Selector contains long numbers (might be auto-generated IDs)")
    
    if selector.count(' ') > 5:
        result.add_warning("Very long selector chain (might be fragile)")
    
    # Check for suspicious patterns
    if 'nth-child' in selector:
        result.add_warning("Position-based selector (nth-child) may be fragile")
    
    return result


def validate_olympic_relevance(text: str) -> Tuple[bool, List[str], float]:
    """
    Check if text content is relevant to 2028 Olympics surveillance.
    
    Args:
        text: Text to analyze (title, description, etc.)
        
    Returns:
        Tuple of (is_relevant, matched_keywords, relevance_score)
    """
    if not text:
        return False, [], 0.0
    
    text_lower = text.lower()
    
    # Olympic-specific keywords (high priority)
    olympic_keywords = [
        '2028', 'olympics', 'olympic', 'los angeles', 'la28',
        'olympic village', 'olympic venues', 'olympic games',
        'paralympics', 'paralympic'
    ]
    
    # Surveillance/security keywords (high priority)
    surveillance_keywords = [
        'surveillance', 'facial recognition', 'biometric', 'monitoring',
        'security camera', 'cctv', 'intelligence', 'tracking',
        'facial detection', 'crowd monitoring', 'perimeter security',
        'access control', 'identity verification', 'screening'
    ]
    
    # Technology keywords (medium priority)
    tech_keywords = [
        'ai', 'artificial intelligence', 'machine learning', 'analytics',
        'data collection', 'database', 'software platform',
        'mobile surveillance', 'drone', 'sensor network'
    ]
    
    # Security services keywords (medium priority)
    security_keywords = [
        'security services', 'police', 'law enforcement',
        'emergency response', 'crowd control', 'perimeter',
        'checkpoint', 'screening', 'patrol'
    ]
    
    matched_keywords = []
    relevance_score = 0.0
    
    # Check Olympic keywords (2x weight)
    for keyword in olympic_keywords:
        if keyword in text_lower:
            matched_keywords.append(keyword)
            relevance_score += 2.0
    
    # Check surveillance keywords (3x weight - highest priority)
    for keyword in surveillance_keywords:
        if keyword in text_lower:
            matched_keywords.append(keyword)
            relevance_score += 3.0
    
    # Check technology keywords (1x weight)
    for keyword in tech_keywords:
        if keyword in text_lower:
            matched_keywords.append(keyword)
            relevance_score += 1.0
    
    # Check security keywords (1.5x weight)
    for keyword in security_keywords:
        if keyword in text_lower:
            matched_keywords.append(keyword)
            relevance_score += 1.5
    
    # Bonus for multiple keyword categories
    keyword_categories = 0
    if any(k in olympic_keywords for k in matched_keywords):
        keyword_categories += 1
    if any(k in surveillance_keywords for k in matched_keywords):
        keyword_categories += 1
    if any(k in tech_keywords for k in matched_keywords):
        keyword_categories += 1
    if any(k in security_keywords for k in matched_keywords):
        keyword_categories += 1
    
    if keyword_categories >= 2:
        relevance_score *= 1.5  # 50% bonus for cross-category matches
    
    # Normalize score (arbitrary scale)
    relevance_score = min(relevance_score / 10.0, 1.0)
    
    is_relevant = relevance_score >= 0.3 or len(matched_keywords) >= 2
    
    return is_relevant, matched_keywords, relevance_score


def validate_rfp_data(rfp_data: Dict[str, Any]) -> ValidationResult:
    """
    Validate complete RFP data structure.
    
    Args:
        rfp_data: Dictionary containing RFP data
        
    Returns:
        ValidationResult with validation status
    """
    result = ValidationResult()
    
    # Required fields
    required_fields = ['id', 'title', 'url', 'source_site']
    for field in required_fields:
        if field not in rfp_data or not rfp_data[field]:
            result.add_error(f"Required field '{field}' is missing or empty")
    
    # Validate URL if present
    if 'url' in rfp_data and rfp_data['url']:
        url_result = validate_url(rfp_data['url'])
        result.merge(url_result)
    
    # Validate extracted fields if present
    if 'extracted_fields' in rfp_data and isinstance(rfp_data['extracted_fields'], dict):
        extracted = rfp_data['extracted_fields']
        
        # Validate date fields
        date_fields = ['posted_date', 'closing_date', 'deadline', 'due_date']
        for field in date_fields:
            if field in extracted and extracted[field]:
                date_result = validate_date_string(extracted[field], field)
                result.merge(date_result)
        
        # Validate currency fields
        currency_fields = ['contract_value', 'value', 'amount', 'budget']
        for field in currency_fields:
            if field in extracted and extracted[field]:
                currency_result = validate_currency_string(extracted[field])
                result.merge(currency_result)
    
    # Check Olympic relevance
    title = rfp_data.get('title', '')
    description = rfp_data.get('extracted_fields', {}).get('description', '')
    full_text = f"{title} {description}"
    
    is_relevant, keywords, score = validate_olympic_relevance(full_text)
    if is_relevant and score > 0.7:
        result.add_warning(f"High-priority Olympic surveillance contract detected (score: {score:.2f})")
    
    return result


def validate_site_config_data(site_data: Dict[str, Any]) -> ValidationResult:
    """
    Validate complete SiteConfig data structure.
    
    Args:
        site_data: Dictionary containing SiteConfig data
        
    Returns:
        ValidationResult with validation status
    """
    result = ValidationResult()
    
    # Required fields
    required_fields = ['id', 'name', 'base_url', 'main_rfp_page_url']
    for field in required_fields:
        if field not in site_data or not site_data[field]:
            result.add_error(f"Required field '{field}' is missing or empty")
    
    # Validate URLs
    url_fields = ['base_url', 'main_rfp_page_url', 'sample_rfp_url']
    for field in url_fields:
        if field in site_data and site_data[field]:
            url_result = validate_url(site_data[field], require_https=False)
            result.merge(url_result)
    
    # Validate field mappings
    if 'field_mappings' in site_data and isinstance(site_data['field_mappings'], list):
        for i, mapping in enumerate(site_data['field_mappings']):
            if not isinstance(mapping, dict):
                result.add_error(f"Field mapping {i} is not a valid object")
                continue
            
            # Check required mapping fields
            mapping_required = ['alias', 'selector', 'data_type']
            for field in mapping_required:
                if field not in mapping or not mapping[field]:
                    result.add_error(f"Field mapping {i} missing required field '{field}'")
            
            # Validate selector if present
            if 'selector' in mapping and mapping['selector']:
                selector_result = validate_css_selector(mapping['selector'])
                result.merge(selector_result)
    
    # Check for required field mappings
    if 'field_mappings' in site_data:
        aliases = [fm.get('alias', '').lower() for fm in site_data['field_mappings'] if isinstance(fm, dict)]
        required_aliases = ['title', 'status']
        
        for required in required_aliases:
            if required not in aliases:
                result.add_warning(f"Recommended field mapping '{required}' is not configured")
    
    return result
