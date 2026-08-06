# Financial Disclosure

## 项目简介与适用场景

Financial Disclosure 是一个面向财务申报核验场景的 FastAPI 服务。它负责接收申报文件、规范化事实、执行精确计算、保存引用和验证结果，并为后续审计提供可追踪记录。

项目把数值计算与语言模型严格分开：金额、比例和容差判断使用 `Decimal` 在服务端完成，模型只能解释已经计算并带有引用的事实，不能直接从原始申报文本生成财务结论。

## 功能清单

- 提供类型化的申报接收和验证运行 API。
- 支持 SEC、XBRL、HTML 等来源适配，并保留离线 Recorded 数据源。
- 维护申报版本、修订关系、事实版本和引用锚点。
- 使用 `Decimal` 完成金额、单位和容差校验，避免浮点误差。
- 持久化事实、查询缓存、Worker 租约、验证运行和审计事件。
- 支持租约过期接管、生命周期回滚和恢复演练。
- 本地 OCR 支持图片和 PDF，包含 Tesseract、Poppler 和质量门禁。
- 可通过 Qwen 解释已计算事实，缺少真实配置时明确报告 blocked。

## 系统架构与核心流程

```text
SEC/XBRL/HTML/本地文件
        |
来源适配 -> 格式识别 -> 规范化 -> 事实抽取 -> Decimal 计算
                                      |
                               引用锚点/版本
                                      |
                       验证运行 -> 审计记录 -> 模型解释

扫描件/PDF -> Poppler 转图 -> Tesseract OCR -> 质量门禁 -> 后续规范化
```

OCR、外部来源和模型是独立适配器。任何一个外部组件不可用时，服务都会保留明确的失败或 blocked 状态，不会用离线数据覆盖真实验证结果。

## 技术栈与运行依赖

- Python 3.12、FastAPI、Pydantic
- `Decimal` 精确计算、SQLite 持久化
- Tesseract OCR、Poppler
- Qwen/DashScope 兼容接口
- Pytest、Ruff、Mypy

## 目录结构说明

```text
app/financial_disclosure/api.py          HTTP API
app/financial_disclosure/ingestion/      文件接收和版本处理
app/financial_disclosure/normalization/  数据规范化
app/financial_disclosure/formulas/       财务公式和精确计算
app/financial_disclosure/retrieval/      事实和引用检索
app/financial_disclosure/ocr/            本地 OCR 与质量门禁
app/financial_disclosure/persistence/    SQLite 持久化、缓存和租约
app/financial_disclosure/model/          离线与真实模型适配器
scripts/financial_disclosure/            live smoke 与恢复演练
tests/                                   单元、契约和集成测试
```

## 环境要求

- Python 3.12+
- Tesseract 5+（只在 OCR 验证时需要）
- Poppler 的 `pdftoppm`（只在 PDF OCR 时需要）
- 真实模型验证需要 `QWEN_API_KEY` 和 `QWEN_CHAT_MODEL`

## 本地快速启动

Windows PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m pip install uvicorn pytest ruff mypy
python -m uvicorn financial_disclosure.api:app --app-dir app --host 127.0.0.1 --port 8001
```

Linux/macOS：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m pip install uvicorn pytest ruff mypy
python -m uvicorn financial_disclosure.api:app --app-dir app --host 127.0.0.1 --port 8001
```

接口文档地址为 <http://127.0.0.1:8001/docs>，健康检查为 <http://127.0.0.1:8001/health>。

## Docker 或中间件启动方式

当前服务没有强制 Docker 依赖。SQLite、Tesseract 和 Poppler 都可以直接在本机运行；如需容器化，可基于 Python 3.12 镜像安装项目，并把数据库目录挂载到容器外。

### 持久化与 OCR

默认数据库为进程内 SQLite，适合测试。需要跨进程保留数据时设置文件路径：

```powershell
$env:FINANCIAL_DISCLOSURE_DB = ".\runtime\financial-disclosure.db"
python -m uvicorn financial_disclosure.api:app --app-dir app --port 8001
```

本地 OCR 不需要注册云服务，但需要安装 Tesseract。PDF 还需要 `pdftoppm`：

```powershell
tesseract --version
tesseract --list-langs
pdftoppm -v
```

如果 Tesseract 未加入 `PATH`，可设置 `FINANCIAL_DISCLOSURE_TESSERACT_BINARY` 指向可执行文件。OCR smoke 在未指定样例时会自动生成测试图片，不要求准备私有文件。

