"""
Change Detection System for RFP Monitoring

Tracks changes in RFP data and generates alerts for significant modifications
that activists should be aware of (status changes, closing dates, etc.).
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.rfp import RFP
from models.serialization import DataManager

logger = logging.getLogger(__name__)


class ChangeType(Enum):
    """Types of changes that can occur in RFP data."""
    NEW_RFP = "new_rfp"
    STATUS_CHANGE = "status_change"
    CLOSING_DATE_CHANGE = "closing_date_change"
    CONTENT_UPDATE = "content_update"
    VALUE_CHANGE = "value_change"
    CATEGORY_CHANGE = "category_change"
    REMOVED_RFP = "removed_rfp"
    URGENT_DEADLINE = "urgent_deadline"


class ChangeSeverity(Enum):
    """Severity levels for change notifications."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ChangeRecord:
    """Represents a detected change in RFP data."""
    change_id: str
    rfp_id: str
    rfp_title: str
    change_type: ChangeType
    severity: ChangeSeverity
    old_value: Any
    new_value: Any
    field_name: str
    detected_at: datetime
    source_site: str
    description: str
    action_required: bool = False
    activist_notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ChangeRecord to dictionary for JSON serialization."""
        return {
            "change_id": self.change_id,
            "rfp_id": self.rfp_id,
            "rfp_title": self.rfp_title,
            "change_type": self.change_type.value,
            "severity": self.severity.value,
            "old_value": str(self.old_value) if self.old_value is not None else None,
            "new_value": str(self.new_value) if self.new_value is not None else None,
            "field_name": self.field_name,
            "detected_at": self.detected_at.isoformat(),
            "source_site": self.source_site,
            "description": self.description,
            "action_required": self.action_required,
            "activist_notes": self.activist_notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChangeRecord':
        """Create ChangeRecord from dictionary."""
        return cls(
            change_id=data["change_id"],
            rfp_id=data["rfp_id"],
            rfp_title=data["rfp_title"],
            change_type=ChangeType(data["change_type"]),
            severity=ChangeSeverity(data["severity"]),
            old_value=data.get("old_value"),
            new_value=data.get("new_value"),
            field_name=data["field_name"],
            detected_at=datetime.fromisoformat(data["detected_at"].replace('Z', '+00:00')),
            source_site=data["source_site"],
            description=data["description"],
            action_required=data.get("action_required", False),
            activist_notes=data.get("activist_notes", "")
        )


class ChangeDetector:
    """
    Detects and tracks changes in RFP data for activist monitoring.
    
    Key features:
    - Detects new RFPs, status changes, deadline changes
    - Prioritizes surveillance/security-related changes
    - Generates alerts for urgent changes (closing soon, etc.)
    - Maintains change history for audit trail
    """
    
    def __init__(self, data_manager: DataManager):
        """
        Initialize ChangeDetector with data manager.
        
        Args:
            data_manager: DataManager instance for loading/saving data
        """
        self.data_manager = data_manager
        self.changes_file = data_manager.data_dir / "changes.json"
        self.snapshot_dir = data_manager.data_dir / "snapshots"
        self.snapshot_dir.mkdir(exist_ok=True)
        
        # Critical fields that should trigger high-priority alerts
        self.critical_fields = {
            'status', 'closing_date', 'contract_value', 'issuer'
        }
        
        # Olympic surveillance keywords for enhanced monitoring
        self.surveillance_keywords = [
            'surveillance', 'monitoring', 'facial recognition', 'biometric',
            'security camera', 'tracking', 'intelligence', 'analytics',
            'predictive policing', 'crowd control', 'social media monitoring',
            'license plate reader', 'cell site simulator', 'stingray'
        ]
    
    def create_snapshot(self, rfps: List[RFP]) -> str:
        """
        Create a timestamped snapshot of current RFP data.
        
        Args:
            rfps: List of current RFPs
            
        Returns:
            Path to created snapshot file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_file = self.snapshot_dir / f"snapshot_{timestamp}.json"
        
        snapshot_data = {
            "timestamp": datetime.now().isoformat(),
            "total_rfps": len(rfps),
            "rfps": [rfp.to_dict() for rfp in rfps]
        }
        
        with open(snapshot_file, 'w', encoding='utf-8') as f:
            json.dump(snapshot_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Created snapshot with {len(rfps)} RFPs: {snapshot_file}")
        return str(snapshot_file)
    
    def load_latest_snapshot(self) -> Optional[List[RFP]]:
        """
        Load the most recent snapshot for comparison.
        
        Returns:
            List of RFPs from latest snapshot, or None if no snapshot exists
        """
        snapshot_files = list(self.snapshot_dir.glob("snapshot_*.json"))
        if not snapshot_files:
            return None
        
        # Get most recent snapshot
        latest_snapshot = max(snapshot_files, key=lambda f: f.stat().st_mtime)
        
        try:
            with open(latest_snapshot, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            rfps = []
            for rfp_dict in data.get("rfps", []):
                try:
                    rfps.append(RFP.from_dict(rfp_dict))
                except Exception as e:
                    logger.warning(f"Failed to load RFP from snapshot: {e}")
            
            logger.info(f"Loaded {len(rfps)} RFPs from snapshot: {latest_snapshot}")
            return rfps
            
        except Exception as e:
            logger.error(f"Failed to load snapshot {latest_snapshot}: {e}")
            return None
    
    def detect_changes(self, current_rfps: List[RFP], 
                      previous_rfps: Optional[List[RFP]] = None) -> List[ChangeRecord]:
        """
        Detect changes between current and previous RFP data.
        
        Args:
            current_rfps: Current list of RFPs
            previous_rfps: Previous list of RFPs (loads from snapshot if None)
            
        Returns:
            List of detected ChangeRecord objects
        """
        if previous_rfps is None:
            previous_rfps = self.load_latest_snapshot()
            if previous_rfps is None:
                logger.info("No previous snapshot found - all RFPs will be marked as new")
                previous_rfps = []
        
        changes = []
        
        # Create lookup dictionaries for efficient comparison
        current_by_id = {rfp.id: rfp for rfp in current_rfps}
        previous_by_id = {rfp.id: rfp for rfp in previous_rfps}
        
        # Detect new RFPs
        new_rfp_ids = set(current_by_id.keys()) - set(previous_by_id.keys())
        for rfp_id in new_rfp_ids:
            rfp = current_by_id[rfp_id]
            severity = self._assess_rfp_severity(rfp)
            
            change = ChangeRecord(
                change_id=f"new_{rfp_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                rfp_id=rfp.id,
                rfp_title=rfp.title,
                change_type=ChangeType.NEW_RFP,
                severity=severity,
                old_value=None,
                new_value="New RFP discovered",
                field_name="rfp_status",
                detected_at=datetime.now(),
                source_site=rfp.source_site,
                description=f"New RFP discovered: {rfp.title}",
                action_required=severity in [ChangeSeverity.HIGH, ChangeSeverity.CRITICAL]
            )
            changes.append(change)
        
        # Detect removed RFPs
        removed_rfp_ids = set(previous_by_id.keys()) - set(current_by_id.keys())
        for rfp_id in removed_rfp_ids:
            rfp = previous_by_id[rfp_id]
            
            change = ChangeRecord(
                change_id=f"removed_{rfp_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                rfp_id=rfp.id,
                rfp_title=rfp.title,
                change_type=ChangeType.REMOVED_RFP,
                severity=ChangeSeverity.MEDIUM,
                old_value="Active",
                new_value="Removed",
                field_name="rfp_status",
                detected_at=datetime.now(),
                source_site=rfp.source_site,
                description=f"RFP no longer available: {rfp.title}",
                action_required=rfp.is_high_priority()
            )
            changes.append(change)
        
        # Detect changes in existing RFPs
        common_rfp_ids = set(current_by_id.keys()) & set(previous_by_id.keys())
        for rfp_id in common_rfp_ids:
            current_rfp = current_by_id[rfp_id]
            previous_rfp = previous_by_id[rfp_id]
            
            rfp_changes = self._compare_rfps(current_rfp, previous_rfp)
            changes.extend(rfp_changes)
        
        # Detect urgent deadlines (closing within 48 hours)
        urgent_changes = self._detect_urgent_deadlines(current_rfps)
        changes.extend(urgent_changes)
        
        logger.info(f"Detected {len(changes)} total changes")
        return changes
    
    def _compare_rfps(self, current: RFP, previous: RFP) -> List[ChangeRecord]:
        """
        Compare two RFP objects and detect specific field changes.
        
        Args:
            current: Current RFP state
            previous: Previous RFP state
            
        Returns:
            List of ChangeRecord objects for detected changes
        """
        changes = []
        
        # Check content hash for overall changes
        if current.content_hash != previous.content_hash:
            # Detailed field-by-field comparison
            field_changes = self._compare_extracted_fields(
                current.extracted_fields, 
                previous.extracted_fields,
                current
            )
            changes.extend(field_changes)
        
        # Check specific critical fields
        critical_changes = self._check_critical_field_changes(current, previous)
        changes.extend(critical_changes)
        
        # Check category changes (especially surveillance-related)
        if set(current.categories) != set(previous.categories):
            change = ChangeRecord(
                change_id=f"cat_{current.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                rfp_id=current.id,
                rfp_title=current.title,
                change_type=ChangeType.CATEGORY_CHANGE,
                severity=ChangeSeverity.MEDIUM,
                old_value=previous.categories,
                new_value=current.categories,
                field_name="categories",
                detected_at=datetime.now(),
                source_site=current.source_site,
                description=f"Categories changed: {previous.categories} → {current.categories}",
                action_required=any(cat in ['surveillance', 'security'] for cat in current.categories)
            )
            changes.append(change)
        
        return changes
    
    def _compare_extracted_fields(self, current_fields: Dict[str, Any], 
                                 previous_fields: Dict[str, Any], 
                                 rfp: RFP) -> List[ChangeRecord]:
        """
        Compare extracted fields between RFP versions.
        
        Args:
            current_fields: Current extracted fields
            previous_fields: Previous extracted fields
            rfp: RFP object for context
            
        Returns:
            List of ChangeRecord objects
        """
        changes = []
        
        # Check all fields present in either version
        all_fields = set(current_fields.keys()) | set(previous_fields.keys())
        
        for field_name in all_fields:
            current_value = current_fields.get(field_name)
            previous_value = previous_fields.get(field_name)
            
            if current_value != previous_value:
                # Determine severity based on field importance
                severity = ChangeSeverity.LOW
                if field_name in self.critical_fields:
                    severity = ChangeSeverity.HIGH
                elif field_name in ['description', 'title']:
                    severity = ChangeSeverity.MEDIUM
                
                # Special handling for surveillance-related content
                if self._contains_surveillance_keywords(str(current_value)):
                    severity = ChangeSeverity.HIGH
                
                change = ChangeRecord(
                    change_id=f"field_{rfp.id}_{field_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    rfp_id=rfp.id,
                    rfp_title=rfp.title,
                    change_type=ChangeType.CONTENT_UPDATE,
                    severity=severity,
                    old_value=previous_value,
                    new_value=current_value,
                    field_name=field_name,
                    detected_at=datetime.now(),
                    source_site=rfp.source_site,
                    description=f"Field '{field_name}' changed: {previous_value} → {current_value}",
                    action_required=severity == ChangeSeverity.HIGH
                )
                changes.append(change)
        
        return changes
    
    def _check_critical_field_changes(self, current: RFP, previous: RFP) -> List[ChangeRecord]:
        """
        Check for changes in critical fields that require immediate attention.
        
        Args:
            current: Current RFP state
            previous: Previous RFP state
            
        Returns:
            List of ChangeRecord objects for critical changes
        """
        changes = []
        
        # Status changes
        current_status = current.extracted_fields.get('status', '')
        previous_status = previous.extracted_fields.get('status', '')
        
        if current_status != previous_status:
            severity = ChangeSeverity.HIGH
            if current_status.lower() in ['cancelled', 'withdrawn', 'awarded']:
                severity = ChangeSeverity.CRITICAL
            
            change = ChangeRecord(
                change_id=f"status_{current.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                rfp_id=current.id,
                rfp_title=current.title,
                change_type=ChangeType.STATUS_CHANGE,
                severity=severity,
                old_value=previous_status,
                new_value=current_status,
                field_name="status",
                detected_at=datetime.now(),
                source_site=current.source_site,
                description=f"RFP status changed: {previous_status} → {current_status}",
                action_required=True
            )
            changes.append(change)
        
        # Closing date changes
        current_closing = current.extracted_fields.get('closing_date')
        previous_closing = previous.extracted_fields.get('closing_date')
        
        if current_closing != previous_closing:
            severity = ChangeSeverity.HIGH
            
            # If new deadline is very soon, make it critical
            if current_closing and current.is_closing_soon(days=2):
                severity = ChangeSeverity.CRITICAL
            
            change = ChangeRecord(
                change_id=f"deadline_{current.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                rfp_id=current.id,
                rfp_title=current.title,
                change_type=ChangeType.CLOSING_DATE_CHANGE,
                severity=severity,
                old_value=previous_closing,
                new_value=current_closing,
                field_name="closing_date",
                detected_at=datetime.now(),
                source_site=current.source_site,
                description=f"Closing date changed: {previous_closing} → {current_closing}",
                action_required=True
            )
            changes.append(change)
        
        return changes
    
    def _detect_urgent_deadlines(self, rfps: List[RFP]) -> List[ChangeRecord]:
        """
        Detect RFPs with urgent deadlines (closing very soon).
        
        Args:
            rfps: List of RFPs to check
            
        Returns:
            List of ChangeRecord objects for urgent deadlines
        """
        changes = []
        
        for rfp in rfps:
            if rfp.is_closing_soon(days=2):  # 48 hours
                severity = ChangeSeverity.CRITICAL if rfp.is_high_priority() else ChangeSeverity.HIGH
                
                change = ChangeRecord(
                    change_id=f"urgent_{rfp.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    rfp_id=rfp.id,
                    rfp_title=rfp.title,
                    change_type=ChangeType.URGENT_DEADLINE,
                    severity=severity,
                    old_value=None,
                    new_value=rfp.extracted_fields.get('closing_date'),
                    field_name="closing_date",
                    detected_at=datetime.now(),
                    source_site=rfp.source_site,
                    description=f"URGENT: RFP closing within 48 hours - {rfp.extracted_fields.get('closing_date')}",
                    action_required=True
                )
                changes.append(change)
        
        return changes
    
    def _assess_rfp_severity(self, rfp: RFP) -> ChangeSeverity:
        """
        Assess the severity level of an RFP for alert prioritization.
        
        Args:
            rfp: RFP to assess
            
        Returns:
            ChangeSeverity level
        """
        if rfp.is_high_priority():
            return ChangeSeverity.HIGH
        
        # Check for surveillance keywords
        text_to_check = f"{rfp.title} {rfp.extracted_fields.get('description', '')}"
        if self._contains_surveillance_keywords(text_to_check):
            return ChangeSeverity.HIGH
        
        # Check if closing soon
        if rfp.is_closing_soon(days=7):
            return ChangeSeverity.MEDIUM
        
        return ChangeSeverity.LOW
    
    def _contains_surveillance_keywords(self, text: str) -> bool:
        """
        Check if text contains surveillance-related keywords.
        
        Args:
            text: Text to check
            
        Returns:
            True if surveillance keywords found
        """
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.surveillance_keywords)
    
    def save_changes(self, changes: List[ChangeRecord]) -> None:
        """
        Save change records to the changes file.
        
        Args:
            changes: List of ChangeRecord objects to save
        """
        if not changes:
            logger.info("No changes to save")
            return
        
        # Load existing changes
        existing_changes = self.load_changes()
        
        # Add new changes
        all_changes = existing_changes + changes
        
        # Keep only recent changes (last 30 days)
        cutoff_date = datetime.now() - timedelta(days=30)
        recent_changes = [
            change for change in all_changes 
            if change.detected_at >= cutoff_date
        ]
        
        # Save to file
        try:
            changes_data = {
                "metadata": {
                    "last_updated": datetime.now().isoformat(),
                    "total_changes": len(recent_changes),
                    "version": "1.0"
                },
                "changes": [change.to_dict() for change in recent_changes]
            }
            
            with open(self.changes_file, 'w', encoding='utf-8') as f:
                json.dump(changes_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(changes)} new changes, {len(recent_changes)} total")
            
        except Exception as e:
            logger.error(f"Failed to save changes: {e}")
            raise
    
    def load_changes(self) -> List[ChangeRecord]:
        """
        Load all change records from the changes file.
        
        Returns:
            List of ChangeRecord objects
        """
        if not self.changes_file.exists():
            return []
        
        try:
            with open(self.changes_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            changes = []
            change_dicts = data.get("changes", [])
            
            for change_dict in change_dicts:
                try:
                    changes.append(ChangeRecord.from_dict(change_dict))
                except Exception as e:
                    logger.warning(f"Failed to load change record: {e}")
            
            logger.info(f"Loaded {len(changes)} change records")
            return changes
            
        except Exception as e:
            logger.error(f"Failed to load changes: {e}")
            return []
    
    def get_changes_by_severity(self, severity: ChangeSeverity, 
                               days_back: int = 7) -> List[ChangeRecord]:
        """
        Get changes of a specific severity level from recent days.
        
        Args:
            severity: Severity level to filter by
            days_back: Number of days to look back
            
        Returns:
            List of ChangeRecord objects matching criteria
        """
        all_changes = self.load_changes()
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        return [
            change for change in all_changes
            if change.severity == severity and change.detected_at >= cutoff_date
        ]
    
    def get_action_required_changes(self, days_back: int = 7) -> List[ChangeRecord]:
        """
        Get all changes that require activist action.
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            List of ChangeRecord objects requiring action
        """
        all_changes = self.load_changes()
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        return [
            change for change in all_changes
            if change.action_required and change.detected_at >= cutoff_date
        ]
    
    def generate_change_summary(self, days_back: int = 7) -> Dict[str, Any]:
        """
        Generate a summary of recent changes for reporting.
        
        Args:
            days_back: Number of days to include in summary
            
        Returns:
            Dictionary with change summary statistics
        """
        all_changes = self.load_changes()
        cutoff_date = datetime.now() - timedelta(days=days_back)
        recent_changes = [
            change for change in all_changes
            if change.detected_at >= cutoff_date
        ]
        
        return {
            "period_days": days_back,
            "total_changes": len(recent_changes),
            "by_severity": {
                "critical": len([c for c in recent_changes if c.severity == ChangeSeverity.CRITICAL]),
                "high": len([c for c in recent_changes if c.severity == ChangeSeverity.HIGH]),
                "medium": len([c for c in recent_changes if c.severity == ChangeSeverity.MEDIUM]),
                "low": len([c for c in recent_changes if c.severity == ChangeSeverity.LOW])
            },
            "by_type": {
                change_type.value: len([c for c in recent_changes if c.change_type == change_type])
                for change_type in ChangeType
            },
            "action_required": len([c for c in recent_changes if c.action_required]),
            "surveillance_related": len([
                c for c in recent_changes 
                if self._contains_surveillance_keywords(c.description)
            ]),
            "generated_at": datetime.now().isoformat()
        }
