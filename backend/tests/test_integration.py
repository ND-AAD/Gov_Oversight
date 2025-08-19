"""
Integration tests for LA 2028 RFP Monitor.

End-to-end testing of complete workflows including scraping, data management,
and CLI functionality.
"""

import pytest
import asyncio
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import DataManager, RFP, SiteConfig, FieldMapping, DataType, FieldMappingStatus
from scrapers import RFPScraper, LocationBinder
from main import cli
from click.testing import CliRunner


class TestEndToEndWorkflow:
    """Test complete end-to-end workflows."""
    
    def setup_method(self):
        """Set up test environment with temporary data directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_manager = DataManager(self.temp_dir)
        self.rfp_scraper = RFPScraper(self.data_manager)
        
    def teardown_method(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_complete_site_setup_workflow(self):
        """Test complete workflow: site creation -> field mapping -> testing -> scraping."""
        
        # Step 1: Create site configuration using LocationBinder
        location_binder = LocationBinder()
        
        field_specs = [
            {
                "alias": "title",
                "sample_value": "Olympic Security Infrastructure RFP",
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
                "sample_value": "$15,000,000",
                "data_type": "currency",
                "description": "Contract value"
            },
            {
                "alias": "closing_date",
                "sample_value": "2025-01-15",
                "data_type": "date",
                "description": "Submission deadline"
            }
        ]
        
        site_info = {
            "id": "la_county_test",
            "name": "LA County Procurement (Test)",
            "base_url": "https://lacounty.gov",
            "main_rfp_page_url": "https://lacounty.gov/government/contracts-bids"
        }
        
        site_config = location_binder.create_site_configuration(
            "https://lacounty.gov/rfp/sample",
            field_specs,
            site_info
        )
        
        assert isinstance(site_config, SiteConfig)
        assert len(site_config.field_mappings) == 4
        assert site_config.id == "la_county_test"
        
        # Step 2: Save site configuration
        self.data_manager.save_site_configs([site_config])
        
        # Verify it was saved
        loaded_configs = self.data_manager.load_site_configs()
        assert len(loaded_configs) == 1
        assert loaded_configs[0].id == "la_county_test"
        
        # Step 3: Test site configuration
        test_results = location_binder.test_site_configuration(site_config)
        assert isinstance(test_results, dict)
        assert "success" in test_results
        
        # Step 4: Mock scraping process
        with patch.object(self.rfp_scraper.base_scraper, 'initialize_browser', new_callable=AsyncMock):
            with patch.object(self.rfp_scraper.base_scraper, 'close_browser', new_callable=AsyncMock):
                with patch.object(self.rfp_scraper, '_discover_rfp_urls', new_callable=AsyncMock) as mock_discover:
                    with patch.object(self.rfp_scraper, '_process_rfp_url', new_callable=AsyncMock) as mock_process:
                        
                        # Mock discovering 2 RFP URLs
                        mock_discover.return_value = [
                            "https://lacounty.gov/rfp/001",
                            "https://lacounty.gov/rfp/002"
                        ]
                        
                        # Mock processing results
                        mock_rfp_1 = RFP(
                            id="rfp_001",
                            title="Olympic Village Security System",
                            url="https://lacounty.gov/rfp/001",
                            source_site="la_county_test",
                            extracted_fields={
                                "status": "Active",
                                "contract_value": "$15,000,000",
                                "closing_date": "2025-01-15"
                            },
                            detected_at=datetime.now(),
                            content_hash="hash001",
                            categories=["Security", "Olympics", "High Priority"]
                        )
                        
                        mock_rfp_2 = RFP(
                            id="rfp_002", 
                            title="Event Transportation Services",
                            url="https://lacounty.gov/rfp/002",
                            source_site="la_county_test",
                            extracted_fields={
                                "status": "Active",
                                "contract_value": "$5,000,000",
                                "closing_date": "2025-02-01"
                            },
                            detected_at=datetime.now(),
                            content_hash="hash002",
                            categories=["Transportation", "Olympics"]
                        )
                        
                        mock_process.side_effect = [
                            {"is_new": True, "is_updated": False, "rfp": mock_rfp_1},
                            {"is_new": True, "is_updated": False, "rfp": mock_rfp_2}
                        ]
                        
                        # Run scraping
                        async def run_scraping():
                            return await self.rfp_scraper.scrape_site(site_config)
                        
                        result = asyncio.run(run_scraping())
                        
                        assert result["success"] is True
                        assert len(result["new_rfps"]) == 2
                        assert len(result["updated_rfps"]) == 0
                        
                        # Verify RFPs were saved
                        saved_rfps = self.data_manager.load_rfps()
                        assert len(saved_rfps) == 2
                        
                        # Check high priority detection
                        high_priority_rfps = [rfp for rfp in saved_rfps if rfp.is_high_priority()]
                        assert len(high_priority_rfps) >= 1  # Security RFP should be high priority
    
    def test_data_persistence_and_recovery(self):
        """Test data persistence, backup, and recovery workflows."""
        
        # Create test RFPs
        rfps = [
            RFP(
                id="test_rfp_001",
                title="Olympic Surveillance Infrastructure",
                url="https://example.gov/rfp/001",
                source_site="test_site",
                extracted_fields={"status": "Active", "value": "$1,000,000"},
                detected_at=datetime.now(),
                content_hash="hash001",
                categories=["Security", "Olympics", "High Priority"]
            ),
            RFP(
                id="test_rfp_002",
                title="Standard Office Equipment",
                url="https://example.gov/rfp/002", 
                source_site="test_site",
                extracted_fields={"status": "Closed", "value": "$50,000"},
                detected_at=datetime.now(),
                content_hash="hash002",
                categories=["General"]
            )
        ]
        
        # Save RFPs
        self.data_manager.save_rfps(rfps)
        
        # Verify save
        loaded_rfps = self.data_manager.load_rfps()
        assert len(loaded_rfps) == 2
        
        # Test backup functionality
        backup_path = self.data_manager.backup_data_files()
        assert os.path.exists(backup_path)
        
        # Test statistics generation
        stats = self.data_manager.get_data_statistics()
        assert stats["rfps"]["total"] == 2
        assert stats["rfps"]["high_priority"] >= 1
        
        # Test filtering functions
        high_priority = self.data_manager.get_high_priority_rfps()
        assert len(high_priority) >= 1
        assert any("Olympics" in rfp.categories for rfp in high_priority)
        
        # Test individual RFP operations
        specific_rfp = self.data_manager.get_rfp_by_id("test_rfp_001")
        assert specific_rfp is not None
        assert specific_rfp.title == "Olympic Surveillance Infrastructure"
        
        # Test update operation
        specific_rfp.update_field("status", "Under Review")
        updated = self.data_manager.update_rfp(specific_rfp)
        assert updated is True
        
        # Verify update persisted
        reloaded_rfp = self.data_manager.get_rfp_by_id("test_rfp_001")
        assert reloaded_rfp.extracted_fields["status"] == "Under Review"
        assert len(reloaded_rfp.change_history) > 0
    
    def test_field_mapping_degradation_workflow(self):
        """Test workflow when field mappings start failing."""
        
        # Create site with field mappings
        field_mappings = [
            FieldMapping(
                alias="title",
                selector=".rfp-title",
                data_type=DataType.TEXT,
                training_value="Sample Title",
                confidence_score=0.9,
                status=FieldMappingStatus.WORKING
            ),
            FieldMapping(
                alias="status",
                selector=".rfp-status", 
                data_type=DataType.TEXT,
                training_value="Active",
                confidence_score=0.8,
                status=FieldMappingStatus.WORKING
            )
        ]
        
        site_config = SiteConfig(
            id="test_site",
            name="Test Site",
            base_url="https://example.com",
            main_rfp_page_url="https://example.com/rfps",
            sample_rfp_url="https://example.com/rfp/sample",
            field_mappings=field_mappings
        )
        
        # Initially healthy
        assert site_config.is_healthy() is True
        assert site_config.has_critical_issues() is False
        
        # Simulate first failure on status field
        status_mapping = site_config.get_field_mapping("status")
        status_mapping.add_validation_error("Selector not found")
        
        # Should be degraded but not critical
        assert status_mapping.status == FieldMappingStatus.DEGRADED
        assert site_config.is_healthy() is True  # Still 50% working (1/2)
        
        # Simulate more failures - becomes broken
        status_mapping.add_validation_error("Second failure")
        status_mapping.add_validation_error("Third failure")
        
        assert status_mapping.status == FieldMappingStatus.BROKEN
        assert site_config.is_healthy() is False  # Now below 80% threshold
        assert site_config.has_critical_issues() is True  # Required field broken
        
        # Get status summary for UI indicators
        summary = site_config.get_status_summary()
        assert summary["working"] == 1
        assert summary["degraded"] == 0
        assert summary["broken"] == 1
        
        # Get broken mappings for user notification
        broken_mappings = site_config.get_broken_field_mappings()
        assert len(broken_mappings) == 1
        assert broken_mappings[0].alias == "status"
        
        # Simulate user fixing the mapping
        status_mapping.clear_validation_errors()
        assert status_mapping.status == FieldMappingStatus.WORKING
        assert site_config.is_healthy() is True
        assert site_config.has_critical_issues() is False
    
    def test_olympic_surveillance_detection_workflow(self):
        """Test Olympic surveillance detection across different scenarios."""
        
        test_cases = [
            {
                "title": "2028 Olympics Facial Recognition Deployment",
                "description": "Comprehensive biometric surveillance system for Olympic venues",
                "expected_high_priority": True,
                "expected_categories": ["Olympics", "Surveillance", "High Priority"]
            },
            {
                "title": "Olympic Village Security Patrol Services", 
                "description": "Security personnel for 2028 Olympics athlete housing",
                "expected_high_priority": True,
                "expected_categories": ["Olympics", "Security", "High Priority"]
            },
            {
                "title": "Standard Office Equipment Procurement",
                "description": "Desks, chairs, and filing cabinets for administrative offices",
                "expected_high_priority": False,
                "expected_categories": ["General"]
            },
            {
                "title": "Los Angeles Traffic Camera Installation",
                "description": "Surveillance cameras for traffic monitoring downtown",
                "expected_high_priority": True,  # LA + surveillance
                "expected_categories": ["Surveillance"]
            }
        ]
        
        rfps = []
        for i, case in enumerate(test_cases):
            rfp = RFP(
                id=f"test_rfp_{i:03d}",
                title=case["title"],
                url=f"https://example.gov/rfp/{i:03d}",
                source_site="test_site",
                extracted_fields={"description": case["description"]},
                detected_at=datetime.now(),
                content_hash=f"hash{i:03d}",
                categories=[]  # Will be set by categorization
            )
            
            # Use the categorization logic
            rfp.categories = self.rfp_scraper._categorize_rfp(rfp.extracted_fields)
            rfps.append(rfp)
            
            # Verify detection worked correctly
            assert rfp.is_high_priority() == case["expected_high_priority"], f"Failed for: {case['title']}"
            
            # Check that expected categories are present
            for expected_cat in case["expected_categories"]:
                if expected_cat == "High Priority":
                    continue  # This is added by is_high_priority logic
                assert expected_cat in rfp.categories, f"Missing category {expected_cat} for: {case['title']}"
        
        # Save and test filtering
        self.data_manager.save_rfps(rfps)
        
        # Test high priority filtering
        high_priority_rfps = self.data_manager.get_high_priority_rfps()
        expected_high_priority_count = sum(1 for case in test_cases if case["expected_high_priority"])
        assert len(high_priority_rfps) == expected_high_priority_count


class TestCLIIntegration:
    """Test CLI functionality."""
    
    def setup_method(self):
        """Set up CLI test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.runner = CliRunner()
    
    def teardown_method(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_cli_stats_command(self):
        """Test CLI stats command."""
        result = self.runner.invoke(cli, ['--data-dir', self.temp_dir, 'stats'])
        assert result.exit_code == 0
        assert "RFPs:" in result.output
        assert "Sites:" in result.output
        assert "Total:" in result.output
    
    def test_cli_list_sites_empty(self):
        """Test CLI list-sites command with no sites."""
        result = self.runner.invoke(cli, ['--data-dir', self.temp_dir, 'list-sites'])
        assert result.exit_code == 0
        assert "No sites configured" in result.output
    
    def test_cli_add_site_basic(self):
        """Test CLI add-site command."""
        result = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'add-site',
            'Test Government Site',
            'https://testgov.example.com',
            'https://testgov.example.com/rfps',
            'https://testgov.example.com/rfp/sample'
        ])
        
        assert result.exit_code == 0
        assert "Successfully added site" in result.output
        
        # Verify site was added
        dm = DataManager(self.temp_dir)
        sites = dm.load_site_configs()
        assert len(sites) == 1
        assert sites[0].name == "Test Government Site"
    
    def test_cli_list_rfps_empty(self):
        """Test CLI list-rfps command with no RFPs."""
        result = self.runner.invoke(cli, ['--data-dir', self.temp_dir, 'list-rfps'])
        assert result.exit_code == 0
        assert "No RFPs found" in result.output
    
    def test_cli_backup_command(self):
        """Test CLI backup command."""
        # Create some dummy data first
        dm = DataManager(self.temp_dir)
        rfps = [RFP(
            id="test_001",
            title="Test RFP",
            url="https://example.com/rfp/1",
            source_site="test",
            extracted_fields={},
            detected_at=datetime.now(),
            content_hash="hash",
            categories=["Test"]
        )]
        dm.save_rfps(rfps)
        
        result = self.runner.invoke(cli, ['--data-dir', self.temp_dir, 'backup'])
        assert result.exit_code == 0
        assert "Backup created" in result.output


