import { useState } from 'react';
import { Dashboard } from './components/Dashboard';
import { SiteManagement } from './components/SiteManagement';
import { SettingsPage } from './components/SettingsPage';
import { Toaster } from './components/ui/sonner';

type Page = 'dashboard' | 'analytics' | 'settings' | 'ignored' | 'sites';

export default function App() {
  const [currentPage, setCurrentPage] = useState<Page>('dashboard');

  const handleNavigate = (page: Page) => {
    setCurrentPage(page);
  };

  const renderCurrentPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <Dashboard onNavigate={handleNavigate} />;
      case 'sites':
        return <SiteManagement onNavigate={handleNavigate} />;
      case 'settings':
        return <SettingsPage onNavigate={handleNavigate} />;
      case 'analytics':
      case 'ignored':
        // For now, redirect to dashboard - in a full implementation these would have their own pages
        setCurrentPage('dashboard');
        return <Dashboard onNavigate={handleNavigate} />;
      default:
        return <Dashboard onNavigate={handleNavigate} />;
    }
  };

  return (
    <>
      {renderCurrentPage()}
      <Toaster />
    </>
  );
}