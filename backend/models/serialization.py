"""Serialization helpers for managing RFP and SiteConfig data files."""

import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import shutil
import logging

from .rfp import RFP
from .site_config import SiteConfig
from .validation import validate_rfp_data, validate_site_config_data, ValidationResult


logger = logging.getLogger(__name__)


class DataManager:
    """Manages loading and saving of RFP and SiteConfig data to JSON files."""
    
    def __init__(self, data_dir: str = "data"):
        """
        Initialize DataManager with data directory path.
        
        Args:
            data_dir: Path to directory containing JSON data files
        """
        self.data_dir = Path(data_dir)
        self.rfps_file = self.data_dir / "rfps.json"
        self.sites_file = self.data_dir / "sites.json"
        self.ignored_file = self.data_dir / "ignored_rfps.json"
        self.history_dir = self.data_dir / "history"
        
        # Ensure directories exist
        self.data_dir.mkdir(exist_ok=True)
        self.history_dir.mkdir(exist_ok=True)
    
    def backup_data_files(self) -> str:
        """
        Create timestamped backup of all data files.
        
        Returns:
            Path to backup directory
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.history_dir / f"backup_{timestamp}"
        backup_dir.mkdir(exist_ok=True)
        
        # Backup each data file if it exists
        files_to_backup = [self.rfps_file, self.sites_file, self.ignored_file]
        
        for file_path in files_to_backup:
            if file_path.exists():
                shutil.copy2(file_path, backup_dir / file_path.name)
                logger.info(f"Backed up {file_path.name} to {backup_dir}")
        
        return str(backup_dir)
    
    def load_rfps(self, validate: bool = True) -> List[RFP]:
        """
        Load all RFPs from the JSON file.
        
        Args:
            validate: Whether to validate loaded data
            
        Returns:
            List of RFP objects
            
        Raises:
            FileNotFoundError: If RFPs file doesn't exist
            json.JSONDecodeError: If file contains invalid JSON
            ValueError: If validation fails and validate=True
        """
        if not self.rfps_file.exists():
            logger.warning(f"RFPs file not found: {self.rfps_file}")
            return []
        
        try:
            with open(self.rfps_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle different JSON structures
            if isinstance(data, list):
                rfp_dicts = data
            elif isinstance(data, dict) and 'rfps' in data:
                rfp_dicts = data['rfps']
            else:
                raise ValueError("Invalid RFPs file structure")
            
            rfps = []
            for i, rfp_dict in enumerate(rfp_dicts):
                try:
                    if validate:
                        validation_result = validate_rfp_data(rfp_dict)
                        if not validation_result.is_valid:
                            logger.warning(f"RFP {i} validation failed: {validation_result.errors}")
                            if validate:  # Skip invalid RFPs if validation is required
                                continue
                    
                    rfp = RFP.from_dict(rfp_dict)
                    rfps.append(rfp)
                    
                except Exception as e:
                    logger.error(f"Failed to load RFP {i}: {e}")
                    if validate:
                        continue  # Skip this RFP
                    else:
                        raise
            
            logger.info(f"Loaded {len(rfps)} RFPs from {self.rfps_file}")
            return rfps
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in RFPs file: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to load RFPs: {e}")
            raise
    
    def save_rfps(self, rfps: List[RFP], backup: bool = True) -> None:
        """
        Save RFPs to the JSON file.
        
        Args:
            rfps: List of RFP objects to save
            backup: Whether to create backup before saving
            
        Raises:
            OSError: If file cannot be written
        """
        if backup and self.rfps_file.exists():
            self.backup_data_files()
        
        try:
            # Convert RFPs to dictionaries
            rfp_dicts = [rfp.to_dict() for rfp in rfps]
            
            # Create structured JSON with metadata
            data = {
                "metadata": {
                    "last_updated": datetime.now().isoformat(),
                    "total_rfps": len(rfps),
                    "version": "1.0"
                },
                "rfps": rfp_dicts
            }
            
            # Write to temporary file first, then rename (atomic operation)
            temp_file = self.rfps_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Atomic rename
            temp_file.rename(self.rfps_file)
            
            logger.info(f"Saved {len(rfps)} RFPs to {self.rfps_file}")
            
        except Exception as e:
            logger.error(f"Failed to save RFPs: {e}")
            # Clean up temporary file if it exists
            temp_file = self.rfps_file.with_suffix('.tmp')
            if temp_file.exists():
                temp_file.unlink()
            raise
    
    def load_site_configs(self, validate: bool = True) -> List[SiteConfig]:
        """
        Load all site configurations from the JSON file.
        
        Args:
            validate: Whether to validate loaded data
            
        Returns:
            List of SiteConfig objects
        """
        if not self.sites_file.exists():
            logger.warning(f"Sites file not found: {self.sites_file}")
            return []
        
        try:
            with open(self.sites_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle different JSON structures
            if isinstance(data, list):
                site_dicts = data
            elif isinstance(data, dict) and 'sites' in data:
                site_dicts = data['sites']
            else:
                raise ValueError("Invalid sites file structure")
            
            sites = []
            for i, site_dict in enumerate(site_dicts):
                try:
                    if validate:
                        validation_result = validate_site_config_data(site_dict)
                        if not validation_result.is_valid:
                            logger.warning(f"Site {i} validation failed: {validation_result.errors}")
                            if validate:
                                continue
                    
                    site = SiteConfig.from_dict(site_dict)
                    sites.append(site)
                    
                except Exception as e:
                    logger.error(f"Failed to load site config {i}: {e}")
                    if validate:
                        continue
                    else:
                        raise
            
            logger.info(f"Loaded {len(sites)} site configurations from {self.sites_file}")
            return sites
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in sites file: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to load site configurations: {e}")
            raise
    
    def save_site_configs(self, sites: List[SiteConfig], backup: bool = True) -> None:
        """
        Save site configurations to the JSON file.
        
        Args:
            sites: List of SiteConfig objects to save
            backup: Whether to create backup before saving
        """
        if backup and self.sites_file.exists():
            self.backup_data_files()
        
        try:
            # Convert sites to dictionaries
            site_dicts = [site.to_dict() for site in sites]
            
            # Create structured JSON with metadata
            data = {
                "metadata": {
                    "last_updated": datetime.now().isoformat(),
                    "total_sites": len(sites),
                    "version": "1.0"
                },
                "sites": site_dicts
            }
            
            # Write atomically
            temp_file = self.sites_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            temp_file.rename(self.sites_file)
            
            logger.info(f"Saved {len(sites)} site configurations to {self.sites_file}")
            
        except Exception as e:
            logger.error(f"Failed to save site configurations: {e}")
            temp_file = self.sites_file.with_suffix('.tmp')
            if temp_file.exists():
                temp_file.unlink()
            raise
    
    def add_rfp(self, rfp: RFP) -> None:
        """
        Add a single RFP to the data file.
        
        Args:
            rfp: RFP object to add
        """
        existing_rfps = self.load_rfps(validate=False)
        
        # Check for duplicates by ID or URL
        for existing in existing_rfps:
            if existing.id == rfp.id:
                logger.warning(f"RFP with ID {rfp.id} already exists, skipping")
                return
            if existing.url == rfp.url:
                logger.warning(f"RFP with URL {rfp.url} already exists, skipping")
                return
        
        existing_rfps.append(rfp)
        self.save_rfps(existing_rfps)
        logger.info(f"Added new RFP: {rfp.id}")
    
    def update_rfp(self, rfp: RFP) -> bool:
        """
        Update an existing RFP in the data file.
        
        Args:
            rfp: RFP object with updated data
            
        Returns:
            True if RFP was found and updated, False otherwise
        """
        existing_rfps = self.load_rfps(validate=False)
        
        for i, existing in enumerate(existing_rfps):
            if existing.id == rfp.id:
                existing_rfps[i] = rfp
                self.save_rfps(existing_rfps)
                logger.info(f"Updated RFP: {rfp.id}")
                return True
        
        logger.warning(f"RFP with ID {rfp.id} not found for update")
        return False
    
    def remove_rfp(self, rfp_id: str) -> bool:
        """
        Remove an RFP from the data file.
        
        Args:
            rfp_id: ID of RFP to remove
            
        Returns:
            True if RFP was found and removed, False otherwise
        """
        existing_rfps = self.load_rfps(validate=False)
        original_count = len(existing_rfps)
        
        existing_rfps = [rfp for rfp in existing_rfps if rfp.id != rfp_id]
        
        if len(existing_rfps) < original_count:
            self.save_rfps(existing_rfps)
            logger.info(f"Removed RFP: {rfp_id}")
            return True
        
        logger.warning(f"RFP with ID {rfp_id} not found for removal")
        return False
    
    def get_rfp_by_id(self, rfp_id: str) -> Optional[RFP]:
        """
        Get a specific RFP by ID.
        
        Args:
            rfp_id: ID of RFP to retrieve
            
        Returns:
            RFP object if found, None otherwise
        """
        rfps = self.load_rfps(validate=False)
        for rfp in rfps:
            if rfp.id == rfp_id:
                return rfp
        return None
    
    def get_rfps_by_site(self, site_id: str) -> List[RFP]:
        """
        Get all RFPs from a specific site.
        
        Args:
            site_id: ID of site to filter by
            
        Returns:
            List of RFP objects from the specified site
        """
        rfps = self.load_rfps(validate=False)
        return [rfp for rfp in rfps if rfp.source_site == site_id]
    
    def get_high_priority_rfps(self) -> List[RFP]:
        """
        Get all high-priority RFPs (surveillance/security related).
        
        Returns:
            List of high-priority RFP objects
        """
        rfps = self.load_rfps(validate=False)
        return [rfp for rfp in rfps if rfp.is_high_priority()]
    
    def get_closing_soon_rfps(self, days: int = 7) -> List[RFP]:
        """
        Get RFPs closing within specified number of days.
        
        Args:
            days: Number of days to look ahead
            
        Returns:
            List of RFP objects closing soon
        """
        rfps = self.load_rfps(validate=False)
        return [rfp for rfp in rfps if rfp.is_closing_soon(days)]
    
    def get_data_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the current data.
        
        Returns:
            Dictionary with data statistics
        """
        try:
            rfps = self.load_rfps(validate=False)
            sites = self.load_site_configs(validate=False)
            
            # RFP statistics
            total_rfps = len(rfps)
            high_priority = len([rfp for rfp in rfps if rfp.is_high_priority()])
            closing_soon = len([rfp for rfp in rfps if rfp.is_closing_soon()])
            
            # Site statistics
            total_sites = len(sites)
            active_sites = len([site for site in sites if site.is_healthy()])
            error_sites = len([site for site in sites if not site.is_healthy()])
            
            return {
                "rfps": {
                    "total": total_rfps,
                    "high_priority": high_priority,
                    "closing_soon": closing_soon
                },
                "sites": {
                    "total": total_sites,
                    "active": active_sites,
                    "errors": error_sites
                },
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate statistics: {e}")
            return {
                "error": str(e),
                "last_updated": datetime.now().isoformat()
            }
    
    def ignore_rfp(self, rfp_id: str) -> bool:
        """
        Move an RFP to the ignored list.
        
        Args:
            rfp_id: ID of RFP to ignore
            
        Returns:
            True if RFP was found and ignored, False otherwise
        """
        try:
            # Load current ignored RFPs
            ignored_rfps = self.load_ignored_rfps()
            
            # Check if already ignored
            if rfp_id in ignored_rfps:
                logger.warning(f"RFP {rfp_id} is already ignored")
                return True
            
            # Find the RFP to ignore
            rfp = self.get_rfp_by_id(rfp_id)
            if not rfp:
                logger.warning(f"RFP {rfp_id} not found for ignoring")
                return False
            
            # Add to ignored list
            ignored_rfps.append(rfp_id)
            self.save_ignored_rfps(ignored_rfps)
            
            # Optionally remove from main RFPs list (keep for audit trail)
            # self.remove_rfp(rfp_id)
            
            logger.info(f"Ignored RFP: {rfp_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to ignore RFP {rfp_id}: {e}")
            return False
    
    def load_ignored_rfps(self) -> List[str]:
        """
        Load list of ignored RFP IDs.
        
        Returns:
            List of ignored RFP IDs
        """
        if not self.ignored_file.exists():
            return []
        
        try:
            with open(self.ignored_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'ignored_rfps' in data:
                return data['ignored_rfps']
            else:
                return []
                
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Failed to load ignored RFPs: {e}")
            return []
    
    def save_ignored_rfps(self, ignored_rfp_ids: List[str]) -> None:
        """
        Save list of ignored RFP IDs.
        
        Args:
            ignored_rfp_ids: List of RFP IDs to mark as ignored
        """
        try:
            data = {
                "metadata": {
                    "last_updated": datetime.now().isoformat(),
                    "total_ignored": len(ignored_rfp_ids),
                    "version": "1.0"
                },
                "ignored_rfps": ignored_rfp_ids
            }
            
            with open(self.ignored_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(ignored_rfp_ids)} ignored RFPs to {self.ignored_file}")
            
        except Exception as e:
            logger.error(f"Failed to save ignored RFPs: {e}")
            raise