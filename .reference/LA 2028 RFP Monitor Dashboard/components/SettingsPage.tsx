import { useState } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Switch } from './ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Separator } from './ui/separator';
import { ArrowLeft, Bell, Eye, Download, Trash2, Save } from 'lucide-react';
import { toast } from 'sonner@2.0.3';

interface SettingsPageProps {
  onNavigate: (page: 'dashboard' | 'settings' | 'ignored' | 'sites') => void;
}

export function SettingsPage({ onNavigate }: SettingsPageProps) {
  const [settings, setSettings] = useState({
    notifications: {
      emailAlerts: true,
      frequency: 'daily',
      newRFPs: true,
      closingSoon: true,
      highValue: false
    },
    display: {
      defaultView: 'grid',
      itemsPerPage: '20',
      dateFormat: 'MMM dd, yyyy',
      theme: 'system'
    },
    filters: {
      autoApplyNewThisWeek: false,
      autoApplyClosingSoon: false,
      saveFilterPresets: true
    }
  });

  const handleSettingChange = (category: string, setting: string, value: any) => {
    setSettings(prev => ({
      ...prev,
      [category]: {
        ...prev[category as keyof typeof prev],
        [setting]: value
      }
    }));
  };

  const handleSaveSettings = () => {
    // In a real app, this would save to backend/localStorage
    localStorage.setItem('rfp-monitor-settings', JSON.stringify(settings));
    toast.success('Settings saved successfully');
  };

  const handleExportData = () => {
    // In a real app, this would export actual data
    const exportData = {
      settings,
      exportDate: new Date().toISOString(),
      version: '1.0'
    };
    
    const dataStr = JSON.stringify(exportData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `rfp-monitor-export-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    
    toast.success('Data exported successfully');
  };

  const handleClearCache = () => {
    // In a real app, this would clear actual cache
    localStorage.removeItem('rfp-monitor-cache');
    toast.success('Cache cleared successfully');
  };

  const handleResetSettings = () => {
    const defaultSettings = {
      notifications: {
        emailAlerts: true,
        frequency: 'daily',
        newRFPs: true,
        closingSoon: true,
        highValue: false
      },
      display: {
        defaultView: 'grid',
        itemsPerPage: '20',
        dateFormat: 'MMM dd, yyyy',
        theme: 'system'
      },
      filters: {
        autoApplyNewThisWeek: false,
        autoApplyClosingSoon: false,
        saveFilterPresets: true
      }
    };
    
    setSettings(defaultSettings);
    toast.success('Settings reset to defaults');
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
                <h1 className="text-3xl font-bold mb-2">Settings</h1>
                <p className="text-muted-foreground">
                  Configure your RFP monitoring preferences
                </p>
              </div>
            </div>
            
            <Button onClick={handleSaveSettings} className="flex items-center gap-2">
              <Save className="h-4 w-4" />
              Save Settings
            </Button>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-6 max-w-4xl">
        <div className="space-y-6">
          {/* Notification Settings */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bell className="h-5 w-5" />
                Notification Preferences
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Email Alerts</Label>
                  <p className="text-sm text-muted-foreground">
                    Receive email notifications for new RFPs and updates
                  </p>
                </div>
                <Switch
                  checked={settings.notifications.emailAlerts}
                  onCheckedChange={(checked) => 
                    handleSettingChange('notifications', 'emailAlerts', checked)
                  }
                />
              </div>

              {settings.notifications.emailAlerts && (
                <>
                  <Separator />
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Notification Frequency</Label>
                      <Select
                        value={settings.notifications.frequency}
                        onValueChange={(value) => 
                          handleSettingChange('notifications', 'frequency', value)
                        }
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="immediate">Immediate</SelectItem>
                          <SelectItem value="daily">Daily Digest</SelectItem>
                          <SelectItem value="weekly">Weekly Summary</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <Label>Alert Types</Label>
                    
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <div>
                          <Label>New RFPs</Label>
                          <p className="text-sm text-muted-foreground">
                            Alert when new RFPs are detected
                          </p>
                        </div>
                        <Switch
                          checked={settings.notifications.newRFPs}
                          onCheckedChange={(checked) => 
                            handleSettingChange('notifications', 'newRFPs', checked)
                          }
                        />
                      </div>

                      <div className="flex items-center justify-between">
                        <div>
                          <Label>Closing Soon</Label>
                          <p className="text-sm text-muted-foreground">
                            Alert for RFPs closing within 7 days
                          </p>
                        </div>
                        <Switch
                          checked={settings.notifications.closingSoon}
                          onCheckedChange={(checked) => 
                            handleSettingChange('notifications', 'closingSoon', checked)
                          }
                        />
                      </div>

                      <div className="flex items-center justify-between">
                        <div>
                          <Label>High Value RFPs</Label>
                          <p className="text-sm text-muted-foreground">
                            Alert for RFPs over $1M in value
                          </p>
                        </div>
                        <Switch
                          checked={settings.notifications.highValue}
                          onCheckedChange={(checked) => 
                            handleSettingChange('notifications', 'highValue', checked)
                          }
                        />
                      </div>
                    </div>
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          {/* Display Settings */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Eye className="h-5 w-5" />
                Display Preferences
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Default View</Label>
                  <Select
                    value={settings.display.defaultView}
                    onValueChange={(value) => 
                      handleSettingChange('display', 'defaultView', value)
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="grid">Grid View</SelectItem>
                      <SelectItem value="list">List View</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>Items Per Page</Label>
                  <Select
                    value={settings.display.itemsPerPage}
                    onValueChange={(value) => 
                      handleSettingChange('display', 'itemsPerPage', value)
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="10">10</SelectItem>
                      <SelectItem value="20">20</SelectItem>
                      <SelectItem value="50">50</SelectItem>
                      <SelectItem value="100">100</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>Date Format</Label>
                  <Select
                    value={settings.display.dateFormat}
                    onValueChange={(value) => 
                      handleSettingChange('display', 'dateFormat', value)
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="MMM dd, yyyy">Dec 16, 2024</SelectItem>
                      <SelectItem value="dd/MM/yyyy">16/12/2024</SelectItem>
                      <SelectItem value="yyyy-MM-dd">2024-12-16</SelectItem>
                      <SelectItem value="MMMM dd, yyyy">December 16, 2024</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>Theme</Label>
                  <Select
                    value={settings.display.theme}
                    onValueChange={(value) => 
                      handleSettingChange('display', 'theme', value)
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="light">Light</SelectItem>
                      <SelectItem value="dark">Dark</SelectItem>
                      <SelectItem value="system">System</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Filter Settings */}
          <Card>
            <CardHeader>
              <CardTitle>Filter Preferences</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label>Auto-apply "New This Week" filter</Label>
                  <p className="text-sm text-muted-foreground">
                    Automatically show only new RFPs when loading the dashboard
                  </p>
                </div>
                <Switch
                  checked={settings.filters.autoApplyNewThisWeek}
                  onCheckedChange={(checked) => 
                    handleSettingChange('filters', 'autoApplyNewThisWeek', checked)
                  }
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <Label>Auto-apply "Closing Soon" filter</Label>
                  <p className="text-sm text-muted-foreground">
                    Automatically highlight RFPs closing within 7 days
                  </p>
                </div>
                <Switch
                  checked={settings.filters.autoApplyClosingSoon}
                  onCheckedChange={(checked) => 
                    handleSettingChange('filters', 'autoApplyClosingSoon', checked)
                  }
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <Label>Save Filter Presets</Label>
                  <p className="text-sm text-muted-foreground">
                    Remember your commonly used filter combinations
                  </p>
                </div>
                <Switch
                  checked={settings.filters.saveFilterPresets}
                  onCheckedChange={(checked) => 
                    handleSettingChange('filters', 'saveFilterPresets', checked)
                  }
                />
              </div>
            </CardContent>
          </Card>

          {/* Data Management */}
          <Card>
            <CardHeader>
              <CardTitle>Data Management</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-wrap gap-3">
                <Button
                  variant="outline"
                  onClick={handleExportData}
                  className="flex items-center gap-2"
                >
                  <Download className="h-4 w-4" />
                  Export All Data
                </Button>

                <Button
                  variant="outline"
                  onClick={handleClearCache}
                  className="flex items-center gap-2"
                >
                  <Trash2 className="h-4 w-4" />
                  Clear Cache
                </Button>

                <Button
                  variant="destructive"
                  onClick={handleResetSettings}
                  className="flex items-center gap-2"
                >
                  <Trash2 className="h-4 w-4" />
                  Reset to Defaults
                </Button>
              </div>

              <div className="text-sm text-muted-foreground">
                <p>• Export includes all settings and preferences</p>
                <p>• Clearing cache will improve performance but may slow initial load</p>
                <p>• Reset will restore all settings to their default values</p>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}