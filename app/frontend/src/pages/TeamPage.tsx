import { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import Layout from '@/components/Layout';
import AuthGuard from '@/components/AuthGuard';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Users, Crown } from 'lucide-react';
import { toast } from 'sonner';
import { client } from '@/lib/api';
import { useI18n } from '@/contexts/I18nContext';

interface OrgItem {
  id: number;
  name: string;
  plan_type: string;
  description?: string;
}
interface MemberItem {
  id: number;
  org_id: number;
  member_email: string;
  role: string;
  status?: string;
}
interface Entitlement {
  plan_type: string;
  report_quota_monthly: number;
  reports_used_month: number;
  reports_remaining: number;
  team_seats: number;
  features: string[];
}

export default function TeamPage() {
  return (
    <AuthGuard>
      <Inner />
    </AuthGuard>
  );
}

function Inner() {
  const { t } = useI18n();
  const [org, setOrg] = useState<OrgItem | null>(null);
  const [members, setMembers] = useState<MemberItem[]>([]);
  const [name, setName] = useState('');
  const [plan, setPlan] = useState('lawyer');
  const [desc, setDesc] = useState('');
  const [memberEmail, setMemberEmail] = useState('');
  const [memberRole, setMemberRole] = useState('member');
  const [loading, setLoading] = useState(false);
  const [entitlement, setEntitlement] = useState<Entitlement | null>(null);

  const canUseTeam =
    entitlement?.features?.includes('team') ||
    entitlement?.features?.includes('all') ||
    ['lawyer', 'enterprise', 'admin'].includes(entitlement?.plan_type || '');

  const loadMembers = useCallback(async (orgId: number) => {
    try {
      const r = await client.entities.organization_members.query({
        query: { org_id: orgId },
        limit: 100,
      });
      setMembers(r?.data?.items ?? []);
    } catch (e) {
      console.error(e);
    }
  }, []);

  useEffect(() => {
    (async () => {
      try {
        const r = await client.entities.organizations.query({ limit: 1 });
        const entitlementResp = await client.apiCall.invoke({
          url: '/api/v1/entitlements/me',
          method: 'GET',
        });
        setEntitlement((entitlementResp?.data ?? entitlementResp) as Entitlement);
        const items: OrgItem[] = r?.data?.items ?? [];
        if (items.length) {
          setOrg(items[0]);
          loadMembers(items[0].id);
        }
      } catch (e) {
        console.error(e);
      }
    })();
  }, [loadMembers]);

  const createOrg = async () => {
    if (!name.trim()) return;
    if (!canUseTeam) {
      toast.error('团队协作需要律师版或企业版订阅');
      return;
    }
    setLoading(true);
    try {
      const r = await client.entities.organizations.create({
        data: { name, plan_type: plan, description: desc },
      });
      const created = r?.data;
      if (created?.id) {
        setOrg(created);
        loadMembers(created.id);
        toast.success('Team created');
      }
    } catch (e) {
      console.error(e);
      toast.error('Create error');
    } finally {
      setLoading(false);
    }
  };

  const inviteMember = async () => {
    if (!org || !memberEmail.trim()) return;
    try {
      await client.entities.organization_members.create({
        data: { org_id: org.id, member_email: memberEmail, role: memberRole, status: 'invited' },
      });
      toast.success('Invited');
      setMemberEmail('');
      loadMembers(org.id);
    } catch (e) {
      console.error(e);
      toast.error('Invite error');
    }
  };

  return (
    <Layout>
      <div className="max-w-4xl mx-auto px-4 py-10 space-y-6">
        <h1 className="text-3xl font-bold text-slate-900">{t('team_title')}</h1>
        {entitlement && (
          <Card>
            <CardContent className="p-4 flex flex-wrap items-center gap-3 text-sm">
              <Badge>{entitlement.plan_type}</Badge>
              <span className="text-slate-600">
                报告额度：{entitlement.reports_used_month}/{entitlement.report_quota_monthly}
              </span>
              <span className="text-slate-600">团队席位：{entitlement.team_seats}</span>
              {!canUseTeam && (
                <Link to="/pricing" className="text-blue-700 underline">
                  升级后开启团队协作
                </Link>
              )}
            </CardContent>
          </Card>
        )}

        {!org ? (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Crown className="w-5 h-5 text-amber-500" /> {t('create_team')}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-slate-600">
                创建团队需要律师版或企业版订阅。{' '}
                <Link to="/pricing" className="text-blue-700 underline">
                  {t('cta_pricing')}
                </Link>
              </p>
              <div>
                <Label>{t('team_name')}</Label>
                <Input value={name} onChange={(e) => setName(e.target.value)} className="mt-1" />
              </div>
              <div>
                <Label>{t('team_plan')}</Label>
                <Select value={plan} onValueChange={setPlan}>
                  <SelectTrigger className="mt-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="lawyer">Lawyer</SelectItem>
                    <SelectItem value="enterprise">Enterprise</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>{t('team_desc')}</Label>
                <Textarea
                  rows={3}
                  value={desc}
                  onChange={(e) => setDesc(e.target.value)}
                  className="mt-1"
                />
              </div>
              <Button
                onClick={createOrg}
                disabled={loading || !canUseTeam}
                className="bg-blue-700 hover:bg-blue-800 text-white"
              >
                {loading ? '...' : t('create_team')}
              </Button>
            </CardContent>
          </Card>
        ) : (
          <>
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="w-5 h-5 text-blue-700" /> {org.name}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2 mb-2">
                  <Badge>{org.plan_type}</Badge>
                  <span className="text-sm text-slate-500">{org.description}</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>{t('invite_member')}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="grid sm:grid-cols-3 gap-3">
                  <Input
                    placeholder={t('member_email')}
                    value={memberEmail}
                    onChange={(e) => setMemberEmail(e.target.value)}
                  />
                  <Select value={memberRole} onValueChange={setMemberRole}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="member">Member</SelectItem>
                      <SelectItem value="admin">Admin</SelectItem>
                    </SelectContent>
                  </Select>
                  <Button
                    onClick={inviteMember}
                    className="bg-blue-700 hover:bg-blue-800 text-white"
                  >
                    {t('invite_member')}
                  </Button>
                </div>
                <div className="pt-3 border-t">
                  {members.length === 0 ? (
                    <p className="text-sm text-slate-500">No members yet.</p>
                  ) : (
                    <ul className="divide-y">
                      {members.map((m) => (
                        <li key={m.id} className="py-2 flex items-center justify-between">
                          <span>{m.member_email}</span>
                          <div className="flex gap-2">
                            <Badge variant="secondary">{m.role}</Badge>
                            {m.status && <Badge variant="outline">{m.status}</Badge>}
                          </div>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </Layout>
  );
}
