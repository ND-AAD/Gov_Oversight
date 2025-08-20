import { useState, useMemo, useEffect } from 'react';
import type { RFP, FilterState } from '../types/rfp';
import { RFPCard } from './RFPCard';
import { FilterBar } from './FilterBar';
import { RFPDetailModal } from './RFPDetailModal';
import { Button } from './ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Tabs, TabsList, TabsTrigger } from './ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogTrigger } from './ui/dialog';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Separator } from './ui/separator';

import { Grid, List, Globe, Plus, ArrowUpDown, Settings, Trash2 } from 'lucide-react';
import { toast } from 'sonner';
import { autoLoadRFPs, createSite } from '../utils/api';

interface DashboardProps {
  onNavigate: (page: 'dashboard' | 'analytics' | 'settings' | 'ignored' | 'sites') => void;
}

type SortOption = 'posted_date_desc' | 'posted_date_asc' | 'closing_date_desc' | 'closing_date_asc' | 'contract_value_desc' | 'contract_value_asc' | 'title_asc' | 'title_desc';

interface CustomParameter {
  id: string;
  alias: string;
  currentValue: string;
  xpath?: string;
}

interface NewSiteConfig {
  name: string;
  baseUrl: string;
  mainRfpPageUrl: string;
  sampleRfpUrl: string;
  description: string;
  isAdvanced: boolean;
  customParameters: CustomParameter[];
}

