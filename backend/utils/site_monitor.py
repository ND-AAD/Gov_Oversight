"""
Site Health Monitoring System

Monitors government websites for availability, changes, and potential issues
that could affect RFP data collection for activist oversight.
"""

import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import json
import hashlib
import time

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.site_config import SiteConfig, SiteStatus
from models.serialization import DataManager
from models.validation import ValidationResult

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels for site monitoring."""
    HEALTHY = "healthy"
    WARNING = "warning" 
    ERROR = "error"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class MonitoringType(Enum):
    """Types of monitoring checks."""
    AVAILABILITY = "availability"
    RESPONSE_TIME = "response_time"
    CONTENT_CHANGE = "content_change"
    ROBOTS_TXT = "robots_txt"
    FIELD_MAPPING = "field_mapping"
    SSL_CERTIFICATE = "ssl_certificate"


@dataclass
class HealthCheck:
    """Represents a health check result."""
    site_id: str
    site_name: str
    check_type: MonitoringType
    status: HealthStatus
    message: str
    details: Dict[str, Any]
    checked_at: datetime
    response_time_ms: Optional[float] = None
    error_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "site_id": self.site_id,
            "site_name": self.site_name,
            "check_type": self.check_type.value,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "checked_at": self.checked_at.isoformat(),
            "response_time_ms": self.response_time_ms,
            "error_count": self.error_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HealthCheck':
        """Create from dictionary."""
        return cls(
            site_id=data["site_id"],
            site_name=data["site_name"],
            check_type=MonitoringType(data["check_type"]),
            status=HealthStatus(data["status"]),
            message=data["message"],
            details=data["details"],
            checked_at=datetime.fromisoformat(data["checked_at"]),
            response_time_ms=data.get("response_time_ms"),
            error_count=data.get("error_count", 0)
        )


@dataclass
class SiteHealthReport:
    """Comprehensive health report for a site."""
    site_id: str
    site_name: str
    overall_status: HealthStatus
    last_checked: datetime
    checks: List[HealthCheck] = field(default_factory=list)
    uptime_percentage: float = 100.0
    avg_response_time: Optional[float] = None
    error_summary: Dict[str, int] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "site_id": self.site_id,
            "site_name": self.site_name,
            "overall_status": self.overall_status.value,
            "last_checked": self.last_checked.isoformat(),
            "checks": [check.to_dict() for check in self.checks],
            "uptime_percentage": self.uptime_percentage,
            "avg_response_time": self.avg_response_time,
            "error_summary": self.error_summary,
            "recommendations": self.recommendations
        }


class SiteMonitor:
    """
    Monitors government websites for health and availability.
    
    Features:
    - Availability monitoring
    - Response time tracking  
    - Content change detection
    - Field mapping validation
    - SSL certificate monitoring
    - Robots.txt compliance checking
    """
    
    def __init__(self, data_manager: DataManager):
        """
        Initialize SiteMonitor.
        
        Args:
            data_manager: DataManager instance
        """
        self.data_manager = data_manager
        self.monitoring_dir = data_manager.data_dir / "monitoring"
        self.monitoring_dir.mkdir(exist_ok=True)
        
        self.health_file = self.monitoring_dir / "site_health.json"
        self.history_dir = self.monitoring_dir / "history"
        self.history_dir.mkdir(exist_ok=True)
        
        # Monitoring configuration
        self.timeout_seconds = 30
        self.max_retries = 3
        self.retry_delay = 5
        self.response_time_threshold = 5000  # 5 seconds
        self.uptime_history_days = 30
        
        # User agent for ethical monitoring
        self.user_agent = "LA 2028 RFP Monitor - Public Oversight Tool (https://github.com/ND-AAD/Gov_Oversight)"
    
    async def monitor_all_sites(self) -> List[SiteHealthReport]:
        """
        Monitor all configured sites.
        
        Returns:
            List of SiteHealthReport objects
        """
        site_configs = self.data_manager.load_site_configs()
        if not site_configs:
            logger.warning("No site configurations found for monitoring")
            return []
        
        reports = []
        
        # Use semaphore to limit concurrent requests (be respectful)
        semaphore = asyncio.Semaphore(3)
        
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout_seconds),
            headers={"User-Agent": self.user_agent}
        ) as session:
            tasks = [
                self._monitor_site_with_semaphore(semaphore, session, site_config)
                for site_config in site_configs
            ]
            
            reports = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and log them
        valid_reports = []
        for i, report in enumerate(reports):
            if isinstance(report, Exception):
                logger.error(f"Monitoring failed for site {site_configs[i].id}: {report}")
            else:
                valid_reports.append(report)
        
        # Save monitoring results
        self._save_health_reports(valid_reports)
        
        logger.info(f"Monitored {len(valid_reports)} sites successfully")
        return valid_reports
    
    async def _monitor_site_with_semaphore(self, semaphore: asyncio.Semaphore,
                                         session: aiohttp.ClientSession,
                                         site_config: SiteConfig) -> SiteHealthReport:
        """Monitor a single site with concurrency control."""
        async with semaphore:
            return await self._monitor_single_site(session, site_config)
    
    async def _monitor_single_site(self, session: aiohttp.ClientSession,
                                 site_config: SiteConfig) -> SiteHealthReport:
        """
        Monitor a single site comprehensively.
        
        Args:
            session: aiohttp ClientSession
            site_config: Site configuration to monitor
            
        Returns:
            SiteHealthReport with all check results
        """
        logger.info(f"Monitoring site: {site_config.name}")
        
        checks = []
        
        # Availability check
        availability_check = await self._check_availability(session, site_config)
        checks.append(availability_check)
        
        # Response time check
        response_time_check = await self._check_response_time(session, site_config)
        checks.append(response_time_check)
        
        # SSL certificate check (if HTTPS)
        if site_config.base_url.startswith('https'):
            ssl_check = await self._check_ssl_certificate(session, site_config)
            checks.append(ssl_check)
        
        # Robots.txt check
        robots_check = await self._check_robots_txt(session, site_config)
        checks.append(robots_check)
        
        # Content change detection
        content_check = await self._check_content_changes(session, site_config)
        checks.append(content_check)
        
        # Field mapping validation (if sample URL available)
        if site_config.sample_rfp_url:
            mapping_check = await self._check_field_mappings(session, site_config)
            checks.append(mapping_check)
        
        # Calculate overall health status
        overall_status = self._calculate_overall_status(checks)
        
        # Calculate metrics
        response_times = [c.response_time_ms for c in checks if c.response_time_ms]
        avg_response_time = sum(response_times) / len(response_times) if response_times else None
        
        # Error summary
        error_summary = {}
        for check in checks:
            if check.status in [HealthStatus.ERROR, HealthStatus.CRITICAL]:
                error_summary[check.check_type.value] = error_summary.get(check.check_type.value, 0) + 1
        
        # Calculate uptime percentage
        uptime_percentage = self._calculate_uptime_percentage(site_config.id)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(checks, site_config)
        
        report = SiteHealthReport(
            site_id=site_config.id,
            site_name=site_config.name,
            overall_status=overall_status,
            last_checked=datetime.now(),
            checks=checks,
            uptime_percentage=uptime_percentage,
            avg_response_time=avg_response_time,
            error_summary=error_summary,
            recommendations=recommendations
        )
        
        # Update site config status
        site_config.status = self._health_to_site_status(overall_status)
        site_config.last_tested = datetime.now()
        
        logger.info(f"Site {site_config.name} monitoring complete: {overall_status.value}")
        return report
    
    async def _check_availability(self, session: aiohttp.ClientSession,
                                site_config: SiteConfig) -> HealthCheck:
        """Check if site is available and responding."""
        start_time = time.time()
        
        try:
            async with session.get(site_config.main_rfp_page_url) as response:
                response_time_ms = (time.time() - start_time) * 1000
                
                if response.status == 200:
                    status = HealthStatus.HEALTHY
                    message = f"Site available (HTTP {response.status})"
                elif response.status in [301, 302, 303, 307, 308]:
                    status = HealthStatus.WARNING
                    message = f"Site redirected (HTTP {response.status})"
                elif response.status in [404, 403]:
                    status = HealthStatus.ERROR
                    message = f"Site not accessible (HTTP {response.status})"
                else:
                    status = HealthStatus.WARNING
                    message = f"Unexpected response (HTTP {response.status})"
                
                return HealthCheck(
                    site_id=site_config.id,
                    site_name=site_config.name,
                    check_type=MonitoringType.AVAILABILITY,
                    status=status,
                    message=message,
                    details={
                        "status_code": response.status,
                        "headers": dict(response.headers),
                        "url": str(response.url)
                    },
                    checked_at=datetime.now(),
                    response_time_ms=response_time_ms
                )
                
        except asyncio.TimeoutError:
            return HealthCheck(
                site_id=site_config.id,
                site_name=site_config.name,
                check_type=MonitoringType.AVAILABILITY,
                status=HealthStatus.ERROR,
                message="Request timeout",
                details={"error": "timeout", "timeout_seconds": self.timeout_seconds},
                checked_at=datetime.now(),
                response_time_ms=(time.time() - start_time) * 1000
            )
        except Exception as e:
            return HealthCheck(
                site_id=site_config.id,
                site_name=site_config.name,
                check_type=MonitoringType.AVAILABILITY,
                status=HealthStatus.CRITICAL,
                message=f"Connection failed: {str(e)}",
                details={"error": str(e), "error_type": type(e).__name__},
                checked_at=datetime.now()
            )
    
    async def _check_response_time(self, session: aiohttp.ClientSession,
                                 site_config: SiteConfig) -> HealthCheck:
        """Check site response time performance."""
        start_time = time.time()
        
        try:
            async with session.get(site_config.main_rfp_page_url) as response:
                response_time_ms = (time.time() - start_time) * 1000
                
                if response_time_ms < 1000:  # Under 1 second
                    status = HealthStatus.HEALTHY
                    message = f"Excellent response time ({response_time_ms:.0f}ms)"
                elif response_time_ms < 3000:  # Under 3 seconds
                    status = HealthStatus.HEALTHY
                    message = f"Good response time ({response_time_ms:.0f}ms)"
                elif response_time_ms < self.response_time_threshold:
                    status = HealthStatus.WARNING
                    message = f"Slow response time ({response_time_ms:.0f}ms)"
                else:
                    status = HealthStatus.ERROR
                    message = f"Very slow response ({response_time_ms:.0f}ms)"
                
                return HealthCheck(
                    site_id=site_config.id,
                    site_name=site_config.name,
                    check_type=MonitoringType.RESPONSE_TIME,
                    status=status,
                    message=message,
                    details={
                        "response_time_ms": response_time_ms,
                        "threshold_ms": self.response_time_threshold
                    },
                    checked_at=datetime.now(),
                    response_time_ms=response_time_ms
                )
                
        except Exception as e:
            return HealthCheck(
                site_id=site_config.id,
                site_name=site_config.name,
                check_type=MonitoringType.RESPONSE_TIME,
                status=HealthStatus.ERROR,
                message=f"Response time check failed: {str(e)}",
                details={"error": str(e)},
                checked_at=datetime.now()
            )
    
    async def _check_ssl_certificate(self, session: aiohttp.ClientSession,
                                   site_config: SiteConfig) -> HealthCheck:
        """Check SSL certificate status for HTTPS sites."""
        try:
            async with session.get(site_config.base_url) as response:
                # Basic SSL check - if we got here, SSL worked
                status = HealthStatus.HEALTHY
                message = "SSL certificate valid"
                details = {
                    "ssl_enabled": True,
                    "url": site_config.base_url
                }
                
                return HealthCheck(
                    site_id=site_config.id,
                    site_name=site_config.name,
                    check_type=MonitoringType.SSL_CERTIFICATE,
                    status=status,
                    message=message,
                    details=details,
                    checked_at=datetime.now()
                )
                
        except Exception as e:
            return HealthCheck(
                site_id=site_config.id,
                site_name=site_config.name,
                check_type=MonitoringType.SSL_CERTIFICATE,
                status=HealthStatus.ERROR,
                message=f"SSL check failed: {str(e)}",
                details={"error": str(e), "url": site_config.base_url},
                checked_at=datetime.now()
            )
    
    async def _check_robots_txt(self, session: aiohttp.ClientSession,
                              site_config: SiteConfig) -> HealthCheck:
        """Check robots.txt compliance."""
        from urllib.parse import urljoin
        
        robots_url = urljoin(site_config.base_url, "/robots.txt")
        
        try:
            async with session.get(robots_url) as response:
                if response.status == 200:
                    robots_content = await response.text()
                    
                    # Check for any disallow rules
                    disallow_rules = []
                    for line in robots_content.split('\n'):
                        line = line.strip().lower()
                        if line.startswith('disallow:'):
                            disallow_rules.append(line)
                    
                    if not disallow_rules:
                        status = HealthStatus.HEALTHY
                        message = "No robots.txt restrictions found"
                    else:
                        status = HealthStatus.WARNING
                        message = f"Found {len(disallow_rules)} robots.txt restrictions"
                    
                    details = {
                        "robots_url": robots_url,
                        "status_code": response.status,
                        "disallow_count": len(disallow_rules),
                        "disallow_rules": disallow_rules[:5]  # First 5 rules
                    }
                
                elif response.status == 404:
                    status = HealthStatus.HEALTHY
                    message = "No robots.txt file (no restrictions)"
                    details = {"robots_url": robots_url, "status_code": 404}
                
                else:
                    status = HealthStatus.WARNING
                    message = f"Robots.txt check returned HTTP {response.status}"
                    details = {"robots_url": robots_url, "status_code": response.status}
                
                return HealthCheck(
                    site_id=site_config.id,
                    site_name=site_config.name,
                    check_type=MonitoringType.ROBOTS_TXT,
                    status=status,
                    message=message,
                    details=details,
                    checked_at=datetime.now()
                )
                
        except Exception as e:
            return HealthCheck(
                site_id=site_config.id,
                site_name=site_config.name,
                check_type=MonitoringType.ROBOTS_TXT,
                status=HealthStatus.WARNING,
                message=f"Robots.txt check failed: {str(e)}",
                details={"error": str(e), "robots_url": robots_url},
                checked_at=datetime.now()
            )
    
    async def _check_content_changes(self, session: aiohttp.ClientSession,
                                   site_config: SiteConfig) -> HealthCheck:
        """Detect significant content changes on the site."""
        try:
            async with session.get(site_config.main_rfp_page_url) as response:
                if response.status != 200:
                    return HealthCheck(
                        site_id=site_config.id,
                        site_name=site_config.name,
                        check_type=MonitoringType.CONTENT_CHANGE,
                        status=HealthStatus.ERROR,
                        message=f"Cannot check content changes (HTTP {response.status})",
                        details={"status_code": response.status},
                        checked_at=datetime.now()
                    )
                
                content = await response.text()
                content_hash = hashlib.sha256(content.encode()).hexdigest()
                
                # Load previous content hash
                previous_hash = self._get_previous_content_hash(site_config.id)
                
                if previous_hash is None:
                    status = HealthStatus.HEALTHY
                    message = "Baseline content hash established"
                    details = {"content_hash": content_hash, "first_check": True}
                elif previous_hash == content_hash:
                    status = HealthStatus.HEALTHY
                    message = "No content changes detected"
                    details = {"content_hash": content_hash, "changed": False}
                else:
                    status = HealthStatus.WARNING
                    message = "Content changes detected"
                    details = {
                        "content_hash": content_hash,
                        "previous_hash": previous_hash,
                        "changed": True
                    }
                
                # Save current hash for next comparison
                self._save_content_hash(site_config.id, content_hash)
                
                return HealthCheck(
                    site_id=site_config.id,
                    site_name=site_config.name,
                    check_type=MonitoringType.CONTENT_CHANGE,
                    status=status,
                    message=message,
                    details=details,
                    checked_at=datetime.now()
                )
                
        except Exception as e:
            return HealthCheck(
                site_id=site_config.id,
                site_name=site_config.name,
                check_type=MonitoringType.CONTENT_CHANGE,
                status=HealthStatus.ERROR,
                message=f"Content change check failed: {str(e)}",
                details={"error": str(e)},
                checked_at=datetime.now()
            )
    
    async def _check_field_mappings(self, session: aiohttp.ClientSession,
                                  site_config: SiteConfig) -> HealthCheck:
        """Validate that field mappings still work."""
        if not site_config.sample_rfp_url:
            return HealthCheck(
                site_id=site_config.id,
                site_name=site_config.name,
                check_type=MonitoringType.FIELD_MAPPING,
                status=HealthStatus.WARNING,
                message="No sample URL configured for field mapping validation",
                details={"sample_url": None},
                checked_at=datetime.now()
            )
        
        try:
            async with session.get(site_config.sample_rfp_url) as response:
                if response.status != 200:
                    return HealthCheck(
                        site_id=site_config.id,
                        site_name=site_config.name,
                        check_type=MonitoringType.FIELD_MAPPING,
                        status=HealthStatus.ERROR,
                        message=f"Sample RFP page not accessible (HTTP {response.status})",
                        details={"status_code": response.status, "sample_url": site_config.sample_rfp_url},
                        checked_at=datetime.now()
                    )
                
                page_content = await response.text()
                
                # Validate field mappings using location binder
                from scrapers.location_binder import LocationBinder
                binder = LocationBinder()
                
                working_mappings = 0
                failed_mappings = 0
                mapping_details = {}
                
                for field_mapping in site_config.field_mappings:
                    try:
                        result = binder.validate_field_mapping(field_mapping, page_content)
                        if result.is_valid:
                            working_mappings += 1
                            mapping_details[field_mapping.alias] = "working"
                        else:
                            failed_mappings += 1
                            mapping_details[field_mapping.alias] = f"failed: {'; '.join(result.errors)}"
                    except Exception as e:
                        failed_mappings += 1
                        mapping_details[field_mapping.alias] = f"error: {str(e)}"
                
                total_mappings = working_mappings + failed_mappings
                success_rate = working_mappings / total_mappings if total_mappings > 0 else 0
                
                if success_rate >= 0.8:  # 80% success rate
                    status = HealthStatus.HEALTHY
                    message = f"Field mappings working well ({working_mappings}/{total_mappings})"
                elif success_rate >= 0.5:  # 50% success rate
                    status = HealthStatus.WARNING
                    message = f"Some field mappings failing ({working_mappings}/{total_mappings})"
                else:
                    status = HealthStatus.ERROR
                    message = f"Many field mappings broken ({working_mappings}/{total_mappings})"
                
                return HealthCheck(
                    site_id=site_config.id,
                    site_name=site_config.name,
                    check_type=MonitoringType.FIELD_MAPPING,
                    status=status,
                    message=message,
                    details={
                        "working_mappings": working_mappings,
                        "failed_mappings": failed_mappings,
                        "success_rate": success_rate,
                        "mapping_details": mapping_details,
                        "sample_url": site_config.sample_rfp_url
                    },
                    checked_at=datetime.now()
                )
                
        except Exception as e:
            return HealthCheck(
                site_id=site_config.id,
                site_name=site_config.name,
                check_type=MonitoringType.FIELD_MAPPING,
                status=HealthStatus.ERROR,
                message=f"Field mapping validation failed: {str(e)}",
                details={"error": str(e), "sample_url": site_config.sample_rfp_url},
                checked_at=datetime.now()
            )
    
    def _calculate_overall_status(self, checks: List[HealthCheck]) -> HealthStatus:
        """Calculate overall health status from individual checks."""
        if not checks:
            return HealthStatus.UNKNOWN
        
        # Count status types
        status_counts = {}
        for check in checks:
            status_counts[check.status] = status_counts.get(check.status, 0) + 1
        
        # Determine overall status based on worst case
        if status_counts.get(HealthStatus.CRITICAL, 0) > 0:
            return HealthStatus.CRITICAL
        elif status_counts.get(HealthStatus.ERROR, 0) > 0:
            return HealthStatus.ERROR
        elif status_counts.get(HealthStatus.WARNING, 0) > 0:
            return HealthStatus.WARNING
        elif status_counts.get(HealthStatus.HEALTHY, 0) > 0:
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.UNKNOWN
    
    def _health_to_site_status(self, health_status: HealthStatus) -> SiteStatus:
        """Convert health status to site status."""
        mapping = {
            HealthStatus.HEALTHY: SiteStatus.ACTIVE,
            HealthStatus.WARNING: SiteStatus.ACTIVE,
            HealthStatus.ERROR: SiteStatus.ERROR,
            HealthStatus.CRITICAL: SiteStatus.ERROR,
            HealthStatus.UNKNOWN: SiteStatus.INACTIVE
        }
        return mapping.get(health_status, SiteStatus.INACTIVE)
    
    def _calculate_uptime_percentage(self, site_id: str) -> float:
        """Calculate uptime percentage over the last 30 days."""
        # This would be implemented with historical data
        # For now, return a default based on current status
        return 95.0  # Placeholder implementation
    
    def _generate_recommendations(self, checks: List[HealthCheck], 
                                site_config: SiteConfig) -> List[str]:
        """Generate recommendations based on check results."""
        recommendations = []
        
        for check in checks:
            if check.status == HealthStatus.ERROR:
                if check.check_type == MonitoringType.AVAILABILITY:
                    recommendations.append(f"Check if {site_config.name} is experiencing downtime")
                elif check.check_type == MonitoringType.FIELD_MAPPING:
                    recommendations.append(f"Review and update field mappings for {site_config.name}")
                elif check.check_type == MonitoringType.RESPONSE_TIME:
                    recommendations.append(f"Monitor {site_config.name} for performance issues")
            elif check.status == HealthStatus.WARNING:
                if check.check_type == MonitoringType.CONTENT_CHANGE:
                    recommendations.append(f"Review content changes on {site_config.name} - may need mapping updates")
                elif check.check_type == MonitoringType.ROBOTS_TXT:
                    recommendations.append(f"Check robots.txt restrictions for {site_config.name}")
        
        return recommendations
    
    def _get_previous_content_hash(self, site_id: str) -> Optional[str]:
        """Get previous content hash for comparison."""
        hash_file = self.monitoring_dir / f"{site_id}_content_hash.txt"
        if hash_file.exists():
            try:
                return hash_file.read_text().strip()
            except Exception:
                return None
        return None
    
    def _save_content_hash(self, site_id: str, content_hash: str) -> None:
        """Save content hash for future comparison."""
        hash_file = self.monitoring_dir / f"{site_id}_content_hash.txt"
        try:
            hash_file.write_text(content_hash)
        except Exception as e:
            logger.warning(f"Failed to save content hash for {site_id}: {e}")
    
    def _save_health_reports(self, reports: List[SiteHealthReport]) -> None:
        """Save health reports to file."""
        try:
            data = {
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "total_sites": len(reports),
                    "version": "1.0"
                },
                "reports": [report.to_dict() for report in reports]
            }
            
            with open(self.health_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Also save to history
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            history_file = self.history_dir / f"health_{timestamp}.json"
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved health reports for {len(reports)} sites")
            
        except Exception as e:
            logger.error(f"Failed to save health reports: {e}")
    
    def load_latest_health_reports(self) -> List[SiteHealthReport]:
        """Load the latest health reports."""
        if not self.health_file.exists():
            return []
        
        try:
            with open(self.health_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            reports = []
            for report_dict in data.get("reports", []):
                try:
                    # Convert checks
                    checks = [HealthCheck.from_dict(check_dict) for check_dict in report_dict.get("checks", [])]
                    
                    report = SiteHealthReport(
                        site_id=report_dict["site_id"],
                        site_name=report_dict["site_name"],
                        overall_status=HealthStatus(report_dict["overall_status"]),
                        last_checked=datetime.fromisoformat(report_dict["last_checked"]),
                        checks=checks,
                        uptime_percentage=report_dict.get("uptime_percentage", 100.0),
                        avg_response_time=report_dict.get("avg_response_time"),
                        error_summary=report_dict.get("error_summary", {}),
                        recommendations=report_dict.get("recommendations", [])
                    )
                    reports.append(report)
                    
                except Exception as e:
                    logger.warning(f"Failed to load health report: {e}")
            
            return reports
            
        except Exception as e:
            logger.error(f"Failed to load health reports: {e}")
            return []
    
    def get_critical_issues(self) -> List[HealthCheck]:
        """Get all critical issues from latest health reports."""
        reports = self.load_latest_health_reports()
        critical_issues = []
        
        for report in reports:
            for check in report.checks:
                if check.status == HealthStatus.CRITICAL:
                    critical_issues.append(check)
        
        return critical_issues
    
    def generate_monitoring_summary(self) -> Dict[str, Any]:
        """Generate a summary of monitoring status."""
        reports = self.load_latest_health_reports()
        
        if not reports:
            return {"error": "No monitoring data available"}
        
        status_counts = {}
        total_sites = len(reports)
        
        for report in reports:
            status = report.overall_status
            status_counts[status.value] = status_counts.get(status.value, 0) + 1
        
        # Calculate averages
        response_times = [r.avg_response_time for r in reports if r.avg_response_time]
        avg_response_time = sum(response_times) / len(response_times) if response_times else None
        
        uptimes = [r.uptime_percentage for r in reports]
        avg_uptime = sum(uptimes) / len(uptimes) if uptimes else 100.0
        
        return {
            "total_sites": total_sites,
            "status_breakdown": status_counts,
            "avg_response_time_ms": avg_response_time,
            "avg_uptime_percentage": avg_uptime,
            "critical_issues": len(self.get_critical_issues()),
            "last_check": max(r.last_checked for r in reports).isoformat() if reports else None,
            "generated_at": datetime.now().isoformat()
        }