## 配置项和环境变量

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `FINANCIAL_DISCLOSURE_BASE_URL` | 空 | live smoke 使用的服务地址 |
| `FINANCIAL_DISCLOSURE_DB` | `:memory:` | SQLite 文件路径 |
| `FINANCIAL_DISCLOSURE_OCR_SAMPLE` | 自动生成 | OCR smoke 输入文件 |
| `FINANCIAL_DISCLOSURE_TESSERACT_BINARY` | `tesseract` | Tesseract 可执行文件 |
| `TESSDATA_PREFIX` | 系统配置 | Tesseract 语言数据目录 |
| `QWEN_API_KEY` | 空 | Qwen API 密钥，不要提交 |
| `QWEN_CHAT_MODEL` | 空 | 文本模型名称 |
| `QWEN_BASE_URL` | DashScope 兼容地址 | OpenAI-compatible API 地址 |

## 主要 API

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| `GET` | `/health` | 健康检查 |
| `POST` | `/filings` | 接收申报内容并建立文档版本 |
| `POST` | `/verification-runs` | 创建事实验证运行 |

## 请求示例与返回结果

### 接收申报

```powershell
curl.exe -X POST http://127.0.0.1:8001/filings `
  -H "Content-Type: application/json" `
  -d '{"filing_id":"filing-2026-001","form":"10-K","format":"xbrl","content":"<xbrl>...</xbrl>","version":"2026-01"}'
```

成功响应示例：

```json
{
  "filing_id": "filing-2026-001",
  "document_version_id": "doc-28ae09d88e1388c6",
  "duplicate": false,
  "amended": false
}
```

### 创建验证运行

```powershell
curl.exe -X POST http://127.0.0.1:8001/verification-runs `
  -H "Content-Type: application/json" `
  -d '{"fact_id":"revenue","value":"1200.50","unit":"USD","expected_value":"1200.50","tolerance":"0.01","citation":{"filing_id":"filing-2026-001","document_version_id":"filing-2026-001:2026-01"}}'
```

服务返回唯一 `run_id`、`accepted` 状态和本次验证使用的事实、单位、容差及引用。

## 离线测试

```powershell
python -m pytest -q
python -m compileall -q app tests scripts
ruff check app tests scripts
mypy app
```

离线测试使用 Recorded 来源和确定性模型适配器，不访问 SEC、模型或 OCR 外部服务。

## 真实服务验证

先启动 API，然后分别执行：

```powershell
$env:FINANCIAL_DISCLOSURE_BASE_URL = "http://127.0.0.1:8001"
python .\scripts\financial_disclosure\live_smoke.py --component health
python .\scripts\financial_disclosure\live_smoke.py --component model
python .\scripts\financial_disclosure\live_smoke.py --component ocr
```

模型 smoke 需要本机配置：

```powershell
$env:QWEN_API_KEY = "本地密钥"
$env:QWEN_CHAT_MODEL = "qwen-plus"
```

退出码 `0` 表示真实验证通过，`1` 表示已连接但校验失败，`2` 表示缺少依赖、服务或授权。

## 常见问题与故障排查

### OCR 报告 blocked

运行 `tesseract --list-langs`，确认至少存在 `eng`；识别中文还需要 `chi_sim`。PDF 输入同时要求 `pdftoppm` 可执行。

### 数据在重启后消失

默认使用内存 SQLite。设置 `FINANCIAL_DISCLOSURE_DB` 为仓库外或本地运行目录中的文件路径，再重启服务。

### 模型 smoke 无法运行

确认 `QWEN_API_KEY`、`QWEN_CHAT_MODEL` 和 `QWEN_BASE_URL` 在当前终端有效。模型只接收计算后的事实和引用，不会接收原始申报全文。

## 安全边界和生产注意事项

- 不提交 `.env`、API key、Cookie、Token、原始申报文件或私有日志。
- 所有金额和容差判断都由服务端 `Decimal` 完成。
- OCR 低质量结果必须通过质量门禁，不得自动进入可信事实集。
- Recorded 数据只用于离线测试，不能作为 SEC 或真实申报来源已经验证的证据。
- 真实数据库、模型、OCR 和外部来源分别验证，结果互不替代。

## License

MIT，详见 [LICENSE](LICENSE)。
