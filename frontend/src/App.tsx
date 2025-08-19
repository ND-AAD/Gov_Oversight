import React, { useState, useEffect } from 'react'
import { Shield, AlertTriangle, Eye, Settings, Database, Activity } from 'lucide-react'
import './App.css'

// Types for our backend data
interface RFP {
  id: string
  title: string
  url: string
  source_site: string
  detected_at: string
  extracted_fields: Record<string, any>
  categories: string[]
  olympic_relevance: boolean
}

interface SiteConfig {
  id: string
  name: string
  base_url: string
  main_rfp_page_url: string
  sample_rfp_url: string
  field_mappings: FieldMapping[]
  status: 'working' | 'degraded' | 'broken' | 'untested'
}

interface FieldMapping {
  alias: string
  selector: string
  data_type: string
  training_value: string
  confidence_score: number
  status: 'working' | 'degraded' | 'broken' | 'untested'
  consecutive_failures: number
}

function App() {
  const [rfps, setRfps] = useState<RFP[]>([])
  const [siteConfigs, setSiteConfigs] = useState<SiteConfig[]>([])
  const [activeTab, setActiveTab] = useState<'dashboard' | 'sites' | 'settings'>('dashboard')
  const [surveillanceCount, setSurveillanceCount] = useState(0)

  // Mock data for demonstration - will be replaced with backend API calls
  useEffect(() => {
    // Demo data matching our validated backend
    const mockRfps: RFP[] = [
      {
        id: 'la28_ramp_208470',
        title: 'LA28 External Recruitment Agency',
        url: 'https://www.rampla.org/s/opportunity/208470',
        source_site: 'LA28 RAMP',
        detected_at: new Date().toISOString(),
        extracted_fields: {
          status: 'Withdrawn',
          organization: 'LA 28',
          post_date: '2023-06-02',
          due_date: '2024-08-01'
        },
        categories: ['recruitment', 'olympic', 'surveillance_risk'],
        olympic_relevance: true
      },
      {
        id: 'la28_ramp_training',
        title: 'LA28 Non-Workforce Training & Development',
        url: 'https://www.rampla.org/s/opportunity/training',
        source_site: 'LA28 RAMP',
        detected_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
        extracted_fields: {
          status: 'Withdrawn',
          organization: 'LA 28',
          post_date: '2023-06-02',
          due_date: '2024-07-01'
        },
        categories: ['training', 'olympic'],
        olympic_relevance: true
      }
    ]

    const mockSiteConfigs: SiteConfig[] = [
      {
        id: 'la28_ramp',
        name: 'LA28 RAMP',
        base_url: 'https://www.rampla.org',
        main_rfp_page_url: 'https://www.rampla.org/s/',
        sample_rfp_url: 'https://www.rampla.org/s/opportunity/208470',
        field_mappings: [
          {
            alias: 'status',
            selector: '*:contains("Withdrawn")',
            data_type: 'TEXT',
            training_value: 'Withdrawn',
            confidence_score: 0.95,
            status: 'working',
            consecutive_failures: 0
          },
          {
            alias: 'organization',
            selector: '*:contains("LA 28")',
            data_type: 'TEXT',
            training_value: 'LA 28',
            confidence_score: 0.92,
            status: 'working',
            consecutive_failures: 0
          }
        ],
        status: 'working'
      }
    ]

    setRfps(mockRfps)
    setSiteConfigs(mockSiteConfigs)
    setSurveillanceCount(mockRfps.filter(rfp => rfp.categories.includes('surveillance_risk')).length)
  }, [])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'working': return 'bg-green-500'
      case 'degraded': return 'bg-yellow-500'
      case 'broken': return 'bg-red-500'
      case 'untested': return 'bg-gray-500'
      default: return 'bg-gray-500'
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString()
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-3">
              <Shield className="h-8 w-8 text-olympic-blue" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Gov_Oversight</h1>
                <p className="text-sm text-gray-600">LA 2028 Olympic RFP Monitor</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2 text-sm">
                <div className="flex items-center space-x-1">
                  <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                  <span>{siteConfigs.filter(s => s.status === 'working').length} Active</span>
                </div>
                <div className="flex items-center space-x-1">
                  <AlertTriangle className="w-4 h-4 text-surveillance-warning" />
                  <span className="text-surveillance-warning font-medium">{surveillanceCount} Surveillance Risks</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {[
              { id: 'dashboard', name: 'Dashboard', icon: Activity },
              { id: 'sites', name: 'Site Configuration', icon: Database },
              { id: 'settings', name: 'Settings', icon: Settings }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-olympic-blue text-olympic-blue'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                <span>{tab.name}</span>
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'dashboard' && (
          <div className="space-y-6">
            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <Database className="h-8 w-8 text-olympic-blue" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Total RFPs</p>
                    <p className="text-2xl font-semibold text-gray-900">{rfps.length}</p>
                  </div>
                </div>
              </div>
              
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <Eye className="h-8 w-8 text-olympic-gold" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Olympic Related</p>
                    <p className="text-2xl font-semibold text-gray-900">
                      {rfps.filter(rfp => rfp.olympic_relevance).length}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <AlertTriangle className="h-8 w-8 text-surveillance-warning" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Surveillance Risks</p>
                    <p className="text-2xl font-semibold text-surveillance-warning">{surveillanceCount}</p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <Activity className="h-8 w-8 text-data-safe" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Active Sites</p>
                    <p className="text-2xl font-semibold text-gray-900">
                      {siteConfigs.filter(s => s.status === 'working').length}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Recent RFPs Table */}
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900">Recent RFPs</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Title
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Source
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Detected
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Categories
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {rfps.map((rfp) => (
                      <tr key={rfp.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            {rfp.categories.includes('surveillance_risk') && (
                              <AlertTriangle className="w-4 h-4 text-surveillance-warning mr-2" />
                            )}
                            <div>
                              <div className="text-sm font-medium text-gray-900">{rfp.title}</div>
                              <div className="text-sm text-gray-500">
                                Organization: {rfp.extracted_fields.organization}
                              </div>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {rfp.source_site}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            rfp.extracted_fields.status === 'Withdrawn' 
                              ? 'bg-red-100 text-red-800'
                              : 'bg-green-100 text-green-800'
                          }`}>
                            {rfp.extracted_fields.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatDate(rfp.detected_at)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex space-x-1">
                            {rfp.categories.map((category) => (
                              <span
                                key={category}
                                className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                                  category === 'surveillance_risk'
                                    ? 'bg-red-100 text-red-800'
                                    : category === 'olympic'
                                    ? 'bg-blue-100 text-blue-800'
                                    : 'bg-gray-100 text-gray-800'
                                }`}
                              >
                                {category}
                              </span>
                            ))}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'sites' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900">Site Configurations</h3>
                <p className="text-sm text-gray-600 mt-1">
                  Manage government procurement sites and their field mappings
                </p>
              </div>
              <div className="p-6">
                {siteConfigs.map((site) => (
                  <div key={site.id} className="border rounded-lg p-4 mb-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className={`w-3 h-3 rounded-full ${getStatusColor(site.status)}`}></div>
                        <div>
                          <h4 className="text-lg font-medium text-gray-900">{site.name}</h4>
                          <p className="text-sm text-gray-600">{site.base_url}</p>
                        </div>
                      </div>
                      <div className="text-sm text-gray-500">
                        {site.field_mappings.length} field mappings
                      </div>
                    </div>
                    
                    <div className="mt-4 grid grid-cols-2 gap-4">
                      {site.field_mappings.map((mapping, index) => (
                        <div key={index} className="bg-gray-50 rounded p-3">
                          <div className="flex items-center space-x-2">
                            <div className={`w-2 h-2 rounded-full ${getStatusColor(mapping.status)}`}></div>
                            <span className="text-sm font-medium">{mapping.alias}</span>
                            <span className="text-xs text-gray-500">
                              {Math.round(mapping.confidence_score * 100)}% confidence
                            </span>
                          </div>
                          <div className="text-xs text-gray-600 mt-1">
                            Training: "{mapping.training_value}"
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
                
                <button className="mt-4 bg-olympic-blue text-white px-4 py-2 rounded hover:bg-blue-700">
                  Add New Site
                </button>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'settings' && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Settings</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Scraping Interval</label>
                <select className="mt-1 block w-full border-gray-300 rounded-md shadow-sm">
                  <option>Every 15 minutes</option>
                  <option>Every hour</option>
                  <option>Every 6 hours</option>
                  <option>Daily</option>
                </select>
              </div>
              <div>
                <label className="flex items-center">
                  <input type="checkbox" className="rounded border-gray-300" defaultChecked />
                  <span className="ml-2 text-sm text-gray-700">Enable surveillance risk alerts</span>
                </label>
              </div>
              <div>
                <label className="flex items-center">
                  <input type="checkbox" className="rounded border-gray-300" defaultChecked />
                  <span className="ml-2 text-sm text-gray-700">Enable Olympic relevance detection</span>
                </label>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

export default App