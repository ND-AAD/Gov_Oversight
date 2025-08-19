import { useState, useMemo } from 'react';
import { RFP, FilterState } from '../types/rfp';
import { mockRFPs, getRecentRFPs, getClosingSoonRFPs, getHighValueRFPs } from '../data/mockData';
import { RFPCard } from './RFPCard';
import { FilterBar } from './FilterBar';
import { RFPDetailModal } from './RFPDetailModal';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogTrigger } from './ui/dialog';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Separator } from './ui/separator';
import { Grid, List, Settings, Globe, Plus, ArrowUpDown, Trash2 } from 'lucide-react';
import { toast } from 'sonner@2.0.3';

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
  const [rfps] = useState<RFP[]>(mockRFPs);
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

  // Filter and sort RFPs
  const filteredAndSortedRFPs = useMemo(() => {
    let filtered = rfps.filter(rfp => !ignoredRFPIds.has(rfp.id));

    // Apply filters (same as before)
    if (filters.searchTerm) {
      const searchLower = filters.searchTerm.toLowerCase();
      filtered = filtered.filter(rfp =>
        rfp.title.toLowerCase().includes(searchLower) ||
        rfp.description.toLowerCase().includes(searchLower) ||
        rfp.issuer?.toLowerCase().includes(searchLower)
      );
    }

    if (filters.issuers.length > 0) {
      filtered = filtered.filter(rfp => 
        rfp.issuer && filters.issuers.includes(rfp.issuer)
      );
    }

    if (filters.eventAssociations.length > 0) {
      filtered = filtered.filter(rfp => 
        rfp.event_association && filters.eventAssociations.includes(rfp.event_association)
      );
    }

    if (filters.procurementTypes.length > 0) {
      filtered = filtered.filter(rfp => 
        rfp.procurement_type && filters.procurementTypes.includes(rfp.procurement_type)
      );
    }

    if (filters.dateRange.start || filters.dateRange.end) {
      filtered = filtered.filter(rfp => {
        const rfpDate = new Date(rfp.posted_date);
        if (filters.dateRange.start && rfpDate < filters.dateRange.start) return false;
        if (filters.dateRange.end && rfpDate > filters.dateRange.end) return false;
        return true;
      });
    }

    if (filters.quickFilters.newThisWeek) {
      const recentRFPs = getRecentRFPs(filtered, 7);
      filtered = filtered.filter(rfp => recentRFPs.includes(rfp));
    }

    if (filters.quickFilters.closingSoon) {
      const closingSoonRFPs = getClosingSoonRFPs(filtered, 7);
      filtered = filtered.filter(rfp => closingSoonRFPs.includes(rfp));
    }

    if (filters.quickFilters.highValue) {
      const highValueRFPs = getHighValueRFPs(filtered, 1000000);
      filtered = filtered.filter(rfp => highValueRFPs.includes(rfp));
    }

    // Apply sorting
    const sorted = [...filtered].sort((a, b) => {
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
          return (b.contract_value || 0) - (a.contract_value || 0);
        case 'contract_value_asc':
          return (a.contract_value || 0) - (b.contract_value || 0);
        case 'title_asc':
          return a.title.localeCompare(b.title);
        case 'title_desc':
          return b.title.localeCompare(a.title);
        default:
          return 0;
      }
    });

    return sorted;
  }, [rfps, filters, ignoredRFPIds, sortBy]);

  const handleViewDetails = (rfp: RFP) => {
    setSelectedRFP(rfp);
    setIsDetailModalOpen(true);
  };

  const handleIgnoreRFP = (id: string) => {
    setIgnoredRFPIds(prev => new Set([...prev, id]));
  };

  const handleToggleStar = (id: string) => {
    setStarredRFPIds(prev => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
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

  const handleAddSite = () => {
    if (!newSite.name.trim() || !newSite.baseUrl.trim()) {
      toast.error('Please fill in required fields');
      return;
    }

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
    toast.success(`Site "${newSite.name}" added successfully`);
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
    total: rfps.length,
    active: filteredAndSortedRFPs.length,
    newThisWeek: getRecentRFPs(rfps, 7).length,
    closingSoon: getClosingSoonRFPs(rfps, 7).length,
    ignored: ignoredRFPIds.size,
    starred: starredRFPIds.size
  };

  const getSortLabel = (sortOption: SortOption) => {
    switch (sortOption) {
      case 'posted_date_desc': return 'Posted Date (Newest)';
      case 'posted_date_asc': return 'Posted Date (Oldest)';
      case 'closing_date_desc': return 'Closing Date (Latest)';
      case 'closing_date_asc': return 'Closing Date (Soonest)';
      case 'contract_value_desc': return 'Contract Value (Highest)';
      case 'contract_value_asc': return 'Contract Value (Lowest)';
      case 'title_asc': return 'Title (A-Z)';
      case 'title_desc': return 'Title (Z-A)';
      default: return '';
    }
  };

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
        rfps={rfps}
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
                            <p className="text-sm text-muted-foreground italic">
                              No custom parameters added yet. Click "Add Parameter" to start mapping fields.
                            </p>
                          ) : (
                            <div className="space-y-3">
                              {newSite.customParameters.map((param) => (
                                <div key={param.id} className="flex gap-2 items-start p-3 border rounded">
                                  <div className="flex-1 space-y-2">
                                    <Input
                                      placeholder="Parameter alias (e.g., 'Contract Value')"
                                      value={param.alias}
                                      onChange={(e) => updateCustomParameter(param.id, 'alias', e.target.value)}
                                    />
                                    <Input
                                      placeholder="Current value from sample RFP (e.g., '$1,500,000')"
                                      value={param.currentValue}
                                      onChange={(e) => updateCustomParameter(param.id, 'currentValue', e.target.value)}
                                    />
                                  </div>
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => removeCustomParameter(param.id)}
                                    className="text-destructive hover:text-destructive"
                                  >
                                    <Trash2 className="h-4 w-4" />
                                  </Button>
                                </div>
                              ))}
                            </div>
                          )}

                          <div className="text-xs text-muted-foreground space-y-1">
                            <p>• <strong>Parameter alias:</strong> What you want to call this field (e.g., "Contract Value", "Deadline")</p>
                            <p>• <strong>Current value:</strong> The actual value from your sample RFP to help the scraper locate it</p>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="flex justify-end gap-2">
                    <Button
                      variant="outline"
                      onClick={() => setIsAddSiteOpen(false)}
                    >
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
              <SelectTrigger className="w-48 flex items-center gap-2">
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
      <RFPDetailModal
        rfp={selectedRFP}
        isOpen={isDetailModalOpen}
        onClose={() => setIsDetailModalOpen(false)}
        onIgnore={handleIgnoreRFP}
      />
    </div>
  );
}