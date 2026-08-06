# Financial Disclosure

Financial Disclosure 是一个基于 FastAPI 的财务披露处理服务，负责文件接收、事实计算、校验、引用和审计。Decimal 计算在服务端完成，模型只解释已经计算出的事实。

## 功能

- 类型化的申报和验证 API
- SEC/XBRL/HTML 来源适配与本地 Recorded 数据源
- 持久化事实、缓存、租约、验证运行和审计记录
- 本地 Tesseract OCR 质量门禁与可恢复流程
- Qwen 解释适配器和独立 live smoke

## 技术栈

Python 3.12、FastAPI、Pydantic、Decimal、Tesseract OCR。真实模型和外部来源按需配置，离线测试不访问外部网络。

## 本地启动

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m uvicorn financial_disclosure.api:app --app-dir app --host 127.0.0.1 --port 8001
```

API 文档：<http://127.0.0.1:8001/docs>。健康检查：<http://127.0.0.1:8001/health>。

## 测试

```powershell
python -m pytest -q
python -m compileall -q app tests scripts
ruff check app tests scripts
mypy app
```

## 真实服务验证

```powershell
$env:FINANCIAL_DISCLOSURE_BASE_URL = "http://127.0.0.1:8001"
python .\scripts\financial_disclosure\live_smoke.py --component health
python .\scripts\financial_disclosure\live_smoke.py --component model
python .\scripts\financial_disclosure\live_smoke.py --component ocr
```

OCR smoke 默认生成临时图片，也可以通过 `FINANCIAL_DISCLOSURE_OCR_SAMPLE` 指定本地文件。模型验证需要 `QWEN_API_KEY` 和 `QWEN_CHAT_MODEL`。退出码 `0` 表示通过，`1` 表示服务可用但校验失败，`2` 表示缺少服务或授权。

## 使用边界

请勿提交 `.env`、API key 或私有数据。Fake/Recorded 适配器仅供离线测试使用，不代表真实服务验证。

## License

MIT，见 [LICENSE](LICENSE)。
