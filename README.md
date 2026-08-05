# Financial Disclosure

## 项目简介

Financial Disclosure 是基于 FastAPI 的财务披露核验服务。系统接收版本化 filing，固定来源和 citation，使用 Decimal 完成数值计算，并通过可恢复的验证运行和审计链输出结果。默认离线运行；真实模型、SEC/XBRL/HTML 来源与本地 OCR 分别通过 live smoke 验证。

## 核心能力

- Filing、事实、查询缓存、worker lease、verification run 和 audit 的版本化持久化。
- Decimal 公式保留单位、精度、舍入规则和输入血缘，模型不能替代数值计算。
- SEC、XBRL、HTML 来源适配器，重复摄取保持幂等并保留来源版本。
- Qwen 解释适配器只解释已经计算的事实，输出必须保留 citation。
- Tesseract 本地 OCR 具有置信度、覆盖率和质量门禁，失败保持 blocked/review。
- 生命周期切换、回滚、缓存恢复、租约恢复、故障演练和 OTel 脱敏。

## 技术栈与架构

- Python 3.12、FastAPI、Pydantic、Decimal、pytest、Ruff、Mypy。
- PostgreSQL 持久化适配层，迁移位于 `migrations/financial_disclosure/`。
- SEC/XBRL/HTML 来源、Qwen、Tesseract、OTel 均通过端口和适配器接入。
- 离线路径使用固定测试数据和离线适配器，不访问真实网络。

## 本地启动

```powershell
Set-Location "D:\Code\agent study\managed-projects\financial-disclosure"
& "D:\py\py3.12\python.exe" -m uvicorn financial_disclosure.api:app `
  --app-dir app --host 127.0.0.1 --port 8001
```

服务地址为 `http://127.0.0.1:8001`，OpenAPI 页面为 `http://127.0.0.1:8001/docs`，健康检查为 `http://127.0.0.1:8001/health`。

## 主要 API

| 方法与路径 | 用途 |
| --- | --- |
| `POST /filings` | 创建 filing 并记录来源身份 |
| `GET /filings/{id}` | 查询 filing 当前版本和状态 |
| `POST /verification-runs` | 创建只读核验运行 |
| `GET /verification-runs/{id}/timeline` | 查询核验状态、事实和审计时间线 |
| `GET /health` | 返回服务健康状态 |

## 离线测试

```powershell
Set-Location "D:\Code\agent study\managed-projects\financial-disclosure"
& "D:\py\py3.12\python.exe" -m pytest -q -p no:cacheprovider
& "D:\py\py3.12\python.exe" -m compileall -q app tests scripts
& "D:\py\py3.12\python.exe" -m ruff check app tests scripts
& "D:\py\py3.12\python.exe" -m mypy app
```

离线测试与真实服务验证分开保存；固定测试数据不能代替外部服务结果。

## 真实服务验证

```powershell
$env:FINANCIAL_DISCLOSURE_BASE_URL = "http://127.0.0.1:8001"

& "D:\py\py3.12\python.exe" ".\scripts\financial_disclosure\live_smoke.py" --component health
& "D:\py\py3.12\python.exe" ".\scripts\financial_disclosure\live_smoke.py" --component model
& "D:\py\py3.12\python.exe" ".\scripts\financial_disclosure\live_smoke.py" --component ocr
```

模型验证需要 `QWEN_API_KEY`、`QWEN_CHAT_MODEL`，可选 `QWEN_BASE_URL`。OCR smoke 默认生成临时测试图，也可通过 `FINANCIAL_DISCLOSURE_OCR_SAMPLE` 指定本地 PDF/图片；本地 Tesseract 不可用时明确返回 blocked。

live smoke 退出码：退出码 `0` 表示真实验证通过，退出码 `1` 表示服务已连接但验证失败，退出码 `2` 表示缺少密钥、授权或服务而 blocked。

## 安全与使用边界

- 密钥只通过本机环境变量或未提交的 `.env` 注入，禁止提交密钥、Cookie、Token 和私有数据。
- Decimal 计算、来源 citation、权限校验和审计事实不能由模型绕过或覆盖。
- 外部来源、数据库、模型、OCR 和 OTel 未配置时保持 blocked/unverified，不静默降级为真实通过。
- 迁移必须可回滚，旧审计事实保留；缓存和 lease 必须支持恢复。

## License

本项目采用 MIT License，完整条款见 [LICENSE](LICENSE)。
