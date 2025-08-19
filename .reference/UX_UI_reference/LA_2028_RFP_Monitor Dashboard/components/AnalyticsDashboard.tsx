import { useMemo } from 'react';
import { mockRFPs } from '../data/mockData';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { ArrowLeft, TrendingUp, Calendar, Building, DollarSign } from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  ResponsiveContainer
} from 'recharts';
import { format, startOfWeek, endOfWeek, eachWeekOfInterval, subWeeks } from '../utils/dateUtils';

interface AnalyticsDashboardProps {
  onNavigate: (page: 'dashboard' | 'analytics' | 'settings' | 'ignored' | 'sites') => void;
}

export function AnalyticsDashboard({ onNavigate }: AnalyticsDashboardProps) {
  const analytics = useMemo(() => {
    const rfps = mockRFPs;
    
    // Timeline data (RFPs posted over time)
    const twelveWeeksAgo = subWeeks(new Date(), 12);
    const weeks = eachWeekOfInterval({
      start: twelveWeeksAgo,
      end: new Date()
    });
    
    const timelineData = weeks.map(week => {
      const weekStart = startOfWeek(week);
      const weekEnd = endOfWeek(week);
      
      const rfpsThisWeek = rfps.filter(rfp => {
        const postedDate = new Date(rfp.posted_date);
        return postedDate >= weekStart && postedDate <= weekEnd;
      });
      
      return {
        week: format(weekStart, 'MMM dd'),
        count: rfpsThisWeek.length,
        value: rfpsThisWeek.reduce((sum, rfp) => sum + (rfp.contract_value || 0), 0)
      };
    });

    // Procurement type distribution
    const procurementTypes = rfps.reduce((acc, rfp) => {
      const type = rfp.procurement_type || 'Unknown';
      acc[type] = (acc[type] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const procurementTypeData = Object.entries(procurementTypes).map(([type, count]) => ({
      name: type,
      value: count
    }));

    // Issuer distribution
    const issuers = rfps.reduce((acc, rfp) => {
      const issuer = rfp.issuer || 'Unknown';
      acc[issuer] = (acc[issuer] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const issuerData = Object.entries(issuers)
      .map(([issuer, count]) => ({
        name: issuer.length > 30 ? issuer.substring(0, 30) + '...' : issuer,
        count
      }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 8);

    // Event association distribution
    const eventAssociations = rfps.reduce((acc, rfp) => {
      const association = rfp.event_association || 'Other';
      acc[association] = (acc[association] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const eventData = Object.entries(eventAssociations).map(([event, count]) => ({
      name: event,
      value: count
    }));

    // Summary statistics
    const totalValue = rfps.reduce((sum, rfp) => sum + (rfp.contract_value || 0), 0);
    const averageValue = totalValue / rfps.filter(rfp => rfp.contract_value).length;
    
    const closingSoonCount = rfps.filter(rfp => {
      if (!rfp.closing_date) return false;
      const closingDate = new Date(rfp.closing_date);
      const sevenDaysFromNow = new Date();
      sevenDaysFromNow.setDate(sevenDaysFromNow.getDate() + 7);
      return closingDate <= sevenDaysFromNow;
    }).length;

    const newThisWeekCount = rfps.filter(rfp => {
      const postedDate = new Date(rfp.posted_date);
      const weekStart = startOfWeek(new Date());
      return postedDate >= weekStart;
    }).length;

    return {
      timelineData,
      procurementTypeData,
      issuerData,
      eventData,
      summary: {
        totalRFPs: rfps.length,
        totalValue,
        averageValue,
        closingSoonCount,
        newThisWeekCount,
        activeIssuers: Object.keys(issuers).length
      }
    };
  }, []);

  const COLORS = ['#2563eb', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6', '#f97316', '#06b6d4', '#84cc16'];

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
      notation: 'compact'
    }).format(amount);
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                variant="outline"
                size="sm"
                onClick={() => onNavigate('dashboard')}
                className="flex items-center gap-1"
              >
                <ArrowLeft className="h-4 w-4" />
                Back to Dashboard
              </Button>
              <div>
                <h1 className="text-2xl font-bold">Analytics Dashboard</h1>
                <p className="text-muted-foreground">
                  RFP trends and insights
                </p>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-6">
        {/* Summary Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total RFPs</CardTitle>
              <Calendar className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{analytics.summary.totalRFPs}</div>
              <p className="text-xs text-muted-foreground">
                {analytics.summary.newThisWeekCount} new this week
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Contract Value</CardTitle>
              <DollarSign className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatCurrency(analytics.summary.totalValue)}</div>
              <p className="text-xs text-muted-foreground">
                Avg: {formatCurrency(analytics.summary.averageValue)}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Issuers</CardTitle>
              <Building className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{analytics.summary.activeIssuers}</div>
              <p className="text-xs text-muted-foreground">
                Government agencies
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Closing Soon</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">{analytics.summary.closingSoonCount}</div>
              <p className="text-xs text-muted-foreground">
                Within 7 days
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Timeline Chart */}
          <Card className="col-span-1 lg:col-span-2">
            <CardHeader>
              <CardTitle>RFPs Posted Over Time</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={analytics.timelineData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="week" />
                  <YAxis />
                  <Tooltip />
                  <Line 
                    type="monotone" 
                    dataKey="count" 
                    stroke="#2563eb" 
                    strokeWidth={2}
                    name="RFPs Posted"
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Procurement Type Distribution */}
          <Card>
            <CardHeader>
              <CardTitle>RFPs by Procurement Type</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={analytics.procurementTypeData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {analytics.procurementTypeData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Event Association Distribution */}
          <Card>
            <CardHeader>
              <CardTitle>RFPs by Event Association</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={analytics.eventData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {analytics.eventData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>

        {/* Issuer Activity Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Most Active Issuing Agencies</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={analytics.issuerData} layout="horizontal">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="name" type="category" width={200} />
                <Tooltip />
                <Bar dataKey="count" fill="#2563eb" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}