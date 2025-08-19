"""
Unit tests for data models.

Tests RFP, SiteConfig, FieldMapping models and their validation/serialization.
"""

import pytest
from datetime import datetime
from unittest.mock import patch
import json

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import (
    RFP, SiteConfig, FieldMapping, DataType, SiteStatus, FieldMappingStatus,
    ValidationResult, DataManager
)
from models.validation import (
    validate_url, validate_date_string, validate_currency_string,
    validate_css_selector, validate_olympic_relevance, validate_rfp_data
)


class TestRFPModel:
    """Test RFP data model functionality."""
    
    def test_rfp_creation(self):
        """Test basic RFP creation."""
        rfp = RFP(
            id="test_rfp_001",
            title="Olympic Security Infrastructure RFP",
            url="https://lacounty.gov/rfp/001",
            source_site="la_county",
            extracted_fields={"status": "Active", "value": "$50,000"},
            detected_at=datetime.now(),
            content_hash="abc123",
            categories=["Security", "Olympics"]
        )
        
        assert rfp.id == "test_rfp_001"
        assert rfp.title == "Olympic Security Infrastructure RFP"
        assert "Security" in rfp.categories
        assert rfp.extracted_fields["status"] == "Active"
    
    def test_content_hash_generation(self):
        """Test automatic content hash generation."""
        rfp = RFP(
            id="test_rfp_002",
            title="Test RFP",
            url="https://example.gov/rfp/2",
            source_site="test_site",
            extracted_fields={"status": "Active"},
            detected_at=datetime.now(),
            content_hash="",  # Empty, should be auto-generated
            categories=["Test"]
        )
        
        assert rfp.content_hash != ""
        assert len(rfp.content_hash) == 64  # SHA256 hex length
    
    def test_change_tracking(self):
        """Test change tracking functionality."""
        rfp = RFP(
            id="test_rfp_003",
            title="Test RFP",
            url="https://example.gov/rfp/3",
            source_site="test_site",
            extracted_fields={"status": "Draft"},
            detected_at=datetime.now(),
            content_hash="abc123",
            categories=["Test"]
        )
        
        # Update a field
        changed = rfp.update_field("status", "Active")
        
        assert changed is True
        assert rfp.extracted_fields["status"] == "Active"
        assert len(rfp.change_history) == 1
        assert rfp.change_history[0]["field"] == "status"
        assert rfp.change_history[0]["old_value"] == "Draft"
        assert rfp.change_history[0]["new_value"] == "Active"
    
    def test_high_priority_detection(self):
        """Test Olympic surveillance priority detection."""
        # High priority RFP
        high_priority_rfp = RFP(
            id="test_rfp_004",
            title="Olympic Village Facial Recognition System",
            url="https://example.gov/rfp/4",
            source_site="test_site",
            extracted_fields={"description": "Biometric surveillance for 2028 Olympics"},
            detected_at=datetime.now(),
            content_hash="abc123",
            categories=["Security", "Olympics"]
        )
        
        assert high_priority_rfp.is_high_priority() is True
        
        # Normal priority RFP
        normal_rfp = RFP(
            id="test_rfp_005",
            title="Office Supplies Contract",
            url="https://example.gov/rfp/5",
            source_site="test_site",
            extracted_fields={"description": "Standard office equipment"},
            detected_at=datetime.now(),
            content_hash="def456",
            categories=["General"]
        )
        
        assert normal_rfp.is_high_priority() is False
    
    def test_closing_soon_detection(self):
        """Test closing soon detection."""
        from datetime import timedelta
        
        # RFP closing tomorrow
        tomorrow = (datetime.now() + timedelta(days=1)).isoformat()
        closing_soon_rfp = RFP(
            id="test_rfp_006",
            title="Test RFP",
            url="https://example.gov/rfp/6",
            source_site="test_site",
            extracted_fields={"closing_date": tomorrow},
            detected_at=datetime.now(),
            content_hash="abc123",
            categories=["Test"]
        )
        
        assert closing_soon_rfp.is_closing_soon(7) is True  # Within 7 days
        assert closing_soon_rfp.is_closing_soon(0) is False  # Not today
    
    def test_display_values(self):
        """Test display value formatting."""
        rfp = RFP(
            id="test_rfp_007",
            title="Test RFP",
            url="https://example.gov/rfp/7",
            source_site="test_site",
            extracted_fields={
                "contract_value": "1500000",
                "posted_date": "2024-12-16",
                "status": "Active"
            },
            detected_at=datetime.now(),
            content_hash="abc123",
            categories=["Test"]
        )
        
        # Test currency formatting
        value_display = rfp.get_display_value("contract_value")
        assert "$" in value_display
        assert "1,500,000" in value_display
        
        # Test date formatting
        date_display = rfp.get_display_value("posted_date")
        assert "December" in date_display or "2024" in date_display
        
        # Test normal text
        status_display = rfp.get_display_value("status")
        assert status_display == "Active"
    
    def test_serialization(self):
        """Test JSON serialization and deserialization."""
        original_rfp = RFP(
            id="test_rfp_008",
            title="Test RFP",
            url="https://example.gov/rfp/8",
            source_site="test_site",
            extracted_fields={"status": "Active"},
            detected_at=datetime.now(),
            content_hash="abc123",
            categories=["Test"]
        )
        
        # Convert to dict
        rfp_dict = original_rfp.to_dict()
        assert isinstance(rfp_dict, dict)
        assert rfp_dict["id"] == "test_rfp_008"
        
        # Convert back to RFP
        restored_rfp = RFP.from_dict(rfp_dict)
        assert restored_rfp.id == original_rfp.id
        assert restored_rfp.title == original_rfp.title
        assert restored_rfp.extracted_fields == original_rfp.extracted_fields


