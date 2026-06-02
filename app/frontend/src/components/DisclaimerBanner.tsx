import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertTriangle } from 'lucide-react';
import { useI18n } from '@/contexts/I18nContext';

export default function DisclaimerBanner() {
  const { t } = useI18n();
  return (
    <Alert className="border-amber-300 bg-amber-50 text-amber-900">
      <AlertTriangle className="h-4 w-4 text-amber-600" />
      <AlertDescription className="text-sm">{t('disclaimer')}</AlertDescription>
    </Alert>
  );
}