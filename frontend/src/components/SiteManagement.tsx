import { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogTrigger } from './ui/dialog';
import { 
  ArrowLeft, 
  Plus, 
  Trash2, 
  Globe, 
  Settings, 
  CheckCircle, 
  XCircle, 
  AlertTriangle,
  Edit,
  TestTube
} from 'lucide-react';
import type { SiteConfig } from '../types/rfp';
import { createSite, createFieldMappings, testSite, softDeleteSite, autoLoadSites } from '../utils/api';
import { toast } from 'sonner';

interface SiteManagementProps {
  onNavigate: (page: 'dashboard' | 'analytics' | 'settings' | 'ignored' | 'sites') => void;
}

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

export function SiteManagement({ onNavigate }: SiteManagementProps) {
  const [sites, setSites] = useState<SiteConfig[]>([]);
  const [loading, setLoading] = useState(true);
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

  // Load sites on mount
  useEffect(() => {
    loadSites();
  }, []);

  const loadSites = async () => {
    try {
      setLoading(true);
      const sitesData = await autoLoadSites();
      setSites(sitesData);
    } catch (error) {
      console.error('Failed to load sites:', error);
      toast.error('Failed to load sites');
    } finally {
      setLoading(false);
    }
  };

  const handleAddSite = async () => {
    if (!newSite.name.trim() || !newSite.baseUrl.trim()) {
      toast.error('Please fill in required fields');
      return;
    }

    // Site creation now handles both API and GitHub modes automatically

    try {
      const siteData = {
        name: newSite.name,
        base_url: newSite.baseUrl,
        main_rfp_page_url: newSite.mainRfpPageUrl || newSite.baseUrl,
        sample_rfp_url: newSite.sampleRfpUrl || '',
        description: newSite.description
      };

      const createdSite = await createSite(siteData);
      
      // If advanced mode and custom parameters, create field mappings
      if (newSite.isAdvanced && newSite.customParameters.length > 0) {
        const fieldMappings = newSite.customParameters.map(param => ({
          alias: param.alias,
          sample_value: param.currentValue,
          data_type: 'text' // Default to text, can be enhanced later
        }));
        
        await createFieldMappings(createdSite.id, fieldMappings);
      }

      // Reload sites
      await loadSites();
      
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
      
      // Different messages for different modes
      const isStaticMode = window.location.hostname.includes('github.io');
      if (isStaticMode) {
        toast.success(`Site "${newSite.name}" queued for addition. It will be processed on the next scraping run.`);
      } else {
        toast.success(`Site "${newSite.name}" added successfully`);
      }
    } catch (error) {
      console.error('Failed to add site:', error);
      toast.error('Failed to add site');
    }
  };

  const handleDeleteSite = async (id: string, name: string) => {
    // Show confirmation dialog
    const confirmed = window.confirm(
      `Are you sure you want to remove "${name}"?\n\n` +
      `This will:\n` +
      `• Stop monitoring RFPs from this site\n` +
      `• Preserve existing RFP data for transparency\n` +
      `• Allow easy restoration if needed\n\n` +
      `Click OK to proceed with soft deletion.`
    );
    
    if (!confirmed) return;
    
    try {
      await softDeleteSite(id, name);
      await loadSites();
      toast.success(`Site "${name}" has been removed from monitoring (data preserved)`);
    } catch (error) {
      console.error('Soft delete process:', error);
      toast.error(error instanceof Error ? error.message : 'Failed to remove site');
    }
  };

  const handleTestSite = async (site: SiteConfig) => {
    try {
      toast.info(`Testing scraper for ${site.name}...`);
      
      const result = await testSite(site.id);
      
      if (result.success) {
        toast.success(`✅ Scraper test completed for ${site.name}`);
      } else {
        toast.error(`❌ Scraper test failed for ${site.name}`);
      }
    } catch (error) {
      console.error('Failed to test site:', error);
      toast.error(`Failed to test ${site.name}`);
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

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'error':
        return <XCircle className="h-4 w-4 text-red-600" />;
      case 'disabled':
        return <AlertTriangle className="h-4 w-4 text-yellow-600" />;
      default:
        return <Globe className="h-4 w-4 text-muted-foreground" />;
    }
  };

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'active':
        return 'default';
      case 'error':
        return 'destructive';
      case 'disabled':
        return 'secondary';
      default:
        return 'outline';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading sites...</p>
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
            <div className="flex items-center gap-4">
              <Button
                variant="outline"
                size="sm"
                onClick={() => onNavigate('dashboard')}
                className="flex items-center gap-2"
              >
                <ArrowLeft className="h-4 w-4" />
                Back to Dashboard
              </Button>
              <div>
                <h1 className="text-3xl font-bold mb-2">Site Management</h1>
                <p className="text-muted-foreground">
                  Configure and manage RFP scraper sites
                </p>
                {window.location.hostname.includes('github.io') && (
                  <div className="mt-2 px-3 py-1 bg-yellow-100 text-yellow-800 text-sm rounded-md border border-yellow-200">
                    📋 Static Mode: Site changes require code commits. Add sites via GitHub repository.
                  </div>
                )}
              </div>
            </div>
            
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
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-6">
        {/* Sites Overview */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-4">Site Overview</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardContent className="p-4">
                <div className="text-center">
                  <div className="text-2xl font-bold">{sites.length}</div>
                  <p className="text-sm text-muted-foreground">Total Sites</p>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="p-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {sites.filter(s => s.status === 'active').length}
                  </div>
                  <p className="text-sm text-muted-foreground">Active</p>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="p-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-red-600">
                    {sites.filter(s => s.status === 'error').length}
                  </div>
                  <p className="text-sm text-muted-foreground">Errors</p>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="p-4">
                <div className="text-center">
                  <div className="text-2xl font-bold">
                    {sites.reduce((sum, site) => sum + site.rfp_count, 0)}
                  </div>
                  <p className="text-sm text-muted-foreground">Total RFPs Found</p>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Sites List */}
        <div className="space-y-4">
          <h2 className="text-xl font-semibold">Configured Sites</h2>
          
          {sites.length === 0 ? (
            <Card>
              <CardContent className="p-8 text-center">
                <Globe className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="font-medium mb-2">No sites configured</h3>
                <p className="text-muted-foreground mb-4">
                  Add your first RFP site to start monitoring government contracts.
                </p>
                <Button onClick={() => setIsAddSiteOpen(true)}>
                  <Plus className="h-4 w-4 mr-2" />
                  Add Site
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4">
              {sites.map((site) => (
                <Card key={site.id}>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        {getStatusIcon(site.status)}
                        <div>
                          <CardTitle className="text-lg">{site.name}</CardTitle>
                          <p className="text-sm text-muted-foreground">{site.base_url}</p>
                        </div>
                      </div>
                      <Badge variant={getStatusBadgeVariant(site.status) as any}>
                        {site.status}
                      </Badge>
                    </div>
                  </CardHeader>
                  
                  <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                      <div>
                        <p className="text-sm text-muted-foreground">RFPs Found</p>
                        <p className="font-medium">{site.rfp_count}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Last Scrape</p>
                        <p className="font-medium">
                          {site.last_scrape 
                            ? new Date(site.last_scrape).toLocaleDateString()
                            : 'Never'
                          }
                        </p>
                      </div>
                      <div className="col-span-2">
                        <div className="flex gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleTestSite(site)}
                            className="flex items-center gap-1"
                          >
                            <TestTube className="h-3 w-3" />
                            Test
                          </Button>
                          
                          <Button
                            variant="outline"
                            size="sm"
                            className="flex items-center gap-1"
                          >
                            <Edit className="h-3 w-3" />
                            Edit
                          </Button>
                          
                          <Button
                            variant="outline"
                            size="sm"
                            className="flex items-center gap-1"
                          >
                            <Settings className="h-3 w-3" />
                            Configure
                          </Button>
                          
                          <Button
                            variant="destructive"
                            size="sm"
                            onClick={() => handleDeleteSite(site.id, site.name)}
                            className="flex items-center gap-1"
                          >
                            <Trash2 className="h-3 w-3" />
                            Delete
                          </Button>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