class TestFieldMappingModel:
    """Test FieldMapping model functionality."""
    
    def test_field_mapping_creation(self):
        """Test basic field mapping creation."""
        mapping = FieldMapping(
            alias="status",
            selector=".rfp-status",
            data_type=DataType.TEXT,
            training_value="Active",
            confidence_score=0.9
        )
        
        assert mapping.alias == "status"
        assert mapping.data_type == DataType.TEXT
        assert mapping.status == FieldMappingStatus.UNTESTED
        assert mapping.consecutive_failures == 0
    
    def test_validation_error_tracking(self):
        """Test validation error tracking and status updates."""
        mapping = FieldMapping(
            alias="status",
            selector=".rfp-status",
            data_type=DataType.TEXT,
            training_value="Active",
            confidence_score=0.9
        )
        
        # Add first error - should become degraded
        mapping.add_validation_error("Selector not found")
        assert mapping.status == FieldMappingStatus.DEGRADED
        assert mapping.consecutive_failures == 1
        assert len(mapping.validation_errors) == 1
        
        # Add more errors - should become broken
        mapping.add_validation_error("Second failure")
        mapping.add_validation_error("Third failure")
        assert mapping.status == FieldMappingStatus.BROKEN
        assert mapping.consecutive_failures == 3
    
    def test_validation_error_clearing(self):
        """Test clearing validation errors."""
        mapping = FieldMapping(
            alias="status",
            selector=".rfp-status",
            data_type=DataType.TEXT,
            training_value="Active",
            confidence_score=0.5
        )
        
        # Add errors
        mapping.add_validation_error("Error 1")
        mapping.add_validation_error("Error 2")
        assert mapping.status == FieldMappingStatus.DEGRADED
        
        # Clear errors
        mapping.clear_validation_errors()
        assert mapping.status == FieldMappingStatus.WORKING
        assert mapping.consecutive_failures == 0
        assert len(mapping.validation_errors) == 0
        assert mapping.last_validated is not None
    
    def test_validity_checking(self):
        """Test field mapping validity checking."""
        # Valid mapping
        valid_mapping = FieldMapping(
            alias="status",
            selector=".rfp-status",
            data_type=DataType.TEXT,
            training_value="Active",
            confidence_score=0.8,
            status=FieldMappingStatus.WORKING
        )
        assert valid_mapping.is_valid() is True
        
        # Invalid mapping - broken status
        broken_mapping = FieldMapping(
            alias="status",
            selector=".rfp-status",
            data_type=DataType.TEXT,
            training_value="Active",
            confidence_score=0.8,
            status=FieldMappingStatus.BROKEN
        )
        assert broken_mapping.is_valid() is False
        
        # Invalid mapping - low confidence
        low_confidence_mapping = FieldMapping(
            alias="status",
            selector=".rfp-status",
            data_type=DataType.TEXT,
            training_value="Active",
            confidence_score=0.3,
            status=FieldMappingStatus.WORKING
        )
        assert low_confidence_mapping.is_valid() is False


