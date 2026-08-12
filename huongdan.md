# Hướng dẫn chạy lab Day 14 (tóm tắt thực tế)

Lab: **AI Evaluation & Benchmarking** — Northstar Student Services.

## 1. Đã chuẩn bị sẵn trong repo

| Thành phần | Trạng thái |
|---|---|
| `template.py` + `solution/solution.py` | Đủ TODO + bonus rerank |
| `golden_dataset.json` | 20 QA, 10/10 documents |
| `exercises.md`, `reflection.md` | Đã điền |
| `demo_server.py` + `demo/index.html` | Trang demo sản phẩm |
| `.env` | Có `OPENAI_API_KEY` + `OPENAI_MODEL` (không commit) |
| Tests | `42 passed` |
| Validator | `PASS` |

## 2. Setup môi trường (Windows PowerShell)

```powershell
cd D:\Lab1\K3_Day14_AI_Evaluation_D303_2A202601329_PhamDucHiep
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Kiểm tra:

```powershell
python -c "import openai, dotenv, pytest; print('Environment OK')"
pytest tests/ -v
python validate_golden_dataset.py
```

Kỳ vọng: **42 passed**, validator **PASS**.

## 3. API key

File `.env` (đã gitignore):

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

Chỉ cần khi chạy `domain_assistant.py` (sinh actual answers bằng OpenAI).

### Lưu ý quan trọng

1. **Đừng commit / đừng dán key lên GitHub hoặc chat công khai.**
2. Key đã từng được paste trong chat → nên **rotate/revoke** trên [OpenAI API keys](https://platform.openai.com/api-keys) rồi cập nhật lại `.env`.
3. Lần chạy gần nhất OpenAI trả `credit_balance_exhausted` → cần nạp credit tại [Billing](https://platform.openai.com/settings/organization/billing/).

## 4. Chạy RAG + benchmark (khi đã có credit)

```powershell
python domain_assistant.py
python evaluate_answers.py
```

Outputs:

- `artifacts/actual_answers.json`
- `artifacts/benchmark_results.json`

Sau đó cập nhật lại bảng Exercise 3.2 và `reflection.md` nếu số liệu đổi.

## 5. Nếu OpenAI hết credit (fallback đã dùng)

Hiện artifact trong `artifacts/` được tạo bằng **extractive fallback** trên cùng BM25 retriever (không gọi GPT), để pipeline eval vẫn chạy được.

Khi có credit, chạy lại:

```powershell
python domain_assistant.py
python evaluate_answers.py
```

để thay bằng answer GPT thật.

## 6. Trang demo sản phẩm (Northstar Eval)

Trang demo 1 page đọc artifact lab và hiển thị:
- pass rate + 5 metrics
- stratification golden dataset
- 3 cases điểm thấp nhất
- bảng 20 cases + so sánh expected vs actual

### File liên quan

| File | Vai trò |
|---|---|
| `demo_server.py` | HTTP server (stdlib, không cần package thêm) |
| `demo/index.html` | UI trang demo |
| `artifacts/benchmark_results.json` | Nguồn metrics |
| `artifacts/actual_answers.json` | Actual answers + agent info |
| `golden_dataset.json` | Expected answers / difficulty |

### Thông số mặc định

| Tham số | Mặc định | Ý nghĩa |
|---|---|---|
| `--host` | `127.0.0.1` | Chỉ mở local |
| `--port` | `8765` | Cổng HTTP |
| URL | `http://127.0.0.1:8765/` | Địa chỉ mở demo |
| `--no-browser` | off | Không tự mở trình duyệt |

### Cách chạy

```powershell
cd D:\Lab1\K3_Day14_AI_Evaluation_D303_2A202601329_PhamDucHiep
.\.venv\Scripts\Activate.ps1
python demo_server.py
```

Mở cổng khác / không auto-open browser:

```powershell
python demo_server.py --port 8899 --no-browser
```

Rồi mở trình duyệt: `http://127.0.0.1:8899/`

### API nội bộ của demo

| Endpoint | Mô tả |
|---|---|
| `GET /` | Trang demo |
| `GET /api/overview` | Tổng hợp golden + actual + benchmark |
| `GET /api/case?id=E01` | Chi tiết 1 case (golden + actual + scores) |

### Refresh dữ liệu trên demo

1. Chạy lại eval (nếu cần):
   ```powershell
   python domain_assistant.py
   python evaluate_answers.py
   ```
2. Trên trang demo bấm **Reload data** (không cần restart server).

### Điều kiện để demo có số liệu

Cần có sẵn:

```text
artifacts/actual_answers.json
artifacts/benchmark_results.json
golden_dataset.json
```

Nếu thiếu artifact, trang vẫn mở nhưng metrics sẽ báo thiếu file.

Dừng server: `Ctrl+C` trong terminal.

---

## 7. Deliverables nộp bài

| File | Kiểm tra |
|---|---|
| `solution/solution.py` | Copy từ `template.py` |
| `golden_dataset.json` | `python validate_golden_dataset.py` → PASS |
| `exercises.md` | Part 1–3 điền đủ |
| `reflection.md` | 3 failures + 5 Whys + regression |
| Không nộp | `.env`, API key |

Checklist nhanh:

```powershell
pytest tests/ -q
python validate_golden_dataset.py
```

## 8. Thứ tự làm việc khuyến nghị

```text
venv + pytest
   → validate golden dataset
   → domain_assistant.py (cần OpenAI credit)
   → evaluate_answers.py
   → python demo_server.py   # demo kết quả
   → điền/ cập nhật exercises.md + reflection.md
   → nộp solution + dataset + worksheets
```

## 9. Troubleshooting

| Lỗi | Cách xử lý |
|---|---|
| `OPENAI_API_KEY is missing` | Copy `.env.example` → `.env` và điền key |
| `429 credit_balance_exhausted` | Nạp credit OpenAI, rồi chạy lại `domain_assistant.py` |
| `ModuleNotFoundError` | Activate `.venv` và `pip install -r requirements.txt` |
| Validator FAIL vì evidence | `text` phải là substring nguyên văn trong `data/student_services/*.md` |
| Demo không mở / port bận | Đổi cổng: `python demo_server.py --port 8899` |
| Demo thiếu metrics | Chạy `python evaluate_answers.py` trước, rồi bấm Reload data |
