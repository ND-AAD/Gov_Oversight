"""
Pytest configuration and shared fixtures for testing.

Provides common test fixtures and configuration for the LA 2028 RFP Monitor test suite.
"""

import pytest
import tempfile
import shutil
from datetime import datetime
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import DataManager, RFP, SiteConfig, FieldMapping, DataType, FieldMappingStatus


@pytest.fixture
def temp_data_dir():
    """Create temporary directory for test data."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def data_manager(temp_data_dir):
    """Create DataManager instance with temporary directory."""
    return DataManager(temp_data_dir)


@pytest.fixture
def sample_rfp():
    """Create sample RFP for testing."""
    return RFP(
        id="test_rfp_001",
        title="Olympic Security Infrastructure RFP",
        url="https://lacounty.gov/rfp/001",
        source_site="la_county",
        extracted_fields={
            "status": "Active",
            "contract_value": "$15,000,000",
            "posted_date": "2024-12-16",
            "closing_date": "2025-01-15",
            "department": "Los Angeles Police Department",
            "description": "Comprehensive security infrastructure for 2028 Olympics including facial recognition systems and biometric monitoring."
        },
        detected_at=datetime.now(),
        content_hash="abc123def456",
        categories=["Security", "Olympics", "High Priority"]
    )


@pytest.fixture
def sample_rfps():
    """Create list of sample RFPs for testing."""
    return [
        RFP(
            id="rfp_001",
            title="Olympic Village Security System",
            url="https://lacounty.gov/rfp/001",
            source_site="la_county",
            extracted_fields={
                "status": "Active",
                "contract_value": "$15,000,000",
                "closing_date": "2025-01-15",
                "description": "Facial recognition and biometric surveillance for Olympic Village"
            },
            detected_at=datetime.now(),
            content_hash="hash001",
            categories=["Security", "Olympics", "High Priority"]
        ),
        RFP(
            id="rfp_002",
            title="Transportation Management System",
            url="https://lacounty.gov/rfp/002",
            source_site="la_county", 
            extracted_fields={
                "status": "Active",
                "contract_value": "$5,000,000",
                "closing_date": "2025-02-01",
                "description": "Traffic monitoring and management for Olympic events"
            },
            detected_at=datetime.now(),
            content_hash="hash002",
            categories=["Transportation", "Olympics"]
        ),
        RFP(
            id="rfp_003",
            title="Standard Office Equipment",
            url="https://cityofla.gov/rfp/003",
            source_site="city_of_la",
            extracted_fields={
                "status": "Closed",
                "contract_value": "$50,000",
                "closing_date": "2024-12-01",
                "description": "Desks, chairs, and filing cabinets"
            },
            detected_at=datetime.now(),
            content_hash="hash003",
            categories=["General"]
        )
    ]


@pytest.fixture
def sample_field_mapping():
    """Create sample field mapping for testing."""
    return FieldMapping(
        alias="status",
        selector=".rfp-status",
        data_type=DataType.TEXT,
        training_value="Active",
        confidence_score=0.9,
        status=FieldMappingStatus.WORKING,
        fallback_selectors=[".status", "[data-field='status']"]
    )


@pytest.fixture
def sample_field_mappings():
    """Create list of sample field mappings for testing."""
    return [
        FieldMapping(
            alias="title",
            selector=".rfp-title h1",
            data_type=DataType.TEXT,
            training_value="Olympic Security Infrastructure RFP",
            confidence_score=0.95,
            status=FieldMappingStatus.WORKING,
            fallback_selectors=[".title", "h1"]
        ),
        FieldMapping(
            alias="status",
            selector=".rfp-status .badge",
            data_type=DataType.TEXT,
            training_value="Active",
            confidence_score=0.9,
            status=FieldMappingStatus.WORKING,
            fallback_selectors=[".status", ".badge"]
        ),
        FieldMapping(
            alias="contract_value",
            selector=".contract-amount",
            data_type=DataType.CURRENCY,
            training_value="$15,000,000",
            confidence_score=0.85,
            status=FieldMappingStatus.WORKING,
            fallback_selectors=[".amount", ".value"]
        ),
        FieldMapping(
            alias="closing_date",
            selector=".deadline-date",
            data_type=DataType.DATE,
            training_value="2025-01-15",
            confidence_score=0.8,
            status=FieldMappingStatus.DEGRADED,  # One degraded mapping
            fallback_selectors=[".deadline", ".due-date"]
        )
    ]


@pytest.fixture
def sample_site_config(sample_field_mappings):
    """Create sample site configuration for testing."""
    return SiteConfig(
        id="la_county_test",
        name="LA County Procurement (Test)",
        base_url="https://lacounty.gov",
        main_rfp_page_url="https://lacounty.gov/government/contracts-bids",
        sample_rfp_url="https://lacounty.gov/rfp/sample",
        field_mappings=sample_field_mappings,
        description="Test configuration for LA County procurement site",
        robots_txt_compliant=True
    )


@pytest.fixture
def sample_site_configs(sample_site_config):
    """Create list of sample site configurations for testing."""
    # Create second site config
    broken_mapping = FieldMapping(
        alias="title",
        selector=".broken-selector",
        data_type=DataType.TEXT,
        training_value="Sample Title",
        confidence_score=0.3,
        status=FieldMappingStatus.BROKEN,
        consecutive_failures=5
    )
    
    broken_site = SiteConfig(
        id="city_of_la_test",
        name="City of LA Procurement (Test)",
        base_url="https://cityofla.gov",
        main_rfp_page_url="https://cityofla.gov/contracts",
        sample_rfp_url="https://cityofla.gov/rfp/sample",
        field_mappings=[broken_mapping],
        description="Test configuration with broken mappings"
    )
    
    return [sample_site_config, broken_site]


@pytest.fixture
def mock_html():
    """Provide mock HTML content for testing."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sample RFP Page</title>
    </head>
    <body>
        <div class="container">
            <div class="rfp-details">
                <h1 class="rfp-title">Olympic Security Infrastructure RFP</h1>
                <div class="rfp-meta">
                    <span class="rfp-status badge">Active</span>
                    <span class="contract-amount">$15,000,000</span>
                    <span class="deadline-date">2025-01-15</span>
                </div>
                <div class="rfp-description">
                    <p>Comprehensive security infrastructure for the 2028 Los Angeles Olympics, 
                    including facial recognition systems, biometric monitoring, and surveillance 
                    camera networks for Olympic venues and athlete housing.</p>
                </div>
                <div class="rfp-details-table">
                    <div class="detail-row">
                        <span class="label">Department:</span>
                        <span class="value">Los Angeles Police Department</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">Posted:</span>
                        <span class="value">2024-12-16</span>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """


@pytest.fixture
def mock_html_list_page():
    """Provide mock HTML for RFP listing page."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Current RFPs</title>
    </head>
    <body>
        <div class="rfp-list">
            <div class="rfp-item">
                <h3><a href="/rfp/001">Olympic Security Infrastructure</a></h3>
                <span class="status">Active</span>
                <span class="deadline">Due: 2025-01-15</span>
            </div>
            <div class="rfp-item">
                <h3><a href="/rfp/002">Transportation Management</a></h3>
                <span class="status">Active</span>
                <span class="deadline">Due: 2025-02-01</span>
            </div>
            <div class="rfp-item">
                <h3><a href="/rfp/003">Office Equipment</a></h3>
                <span class="status">Closed</span>
                <span class="deadline">Due: 2024-12-01</span>
            </div>
        </div>
    </body>
    </html>
    """


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "cli: marks tests as CLI tests"
    )
