"""
Main entry point for the LA 2028 RFP Monitor backend.

Command-line interface for scraping, testing, and managing RFP data.
"""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path
import click
import json

# Add the backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from models import DataManager, SiteConfig, FieldMapping, DataType, FieldMappingStatus
from scrapers import LocationBinder, RFPScraper
from models.validation import validate_site_config_data

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
@click.option('--site-id', help='Scrape specific site only')
@click.pass_context
def scrape(ctx, force, site_id):
    """Scrape configured sites for new RFPs."""
    logger.info("Starting RFP scraping process")
    
    data_manager = ctx.obj['data_manager']
    
    async def run_scraping():
        scraper = RFPScraper(data_manager)
        
        if site_id:
            # Scrape specific site
            site_configs = data_manager.load_site_configs()
            site_config = next((s for s in site_configs if s.id == site_id), None)
            
            if not site_config:
                click.echo(f"Site with ID '{site_id}' not found", err=True)
                return
            
            result = await scraper.scrape_site(site_config, force)
            click.echo(f"Scraped {site_config.name}: {len(result['new_rfps'])} new RFPs")
        else:
            # Scrape all sites
            results = await scraper.scrape_all_sites(force)
            
            click.echo(f"Scraping completed:")
            click.echo(f"  Sites processed: {results['sites_processed']}")
            click.echo(f"  Sites failed: {results['sites_failed']}")
            click.echo(f"  New RFPs: {len(results['new_rfps'])}")
            click.echo(f"  Updated RFPs: {len(results['updated_rfps'])}")
            
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


if __name__ == '__main__':
    cli()
