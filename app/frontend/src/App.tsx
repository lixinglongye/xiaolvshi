import { Toaster } from '@/components/ui/sonner';
import { TooltipProvider } from '@/components/ui/tooltip';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { I18nProvider, useI18n } from './contexts/I18nContext';
import PointerSpotlight from './components/PointerSpotlight';
import { normalizeEnglishStaticText } from './lib/staticEnglishText';
import BlogRoutes from './blog-routes';
import Index from './pages/Index';
import AuthCallback from './pages/AuthCallback';
import AuthError from './pages/AuthError';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import LogoutCallbackPage from './pages/LogoutCallbackPage';
import PricingPage from './pages/PricingPage';
import DashboardPage from './pages/DashboardPage';
import UploadPage from './pages/UploadPage';
import ReviewProgressPage from './pages/ReviewProgressPage';
import ReportPage from './pages/ReportPage';
import DeepReportPage from './pages/DeepReportPage';
import GeneratePage from './pages/GeneratePage';
import DocumentsPage from './pages/DocumentsPage';
import CasesPage from './pages/CasesPage';
import NewCasePage from './pages/NewCasePage';
import CaseDetailPage from './pages/CaseDetailPage';
import LawyerImportPage from './pages/LawyerImportPage';
import PipelineConfigPage from './pages/PipelineConfigPage';
import ModelOpsPage from './pages/ModelOpsPage';
import TeamPage from './pages/TeamPage';
import SettingsPage from './pages/SettingsPage';
import AdminPage from './pages/AdminPage';
import PaymentSuccessPage from './pages/PaymentSuccessPage';
import PrivacyPage from './pages/legal/PrivacyPage';
import TermsPage from './pages/legal/TermsPage';
import DisclaimerPage from './pages/legal/DisclaimerPage';
import DataDeletionPage from './pages/legal/DataDeletionPage';

const queryClient = new QueryClient();

const DocumentLanguage = () => {
  const { lang, t } = useI18n();

  useEffect(() => {
    document.documentElement.lang = lang === 'zh' ? 'zh-CN' : 'en';
    document.title = lang === 'zh' ? `${t('brand')} · ${t('brand_en')}` : 'LawAudit Radar';
    if (lang === 'en') {
      const stop = normalizeEnglishStaticText();
      return stop;
    }
  }, [lang, t]);

  return null;
};

const AppRoutes = () => (
  <Routes>
    <Route path="/" element={<Index />} />
    <Route path="/auth/callback" element={<AuthCallback />} />
    <Route path="/auth/error" element={<AuthError />} />
    <Route path="/logout-callback" element={<LogoutCallbackPage />} />
    <Route path="/login" element={<LoginPage />} />
    <Route path="/signup" element={<SignupPage />} />
    <Route path="/pricing" element={<PricingPage />} />
    <Route path="/dashboard" element={<DashboardPage />} />
    <Route path="/upload" element={<UploadPage />} />
    <Route path="/review/:id" element={<ReviewProgressPage />} />
    <Route path="/report/:id" element={<ReportPage />} />
    <Route path="/deep-report/:id" element={<DeepReportPage />} />
    <Route path="/generate" element={<GeneratePage />} />
    <Route path="/documents" element={<DocumentsPage />} />
    <Route path="/cases" element={<CasesPage />} />
    <Route path="/cases/new" element={<NewCasePage />} />
    <Route path="/cases/:id" element={<CaseDetailPage />} />
    <Route path="/lawyer/import" element={<LawyerImportPage />} />
    <Route path="/lawyer/cases/:id" element={<CaseDetailPage />} />
    <Route path="/pipeline" element={<PipelineConfigPage />} />
    <Route path="/model-ops" element={<ModelOpsPage />} />
    <Route path="/team" element={<TeamPage />} />
    <Route path="/settings" element={<SettingsPage />} />
    <Route path="/admin" element={<AdminPage />} />
    <Route path="/payment-success" element={<PaymentSuccessPage />} />
    <Route path="/legal/privacy" element={<PrivacyPage />} />
    <Route path="/legal/terms" element={<TermsPage />} />
    <Route path="/legal/disclaimer" element={<DisclaimerPage />} />
    <Route path="/legal/data-deletion" element={<DataDeletionPage />} />
    <Route path="/blog/*" element={<BlogRoutes />} />
  </Routes>
);

const App = () => (
  <QueryClientProvider client={queryClient}>
    <I18nProvider>
      <AuthProvider>
        <TooltipProvider>
          <DocumentLanguage />
          <PointerSpotlight />
          <Toaster />
          <BrowserRouter>
            <AppRoutes />
          </BrowserRouter>
        </TooltipProvider>
      </AuthProvider>
    </I18nProvider>
  </QueryClientProvider>
);

export default App;
