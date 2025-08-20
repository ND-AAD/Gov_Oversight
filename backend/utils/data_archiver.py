"""
Data Archiving System for RFP Historical Data

Manages historical RFP data with efficient storage, compression, and retrieval.
Designed for transparency and long-term activist research needs.
"""

import json
import gzip
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Iterator
from pathlib import Path
from dataclasses import dataclass
import hashlib
import shutil

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.rfp import RFP
from models.serialization import DataManager

logger = logging.getLogger(__name__)


@dataclass
class ArchiveMetadata:
    """Metadata for archived RFP data."""
    archive_id: str
    created_at: datetime
    rfp_count: int
    source_file: str
    compression_ratio: float
    data_hash: str
    description: str
    tags: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "archive_id": self.archive_id,
            "created_at": self.created_at.isoformat(),
            "rfp_count": self.rfp_count,
            "source_file": self.source_file,
            "compression_ratio": self.compression_ratio,
            "data_hash": self.data_hash,
            "description": self.description,
            "tags": self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ArchiveMetadata':
        """Create from dictionary."""
        return cls(
            archive_id=data["archive_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            rfp_count=data["rfp_count"],
            source_file=data["source_file"],
            compression_ratio=data["compression_ratio"],
            data_hash=data["data_hash"],
            description=data["description"],
            tags=data["tags"]
        )


class DataArchiver:
    """
    Manages historical RFP data with compression and efficient storage.
    
    Features:
    - Compressed historical snapshots
    - Efficient data retrieval
    - Audit trail preservation
    - Surveillance-focused archiving
    - Research-friendly data export
    """
    
    def __init__(self, data_manager: DataManager):
        """
        Initialize DataArchiver.
        
        Args:
            data_manager: DataManager instance
        """
        self.data_manager = data_manager
        self.archive_dir = data_manager.data_dir / "archives"
        self.archive_dir.mkdir(exist_ok=True)
        
        self.metadata_file = self.archive_dir / "archive_metadata.json"
        self.max_archive_age_days = 365  # Keep archives for 1 year
        self.compression_level = 6  # Balance between compression and speed
    
    def create_daily_archive(self, rfps: List[RFP], tags: Optional[List[str]] = None) -> str:
        """
        Create a daily archive of RFP data.
        
        Args:
            rfps: List of RFPs to archive
            tags: Optional tags for categorizing the archive
            
        Returns:
            Archive ID of created archive
        """
        if not rfps:
            logger.warning("No RFPs provided for archiving")
            return ""
        
        timestamp = datetime.now()
        archive_id = f"daily_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        
        # Create archive data structure
        archive_data = {
            "metadata": {
                "archive_id": archive_id,
                "created_at": timestamp.isoformat(),
                "archive_type": "daily_snapshot",
                "rfp_count": len(rfps),
                "generator": "LA 2028 RFP Monitor",
                "version": "1.0"
            },
            "rfps": [rfp.to_dict() for rfp in rfps],
            "statistics": self._generate_archive_statistics(rfps),
            "surveillance_summary": self._generate_surveillance_summary(rfps)
        }
        
        # Calculate data hash for integrity verification
        data_json = json.dumps(archive_data, sort_keys=True)
        data_hash = hashlib.sha256(data_json.encode()).hexdigest()
        
        # Compress and save archive
        archive_file = self.archive_dir / f"{archive_id}.json.gz"
        
        with gzip.open(archive_file, 'wt', encoding='utf-8', compresslevel=self.compression_level) as f:
            json.dump(archive_data, f, indent=2, ensure_ascii=False)
        
        # Calculate compression ratio
        original_size = len(data_json.encode())
        compressed_size = archive_file.stat().st_size
        compression_ratio = compressed_size / original_size if original_size > 0 else 1.0
        
        # Create metadata record
        metadata = ArchiveMetadata(
            archive_id=archive_id,
            created_at=timestamp,
            rfp_count=len(rfps),
            source_file=str(archive_file),
            compression_ratio=compression_ratio,
            data_hash=data_hash,
            description=f"Daily RFP snapshot - {len(rfps)} RFPs",
            tags=tags or ["daily", "snapshot"]
        )
        
        # Save metadata
        self._save_archive_metadata(metadata)
        
        logger.info(f"Created daily archive {archive_id} with {len(rfps)} RFPs "
                   f"(compression: {compression_ratio:.2%})")
        
        return archive_id
    
    def create_surveillance_archive(self, rfps: List[RFP]) -> str:
        """
        Create a specialized archive focusing on surveillance-related RFPs.
        
        Args:
            rfps: List of all RFPs (surveillance ones will be filtered)
            
        Returns:
            Archive ID of created surveillance archive
        """
        # Filter for surveillance-related RFPs
        surveillance_rfps = [
            rfp for rfp in rfps 
            if rfp.is_high_priority() or self._is_surveillance_related(rfp)
        ]
        
        if not surveillance_rfps:
            logger.info("No surveillance-related RFPs found for archiving")
            return ""
        
        timestamp = datetime.now()
        archive_id = f"surveillance_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        
        # Enhanced metadata for surveillance tracking
        archive_data = {
            "metadata": {
                "archive_id": archive_id,
                "created_at": timestamp.isoformat(),
                "archive_type": "surveillance_focused",
                "rfp_count": len(surveillance_rfps),
                "total_rfps_scanned": len(rfps),
                "surveillance_ratio": len(surveillance_rfps) / len(rfps),
                "generator": "LA 2028 RFP Monitor - Surveillance Tracker",
                "version": "1.0"
            },
            "rfps": [rfp.to_dict() for rfp in surveillance_rfps],
            "analysis": {
                "high_priority_count": len([rfp for rfp in surveillance_rfps if rfp.is_high_priority()]),
                "categories": self._analyze_surveillance_categories(surveillance_rfps),
                "agencies": self._analyze_issuing_agencies(surveillance_rfps),
                "total_value": self._calculate_total_value(surveillance_rfps),
                "timeline": self._analyze_timeline_patterns(surveillance_rfps)
            },
            "activist_intelligence": self._generate_activist_intelligence(surveillance_rfps)
        }
        
        # Save with special naming for surveillance archives
        archive_file = self.archive_dir / f"{archive_id}_SURVEILLANCE.json.gz"
        
        with gzip.open(archive_file, 'wt', encoding='utf-8', compresslevel=self.compression_level) as f:
            json.dump(archive_data, f, indent=2, ensure_ascii=False)
        
        # Calculate metadata
        data_json = json.dumps(archive_data, sort_keys=True)
        data_hash = hashlib.sha256(data_json.encode()).hexdigest()
        compression_ratio = archive_file.stat().st_size / len(data_json.encode())
        
        metadata = ArchiveMetadata(
            archive_id=archive_id,
            created_at=timestamp,
            rfp_count=len(surveillance_rfps),
            source_file=str(archive_file),
            compression_ratio=compression_ratio,
            data_hash=data_hash,
            description=f"Surveillance-focused archive - {len(surveillance_rfps)} concerning RFPs",
            tags=["surveillance", "high_priority", "activist_research"]
        )
        
        self._save_archive_metadata(metadata)
        
        logger.info(f"Created surveillance archive {archive_id} with {len(surveillance_rfps)} RFPs")
        return archive_id
    
    def load_archive(self, archive_id: str) -> Optional[List[RFP]]:
        """
        Load RFPs from a specific archive.
        
        Args:
            archive_id: ID of archive to load
            
        Returns:
            List of RFPs from archive, or None if not found
        """
        metadata = self._get_archive_metadata(archive_id)
        if not metadata:
            logger.error(f"Archive {archive_id} not found in metadata")
            return None
        
        archive_file = Path(metadata.source_file)
        if not archive_file.exists():
            logger.error(f"Archive file {archive_file} not found")
            return None
        
        try:
            with gzip.open(archive_file, 'rt', encoding='utf-8') as f:
                data = json.load(f)
            
            # Verify data integrity
            data_json = json.dumps(data, sort_keys=True)
            calculated_hash = hashlib.sha256(data_json.encode()).hexdigest()
            
            if calculated_hash != metadata.data_hash:
                logger.warning(f"Archive {archive_id} data integrity check failed")
            
            # Convert to RFP objects
            rfps = []
            for rfp_dict in data.get("rfps", []):
                try:
                    rfps.append(RFP.from_dict(rfp_dict))
                except Exception as e:
                    logger.warning(f"Failed to load RFP from archive: {e}")
            
            logger.info(f"Loaded {len(rfps)} RFPs from archive {archive_id}")
            return rfps
            
        except Exception as e:
            logger.error(f"Failed to load archive {archive_id}: {e}")
            return None
    
    def list_archives(self, tags: Optional[List[str]] = None, 
                     days_back: Optional[int] = None) -> List[ArchiveMetadata]:
        """
        List available archives with optional filtering.
        
        Args:
            tags: Filter by tags (if provided)
            days_back: Only include archives from last N days
            
        Returns:
            List of ArchiveMetadata objects
        """
        all_metadata = self._load_all_archive_metadata()
        
        filtered = all_metadata
        
        # Filter by date
        if days_back:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            filtered = [m for m in filtered if m.created_at >= cutoff_date]
        
        # Filter by tags
        if tags:
            filtered = [
                m for m in filtered 
                if any(tag in m.tags for tag in tags)
            ]
        
        # Sort by creation date (newest first)
        filtered.sort(key=lambda m: m.created_at, reverse=True)
        
        return filtered
    
    def cleanup_old_archives(self) -> int:
        """
        Clean up archives older than max_archive_age_days.
        
        Returns:
            Number of archives removed
        """
        cutoff_date = datetime.now() - timedelta(days=self.max_archive_age_days)
        all_metadata = self._load_all_archive_metadata()
        
        removed_count = 0
        remaining_metadata = []
        
        for metadata in all_metadata:
            if metadata.created_at < cutoff_date:
                # Remove archive file
                archive_file = Path(metadata.source_file)
                if archive_file.exists():
                    archive_file.unlink()
                    logger.info(f"Removed old archive: {metadata.archive_id}")
                    removed_count += 1
            else:
                remaining_metadata.append(metadata)
        
        # Update metadata file
        self._save_all_archive_metadata(remaining_metadata)
        
        logger.info(f"Cleaned up {removed_count} old archives")
        return removed_count
    
    def export_research_data(self, start_date: datetime, end_date: datetime, 
                           surveillance_only: bool = False) -> Dict[str, Any]:
        """
        Export data for activist research over a date range.
        
        Args:
            start_date: Start of date range
            end_date: End of date range
            surveillance_only: Only include surveillance-related RFPs
            
        Returns:
            Research data dictionary
        """
        relevant_archives = [
            metadata for metadata in self._load_all_archive_metadata()
            if start_date <= metadata.created_at <= end_date
        ]
        
        all_rfps = []
        for metadata in relevant_archives:
            rfps = self.load_archive(metadata.archive_id)
            if rfps:
                all_rfps.extend(rfps)
        
        # Remove duplicates by ID
        unique_rfps = {rfp.id: rfp for rfp in all_rfps}.values()
        
        # Filter for surveillance if requested
        if surveillance_only:
            unique_rfps = [rfp for rfp in unique_rfps if self._is_surveillance_related(rfp)]
        
        research_data = {
            "export_metadata": {
                "generated_at": datetime.now().isoformat(),
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "surveillance_only": surveillance_only,
                "archives_included": len(relevant_archives),
                "total_rfps": len(unique_rfps)
            },
            "rfps": [rfp.to_dict() for rfp in unique_rfps],
            "analysis": {
                "surveillance_analysis": self._generate_surveillance_summary(unique_rfps),
                "agency_breakdown": self._analyze_issuing_agencies(unique_rfps),
                "value_analysis": self._analyze_contract_values(unique_rfps),
                "timeline_analysis": self._analyze_timeline_patterns(unique_rfps)
            },
            "research_notes": self._generate_research_notes(unique_rfps, start_date, end_date)
        }
        
        return research_data
    
    def _generate_archive_statistics(self, rfps: List[RFP]) -> Dict[str, Any]:
        """Generate statistical summary of RFPs for archive."""
        return {
            "total_rfps": len(rfps),
            "high_priority": len([rfp for rfp in rfps if rfp.is_high_priority()]),
            "closing_soon": len([rfp for rfp in rfps if rfp.is_closing_soon()]),
            "by_source": {
                site: len([rfp for rfp in rfps if rfp.source_site == site])
                for site in set(rfp.source_site for rfp in rfps)
            },
            "by_category": {
                category: len([rfp for rfp in rfps if category in rfp.categories])
                for category in set(cat for rfp in rfps for cat in rfp.categories)
            }
        }
    
    def _generate_surveillance_summary(self, rfps: List[RFP]) -> Dict[str, Any]:
        """Generate surveillance-focused summary."""
        surveillance_rfps = [rfp for rfp in rfps if self._is_surveillance_related(rfp)]
        
        return {
            "total_surveillance_rfps": len(surveillance_rfps),
            "surveillance_ratio": len(surveillance_rfps) / len(rfps) if rfps else 0,
            "surveillance_categories": self._analyze_surveillance_categories(surveillance_rfps),
            "concerning_agencies": self._identify_concerning_agencies(surveillance_rfps),
            "total_surveillance_value": self._calculate_total_value(surveillance_rfps),
            "urgent_surveillance": len([
                rfp for rfp in surveillance_rfps 
                if rfp.is_closing_soon(days=7)
            ])
        }
    
    def _analyze_surveillance_categories(self, rfps: List[RFP]) -> Dict[str, int]:
        """Analyze surveillance categories in RFPs."""
        surveillance_keywords = {
            "facial_recognition": ["facial recognition", "face recognition", "biometric"],
            "tracking": ["tracking", "location", "gps", "surveillance"],
            "monitoring": ["monitoring", "watch", "observe", "intelligence"],
            "data_collection": ["data collection", "analytics", "database"],
            "security_cameras": ["camera", "cctv", "video surveillance"],
            "social_media": ["social media", "online monitoring", "digital surveillance"]
        }
        
        categories = {}
        for category, keywords in surveillance_keywords.items():
            count = 0
            for rfp in rfps:
                text = f"{rfp.title} {rfp.extracted_fields.get('description', '')}".lower()
                if any(keyword in text for keyword in keywords):
                    count += 1
            categories[category] = count
        
        return categories
    
    def _analyze_issuing_agencies(self, rfps: List[RFP]) -> Dict[str, int]:
        """Analyze which agencies are issuing RFPs."""
        agencies = {}
        for rfp in rfps:
            agency = rfp.extracted_fields.get('issuer', 'Unknown')
            agencies[agency] = agencies.get(agency, 0) + 1
        
        return dict(sorted(agencies.items(), key=lambda x: x[1], reverse=True))
    
    def _calculate_total_value(self, rfps: List[RFP]) -> float:
        """Calculate total contract value from RFPs."""
        total = 0.0
        for rfp in rfps:
            value_str = rfp.extracted_fields.get('contract_value', '')
            if value_str:
                try:
                    # Extract numeric value from string like "$1,500,000"
                    numeric_str = ''.join(c for c in value_str if c.isdigit() or c == '.')
                    if numeric_str:
                        total += float(numeric_str)
                except ValueError:
                    pass
        
        return total
    
    def _analyze_timeline_patterns(self, rfps: List[RFP]) -> Dict[str, Any]:
        """Analyze timeline patterns in RFPs."""
        if not rfps:
            return {}
        
        posting_dates = []
        for rfp in rfps:
            try:
                posting_dates.append(datetime.fromisoformat(rfp.posted_date.replace('Z', '+00:00')))
            except:
                pass
        
        if not posting_dates:
            return {}
        
        posting_dates.sort()
        
        return {
            "earliest_rfp": posting_dates[0].isoformat(),
            "latest_rfp": posting_dates[-1].isoformat(),
            "posting_span_days": (posting_dates[-1] - posting_dates[0]).days,
            "average_per_month": len(posting_dates) / max(1, (posting_dates[-1] - posting_dates[0]).days / 30)
        }
    
    def _analyze_contract_values(self, rfps: List[RFP]) -> Dict[str, Any]:
        """Analyze contract value patterns."""
        values = []
        for rfp in rfps:
            value_str = rfp.extracted_fields.get('contract_value', '')
            if value_str:
                try:
                    numeric_str = ''.join(c for c in value_str if c.isdigit() or c == '.')
                    if numeric_str:
                        values.append(float(numeric_str))
                except ValueError:
                    pass
        
        if not values:
            return {"total_analyzed": 0}
        
        values.sort()
        
        return {
            "total_analyzed": len(values),
            "total_value": sum(values),
            "average_value": sum(values) / len(values),
            "median_value": values[len(values) // 2],
            "largest_contract": max(values),
            "smallest_contract": min(values)
        }
    
    def _is_surveillance_related(self, rfp: RFP) -> bool:
        """Check if RFP is surveillance-related."""
        surveillance_keywords = [
            'surveillance', 'monitoring', 'facial recognition', 'biometric',
            'security camera', 'tracking', 'intelligence', 'analytics',
            'predictive policing', 'crowd control', 'social media monitoring'
        ]
        
        text = f"{rfp.title} {rfp.extracted_fields.get('description', '')}".lower()
        return any(keyword in text for keyword in surveillance_keywords)
    
    def _identify_concerning_agencies(self, rfps: List[RFP]) -> List[str]:
        """Identify agencies with high surveillance RFP activity."""
        agency_counts = self._analyze_issuing_agencies(rfps)
        # Return agencies with more than 2 surveillance RFPs
        return [agency for agency, count in agency_counts.items() if count > 2]
    
    def _generate_activist_intelligence(self, rfps: List[RFP]) -> Dict[str, Any]:
        """Generate intelligence summary for activist use."""
        return {
            "key_concerns": self._identify_key_concerns(rfps),
            "action_items": self._generate_action_items(rfps),
            "research_priorities": self._identify_research_priorities(rfps),
            "media_angles": self._suggest_media_angles(rfps)
        }
    
    def _identify_key_concerns(self, rfps: List[RFP]) -> List[str]:
        """Identify key concerns from surveillance RFPs."""
        concerns = []
        
        facial_recognition_count = len([
            rfp for rfp in rfps 
            if 'facial recognition' in f"{rfp.title} {rfp.extracted_fields.get('description', '')}".lower()
        ])
        if facial_recognition_count > 0:
            concerns.append(f"Facial recognition technology in {facial_recognition_count} RFPs")
        
        high_value_surveillance = [
            rfp for rfp in rfps 
            if self._calculate_total_value([rfp]) > 1000000  # $1M+
        ]
        if high_value_surveillance:
            concerns.append(f"{len(high_value_surveillance)} high-value surveillance contracts")
        
        return concerns
    
    def _generate_action_items(self, rfps: List[RFP]) -> List[str]:
        """Generate action items for activists."""
        actions = []
        
        closing_soon = [rfp for rfp in rfps if rfp.is_closing_soon(days=14)]
        if closing_soon:
            actions.append(f"Monitor {len(closing_soon)} RFPs closing within 2 weeks")
        
        high_priority = [rfp for rfp in rfps if rfp.is_high_priority()]
        if high_priority:
            actions.append(f"Investigate {len(high_priority)} high-priority surveillance RFPs")
        
        return actions
    
    def _identify_research_priorities(self, rfps: List[RFP]) -> List[str]:
        """Identify research priorities based on RFP data."""
        priorities = []
        
        agency_counts = self._analyze_issuing_agencies(rfps)
        top_agencies = list(agency_counts.keys())[:3]
        
        for agency in top_agencies:
            priorities.append(f"Research {agency} surveillance capabilities and history")
        
        return priorities
    
    def _suggest_media_angles(self, rfps: List[RFP]) -> List[str]:
        """Suggest media angles based on RFP content."""
        angles = []
        
        total_value = self._calculate_total_value(rfps)
        if total_value > 0:
            angles.append(f"Olympic surveillance spending: ${total_value:,.0f} in contracts")
        
        if len(rfps) > 10:
            angles.append(f"LA 2028 driving surveillance expansion: {len(rfps)} concerning contracts")
        
        return angles
    
    def _generate_research_notes(self, rfps: List[RFP], start_date: datetime, 
                                end_date: datetime) -> Dict[str, Any]:
        """Generate research notes for exported data."""
        return {
            "data_quality": {
                "completeness": "High - all available RFPs included",
                "reliability": "Government sources only",
                "limitations": "Limited to publicly posted RFPs"
            },
            "research_methodology": {
                "data_collection": "Automated web scraping of government RFP sites",
                "filtering": "Olympic 2028 related contracts with surveillance focus",
                "verification": "Manual review of high-priority contracts"
            },
            "recommended_analysis": [
                "Timeline analysis of surveillance contract posting patterns",
                "Agency-by-agency spending breakdown",
                "Technology type categorization and risk assessment",
                "Public comment opportunity identification"
            ]
        }
    
    def _save_archive_metadata(self, metadata: ArchiveMetadata) -> None:
        """Save archive metadata to metadata file."""
        all_metadata = self._load_all_archive_metadata()
        all_metadata.append(metadata)
        self._save_all_archive_metadata(all_metadata)
    
    def _load_all_archive_metadata(self) -> List[ArchiveMetadata]:
        """Load all archive metadata."""
        if not self.metadata_file.exists():
            return []
        
        try:
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            metadata_list = []
            for item in data.get("archives", []):
                try:
                    metadata_list.append(ArchiveMetadata.from_dict(item))
                except Exception as e:
                    logger.warning(f"Failed to load archive metadata: {e}")
            
            return metadata_list
            
        except Exception as e:
            logger.error(f"Failed to load archive metadata: {e}")
            return []
    
    def _save_all_archive_metadata(self, metadata_list: List[ArchiveMetadata]) -> None:
        """Save all archive metadata."""
        try:
            data = {
                "metadata": {
                    "last_updated": datetime.now().isoformat(),
                    "total_archives": len(metadata_list),
                    "version": "1.0"
                },
                "archives": [metadata.to_dict() for metadata in metadata_list]
            }
            
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Failed to save archive metadata: {e}")
            raise
    
    def _get_archive_metadata(self, archive_id: str) -> Optional[ArchiveMetadata]:
        """Get metadata for specific archive."""
        all_metadata = self._load_all_archive_metadata()
        for metadata in all_metadata:
            if metadata.archive_id == archive_id:
                return metadata
        return None
