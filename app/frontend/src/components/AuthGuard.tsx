import { ReactNode, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useI18n } from '@/contexts/I18nContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { client } from '@/lib/api';
import LoadingSpinner from './LoadingSpinner';
import { Scale } from 'lucide-react';

export default function AuthGuard({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  const { t } = useI18n();
  const isLocalDev =
    typeof window !== 'undefined' &&
    ['localhost', '127.0.0.1', '0.0.0.0'].includes(window.location.hostname);
  const localDevLoginUrl =
    typeof window !== 'undefined'
      ? `/api/v1/auth/dev-login?role=admin&frontend_origin=${encodeURIComponent(window.location.origin)}`
      : '/api/v1/auth/dev-login?role=admin';

  useEffect(() => {
    if (loading || user || !isLocalDev || typeof window === 'undefined') return;
    if (window.location.pathname.startsWith('/auth/')) return;
    window.location.href = localDevLoginUrl;
  }, [isLocalDev, loading, localDevLoginUrl, user]);

  if (loading || (!user && isLocalDev)) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <LoadingSpinner />
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex items-center justify-center min-h-[60vh] p-6">
        <Card className="max-w-md w-full">
          <CardHeader className="text-center">
            <div className="mx-auto w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center mb-3">
              <Scale className="w-6 h-6 text-blue-700" />
            </div>
            <CardTitle>{t('please_login')}</CardTitle>
          </CardHeader>
          <CardContent className="text-center">
            <p className="text-slate-600 mb-6">{t('please_login_desc')}</p>
            <Button
              className="w-full bg-blue-700 hover:bg-blue-800 text-white"
              onClick={() => client.auth.toLogin()}
            >
              {t('btn_login')}
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return <>{children}</>;
}
