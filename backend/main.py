"""
Main entry point for the LA 2028 RFP Monitor backend.

Command-line interface for scraping, testing, and managing RFP data.
Enhanced Phase 3 version with monitoring, archiving, and change detection.
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
import click
import json

# Add the backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from models import DataManager, SiteConfig, FieldMapping, DataType, FieldMappingStatus
from scrapers import LocationBinder, RFPScraper
from models.validation import validate_site_config_data
from utils.change_detector import ChangeDetector, ChangeSeverity
from utils.data_archiver import DataArchiver
from utils.site_monitor import SiteMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('rfp_monitor.log')
    ]
)

logger = logging.getLogger(__name__)


@click.group()
@click.option('--data-dir', default='../data', help='Directory containing data files')
@click.pass_context
def cli(ctx, data_dir):
    """LA 2028 RFP Monitor - Government Procurement Transparency Tool"""
    ctx.ensure_object(dict)
    ctx.obj['data_manager'] = DataManager(data_dir)


@cli.command()
@click.option('--force', is_flag=True, help='Force full scan regardless of last update')
@click.option('--sites', help='Comma-separated site IDs to scrape (leave empty for all)')
@click.option('--output-dir', help='Output directory for data files')
@click.option('--detect-changes', is_flag=True, help='Enable change detection and alerts')
@click.option('--create-archive', is_flag=True, help='Create archive after scraping')
@click.pass_context
def scrape(ctx, force, sites, output_dir, detect_changes, create_archive):
    """Scrape configured sites for new RFPs with enhanced Phase 3 features."""
    logger.info("Starting RFP scraping process")
    
    data_manager = ctx.obj['data_manager']
    if output_dir:
        data_manager = DataManager(output_dir)
    
    async def run_scraping():
        scraper = RFPScraper(data_manager)
        change_detector = ChangeDetector(data_manager)
        archiver = DataArchiver(data_manager)
        
        # Load previous RFPs for change detection
        previous_rfps = None
        if detect_changes:
            previous_rfps = data_manager.load_rfps(validate=False)
            click.echo(f"Loaded {len(previous_rfps)} existing RFPs for change detection")
        
        if sites:
            # Scrape specific sites
            site_ids = [s.strip() for s in sites.split(',')]
            site_configs = data_manager.load_site_configs()
            target_configs = [s for s in site_configs if s.id in site_ids]
            
            if not target_configs:
                click.echo(f"No sites found matching IDs: {sites}", err=True)
                return
            
            all_results = {'new_rfps': [], 'updated_rfps': [], 'sites_processed': 0, 'sites_failed': 0, 'errors': []}
            
            for site_config in target_configs:
                try:
                    result = await scraper.scrape_site(site_config, force)
                    all_results['new_rfps'].extend(result.get('new_rfps', []))
                    all_results['updated_rfps'].extend(result.get('updated_rfps', []))
                    all_results['sites_processed'] += 1
                    click.echo(f"Scraped {site_config.name}: {len(result.get('new_rfps', []))} new RFPs")
                except Exception as e:
                    all_results['sites_failed'] += 1
                    all_results['errors'].append(f"{site_config.name}: {str(e)}")
                    logger.error(f"Failed to scrape {site_config.name}: {e}")
            
            results = all_results
        else:
            # Scrape all sites
            results = await scraper.scrape_all_sites(force)
        
        # Get current RFPs after scraping
        current_rfps = data_manager.load_rfps(validate=False)
        
        # Change detection
        changes = []
        if detect_changes and previous_rfps is not None:
            click.echo("🔍 Detecting changes...")
            changes = change_detector.detect_changes(current_rfps, previous_rfps)
            
            # Save snapshot for next comparison
            change_detector.create_snapshot(current_rfps)
            change_detector.save_changes(changes)
            
            if changes:
                click.echo(f"📊 Detected {len(changes)} changes:")
                
                # Show critical and high priority changes
                critical_changes = [c for c in changes if c.severity == ChangeSeverity.CRITICAL]
                high_changes = [c for c in changes if c.severity == ChangeSeverity.HIGH]
                
                if critical_changes:
                    click.echo(f"  🚨 Critical: {len(critical_changes)}")
                    for change in critical_changes[:3]:  # Show first 3
                        click.echo(f"    - {change.description}")
                
                if high_changes:
                    click.echo(f"  ⚠️  High Priority: {len(high_changes)}")
                    for change in high_changes[:3]:  # Show first 3
                        click.echo(f"    - {change.description}")
            else:
                click.echo("✅ No significant changes detected")
        
        # Create archive
        if create_archive:
            click.echo("📦 Creating archive...")
            archive_id = archiver.create_daily_archive(current_rfps)
            
            # Also create surveillance-focused archive if relevant RFPs found
            surveillance_archive_id = archiver.create_surveillance_archive(current_rfps)
            
            if surveillance_archive_id:
                click.echo(f"📊 Archives created: {archive_id}, {surveillance_archive_id}")
            else:
                click.echo(f"📊 Archive created: {archive_id}")
        
        # Show results
        click.echo(f"\n🎯 Scraping completed:")
        click.echo(f"  Sites processed: {results['sites_processed']}")
        click.echo(f"  Sites failed: {results['sites_failed']}")
        click.echo(f"  New RFPs: {len(results['new_rfps'])}")
        click.echo(f"  Updated RFPs: {len(results['updated_rfps'])}")
        
        if detect_changes:
            click.echo(f"  Changes detected: {len(changes)}")
            action_required = len([c for c in changes if c.action_required])
            if action_required > 0:
                click.echo(f"  🚨 Action required: {action_required} changes need attention")
        
        if results['errors']:
            click.echo(f"  Errors: {len(results['errors'])}")
            for error in results['errors'][:5]:  # Show first 5 errors
                click.echo(f"    - {error}")
    
    try:
        asyncio.run(run_scraping())
    except KeyboardInterrupt:
        click.echo("Scraping interrupted by user")
    except Exception as e:
        click.echo(f"Scraping failed: {e}", err=True)
        logger.error(f"Scraping failed: {e}")


@cli.command()
@click.pass_context
def list_sites(ctx):
    """List all configured sites."""
    data_manager = ctx.obj['data_manager']
    
    try:
        site_configs = data_manager.load_site_configs()
        
        if not site_configs:
            click.echo("No sites configured")
            return
        
        click.echo(f"Found {len(site_configs)} configured sites:\n")
        
        for site in site_configs:
            status_summary = site.get_status_summary()
            health_indicator = "🟢" if site.is_healthy() else "🔴"
            
            click.echo(f"{health_indicator} {site.name} ({site.id})")
            click.echo(f"   URL: {site.base_url}")
            click.echo(f"   Status: {site.status.value}")
            click.echo(f"   Fields: {len(site.field_mappings)} total")
            click.echo(f"     - Working: {status_summary['working']}")
            click.echo(f"     - Degraded: {status_summary['degraded']}")
            click.echo(f"     - Broken: {status_summary['broken']}")
            click.echo(f"     - Untested: {status_summary['untested']}")
            
            if site.last_scrape:
                click.echo(f"   Last scraped: {site.last_scrape.strftime('%Y-%m-%d %H:%M')}")
            
            click.echo()
            
    except Exception as e:
        click.echo(f"Error listing sites: {e}", err=True)


@cli.command()
@click.argument('site_id')
@click.pass_context
def test_site(ctx, site_id):
    """Test a site configuration."""
    data_manager = ctx.obj['data_manager']
    
    async def run_test():
        try:
            site_configs = data_manager.load_site_configs()
            site_config = next((s for s in site_configs if s.id == site_id), None)
            
            if not site_config:
                click.echo(f"Site with ID '{site_id}' not found", err=True)
                return
            
            click.echo(f"Testing site configuration: {site_config.name}")
            
            scraper = RFPScraper(data_manager)
            result = await scraper.test_site_configuration(site_config)
            
            if result.is_valid:
                click.echo("✅ Site configuration test passed")
            else:
                click.echo("❌ Site configuration test failed")
                for error in result.errors:
                    click.echo(f"   Error: {error}")
            
            if result.warnings:
                for warning in result.warnings:
                    click.echo(f"   Warning: {warning}")
                    
        except Exception as e:
            click.echo(f"Test failed: {e}", err=True)
    
    asyncio.run(run_test())


@cli.command()
@click.option('--high-priority', is_flag=True, help='Show only high-priority RFPs')
@click.option('--closing-soon', type=int, help='Show RFPs closing within N days')
@click.option('--site-id', help='Filter by site ID')
@click.option('--limit', type=int, default=10, help='Maximum number of RFPs to show')
@click.pass_context
def list_rfps(ctx, high_priority, closing_soon, site_id, limit):
    """List RFPs with filtering options."""
    data_manager = ctx.obj['data_manager']
    
    try:
        rfps = data_manager.load_rfps()
        
        # Apply filters
        if high_priority:
            rfps = [rfp for rfp in rfps if rfp.is_high_priority()]
        
        if closing_soon:
            rfps = [rfp for rfp in rfps if rfp.is_closing_soon(closing_soon)]
        
        if site_id:
            rfps = [rfp for rfp in rfps if rfp.source_site == site_id]
        
        # Sort by detected date (newest first)
        rfps.sort(key=lambda r: r.detected_at, reverse=True)
        
        # Limit results
        rfps = rfps[:limit]
        
        if not rfps:
            click.echo("No RFPs found matching criteria")
            return
        
        click.echo(f"Found {len(rfps)} RFPs:\n")
        
        for rfp in rfps:
            priority_indicator = "🚨" if rfp.is_high_priority() else "📄"
            closing_indicator = "⏰" if rfp.is_closing_soon() else ""
            
            click.echo(f"{priority_indicator} {closing_indicator} {rfp.title}")
            click.echo(f"   ID: {rfp.id}")
            click.echo(f"   Site: {rfp.source_site}")
            click.echo(f"   URL: {rfp.url}")
            click.echo(f"   Categories: {', '.join(rfp.categories)}")
            click.echo(f"   Detected: {rfp.detected_at.strftime('%Y-%m-%d %H:%M')}")
            
            # Show key extracted fields
            status = rfp.get_display_value('status')
            value = rfp.get_display_value('contract_value')
            closing = rfp.get_display_value('closing_date')
            
            if status != "N/A":
                click.echo(f"   Status: {status}")
            if value != "N/A":
                click.echo(f"   Value: {value}")
            if closing != "N/A":
                click.echo(f"   Closing: {closing}")
            
            click.echo()
            
    except Exception as e:
        click.echo(f"Error listing RFPs: {e}", err=True)


@cli.command()
@click.pass_context
def stats(ctx):
    """Show data statistics and health information."""
    data_manager = ctx.obj['data_manager']
    
    try:
        stats = data_manager.get_data_statistics()
        
        click.echo("📊 LA 2028 RFP Monitor Statistics\n")
        
        # RFP statistics
        rfp_stats = stats["rfps"]
        click.echo(f"RFPs:")
        click.echo(f"  Total: {rfp_stats['total']}")
        click.echo(f"  High Priority: {rfp_stats['high_priority']}")
        click.echo(f"  Closing Soon: {rfp_stats['closing_soon']}")
        
        # Site statistics
        site_stats = stats["sites"]
        click.echo(f"\nSites:")
        click.echo(f"  Total: {site_stats['total']}")
        click.echo(f"  Active: {site_stats['active']}")
        click.echo(f"  Errors: {site_stats['errors']}")
        
        click.echo(f"\nLast Updated: {stats['last_updated']}")
        
    except Exception as e:
        click.echo(f"Error getting statistics: {e}", err=True)


@cli.command()
@click.argument('name')
@click.argument('base_url')
@click.argument('rfp_page_url') 
@click.argument('sample_rfp_url')
@click.pass_context
def add_site(ctx, name, base_url, rfp_page_url, sample_rfp_url):
    """Add a new site configuration (basic version)."""
    data_manager = ctx.obj['data_manager']
    
    click.echo(f"Adding site: {name}")
    click.echo("Note: This is a basic site addition. Use the frontend for advanced location-binding setup.")
    
    try:
        # Create basic site configuration
        site_id = name.lower().replace(' ', '_').replace('.', '_')
        
        site_config = SiteConfig(
            id=site_id,
            name=name,
            base_url=base_url,
            main_rfp_page_url=rfp_page_url,
            sample_rfp_url=sample_rfp_url,
            field_mappings=[],  # Will be configured via frontend
            description=f"Basic configuration for {name}"
        )
        
        # Validate configuration
        validation_result = validate_site_config_data(site_config.to_dict())
        
        if not validation_result.is_valid:
            click.echo("❌ Site configuration validation failed:")
            for error in validation_result.errors:
                click.echo(f"   Error: {error}")
            return
        
        # Add to existing sites
        site_configs = data_manager.load_site_configs()
        
        # Check for duplicate IDs
        if any(s.id == site_id for s in site_configs):
            click.echo(f"❌ Site with ID '{site_id}' already exists")
            return
        
        site_configs.append(site_config)
        data_manager.save_site_configs(site_configs)
        
        click.echo(f"✅ Successfully added site: {name} ({site_id})")
        click.echo("Next steps:")
        click.echo("1. Use the frontend to configure field mappings")
        click.echo("2. Test the configuration with: python main.py test-site {site_id}")
        
    except Exception as e:
        click.echo(f"Error adding site: {e}", err=True)


@cli.command()
@click.option('--backup-dir', help='Directory to save backup (defaults to data/history)')
@click.pass_context
def backup(ctx, backup_dir):
    """Create backup of all data files."""
    data_manager = ctx.obj['data_manager']
    
    try:
        backup_path = data_manager.backup_data_files()
        click.echo(f"✅ Backup created: {backup_path}")
        
    except Exception as e:
        click.echo(f"Error creating backup: {e}", err=True)


@cli.command()
@click.pass_context
def monitor(ctx):
    """Monitor all configured sites for health and availability."""
    data_manager = ctx.obj['data_manager']
    
    async def run_monitoring():
        monitor = SiteMonitor(data_manager)
        
        click.echo("🔍 Monitoring all configured sites...")
        reports = await monitor.monitor_all_sites()
        
        if not reports:
            click.echo("No sites to monitor")
            return
        
        # Show summary
        healthy = len([r for r in reports if r.overall_status.value == 'healthy'])
        warning = len([r for r in reports if r.overall_status.value == 'warning'])
        error = len([r for r in reports if r.overall_status.value in ['error', 'critical']])
        
        click.echo(f"\n📊 Monitoring Results:")
        click.echo(f"  Total sites: {len(reports)}")
        click.echo(f"  🟢 Healthy: {healthy}")
        click.echo(f"  🟡 Warning: {warning}")
        click.echo(f"  🔴 Error/Critical: {error}")
        
        # Show detailed results for problematic sites
        problem_sites = [r for r in reports if r.overall_status.value in ['warning', 'error', 'critical']]
        
        if problem_sites:
            click.echo(f"\n⚠️  Sites requiring attention:")
            for report in problem_sites:
                click.echo(f"  {report.site_name} ({report.overall_status.value})")
                for check in report.checks:
                    if check.status.value in ['warning', 'error', 'critical']:
                        click.echo(f"    - {check.check_type.value}: {check.message}")
                
                if report.recommendations:
                    click.echo(f"    Recommendations:")
                    for rec in report.recommendations[:2]:  # Show first 2
                        click.echo(f"      • {rec}")
                click.echo()
        
        # Show critical issues
        critical_issues = monitor.get_critical_issues()
        if critical_issues:
            click.echo(f"🚨 {len(critical_issues)} critical issues require immediate attention:")
            for issue in critical_issues:
                click.echo(f"  - {issue.site_name}: {issue.message}")
    
    try:
        asyncio.run(run_monitoring())
    except Exception as e:
        click.echo(f"Monitoring failed: {e}", err=True)


@cli.command()
@click.option('--surveillance-only', is_flag=True, help='Create surveillance-focused archive only')
@click.option('--tags', help='Comma-separated tags for the archive')
@click.pass_context
def archive(ctx, surveillance_only, tags):
    """Create archive of current RFP data."""
    data_manager = ctx.obj['data_manager']
    
    try:
        archiver = DataArchiver(data_manager)
        rfps = data_manager.load_rfps(validate=False)
        
        if not rfps:
            click.echo("No RFPs found to archive")
            return
        
        tag_list = [t.strip() for t in tags.split(',')] if tags else None
        
        if surveillance_only:
            archive_id = archiver.create_surveillance_archive(rfps)
            if archive_id:
                click.echo(f"✅ Surveillance archive created: {archive_id}")
            else:
                click.echo("No surveillance-related RFPs found")
        else:
            archive_id = archiver.create_daily_archive(rfps, tag_list)
            click.echo(f"✅ Archive created: {archive_id}")
            
            # Also create surveillance archive if relevant RFPs exist
            surveillance_id = archiver.create_surveillance_archive(rfps)
            if surveillance_id:
                click.echo(f"✅ Additional surveillance archive: {surveillance_id}")
        
    except Exception as e:
        click.echo(f"Error creating archive: {e}", err=True)


@cli.command()
@click.option('--days', type=int, default=7, help='Number of days to look back for changes')
@click.option('--severity', type=click.Choice(['low', 'medium', 'high', 'critical']), 
              help='Filter by severity level')
@click.option('--action-required', is_flag=True, help='Show only changes requiring action')
@click.pass_context  
def changes(ctx, days, severity, action_required):
    """Show recent changes in RFP data."""
    data_manager = ctx.obj['data_manager']
    
    try:
        change_detector = ChangeDetector(data_manager)
        
        if severity:
            from utils.change_detector import ChangeSeverity
            severity_enum = ChangeSeverity(severity)
            changes = change_detector.get_changes_by_severity(severity_enum, days)
        elif action_required:
            changes = change_detector.get_action_required_changes(days)
        else:
            all_changes = change_detector.load_changes()
            cutoff_date = datetime.now() - timedelta(days=days)
            changes = [c for c in all_changes if c.detected_at >= cutoff_date]
        
        if not changes:
            click.echo(f"No changes found in the last {days} days")
            return
        
        click.echo(f"📊 Found {len(changes)} changes in the last {days} days:\n")
        
        # Group by severity
        by_severity = {}
        for change in changes:
            severity_key = change.severity.value
            if severity_key not in by_severity:
                by_severity[severity_key] = []
            by_severity[severity_key].append(change)
        
        # Show in severity order
        severity_order = ['critical', 'high', 'medium', 'low']
        for sev in severity_order:
            if sev in by_severity:
                sev_changes = by_severity[sev]
                emoji = {'critical': '🚨', 'high': '⚠️', 'medium': '📊', 'low': '📝'}[sev]
                click.echo(f"{emoji} {sev.upper()} ({len(sev_changes)} changes):")
                
                for change in sev_changes[:5]:  # Show first 5 per severity
                    action_flag = " [ACTION REQUIRED]" if change.action_required else ""
                    click.echo(f"  • {change.rfp_title}{action_flag}")
                    click.echo(f"    {change.description}")
                    click.echo(f"    Detected: {change.detected_at.strftime('%Y-%m-%d %H:%M')}")
                    click.echo()
        
        # Show summary
        summary = change_detector.generate_change_summary(days)
        action_count = summary.get('action_required', 0)
        if action_count > 0:
            click.echo(f"🚨 {action_count} changes require activist attention")
        
    except Exception as e:
        click.echo(f"Error getting changes: {e}", err=True)


@cli.command()
@click.option('--tags', help='Filter archives by tags (comma-separated)')
@click.option('--days', type=int, help='Only show archives from last N days')
@click.pass_context
def list_archives(ctx, tags, days):
    """List available data archives."""
    data_manager = ctx.obj['data_manager']
    
    try:
        archiver = DataArchiver(data_manager)
        
        tag_list = [t.strip() for t in tags.split(',')] if tags else None
        archives = archiver.list_archives(tag_list, days)
        
        if not archives:
            click.echo("No archives found")
            return
        
        click.echo(f"📦 Found {len(archives)} archives:\n")
        
        for archive in archives:
            # Age calculation
            age = datetime.now() - archive.created_at
            age_str = f"{age.days}d {age.seconds//3600}h ago"
            
            click.echo(f"📊 {archive.archive_id}")
            click.echo(f"   Created: {archive.created_at.strftime('%Y-%m-%d %H:%M')} ({age_str})")
            click.echo(f"   RFPs: {archive.rfp_count}")
            click.echo(f"   Description: {archive.description}")
            click.echo(f"   Tags: {', '.join(archive.tags)}")
            click.echo(f"   Compression: {archive.compression_ratio:.1%}")
            click.echo()
        
    except Exception as e:
        click.echo(f"Error listing archives: {e}", err=True)


@cli.command()
@click.argument('start_date', type=click.DateTime(formats=['%Y-%m-%d']))
@click.argument('end_date', type=click.DateTime(formats=['%Y-%m-%d']))
@click.option('--surveillance-only', is_flag=True, help='Export only surveillance-related RFPs')
@click.option('--output', help='Output file for research data (default: research_export.json)')
@click.pass_context
def export_research(ctx, start_date, end_date, surveillance_only, output):
    """Export RFP data for activist research over a date range."""
    data_manager = ctx.obj['data_manager']
    
    try:
        archiver = DataArchiver(data_manager)
        
        output_file = output or f"research_export_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.json"
        
        click.echo(f"📊 Exporting research data from {start_date.date()} to {end_date.date()}")
        if surveillance_only:
            click.echo("🔍 Filtering for surveillance-related RFPs only")
        
        research_data = archiver.export_research_data(start_date, end_date, surveillance_only)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(research_data, f, indent=2, ensure_ascii=False)
        
        # Show summary
        metadata = research_data['export_metadata']
        analysis = research_data['analysis']
        
        click.echo(f"\n✅ Research export complete:")
        click.echo(f"  File: {output_file}")
        click.echo(f"  RFPs included: {metadata['total_rfps']}")
        click.echo(f"  Archives processed: {metadata['archives_included']}")
        
        if 'surveillance_analysis' in analysis:
            surv_analysis = analysis['surveillance_analysis']
            click.echo(f"  Surveillance RFPs: {surv_analysis['total_surveillance_rfps']}")
            if surv_analysis['total_surveillance_value'] > 0:
                click.echo(f"  Total surveillance value: ${surv_analysis['total_surveillance_value']:,.0f}")
        
        click.echo(f"\n📋 Research notes and methodology included in export")
        
    except Exception as e:
        click.echo(f"Error exporting research data: {e}", err=True)


if __name__ == '__main__':
    cli()
