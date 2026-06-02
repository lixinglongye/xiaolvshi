import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Layout from '@/components/Layout';
import AuthGuard from '@/components/AuthGuard';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Briefcase, ArrowLeft, Save } from 'lucide-react';
import { toast } from 'sonner';
import { createCase, createCaseParty } from '@/lib/caseApi';

export default function NewCasePage() {
  return (
    <AuthGuard>
      <Inner />
    </AuthGuard>
  );
}

function Inner() {
  const navigate = useNavigate();
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    title: '',
    case_type: '',
    stage: '',
    role: '',
    client_name: '',
    opponent: '',
    amount: '',
    jurisdiction: '',
    court_or_arbitration: '',
    owner_name: '',
    team_members: '',
    key_deadline: '',
    dispute_focus: '',
    claims: '',
    missing_materials: '',
    next_steps: '',
    summary: '',
  });

  const update = (key: string, val: string) => setForm((p) => ({ ...p, [key]: val }));

  const handleSubmit = async () => {
    if (!form.title) { toast.error('请输入案件名称'); return; }
    if (!form.case_type) { toast.error('请选择案件类型'); return; }
    setSaving(true);
    try {
      const created = await createCase({
        title: form.title,
        case_type: form.case_type,
        stage: form.stage || '咨询',
        role: form.role,
        client_name: form.client_name,
        opposing_party: form.opponent,
        amount: form.amount ? Number(form.amount) : undefined,
        jurisdiction: form.jurisdiction,
        court_or_arbitration: form.court_or_arbitration,
        owner_name: form.owner_name,
        team_members: form.team_members,
        key_deadline: form.key_deadline,
        dispute_focus: form.dispute_focus,
        claims: form.claims,
        missing_materials: form.missing_materials,
        next_steps: form.next_steps,
        summary: form.summary,
        risk_level: '中',
        material_count: 0,
        evidence_completeness: '低',
      });
      if (form.client_name) {
        await createCaseParty({
          case_id: created.id,
          name: form.client_name,
          party_type: form.role || '我方',
          identity_type: '待核实',
        }).catch(() => undefined);
      }
      if (form.opponent) {
        await createCaseParty({
          case_id: created.id,
          name: form.opponent,
          party_type: form.role === '原告' ? '被告' : form.role === '申请人' ? '被申请人' : '对方当事人',
          identity_type: '待核实',
        }).catch(() => undefined);
      }
      toast.success('案件创建成功');
      navigate(`/cases/${created.id}`);
    } catch {
      toast.error('创建失败，请重试');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Layout>
      <div className="max-w-3xl mx-auto px-4 py-6 space-y-6">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm" onClick={() => navigate('/cases')}>
            <ArrowLeft className="w-4 h-4 mr-1" />返回
          </Button>
          <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <Briefcase className="w-6 h-6 text-blue-600" />新建案件
          </h1>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">案件基本信息</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <Label>案件名称 *</Label>
                <Input placeholder="例：张三与某公司服务合同纠纷" value={form.title} onChange={(e) => update('title', e.target.value)} />
              </div>

              <div>
                <Label>案件类型 *</Label>
                <Select value={form.case_type} onValueChange={(v) => update('case_type', v)}>
                  <SelectTrigger><SelectValue placeholder="选择案件类型" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="合同纠纷">合同纠纷</SelectItem>
                    <SelectItem value="劳动争议">劳动争议</SelectItem>
                    <SelectItem value="租赁纠纷">租赁纠纷</SelectItem>
                    <SelectItem value="侵权纠纷">侵权纠纷</SelectItem>
                    <SelectItem value="知识产权">知识产权</SelectItem>
                    <SelectItem value="公司纠纷">公司纠纷</SelectItem>
                    <SelectItem value="婚姻家事">婚姻家事</SelectItem>
                    <SelectItem value="刑事案件">刑事案件</SelectItem>
                    <SelectItem value="行政案件">行政案件</SelectItem>
                    <SelectItem value="其他">其他</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label>案件阶段</Label>
                <Select value={form.stage} onValueChange={(v) => update('stage', v)}>
                  <SelectTrigger><SelectValue placeholder="选择阶段" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="咨询">咨询</SelectItem>
                    <SelectItem value="诉前">诉前</SelectItem>
                    <SelectItem value="一审">一审</SelectItem>
                    <SelectItem value="二审">二审</SelectItem>
                    <SelectItem value="仲裁">仲裁</SelectItem>
                    <SelectItem value="执行">执行</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label>代理方/用户立场</Label>
                <Select value={form.role} onValueChange={(v) => update('role', v)}>
                  <SelectTrigger><SelectValue placeholder="选择立场" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="原告">原告</SelectItem>
                    <SelectItem value="被告">被告</SelectItem>
                    <SelectItem value="申请人">申请人</SelectItem>
                    <SelectItem value="被申请人">被申请人</SelectItem>
                    <SelectItem value="第三人">第三人</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label>客户姓名/公司名</Label>
                <Input placeholder="客户名称" value={form.client_name} onChange={(e) => update('client_name', e.target.value)} />
              </div>

              <div>
                <Label>对方当事人</Label>
                <Input placeholder="对方当事人名称" value={form.opponent} onChange={(e) => update('opponent', e.target.value)} />
              </div>

              <div>
                <Label>案涉金额（元）</Label>
                <Input type="number" placeholder="0" value={form.amount} onChange={(e) => update('amount', e.target.value)} />
              </div>

              <div>
                <Label>管辖地区</Label>
                <Input placeholder="例：上海" value={form.jurisdiction} onChange={(e) => update('jurisdiction', e.target.value)} />
              </div>

              <div>
                <Label>管辖法院/仲裁机构</Label>
                <Input placeholder="例：上海市浦东新区人民法院" value={form.court_or_arbitration} onChange={(e) => update('court_or_arbitration', e.target.value)} />
              </div>

              <div>
                <Label>负责人</Label>
                <Input placeholder="主办律师/负责人" value={form.owner_name} onChange={(e) => update('owner_name', e.target.value)} />
              </div>

              <div>
                <Label>团队成员</Label>
                <Input placeholder="用逗号分隔多个成员" value={form.team_members} onChange={(e) => update('team_members', e.target.value)} />
              </div>

              <div>
                <Label>关键期限</Label>
                <Input placeholder="例：2026-06-15 举证期限届满" value={form.key_deadline} onChange={(e) => update('key_deadline', e.target.value)} />
              </div>

              <div>
                <Label>诉讼请求/目标</Label>
                <Input placeholder="例：解除合同、返还押金、赔偿损失" value={form.claims} onChange={(e) => update('claims', e.target.value)} />
              </div>

              <div className="md:col-span-2">
                <Label>争议焦点</Label>
                <Textarea placeholder="列出当前已知争议焦点，可用换行分隔" rows={3} value={form.dispute_focus} onChange={(e) => update('dispute_focus', e.target.value)} />
              </div>

              <div className="md:col-span-2">
                <Label>待补材料</Label>
                <Textarea placeholder="列出身份证明、合同、付款凭证、聊天记录等待补材料" rows={3} value={form.missing_materials} onChange={(e) => update('missing_materials', e.target.value)} />
              </div>

              <div className="md:col-span-2">
                <Label>下一步建议</Label>
                <Textarea placeholder="例：补充证据、发函催告、准备起诉状" rows={3} value={form.next_steps} onChange={(e) => update('next_steps', e.target.value)} />
              </div>

              <div className="md:col-span-2">
                <Label>案件简介</Label>
                <Textarea placeholder="简要描述案件背景和争议焦点…" rows={4} value={form.summary} onChange={(e) => update('summary', e.target.value)} />
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-4">
              <Button variant="outline" onClick={() => navigate('/cases')}>取消</Button>
              <Button className="bg-blue-700 hover:bg-blue-800 text-white" onClick={handleSubmit} disabled={saving}>
                <Save className="w-4 h-4 mr-2" />{saving ? '创建中…' : '创建案件'}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}