export function Dashboard({ onNavigate }: DashboardProps) {
  const [rfps, setRfps] = useState<RFP[]>([]);
  const [loading, setLoading] = useState(true);
  const [ignoredRFPIds, setIgnoredRFPIds] = useState<Set<string>>(new Set());
  const [starredRFPIds, setStarredRFPIds] = useState<Set<string>>(new Set());
  const [selectedRFP, setSelectedRFP] = useState<RFP | null>(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [sortBy, setSortBy] = useState<SortOption>('posted_date_desc');
  const [isAddSiteOpen, setIsAddSiteOpen] = useState(false);
  const [newSite, setNewSite] = useState<NewSiteConfig>({
    name: '',
    baseUrl: '',
    mainRfpPageUrl: '',
    sampleRfpUrl: '',
    description: '',
    isAdvanced: false,
    customParameters: []
  });

  // Filter state
  const [filters, setFilters] = useState<FilterState>({
    searchTerm: '',
    issuers: [],
    eventAssociations: [],
    procurementTypes: [],
    dateRange: {},
    showIgnored: false,
    quickFilters: {
      newThisWeek: false,
      closingSoon: false,
      highValue: false
    }
  });

  // Load RFPs from backend
  useEffect(() => {
    loadRFPs();
  }, []);

  const loadRFPs = async () => {
    try {
      setLoading(true);
      const rfpsData = await autoLoadRFPs();

      setRfps(rfpsData);
    } catch (error) {
      console.error('Failed to load RFPs:', error);
      toast.error('Failed to load RFPs');
    } finally {
      setLoading(false);
    }
  };

  // Helper function to get value from extracted_fields
  const getExtractedValue = (rfp: RFP, field: string) => {
    return rfp.extracted_fields?.[field] || '';
  };

  // Enhanced RFP data with extracted fields flattened for easier filtering
  const enhancedRFPs = useMemo(() => {
    const enhanced = rfps.map(rfp => ({
      ...rfp,
      issuer: getExtractedValue(rfp, 'issuer'),
      event_association: getExtractedValue(rfp, 'event_association'),
      procurement_type: getExtractedValue(rfp, 'procurement_type'),
      contract_value: getExtractedValue(rfp, 'contract_value'),
      status: getExtractedValue(rfp, 'status') || 'active',
      isStarred: starredRFPIds.has(rfp.id)
    }));

    return enhanced;
  }, [rfps, starredRFPIds]);

  // Filter and sort RFPs
  const filteredAndSortedRFPs = useMemo(() => {
    let filtered = enhancedRFPs.filter(rfp => !ignoredRFPIds.has(rfp.id));

    // Apply filters
    if (filters.searchTerm) {
      const searchLower = filters.searchTerm.toLowerCase();
      filtered = filtered.filter(rfp =>
        rfp.title.toLowerCase().includes(searchLower) ||
        rfp.description.toLowerCase().includes(searchLower) ||
        getExtractedValue(rfp, 'issuer').toLowerCase().includes(searchLower)
      );
    }

    if (filters.issuers.length > 0) {
      filtered = filtered.filter(rfp => 
        filters.issuers.includes(getExtractedValue(rfp, 'issuer'))
      );
    }

    if (filters.eventAssociations.length > 0) {
      filtered = filtered.filter(rfp => 
        filters.eventAssociations.includes(getExtractedValue(rfp, 'event_association'))
      );
    }

    if (filters.procurementTypes.length > 0) {
      filtered = filtered.filter(rfp => 
        filters.procurementTypes.includes(getExtractedValue(rfp, 'procurement_type'))
      );
    }

    // Date range filter
    if (filters.dateRange.start || filters.dateRange.end) {
      filtered = filtered.filter(rfp => {
        const postedDate = new Date(rfp.posted_date);
        if (filters.dateRange.start && postedDate < filters.dateRange.start) return false;
        if (filters.dateRange.end && postedDate > filters.dateRange.end) return false;
        return true;
      });
    }

    // Quick filters
    if (filters.quickFilters.newThisWeek) {
      const weekAgo = new Date();
      weekAgo.setDate(weekAgo.getDate() - 7);
      filtered = filtered.filter(rfp => new Date(rfp.posted_date) >= weekAgo);
    }

    if (filters.quickFilters.closingSoon) {
      const threeDaysFromNow = new Date();
      threeDaysFromNow.setDate(threeDaysFromNow.getDate() + 3);
      filtered = filtered.filter(rfp => 
        rfp.closing_date && new Date(rfp.closing_date) <= threeDaysFromNow
      );
    }

    if (filters.quickFilters.highValue) {
      filtered = filtered.filter(rfp => {
        const contractValue = getExtractedValue(rfp, 'contract_value');
        return contractValue && Number(contractValue) >= 1000000;
      });
    }

    // Sort
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'posted_date_desc':
          return new Date(b.posted_date).getTime() - new Date(a.posted_date).getTime();
        case 'posted_date_asc':
          return new Date(a.posted_date).getTime() - new Date(b.posted_date).getTime();
        case 'closing_date_desc':
          if (!a.closing_date && !b.closing_date) return 0;
          if (!a.closing_date) return 1;
          if (!b.closing_date) return -1;
          return new Date(b.closing_date).getTime() - new Date(a.closing_date).getTime();
        case 'closing_date_asc':
          if (!a.closing_date && !b.closing_date) return 0;
          if (!a.closing_date) return 1;
          if (!b.closing_date) return -1;
          return new Date(a.closing_date).getTime() - new Date(b.closing_date).getTime();
        case 'contract_value_desc':
          const aValue = Number(getExtractedValue(a, 'contract_value')) || 0;
          const bValue = Number(getExtractedValue(b, 'contract_value')) || 0;
          return bValue - aValue;
        case 'contract_value_asc':
          const aValueAsc = Number(getExtractedValue(a, 'contract_value')) || 0;
          const bValueAsc = Number(getExtractedValue(b, 'contract_value')) || 0;
          return aValueAsc - bValueAsc;
        case 'title_asc':
          return a.title.localeCompare(b.title);
        case 'title_desc':
          return b.title.localeCompare(a.title);
        default:
          return 0;
      }
    });

    return filtered;
  }, [enhancedRFPs, filters, ignoredRFPIds, sortBy]);

  const handleViewDetails = (rfp: RFP) => {
    setSelectedRFP(rfp);
    setIsDetailModalOpen(true);
  };

  const handleIgnoreRFP = (id: string) => {
    setIgnoredRFPIds(prev => new Set([...prev, id]));
    toast.success('RFP ignored');
  };

  const handleToggleStar = (id: string) => {
    setStarredRFPIds(prev => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
        toast.success('RFP unstarred');
      } else {
        newSet.add(id);
        toast.success('RFP starred');
      }
      return newSet;
    });
  };

  const handleClearFilters = () => {
    setFilters({
      searchTerm: '',
      issuers: [],
      eventAssociations: [],
      procurementTypes: [],
      dateRange: {},
      showIgnored: false,
      quickFilters: {
        newThisWeek: false,
        closingSoon: false,
        highValue: false
      }
    });
  };

  const handleAddSite = async () => {
    if (!newSite.name.trim() || !newSite.baseUrl.trim()) {
      toast.error('Please fill in required fields');
      return;
    }

    try {
      // Prepare site data for submission
      const siteData = {
        name: newSite.name,
        base_url: newSite.baseUrl,
        main_rfp_page_url: newSite.mainRfpPageUrl || newSite.baseUrl,
        sample_rfp_url: newSite.sampleRfpUrl || newSite.mainRfpPageUrl || newSite.baseUrl,
        description: newSite.description,
        field_mappings: newSite.customParameters.map(param => ({
          alias: param.alias,
          sample_value: param.currentValue,
          data_type: 'text' // Default to text for now
        }))
      };

      // Submit the site addition request
      await createSite(siteData);

      // Reset form
      setNewSite({
        name: '',
        baseUrl: '',
        mainRfpPageUrl: '',
        sampleRfpUrl: '',
        description: '',
        isAdvanced: false,
        customParameters: []
      });
      
      setIsAddSiteOpen(false);
      
      // Show success message with next steps
      toast.success(
        `Site "${newSite.name}" request submitted! It will be processed automatically within 1 hour and appear in the next scraping run.`,
        { duration: 6000 }
      );

      // Reload sites to show the pending site
      loadRFPs();
      
    } catch (error) {
      console.error('Failed to add site:', error);
      toast.error(`Failed to add site: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  const addCustomParameter = () => {
    const newParam: CustomParameter = {
      id: `param-${Date.now()}`,
      alias: '',
      currentValue: ''
    };
    
    setNewSite(prev => ({
      ...prev,
      customParameters: [...prev.customParameters, newParam]
    }));
  };

  const updateCustomParameter = (id: string, field: keyof CustomParameter, value: string) => {
    setNewSite(prev => ({
      ...prev,
      customParameters: prev.customParameters.map(param =>
        param.id === id ? { ...param, [field]: value } : param
      )
    }));
  };

  const removeCustomParameter = (id: string) => {
    setNewSite(prev => ({
      ...prev,
      customParameters: prev.customParameters.filter(param => param.id !== id)
    }));
  };



  // Calculate stats
  const stats = {
    total: enhancedRFPs.length,
    active: filteredAndSortedRFPs.length,
    ignored: ignoredRFPIds.size,
    starred: starredRFPIds.size
  };



  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading RFPs...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold mb-2">LA 2028 RFP Monitor</h1>
              <p className="text-muted-foreground">
                Track government procurement opportunities for the 2028 LA Olympics
              </p>
            </div>
            
            <div className="flex items-center gap-3">
              <Button
                variant="outline"
                size="sm"
                onClick={() => onNavigate('sites')}
                className="flex items-center gap-2"
              >
                <Globe className="h-4 w-4" />
                Sites
              </Button>
              
              <Button
                variant="outline"
                size="sm"
                onClick={() => onNavigate('settings')}
                className="flex items-center gap-2"
              >
                <Settings className="h-4 w-4" />
                Settings
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Filter Bar */}
      <FilterBar
        rfps={enhancedRFPs}
        filters={filters}
        onFiltersChange={setFilters}
        onClearFilters={handleClearFilters}
      />

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6">
        {/* Controls and Results */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
          <div className="flex items-center gap-4">
            <h2 className="text-xl">
              Showing {filteredAndSortedRFPs.length} of {stats.total} RFPs
            </h2>
            {ignoredRFPIds.size > 0 && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => onNavigate('ignored')}
                className="flex items-center gap-1"
              >
                View Ignored ({ignoredRFPIds.size})
              </Button>
            )}
          </div>

          {/* Control Bar */}
          <div className="flex items-center gap-3">
            {/* Add Site Button */}
            <Dialog open={isAddSiteOpen} onOpenChange={setIsAddSiteOpen}>
              <DialogTrigger asChild>
                <Button className="flex items-center gap-2">
                  <Plus className="h-4 w-4" />
                  Add Site
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                  <DialogTitle>Add New RFP Site</DialogTitle>
                  <DialogDescription>
                    Configure a new website for RFP monitoring. Use advanced mode to set up custom field mapping for better data extraction.
                  </DialogDescription>
                </DialogHeader>
                
                <div className="space-y-6">
                  {/* Basic Fields */}
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="siteName">Site Name / Alias *</Label>
                      <Input
                        id="siteName"
                        placeholder="e.g., LA City Portal"
                        value={newSite.name}
                        onChange={(e) => setNewSite(prev => ({ ...prev, name: e.target.value }))}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="baseUrl">Main RFP Page URL *</Label>
                      <Input
                        id="baseUrl"
                        placeholder="https://example.gov/rfps"
                        value={newSite.baseUrl}
                        onChange={(e) => setNewSite(prev => ({ ...prev, baseUrl: e.target.value }))}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="description">Description (Optional)</Label>
                      <Textarea
                        id="description"
                        placeholder="Brief description of this RFP site..."
                        value={newSite.description}
                        onChange={(e) => setNewSite(prev => ({ ...prev, description: e.target.value }))}
                        rows={2}
                      />
                    </div>
                  </div>

                  <Separator />

                  {/* Advanced Configuration Toggle */}
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-medium">Advanced Configuration</h3>
                        <p className="text-sm text-muted-foreground">
                          Configure custom field mapping for better data extraction
                        </p>
                      </div>
                      <Button
                        variant={newSite.isAdvanced ? "default" : "outline"}
                        size="sm"
                        onClick={() => setNewSite(prev => ({ ...prev, isAdvanced: !prev.isAdvanced }))}
                      >
                        {newSite.isAdvanced ? 'Enabled' : 'Enable'}
                      </Button>
                    </div>

                    {newSite.isAdvanced && (
                      <div className="space-y-4 p-4 border rounded-lg bg-muted/20">
                        <div className="space-y-2">
                          <Label htmlFor="sampleUrl">Sample RFP URL *</Label>
                          <Input
                            id="sampleUrl"
                            placeholder="https://example.gov/rfp/sample-rfp-123"
                            value={newSite.sampleRfpUrl}
                            onChange={(e) => setNewSite(prev => ({ ...prev, sampleRfpUrl: e.target.value }))}
                          />
                          <p className="text-xs text-muted-foreground">
                            Link to a specific RFP on this site to help train the scraper
                          </p>
                        </div>

                        <div className="space-y-3">
                          <div className="flex items-center justify-between">
                            <Label>Custom Parameters</Label>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={addCustomParameter}
                              className="flex items-center gap-1"
                            >
                              <Plus className="h-3 w-3" />
                              Add Parameter
                            </Button>
                          </div>

                          {newSite.customParameters.length === 0 ? (
                            <p className="text-sm text-muted-foreground text-center py-4 border-2 border-dashed rounded-lg">
                              No custom parameters defined. Click "Add Parameter" to create location-bound field mappings.
                            </p>
                          ) : (
                            <div className="space-y-3">
                              {newSite.customParameters.map((param) => (
                                <div key={param.id} className="space-y-2 p-3 border rounded-lg">
                                  <div className="flex items-center justify-between">
                                    <Label className="text-sm font-medium">Custom Parameter</Label>
                                    <Button
                                      variant="ghost"
                                      size="sm"
                                      onClick={() => removeCustomParameter(param.id)}
                                      className="h-6 w-6 p-0 text-destructive hover:text-destructive"
                                    >
                                      <Trash2 className="h-3 w-3" />
                                    </Button>
                                  </div>
                                  
                                  <div className="grid grid-cols-2 gap-2">
                                    <div>
                                      <Label htmlFor={`alias-${param.id}`} className="text-xs">Field Alias</Label>
                                      <Input
                                        id={`alias-${param.id}`}
                                        placeholder="e.g., contact_email"
                                        value={param.alias}
                                        onChange={(e) => updateCustomParameter(param.id, 'alias', e.target.value)}
                                        className="text-sm"
                                      />
                                    </div>
                                    <div>
                                      <Label htmlFor={`value-${param.id}`} className="text-xs">Current Value</Label>
                                      <Input
                                        id={`value-${param.id}`}
                                        placeholder="e.g., procurement@city.gov"
                                        value={param.currentValue}
                                        onChange={(e) => updateCustomParameter(param.id, 'currentValue', e.target.value)}
                                        className="text-sm"
                                      />
                                    </div>
                                  </div>
                                  
                                  <div>
                                    <Label htmlFor={`xpath-${param.id}`} className="text-xs">XPath (Optional)</Label>
                                    <Input
                                      id={`xpath-${param.id}`}
                                      placeholder="//div[@class='contact-info']//a[contains(@href,'mailto')]"
                                      value={param.xpath || ''}
                                      onChange={(e) => updateCustomParameter(param.id, 'xpath', e.target.value)}
                                      className="text-sm font-mono"
                                    />
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="flex justify-end gap-3">
                    <Button variant="outline" onClick={() => setIsAddSiteOpen(false)}>
                      Cancel
                    </Button>
                    <Button onClick={handleAddSite}>
                      Add Site
                    </Button>
                  </div>
                </div>
              </DialogContent>
            </Dialog>

            {/* Sort Dropdown */}
            <Select value={sortBy} onValueChange={(value: SortOption) => setSortBy(value)}>
              <SelectTrigger className="w-fit min-w-48 flex items-center gap-2 px-3">
                <ArrowUpDown className="h-4 w-4" />
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="posted_date_desc">Posted Date (Newest)</SelectItem>
                <SelectItem value="posted_date_asc">Posted Date (Oldest)</SelectItem>
                <SelectItem value="closing_date_asc">Closing Date (Soonest)</SelectItem>
                <SelectItem value="closing_date_desc">Closing Date (Latest)</SelectItem>
                <SelectItem value="contract_value_desc">Contract Value (Highest)</SelectItem>
                <SelectItem value="contract_value_asc">Contract Value (Lowest)</SelectItem>
                <SelectItem value="title_asc">Title (A-Z)</SelectItem>
                <SelectItem value="title_desc">Title (Z-A)</SelectItem>
              </SelectContent>
            </Select>

            {/* View Mode Toggle */}
            <Tabs value={viewMode} onValueChange={(value) => setViewMode(value as 'grid' | 'list')}>
              <TabsList>
                <TabsTrigger value="grid" className="flex items-center gap-1">
                  <Grid className="h-4 w-4" />
                  Grid
                </TabsTrigger>
                <TabsTrigger value="list" className="flex items-center gap-1">
                  <List className="h-4 w-4" />
                  List
                </TabsTrigger>
              </TabsList>
            </Tabs>
          </div>
        </div>

        {/* RFP Grid/List */}
        {filteredAndSortedRFPs.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-muted-foreground mb-4">No RFPs match your current filters.</p>
            <Button onClick={handleClearFilters}>Clear All Filters</Button>
          </div>
        ) : (
          <div className={
            viewMode === 'grid' 
              ? "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
              : "space-y-4"
          }>
            {filteredAndSortedRFPs.map(rfp => (
              <RFPCard
                key={rfp.id}
                rfp={rfp}
                onViewDetails={handleViewDetails}
                onIgnore={handleIgnoreRFP}
                onToggleStar={handleToggleStar}
                isStarred={starredRFPIds.has(rfp.id)}
              />
            ))}
          </div>
        )}
      </main>

      {/* RFP Detail Modal */}
      {selectedRFP && (
        <RFPDetailModal
          rfp={selectedRFP}
          isOpen={isDetailModalOpen}
          onClose={() => setIsDetailModalOpen(false)}
          onIgnore={handleIgnoreRFP}
          onToggleStar={handleToggleStar}
          isIgnored={ignoredRFPIds.has(selectedRFP.id)}
          isStarred={starredRFPIds.has(selectedRFP.id)}
        />
      )}
    </div>
  );
}