class TestSiteConfigModel:
    """Test SiteConfig model functionality."""
    
    def test_site_config_creation(self):
        """Test basic site configuration creation."""
        mapping = FieldMapping(
            alias="title",
            selector=".rfp-title",
            data_type=DataType.TEXT,
            training_value="Sample RFP Title",
            confidence_score=0.9
        )
        
        site_config = SiteConfig(
            id="test_site",
            name="Test Government Site",
            base_url="https://testgov.example.com",
            main_rfp_page_url="https://testgov.example.com/rfps",
            sample_rfp_url="https://testgov.example.com/rfp/sample",
            field_mappings=[mapping]
        )
        
        assert site_config.id == "test_site"
        assert site_config.status == SiteStatus.TESTING
        assert len(site_config.field_mappings) == 1
        assert site_config.scraper_settings is not None
    
    def test_field_mapping_management(self):
        """Test adding/removing field mappings."""
        site_config = SiteConfig(
            id="test_site",
            name="Test Site",
            base_url="https://example.com",
            main_rfp_page_url="https://example.com/rfps",
            sample_rfp_url="https://example.com/rfp/1",
            field_mappings=[]
        )
        
        # Add field mapping
        mapping = FieldMapping(
            alias="status",
            selector=".status",
            data_type=DataType.TEXT,
            training_value="Active",
            confidence_score=0.8
        )
        
        site_config.add_field_mapping(mapping)
        assert len(site_config.field_mappings) == 1
        
        # Try to add duplicate alias - should raise error
        duplicate_mapping = FieldMapping(
            alias="status",  # Same alias
            selector=".other-status",
            data_type=DataType.TEXT,
            training_value="Draft",
            confidence_score=0.7
        )
        
        with pytest.raises(ValueError):
            site_config.add_field_mapping(duplicate_mapping)
        
        # Remove field mapping
        removed = site_config.remove_field_mapping("status")
        assert removed is True
        assert len(site_config.field_mappings) == 0
        
        # Try to remove non-existent mapping
        removed = site_config.remove_field_mapping("nonexistent")
        assert removed is False
    
    def test_health_checking(self):
        """Test site health checking."""
        # Create site with mostly working mappings
        working_mapping = FieldMapping(
            alias="title",
            selector=".title",
            data_type=DataType.TEXT,
            training_value="Sample",
            confidence_score=0.9,
            status=FieldMappingStatus.WORKING
        )
        
        broken_mapping = FieldMapping(
            alias="status",
            selector=".status",
            data_type=DataType.TEXT,
            training_value="Active",
            confidence_score=0.5,
            status=FieldMappingStatus.BROKEN
        )
        
        site_config = SiteConfig(
            id="test_site",
            name="Test Site",
            base_url="https://example.com",
            main_rfp_page_url="https://example.com/rfps",
            sample_rfp_url="https://example.com/rfp/1",
            field_mappings=[working_mapping, broken_mapping],
            status=SiteStatus.ACTIVE
        )
        
        # Should be healthy with 50% success rate (1/2 = 50%, but threshold is 80%)
        assert site_config.is_healthy() is False
        
        # Fix the broken mapping
        broken_mapping.status = FieldMappingStatus.WORKING
        assert site_config.is_healthy() is True
    
    def test_status_summary(self):
        """Test field mapping status summary."""
        mappings = [
            FieldMapping("f1", ".s1", DataType.TEXT, "v1", 0.9, status=FieldMappingStatus.WORKING),
            FieldMapping("f2", ".s2", DataType.TEXT, "v2", 0.8, status=FieldMappingStatus.WORKING),
            FieldMapping("f3", ".s3", DataType.TEXT, "v3", 0.7, status=FieldMappingStatus.DEGRADED),
            FieldMapping("f4", ".s4", DataType.TEXT, "v4", 0.6, status=FieldMappingStatus.BROKEN),
            FieldMapping("f5", ".s5", DataType.TEXT, "v5", 0.5, status=FieldMappingStatus.UNTESTED),
        ]
        
        site_config = SiteConfig(
            id="test_site",
            name="Test Site",
            base_url="https://example.com",
            main_rfp_page_url="https://example.com/rfps",
            sample_rfp_url="https://example.com/rfp/1",
            field_mappings=mappings
        )
        
        summary = site_config.get_status_summary()
        assert summary["working"] == 2
        assert summary["degraded"] == 1
        assert summary["broken"] == 1
        assert summary["untested"] == 1
    
    def test_critical_issues_detection(self):
        """Test critical issues detection."""
        # Create site with broken required field
        title_mapping = FieldMapping(
            alias="title",  # Required field
            selector=".title",
            data_type=DataType.TEXT,
            training_value="Sample",
            confidence_score=0.9,
            status=FieldMappingStatus.BROKEN
        )
        
        site_config = SiteConfig(
            id="test_site",
            name="Test Site",
            base_url="https://example.com",
            main_rfp_page_url="https://example.com/rfps",
            sample_rfp_url="https://example.com/rfp/1",
            field_mappings=[title_mapping]
        )
        
        assert site_config.has_critical_issues() is True


