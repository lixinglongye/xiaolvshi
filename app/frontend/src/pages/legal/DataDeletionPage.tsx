import Layout from '@/components/Layout';
import { Link } from 'react-router-dom';

export default function DataDeletionPage() {
  return (
    <Layout>
      <div className="max-w-3xl mx-auto px-4 py-10 prose prose-slate">
        <h1>数据删除说明 / Data Deletion</h1>
        <p>我们尊重并保障您对个人数据的控制权。您可以通过以下方式删除您的数据：</p>
        <ol>
          <li>在"我的文书"中点击删除按钮，单份文书将被立即软删除并在 30 天内永久销毁。</li>
          <li>
            在
            <Link to="/settings" className="text-blue-700 underline">
              {' '}
              设置页面{' '}
            </Link>
            提交"数据删除请求"，描述删除范围与原因。
          </li>
          <li>邮件方式：通过反馈渠道发送删除请求，我们将在 7 个工作日内回复并处理。</li>
        </ol>
        <p>注：因法律法规要求需保留的最小操作日志（如计费、审计），将在保留期满后销毁。</p>
      </div>
    </Layout>
  );
}