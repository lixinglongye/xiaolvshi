import { ReactNode, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Scale, Globe, User as UserIcon, LogOut, Settings as SettingsIcon, Upload, PenLine, ShieldCheck, Menu, X } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useI18n } from '@/contexts/I18nContext';
import { client } from '@/lib/api';

interface LayoutProps {
  children: ReactNode;
  hideFooter?: boolean;
}

export default function Layout({ children, hideFooter }: LayoutProps) {
  const { user } = useAuth();
  const { lang, setLang, t } = useI18n();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  const navItems = [
    ['/', t('nav_home')],
    ['/pricing', t('nav_pricing')],
    ['/dashboard', t('nav_dashboard')],
    ['/cases', t('nav_cases')],
    ['/documents', t('nav_documents')],
    ['/generate', t('nav_generate')],
    ['/team', t('nav_team')],
    ...(user?.role === 'admin' ? [['/admin', t('nav_admin')]] : []),
  ] as Array<[string, string]>;

  const navLink = (to: string, label: string) => {
    const active = location.pathname === to;
    return (
      <Link
        key={to}
        to={to}
        onClick={() => setMobileOpen(false)}
        className={`px-1 py-2 text-sm font-semibold transition-colors ${
          active ? 'text-stone-950 underline decoration-[0.12em] underline-offset-[0.2em]' : 'text-stone-600 hover:text-stone-950'
        }`}
      >
        {label}
      </Link>
    );
  };

  const handleLogin = async () => {
    try {
      await client.auth.toLogin();
    } catch (e) {
      console.error(e);
    }
  };

  const handleLogout = async () => {
    try {
      await client.auth.logout();
      window.location.href = '/';
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="app-shell flex flex-col">
      <header className="sticky top-0 z-40 border-b border-stone-950/20 bg-[#f8f5ee]/92 backdrop-blur-xl">
        <div className="law-container h-[68px] flex items-center justify-between gap-4">
          <Link to="/" className="flex items-center gap-3 min-w-0" onClick={() => setMobileOpen(false)}>
            <div className="w-10 h-10 rounded-[6px] bg-stone-950 flex items-center justify-center">
              <Scale className="w-5 h-5 text-white" />
            </div>
            <div className="leading-tight">
              <div className="font-black tracking-normal text-stone-950">{t('brand')}</div>
              <div className="text-[11px] uppercase tracking-[0.18em] text-stone-500">{t('brand_en')}</div>
            </div>
          </Link>

          <nav className="hidden lg:flex items-center gap-5">
            {navItems.map(([to, label]) => navLink(to, label))}
          </nav>

          <div className="flex items-center gap-2">
            <Button asChild size="sm" variant="outline" className="hidden xl:inline-flex soft-button">
              <Link to="/upload">
                <Upload className="w-4 h-4" />
                {t('cta_upload')}
              </Link>
            </Button>
            <Button asChild size="sm" className="hidden sm:inline-flex quiet-button">
              <Link to="/generate">
                <PenLine className="w-4 h-4" />
                {t('nav_generate')}
              </Link>
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setLang(lang === 'zh' ? 'en' : 'zh')}
              className="hidden sm:inline-flex text-stone-600"
            >
              <Globe className="w-4 h-4 mr-1" />
              {lang === 'zh' ? '中' : 'EN'}
            </Button>
            {user ? (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="outline" size="sm" className="hidden sm:inline-flex w-9 h-9 p-0 border-stone-950/25 bg-transparent">
                    <UserIcon className="w-4 h-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  {user.role === 'admin' && (
                    <DropdownMenuItem asChild>
                      <Link to="/admin">
                        <ShieldCheck className="w-4 h-4 mr-2" />
                        {t('nav_admin')}
                      </Link>
                    </DropdownMenuItem>
                  )}
                  <DropdownMenuItem asChild>
                    <Link to="/settings">
                      <SettingsIcon className="w-4 h-4 mr-2" />
                      {t('settings')}
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={handleLogout}>
                    <LogOut className="w-4 h-4 mr-2" />
                    {t('logout')}
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            ) : (
              <Button size="sm" className="hidden sm:inline-flex quiet-button" onClick={handleLogin}>
                {t('login')}
              </Button>
            )}
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="lg:hidden text-stone-950"
              aria-label={mobileOpen ? 'Close menu' : 'Open menu'}
              onClick={() => setMobileOpen((value) => !value)}
            >
              {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </Button>
          </div>
        </div>

        {mobileOpen && (
          <div className="lg:hidden border-t border-stone-950/15 bg-[#f8f5ee]">
            <nav className="law-container py-4 grid grid-cols-2 gap-x-6 gap-y-2">
              {navItems.map(([to, label]) => navLink(to, label))}
              <button
                type="button"
                onClick={() => {
                  setLang(lang === 'zh' ? 'en' : 'zh');
                  setMobileOpen(false);
                }}
                className="px-1 py-2 text-left text-sm font-semibold text-stone-600"
              >
                {lang === 'zh' ? 'English' : '中文'}
              </button>
              {user ? (
                <button
                  type="button"
                  onClick={handleLogout}
                  className="px-1 py-2 text-left text-sm font-semibold text-stone-600"
                >
                  {t('logout')}
                </button>
              ) : (
                <button
                  type="button"
                  onClick={handleLogin}
                  className="px-1 py-2 text-left text-sm font-semibold text-stone-950"
                >
                  {t('login')}
                </button>
              )}
            </nav>
          </div>
        )}
      </header>

      <main className="flex-1">{children}</main>

      {!hideFooter && <footer className="border-t border-stone-950/20 bg-[#efebe1] text-stone-600 mt-12">
        <div className="law-container py-10">
          <div className="grid md:grid-cols-[1.4fr_0.8fr_0.8fr] gap-8">
            <div>
              <div className="flex items-center gap-2 mb-3">
                <Scale className="w-5 h-5 text-stone-950" />
                <span className="font-semibold text-stone-950">
                  {t('brand')} · {t('brand_en')}
                </span>
              </div>
              <p className="text-sm leading-relaxed">{t('disclaimer')}</p>
            </div>
            <div>
              <div className="font-semibold text-stone-950 mb-3">Legal</div>
              <ul className="space-y-2 text-sm">
                <li>
                  <Link to="/legal/privacy" className="hover:text-stone-950">
                    {t('footer_privacy')}
                  </Link>
                </li>
                <li>
                  <Link to="/legal/terms" className="hover:text-stone-950">
                    {t('footer_terms')}
                  </Link>
                </li>
                <li>
                  <Link to="/legal/disclaimer" className="hover:text-stone-950">
                    {t('footer_disclaimer')}
                  </Link>
                </li>
                <li>
                  <Link to="/legal/data-deletion" className="hover:text-stone-950">
                    {t('footer_data_deletion')}
                  </Link>
                </li>
              </ul>
            </div>
            <div>
              <div className="font-semibold text-stone-950 mb-3">Product</div>
              <ul className="space-y-2 text-sm">
                <li>
                  <Link to="/pricing" className="hover:text-stone-950">
                    {t('nav_pricing')}
                  </Link>
                </li>
                <li>
                  <Link to="/upload" className="hover:text-stone-950">
                    {t('cta_upload')}
                  </Link>
                </li>
                <li>
                  <Link to="/generate" className="hover:text-stone-950">
                    {t('nav_generate')}
                  </Link>
                </li>
              </ul>
            </div>
          </div>
          <div className="border-t border-stone-950/15 mt-8 pt-6 text-xs text-stone-500 text-center">
            © {new Date().getFullYear()} {t('brand')} · {t('brand_en')}
          </div>
        </div>
      </footer>}
    </div>
  );
}
