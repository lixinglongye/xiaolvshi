import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import Layout from '@/components/Layout';
import AuthGuard from '@/components/AuthGuard';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { AlertTriangle, ArrowLeft, Briefcase, CheckCircle2, FileArchive, FolderGit2, Loader2, ShieldCheck } from 'lucide-react';
import { toast } from 'sonner';
import {
  confirmCaseImportClusters,
  importCaseZip,
  type CaseImportJob,
} from '@/lib/caseApi';

type UploadMode = 'single_case' | 'multi_case' | 'auto';

export default function LawyerImportPage() {
  return (
    <AuthGuard>
      <ImportInner />
    </AuthGuard>
  );
}

function ImportInner() {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [mode, setMode] = useState<UploadMode>('auto');
  const [submitting, setSubmitting] = useState(false);
  const [job, setJob] = useState<CaseImportJob | null>(null);
  const [confirming, setConfirming] = useState<string | null>(null);

  const submit = async () => {
    if (!file) {
      toast.error('请选择 ZIP 案件材料包');
      return;
    }
    setSubmitting(true);
    setJob(null);
    try {
      const result = await importCaseZip(file, mode);
      setJob(result);
      if (result.created_case_ids?.length) {
        toast.success(`已自动创建 ${result.created_case_ids.length} 个案件`);
      } else {
        toast.info('案件包已扫描，请确认分组后建案');
      }
    } catch (error) {
      toast.error(error instanceof Error ? error.message : '案件包导入失败');
    } finally {
      setSubmitting(false);
    }
  };

  const confirmCluster = async (cluster: CaseImportJob['clusters'][number]) => {
    if (!job) return;
    setConfirming(cluster.cluster_id);
    try {
      const result = await confirmCaseImportClusters(job.import_job_id, [{
        cluster_id: cluster.cluster_id,
        case_name: cluster.suggested_case_name,
        file_ids: cluster.file_ids,
      }]);
      toast.success('已按当前分组创建案件');
      if (result.created_case_ids?.[0]) {
        navigate(`/lawyer/cases/${result.created_case_ids[0]}`);
      }
    } catch (error) {
      toast.error(error instanceof Error ? error.message : '确认分组失败');
    } finally {
      setConfirming(null);
    }
  };

  return (
    <Layout hideFooter>
      <div className="law-container py-8 lg:py-10 space-y-6">
        <div className="flex flex-col gap-4 border-b border-stone-950/15 pb-5 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <Link to="/cases" className="mb-3 inline-flex items-center text-sm font-semibold text-stone-500 hover:text-stone-950">
              <ArrowLeft className="mr-1 h-4 w-4" />返回案件列表
            </Link>
            <div className="eyebrow mb-2">Case package ingestion</div>
            <h1 className="flex items-center gap-3 text-3xl font-semibold tracking-tight text-stone-950 sm:text-5xl">
              <FileArchive className="h-8 w-8 text-amber-700" />案件包导入
            </h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-stone-600">
              上传律师案件 ZIP，系统会先做安全解压、文件识别、OCR/解析、材料分类、案件聚类，再写入案件工作台。
            </p>
          </div>
          {job?.created_case_ids?.[0] ? (
            <Button onClick={() => navigate(`/lawyer/cases/${job.created_case_ids?.[0]}`)} className="quiet-button">
              <Briefcase className="mr-2 h-4 w-4" />进入已创建案件
            </Button>
          ) : null}
        </div>

        <div className="grid gap-6 lg:grid-cols-[420px_1fr]">
          <Card className="surface-card h-fit">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <ShieldCheck className="h-4 w-4 text-emerald-800" />导入设置
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-5">
              <label className="block cursor-pointer rounded-lg border border-dashed border-stone-950/20 bg-[#fbfaf6] p-5 transition-colors hover:border-stone-950/40">
                <div className="flex items-start gap-3">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-stone-950/10 bg-white">
                    <FileArchive className="h-5 w-5 text-stone-800" />
                  </div>
                  <div className="min-w-0">
                    <div className="truncate text-sm font-semibold text-stone-950">{file ? file.name : '选择 ZIP 案件材料包'}</div>
                    <div className="mt-1 text-xs text-stone-500">支持单案件包、多案件批量包和不确定自动判断</div>
                    {file ? <div className="mt-2 text-xs text-emerald-800">{(file.size / 1024 / 1024).toFixed(2)} MB</div> : null}
                  </div>
                </div>
                <Input type="file" accept=".zip,application/zip" className="sr-only" disabled={submitting} onChange={(event) => setFile(event.target.files?.[0] ?? null)} />
              </label>

              <div>
                <Label>本次上传类型</Label>
                <Select value={mode} onValueChange={(value) => setMode(value as UploadMode)} disabled={submitting}>
                  <SelectTrigger className="mt-1 bg-white"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="single_case">单个案件材料包</SelectItem>
                    <SelectItem value="multi_case">多个案件批量包</SelectItem>
                    <SelectItem value="auto">不确定，请系统判断</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <Button className="w-full quiet-button" disabled={!file || submitting} onClick={submit}>
                {submitting ? <><Loader2 className="h-4 w-4 animate-spin" />正在导入</> : <><FolderGit2 className="h-4 w-4" />开始扫描并建案</>}
              </Button>

              <Alert className="border-amber-200 bg-amber-50 text-amber-950">
                <AlertTriangle className="h-4 w-4 text-amber-700" />
                <AlertTitle>导入安全规则</AlertTitle>
                <AlertDescription className="text-xs leading-5">
                  后台会阻止路径穿越、执行文件、空文件和超限解压；低置信分组不会直接建案，需要律师确认。
                </AlertDescription>
              </Alert>
            </CardContent>
          </Card>

          <div className="space-y-4">
            <Card className="surface-card">
              <CardHeader>
                <CardTitle className="text-base">导入状态</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {job ? (
                  <>
                    <div className="flex flex-wrap items-center gap-3 text-sm">
                      <Badge className="bg-emerald-50 text-emerald-800 border border-emerald-200">{job.status}</Badge>
                      <span>文件 {job.parsed_files}/{job.total_files}</span>
                      <span>案件分组 {job.clusters.length}</span>
                      <span>未归类 {job.unclassified_files}</span>
                    </div>
                    <Progress value={(job.progress || 0) * 100} className="h-2" />
                    {job.warnings?.length ? (
                      <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs leading-5 text-amber-900">
                        {job.warnings.slice(0, 4).map((item) => <div key={item}>- {item}</div>)}
                      </div>
                    ) : null}
                  </>
                ) : (
                  <div className="rounded-lg border border-dashed border-stone-950/20 bg-[#efebe1]/70 p-8 text-center text-sm text-stone-500">
                    导入结果会显示案件分组、文件分类和自动建案状态。
                  </div>
                )}
              </CardContent>
            </Card>

            {job?.clusters?.length ? (
              <Card className="surface-card">
                <CardHeader>
                  <CardTitle className="text-base">案件分组建议</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {job.clusters.map((cluster) => (
                    <div key={cluster.cluster_id} className="rounded-lg border border-stone-950/12 bg-white p-4">
                      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                        <div>
                          <div className="flex flex-wrap items-center gap-2">
                            <h3 className="font-semibold text-stone-950">{cluster.suggested_case_name}</h3>
                            <Badge variant="outline">置信度 {(cluster.confidence * 100).toFixed(0)}%</Badge>
                            {cluster.needs_human_review ? <Badge className="bg-amber-100 text-amber-800">需确认</Badge> : <Badge className="bg-emerald-50 text-emerald-800">已自动处理</Badge>}
                          </div>
                          <p className="mt-2 text-xs leading-5 text-stone-500">{cluster.reason || '系统根据文件夹、文件名、主体、金额和日期线索聚类。'}</p>
                          <p className="mt-1 text-xs text-stone-500">包含 {cluster.file_count || cluster.file_ids.length} 份文件</p>
                        </div>
                        <div className="flex gap-2">
                          {cluster.case_id ? (
                            <Button size="sm" variant="outline" onClick={() => navigate(`/lawyer/cases/${cluster.case_id}`)}>
                              进入案件
                            </Button>
                          ) : (
                            <Button size="sm" disabled={confirming === cluster.cluster_id} onClick={() => confirmCluster(cluster)}>
                              {confirming === cluster.cluster_id ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle2 className="h-4 w-4" />}
                              确认建案
                            </Button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>
            ) : null}

            {job?.files?.length ? (
              <Card className="surface-card">
                <CardHeader>
                  <CardTitle className="text-base">文件扫描结果</CardTitle>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>文件</TableHead>
                        <TableHead>分类</TableHead>
                        <TableHead>状态</TableHead>
                        <TableHead>置信度</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {job.files.slice(0, 30).map((item) => (
                        <TableRow key={item.file_id}>
                          <TableCell className="max-w-[320px] truncate">{item.relative_path || item.original_name}</TableCell>
                          <TableCell>{item.evidence_category || item.doc_type}</TableCell>
                          <TableCell>{item.ocr_required ? '需OCR/复核' : item.processing_status}</TableCell>
                          <TableCell>{typeof item.confidence === 'number' ? `${(item.confidence * 100).toFixed(0)}%` : '-'}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            ) : null}
          </div>
        </div>
      </div>
    </Layout>
  );
}
