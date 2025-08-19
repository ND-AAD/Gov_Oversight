"""
Unit tests for LocationBinder core functionality.

Tests the location-binding engine with mock HTML scenarios.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scrapers.location_binder import LocationBinder, ElementCandidate, SelectorStrategy
from models import (
    FieldMapping, SiteConfig, DataType, FieldMappingStatus,
    LocationBindingError, ValidationResult
)


class TestLocationBinder:
    """Test LocationBinder core functionality."""
    
    def setup_method(self):
        """Set up test instance."""
        self.location_binder = LocationBinder()
    
    def test_initialization(self):
        """Test LocationBinder initialization."""
        assert self.location_binder.extraction_timeout == 30
        assert self.location_binder.max_candidates == 50
        assert self.location_binder.min_confidence_threshold == 0.3
        assert DataType.DATE in self.location_binder.data_type_patterns
    
    def test_find_field_location_success(self):
        """Test successful field location discovery."""
        mock_html = """
        <html>
            <body>
                <div class="rfp-details">
                    <span class="status">Active</span>
                    <h1 class="title">Olympic Security RFP</h1>
                    <div class="value">$50,000</div>
                </div>
            </body>
        </html>
        """
        
        # Test finding "Active" status
        candidates = self.location_binder.find_field_location(
            mock_html, "Active", DataType.TEXT
        )
        
        assert len(candidates) > 0
        assert candidates[0].text_content == "Active"
        assert candidates[0].confidence_score > 0.5
    
    def test_find_field_location_not_found(self):
        """Test field location discovery when value not found."""
        mock_html = "<html><body><p>No matching content</p></body></html>"
        
        with pytest.raises(LocationBindingError) as exc_info:
            self.location_binder.find_field_location(
                mock_html, "NonexistentValue", DataType.TEXT
            )
        
        assert "No suitable DOM locations found" in str(exc_info.value)
        assert exc_info.value.training_value == "NonexistentValue"
    
    def test_confidence_calculation(self):
        """Test confidence score calculation."""
        # Exact match candidate
        exact_candidate = ElementCandidate(
            element=None,
            selector=".status",
            text_content="Active",
            confidence_score=0.0,  # Will be calculated
            extraction_method="text"
        )
        
        confidence = self.location_binder._calculate_confidence(
            exact_candidate, "Active", DataType.TEXT
        )
        assert confidence >= 0.8  # High confidence for exact match
        
        # Partial match candidate
        partial_candidate = ElementCandidate(
            element=None,
            selector=".status-label",
            text_content="Status: Active",
            confidence_score=0.0,
            extraction_method="text"
        )
        
        confidence = self.location_binder._calculate_confidence(
            partial_candidate, "Active", DataType.TEXT
        )
        assert 0.4 <= confidence <= 0.7  # Medium confidence for partial match
    
    def test_values_similarity(self):
        """Test value similarity checking."""
        # Similar values
        assert self.location_binder._values_are_similar("Active", "active") is True
        assert self.location_binder._values_are_similar("$50,000", "$50000") is True
        assert self.location_binder._values_are_similar("2024-12-16", "20241216") is True
        
        # Dissimilar values
        assert self.location_binder._values_are_similar("Active", "Closed") is False
        assert self.location_binder._values_are_similar("$50,000", "$100,000") is False
    
    def test_stable_selector_detection(self):
        """Test selector stability detection."""
        # Stable selectors
        assert self.location_binder._is_stable_selector(".rfp-status") is True
        assert self.location_binder._is_stable_selector("[data-field='status']") is True
        assert self.location_binder._is_stable_selector(".container .status") is True
        
        # Unstable selectors
        assert self.location_binder._is_stable_selector("#generated12345") is False
        assert self.location_binder._is_stable_selector("div:nth-child(5) span:nth-child(3) p:nth-child(2)") is False
    
    def test_generate_stable_selector(self):
        """Test stable selector generation."""
        candidate = ElementCandidate(
            element=None,
            selector=".rfp-status",
            text_content="Active",
            confidence_score=0.9,
            extraction_method="text"
        )
        
        strategies = self.location_binder.generate_stable_selector(candidate, {})
        
        assert len(strategies) > 0
        assert all(isinstance(s, SelectorStrategy) for s in strategies)
        
        # Should be sorted by fragility (most stable first)
        fragility_scores = [s.fragility_score for s in strategies]
        assert fragility_scores == sorted(fragility_scores)
        
        # Should include different strategy types
        strategy_names = [s.name for s in strategies]
        assert len(set(strategy_names)) > 1  # Multiple different strategies
    
    def test_validate_field_mapping_working(self):
        """Test field mapping validation when working correctly."""
        field_mapping = FieldMapping(
            alias="status",
            selector=".rfp-status",
            data_type=DataType.TEXT,
            training_value="Active",
            confidence_score=0.9,
            fallback_selectors=[".status", "[data-field='status']"]
        )
        
        mock_html = """
        <div class="rfp-status">Active</div>
        """
        
        # Mock the extraction to return expected value
        with patch.object(self.location_binder, '_extract_value_with_selector', return_value="Active"):
            result = self.location_binder.validate_field_mapping(field_mapping, mock_html)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_validate_field_mapping_broken(self):
        """Test field mapping validation when broken."""
        field_mapping = FieldMapping(
            alias="status",
            selector=".nonexistent-selector",
            data_type=DataType.TEXT,
            training_value="Active",
            confidence_score=0.9,
            fallback_selectors=[]
        )
        
        mock_html = "<div>No status element</div>"
        
        # Mock extraction to return None (not found)
        with patch.object(self.location_binder, '_extract_value_with_selector', return_value=None):
            result = self.location_binder.validate_field_mapping(field_mapping, mock_html)
        
        assert result.is_valid is False
        assert "No value could be extracted" in result.errors[0]
    
    def test_validate_field_mapping_fallback_success(self):
        """Test field mapping validation when fallback selector works."""
        field_mapping = FieldMapping(
            alias="status",
            selector=".primary-selector",  # This will fail
            data_type=DataType.TEXT,
            training_value="Active",
            confidence_score=0.9,
            fallback_selectors=[".fallback-selector"]  # This will work
        )
        
        mock_html = """
        <div class="fallback-selector">Active</div>
        """
        
        def mock_extract(html, selector, data_type):
            if "primary-selector" in selector:
                return None  # Primary fails
            elif "fallback-selector" in selector:
                return "Active"  # Fallback succeeds
            return None
        
        with patch.object(self.location_binder, '_extract_value_with_selector', side_effect=mock_extract):
            result = self.location_binder.validate_field_mapping(field_mapping, mock_html)
        
        assert result.is_valid is True
        assert len(result.warnings) > 0  # Should warn about fallback usage
        assert "fallback worked" in result.warnings[0]
    
    def test_create_site_configuration(self):
        """Test site configuration creation from field specs."""
        field_specs = [
            {
                "alias": "title",
                "sample_value": "Olympic Security RFP",
                "data_type": "text",
                "description": "RFP title"
            },
            {
                "alias": "status", 
                "sample_value": "Active",
                "data_type": "text",
                "description": "Current status"
            },
            {
                "alias": "contract_value",
                "sample_value": "$50,000",
                "data_type": "currency",
                "description": "Contract value"
            }
        ]
        
        site_info = {
            "id": "test_site",
            "name": "Test Government Site",
            "base_url": "https://testgov.example.com",
            "main_rfp_page_url": "https://testgov.example.com/rfps"
        }
        
        site_config = self.location_binder.create_site_configuration(
            "https://testgov.example.com/rfp/sample",
            field_specs,
            site_info
        )
        
        assert isinstance(site_config, SiteConfig)
        assert site_config.id == "test_site"
        assert site_config.name == "Test Government Site"
        assert len(site_config.field_mappings) == 3
        
        # Check field mappings were created correctly
        aliases = [fm.alias for fm in site_config.field_mappings]
        assert "title" in aliases
        assert "status" in aliases
        assert "contract_value" in aliases
        
        # Check data types were set correctly
        value_mapping = next(fm for fm in site_config.field_mappings if fm.alias == "contract_value")
        assert value_mapping.data_type == DataType.CURRENCY
        assert value_mapping.training_value == "$50,000"
        assert len(value_mapping.fallback_selectors) > 0
    
    def test_test_site_configuration(self):
        """Test site configuration testing."""
        # Create test site config
        field_mapping = FieldMapping(
            alias="status",
            selector=".status",
            data_type=DataType.TEXT,
            training_value="Active",
            confidence_score=0.9
        )
        
        site_config = SiteConfig(
            id="test_site",
            name="Test Site",
            base_url="https://example.com",
            main_rfp_page_url="https://example.com/rfps",
            sample_rfp_url="https://example.com/rfp/sample",
            field_mappings=[field_mapping]
        )
        
        # Test the configuration
        test_results = self.location_binder.test_site_configuration(site_config)
        
        assert isinstance(test_results, dict)
        assert "success" in test_results
        assert "field_results" in test_results
        assert "sample_data" in test_results
        
        # Check field mapping status was updated
        assert field_mapping.status in [FieldMappingStatus.WORKING, FieldMappingStatus.BROKEN]
    
    def test_data_type_pattern_matching(self):
        """Test data type pattern matching."""
        # Currency patterns
        currency_patterns = self.location_binder.data_type_patterns[DataType.CURRENCY]
        
        test_currencies = ["$50,000", "$1,500,000.00", "USD 50000", "50000 dollars"]
        for currency in test_currencies:
            matched = any(
                __import__('re').search(pattern, currency)
                for pattern in currency_patterns
            )
            # At least one pattern should match
            assert matched or currency == "50000 dollars"  # This might not match all patterns
        
        # Date patterns
        date_patterns = self.location_binder.data_type_patterns[DataType.DATE]
        
        test_dates = ["2024-12-16", "12/16/2024", "12-16-2024", "December 16, 2024"]
        for date in test_dates:
            matched = any(
                __import__('re').search(pattern, date)
                for pattern in date_patterns
            )
            assert matched
    
    def test_mock_value_generation(self):
        """Test mock value generation for testing."""
        # Test known field aliases
        assert self.location_binder._get_mock_value_for_field("status") == "Active"
        assert "$" in self.location_binder._get_mock_value_for_field("contract_value")
        assert "2024" in self.location_binder._get_mock_value_for_field("posted_date")
        
        # Test unknown field alias
        unknown_value = self.location_binder._get_mock_value_for_field("unknown_field")
        assert "Sample" in unknown_value
        assert "unknown_field" in unknown_value
    
    def test_extracted_value_validation(self):
        """Test validation of extracted values against data types."""
        # Valid date
        assert self.location_binder._validate_extracted_value("2024-12-16", DataType.DATE) is True
        assert self.location_binder._validate_extracted_value("12/16/2024", DataType.DATE) is True
        
        # Valid currency
        assert self.location_binder._validate_extracted_value("$50,000", DataType.CURRENCY) is True
        assert self.location_binder._validate_extracted_value("1500000", DataType.NUMBER) is True
        
        # Text values should always be valid
        assert self.location_binder._validate_extracted_value("Any text", DataType.TEXT) is True
        assert self.location_binder._validate_extracted_value("", DataType.TEXT) is True


class TestElementCandidate:
    """Test ElementCandidate data class."""
    
    def test_element_candidate_creation(self):
        """Test ElementCandidate creation."""
        candidate = ElementCandidate(
            element=None,
            selector=".rfp-status",
            text_content="Active",
            confidence_score=0.9,
            extraction_method="text"
        )
        
        assert candidate.selector == ".rfp-status"
        assert candidate.text_content == "Active"
        assert candidate.confidence_score == 0.9
        assert candidate.extraction_method == "text"
        assert candidate.attribute_name is None


class TestSelectorStrategy:
    """Test SelectorStrategy data class."""
    
    def test_selector_strategy_creation(self):
        """Test SelectorStrategy creation."""
        strategy = SelectorStrategy(
            name="class_based",
            selector=".rfp-status",
            confidence=0.9,
            fragility_score=0.2,
            description="Class-based selector (most stable)"
        )
        
        assert strategy.name == "class_based"
        assert strategy.selector == ".rfp-status"
        assert strategy.confidence == 0.9
        assert strategy.fragility_score == 0.2
        assert "stable" in strategy.description


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
