# 律审雷达

法律文书智能审查与生成平台。当前项目由 FastAPI 后端、React/Vite 前端、本地法律知识库和文档审查算法模块组成。

## 快速入口

- 项目结构说明：[docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)
- 后端入口：`app/backend/main.py`
- 前端入口：`app/frontend/src/App.tsx`
- 合同审查知识库：`app/backend/data/legal_knowledge/contract_law_seed.json`
- 后端环境变量示例：`app/backend/.env.example`

## 本地运行

后端：

```powershell
cd D:\小律师\app\backend
.\.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000
```

前端：

```powershell
cd D:\小律师\app\frontend
corepack pnpm run dev --host 0.0.0.0 --port 3000
```

法律知识库入库：

```powershell
cd D:\小律师\app\backend
.\.venv\Scripts\python.exe scripts\update_legal_knowledge.py
```

本地未配置 `OSS_SERVICE_URL` / `OSS_API_KEY` 时，上传文件会自动落到 `app/backend/local_storage/`，用于本地测试。

## API Key 配置

后端模型网关配置在 `app/backend/.env`：

```env
APP_AI_BASE_URL=https://your-ai-gateway.example.com/v1
APP_AI_KEY=replace-with-your-key
APP_OCR_MODEL=gemini-2.5-flash
```

`app/backend/.env.example` 保留模板，不放真实密钥。
