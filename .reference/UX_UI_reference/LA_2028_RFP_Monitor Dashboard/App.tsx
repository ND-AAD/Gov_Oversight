import { useState } from 'react';
import { Dashboard } from './components/Dashboard';
import { SettingsPage } from './components/SettingsPage';
import { SiteManagement } from './components/SiteManagement';
import { Toaster } from './components/ui/sonner';

type Page = 'dashboard' | 'settings' | 'ignored' | 'sites';

export default function App() {
  const [currentPage, setCurrentPage] = useState<Page>('dashboard');

  const handleNavigate = (page: Page) => {
    setCurrentPage(page);
  };

  const renderCurrentPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <Dashboard onNavigate={handleNavigate} />;
      case 'settings':
        return <SettingsPage onNavigate={handleNavigate} />;
      case 'sites':
        return <SiteManagement onNavigate={handleNavigate} />;
      case 'ignored':
        // For now, redirect to dashboard - in a full implementation this would show ignored RFPs
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