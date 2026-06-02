import Layout from '@/components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Scale } from 'lucide-react';
import { client } from '@/lib/api';
import { useI18n } from '@/contexts/I18nContext';

export default function SignupPage() {
  const { t } = useI18n();
  return (
    <Layout>
      <div className="flex items-center justify-center min-h-[70vh] p-6">
        <Card className="max-w-md w-full">
          <CardHeader className="text-center">
            <div className="mx-auto w-14 h-14 rounded-full bg-blue-100 flex items-center justify-center mb-3">
              <Scale className="w-7 h-7 text-blue-700" />
            </div>
            <CardTitle>{t('welcome_signup')}</CardTitle>
          </CardHeader>
          <CardContent className="text-center space-y-4">
            <p className="text-slate-600">{t('please_login_desc')}</p>
            <Button
              className="w-full bg-blue-700 hover:bg-blue-800 text-white"
              onClick={() => client.auth.toLogin()}
            >
              {t('btn_login')}
            </Button>
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}