class TestValidationFunctions:
    """Test validation functions."""
    
    def test_url_validation(self):
        """Test URL validation function."""
        # Valid URLs
        result = validate_url("https://lacounty.gov/rfps")
        assert result.is_valid is True
        
        result = validate_url("http://example.gov/page")
        assert result.is_valid is True
        
        # Invalid URLs
        result = validate_url("not-a-url")
        assert result.is_valid is False
        
        result = validate_url("")
        assert result.is_valid is False
        
        # Non-government domain warning
        result = validate_url("https://example.com/test")
        assert result.is_valid is True
        assert len(result.warnings) > 0
    
    def test_date_validation(self):
        """Test date string validation."""
        # Valid dates
        result = validate_date_string("2024-12-16")
        assert result.is_valid is True
        
        result = validate_date_string("12/16/2024")
        assert result.is_valid is True
        
        result = validate_date_string("December 16, 2024")
        assert result.is_valid is True
        
        # Invalid dates
        result = validate_date_string("not-a-date")
        assert result.is_valid is False
        
        result = validate_date_string("")
        assert result.is_valid is False
    
    def test_currency_validation(self):
        """Test currency string validation."""
        # Valid currencies
        result = validate_currency_string("$50,000")
        assert result.is_valid is True
        
        result = validate_currency_string("1500000")
        assert result.is_valid is True
        
        result = validate_currency_string("$1,500,000.00")
        assert result.is_valid is True
        
        # Invalid currencies
        result = validate_currency_string("not-currency")
        assert result.is_valid is False
        
        result = validate_currency_string("")
        assert result.is_valid is False
    
    def test_css_selector_validation(self):
        """Test CSS selector validation."""
        # Valid selectors
        result = validate_css_selector(".rfp-title")
        assert result.is_valid is True
        
        result = validate_css_selector("#main-content .status")
        assert result.is_valid is True
        
        # Potentially fragile selectors (warnings)
        result = validate_css_selector("div:nth-child(5) span:nth-child(3)")
        assert result.is_valid is True
        assert len(result.warnings) > 0
        
        # Invalid selectors
        result = validate_css_selector("")
        assert result.is_valid is False
        
        result = validate_css_selector("div[unclosed")
        assert result.is_valid is False
    
    def test_olympic_relevance_detection(self):
        """Test Olympic surveillance relevance detection."""
        # High relevance
        is_relevant, keywords, score = validate_olympic_relevance(
            "2028 Olympics facial recognition surveillance system"
        )
        assert is_relevant is True
        assert score > 0.5
        assert "2028" in keywords
        assert "facial recognition" in keywords
        
        # Medium relevance
        is_relevant, keywords, score = validate_olympic_relevance(
            "Los Angeles security camera installation"
        )
        assert is_relevant is True
        assert "los angeles" in keywords
        
        # Low relevance
        is_relevant, keywords, score = validate_olympic_relevance(
            "Office furniture procurement"
        )
        assert is_relevant is False
        assert score < 0.3


class TestDataManager:
    """Test DataManager functionality."""
    
    def test_data_manager_initialization(self):
        """Test DataManager initialization."""
        dm = DataManager("test_data")
        assert dm.data_dir.name == "test_data"
        assert dm.rfps_file.name == "rfps.json"
        assert dm.sites_file.name == "sites.json"
    
    @patch('pathlib.Path.exists')
    @patch('builtins.open')
    @patch('json.load')
    def test_load_rfps_empty_file(self, mock_json_load, mock_open, mock_exists):
        """Test loading RFPs when file doesn't exist."""
        mock_exists.return_value = False
        
        dm = DataManager("test_data")
        rfps = dm.load_rfps()
        
        assert rfps == []
    
    def test_rfp_id_generation(self):
        """Test RFP ID generation and uniqueness."""
        dm = DataManager("test_data")
        
        # Create test RFPs with same URL but different titles
        rfp1 = RFP(
            id="test1",
            title="Title 1",
            url="https://example.com/rfp1",
            source_site="test",
            extracted_fields={},
            detected_at=datetime.now(),
            content_hash="hash1",
            categories=[]
        )
        
        rfp2 = RFP(
            id="test2",
            title="Title 2", 
            url="https://example.com/rfp1",  # Same URL
            source_site="test",
            extracted_fields={},
            detected_at=datetime.now(),
            content_hash="hash2",
            categories=[]
        )
        
        # IDs should be different despite same URL
        assert rfp1.id != rfp2.id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
