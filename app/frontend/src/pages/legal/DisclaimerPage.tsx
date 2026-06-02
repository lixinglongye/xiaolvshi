import Layout from '@/components/Layout';

export default function DisclaimerPage() {
  return (
    <Layout>
      <div className="max-w-3xl mx-auto px-4 py-10 prose prose-slate">
        <h1>免责声明 / Disclaimer</h1>
        <p>
          本产品输出为 AI
          辅助生成的风险提示和文书草稿，不构成正式法律意见；复杂事项请咨询执业律师。
        </p>
        <ul>
          <li>AI 输出可能存在错误或遗漏，最终决定权在用户。</li>
          <li>不同司法辖区法律差异较大，请以最终适用法律为准。</li>
          <li>对诉讼文书、律师函等草稿，建议由执业律师签发并负责。</li>
          <li>本产品不收集亦不要求上传敏感个人信息，请用户自行脱敏。</li>
        </ul>
      </div>
    </Layout>
  );
}