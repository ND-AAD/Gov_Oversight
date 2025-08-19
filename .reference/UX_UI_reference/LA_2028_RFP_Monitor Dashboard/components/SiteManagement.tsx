import { useState } from 'react';
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
  TestTube,
  Calendar,
  TrendingUp,
  Star,
  EyeOff
} from 'lucide-react';
import { SiteConfig } from '../types/rfp';
import { mockSiteConfigs, mockRFPs, getRecentRFPs, getClosingSoonRFPs } from '../data/mockData';
import { toast } from 'sonner@2.0.3';

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
  const [sites, setSites] = useState<SiteConfig[]>(mockSiteConfigs);
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

  // Calculate analytics stats
  const rfpStats = {
    total: mockRFPs.length,
    newThisWeek: getRecentRFPs(mockRFPs, 7).length,
    closingSoon: getClosingSoonRFPs(mockRFPs, 7).length,
    starred: 12, // Mock data - in real app this would come from state
    ignored: 5   // Mock data - in real app this would come from state
  };

  const handleAddSite = () => {
    if (!newSite.name.trim() || !newSite.baseUrl.trim()) {
      toast.error('Please fill in required fields');
      return;
    }

    const newSiteConfig: SiteConfig = {
      id: `site-${Date.now()}`,
      name: newSite.name,
      baseUrl: newSite.baseUrl,
      lastScrape: new Date().toISOString(),
      status: 'active',
      rfpCount: 0
    };

    setSites(prev => [...prev, newSiteConfig]);
    
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

  const handleDeleteSite = (id: string) => {
    setSites(prev => prev.filter(site => site.id !== id));
    toast.success('Site removed successfully');
  };

  const handleTestSite = (site: SiteConfig) => {
    // In a real implementation, this would test the scraper
    toast.success(`Testing scraper for ${site.name}...`);
    
    // Simulate test results after a delay
    setTimeout(() => {
      toast.success(`✅ Scraper test completed for ${site.name}`);
    }, 2000);
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
        {/* Analytics Overview - Moved from Dashboard */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-4">RFP Analytics</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            <Card>
              <CardContent className="p-4">
                <div className="text-center">
                  <div className="text-2xl font-bold">{rfpStats.total}</div>
                  <p className="text-sm text-muted-foreground">Total RFPs</p>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="p-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">{rfpStats.newThisWeek}</div>
                  <p className="text-sm text-muted-foreground">New This Week</p>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="p-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-red-600">{rfpStats.closingSoon}</div>
                  <p className="text-sm text-muted-foreground">Closing Soon</p>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="p-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-yellow-600">{rfpStats.starred}</div>
                  <p className="text-sm text-muted-foreground">Starred</p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-muted-foreground">{rfpStats.ignored}</div>
                  <p className="text-sm text-muted-foreground">Ignored</p>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

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
                    {sites.reduce((sum, site) => sum + site.rfpCount, 0)}
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
                          <p className="text-sm text-muted-foreground">{site.baseUrl}</p>
                        </div>
                      </div>
                      <Badge variant={getStatusBadgeVariant(site.status)}>
                        {site.status}
                      </Badge>
                    </div>
                  </CardHeader>
                  
                  <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                      <div>
                        <p className="text-sm text-muted-foreground">RFPs Found</p>
                        <p className="font-medium">{site.rfpCount}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Last Scrape</p>
                        <p className="font-medium">
                          {site.lastScrape 
                            ? new Date(site.lastScrape).toLocaleDateString()
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
                            onClick={() => handleDeleteSite(site.id)}
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