class TestErrorHandlingWorkflows:
    """Test error handling and recovery workflows."""
    
    def setup_method(self):
        """Set up error testing environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_manager = DataManager(self.temp_dir)
    
    def teardown_method(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_corrupted_data_recovery(self):
        """Test recovery from corrupted data files."""
        # Create corrupted JSON file
        rfps_file = Path(self.temp_dir) / "rfps.json"
        with open(rfps_file, 'w') as f:
            f.write("{ invalid json }")
        
        # Should handle gracefully
        with pytest.raises(json.JSONDecodeError):
            self.data_manager.load_rfps()
        
        # Should still work without validation
        rfps = self.data_manager.load_rfps(validate=False)
        assert rfps == []  # Returns empty list when file is corrupted
    
    def test_missing_data_files(self):
        """Test handling of missing data files."""
        # Try to load from non-existent files
        rfps = self.data_manager.load_rfps()
        assert rfps == []
        
        sites = self.data_manager.load_site_configs()
        assert sites == []
        
        # Should still generate stats
        stats = self.data_manager.get_data_statistics()
        assert stats["rfps"]["total"] == 0
        assert stats["sites"]["total"] == 0
    
    def test_validation_error_handling(self):
        """Test handling of validation errors."""
        # Create RFP with invalid data
        invalid_rfp_data = {
            "id": "test_001",
            "title": "",  # Empty title should cause validation error
            "url": "not-a-valid-url",  # Invalid URL
            "source_site": "test",
            "extracted_fields": {"invalid_date": "not-a-date"},
            "detected_at": datetime.now().isoformat(),
            "content_hash": "hash",
            "categories": []
        }
        
        # Save invalid data
        rfps_file = Path(self.temp_dir) / "rfps.json"
        with open(rfps_file, 'w') as f:
            json.dump({"rfps": [invalid_rfp_data]}, f)
        
        # Loading with validation should skip invalid items
        rfps = self.data_manager.load_rfps(validate=True)
        assert len(rfps) == 0  # Invalid RFP should be skipped
        
        # Loading without validation should include all items
        rfps = self.data_manager.load_rfps(validate=False)
        assert len(rfps) == 1  # Invalid RFP included but may cause issues later


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
