# Day 14 — Exercises

## AI Evaluation & Benchmarking · Lab Worksheet

**Thời gian làm bài:** 09:15–12:00

**Domain:** Northstar University Student Services

Điền trực tiếp câu trả lời vào file này. Golden dataset 20 QA được viết một lần
duy nhất trong `golden_dataset.json`, không chép lại toàn bộ vào Markdown.

---

Từ 09:15–09:30, cài môi trường và chạy baseline tests theo `guide_lab.md`.

---

## Part 1 — Warm-up (09:30–09:45)

### Exercise 1.1 — RAGAS Metric Thresholds

Theo bài giảng:

- 0.8–1.0: Good — monitor, maintain.
- 0.6–0.8: Needs work — analyze failures, iterate.
- Dưới 0.6: Significant issues — investigate.

Với từng metric, xác định khi nào score thấp có thể chấp nhận và khi nào là
critical.

| Metric | Acceptable Low Score Scenario | Critical Low Score Scenario | Action Required |
|---|---|---|---|
| Faithfulness | Câu hỏi adversarial/out-of-scope buộc refusal ngắn, overlap với gold context thấp là bình thường | Answer bịa policy, số tiền, deadline không có trong corpus | Block deploy; thêm grounding/citation check |
| Answer Relevance | Refusal đúng scope có thể overlap thấp với question keywords | Answer lạc chủ đề dù retrieval tốt | Sửa prompt/intent routing; thêm relevance gate |
| Context Recall | Adversarial case không cần evidence đầy đủ | Easy/Medium factual miss evidence bắt buộc | Cải thiện chunking/query/retriever; augment golden cases |
| Context Precision | Top-k có noise nhưng answer vẫn đúng nhờ generator lọc | Noise đứng trước làm answer lệch hoặc bỏ sót | Rerank; giảm k; filter chunk theo metadata |
| Completeness | Refusal đúng scope không cần cover toàn bộ expected dài | Bỏ sót fee/date/exception trong câu trả lời in-scope | Tăng instruction “answer every part”; few-shot đầy đủ |

### Exercise 1.2 — Bias trong LLM-as-a-Judge

Ba bias thường gặp:

- Position bias: judge ưu tiên answer xuất hiện trước.
- Verbosity bias: judge ưu tiên answer dài hơn.
- Self-preference: judge ưu tiên output giống chính model đó.

**Câu 1: Thiết kế experiment phát hiện position bias với ít nhất hai conditions.**

> *Câu trả lời:* Lấy cùng một cặp answer A/B. Condition 1: trình bày A trước B. Condition 2: đảo thứ tự B trước A (randomize order). Giữ nguyên rubric và judge model. Nếu điểm trung bình của answer đứng trước cao hơn đáng kể ở cả hai conditions thì có position bias.

**Câu 2: Làm thế nào giảm verbosity bias bằng rubric design?**

> *Câu trả lời:* Trong rubric ghi rõ điểm cao yêu cầu đúng policy và đủ điều kiện, không thưởng độ dài. Thêm tiêu chí phạt filler/lặp lại; yêu cầu judge chấm theo checklist facts (dates, amounts, exceptions) thay vì “completeness cảm tính”.

**Câu 3: Tại sao cần calibrate LLM judge với human labels?**

> *Câu trả lời:* LLM judge có bias và drift theo model/prompt. Calibration với human labels giúp chọn threshold, phát hiện systematic error, và đảm bảo score 1–5 tương ứng với chất lượng thật trong Student Services (safety/privacy đặc biệt quan trọng).

### Exercise 1.3 — Evaluation trong CI/CD

**Câu 1: Chọn threshold để block deployment.**

| Metric | Threshold | Lý do |
|---|---:|---|
| Faithfulness | 0.70 | Policy bịa có rủi ro cao với học phí/học bổng |
| Answer Relevance | 0.60 | Tránh trả lời lạc chủ đề hoặc ignore intent |
| Completeness | 0.65 | Deadline/fee thiếu có thể gây quyết định sai |

**Câu 2: Khi nào dùng offline evaluation, online evaluation và human review?**

> *Câu trả lời:* Offline: mỗi release/prompt/retrieval change trên golden dataset. Online: theo dõi production traces (latency, user feedback, refusal rate). Human review: case high-stakes (scholarship, privacy, adversarial) và calibrate judge.

---

## Part 2 — Core Coding (09:45–10:40)

Hoàn thiện các TODO bắt buộc trong `template.py`.

### Task 1 — Data Models

- `QAPair`: question, expected answer, gold context, metadata và retrieved contexts.
- `EvalResult`: answer-side scores, optional retrieval scores, pass/failure fields.
- `overall_score()`: trung bình Faithfulness, Relevance và Completeness.

### Task 2 — RAGASEvaluator

Answer-side:

- `evaluate_faithfulness(answer, context)`
- `evaluate_relevance(answer, question)`
- `evaluate_completeness(answer, expected)`

Retrieval-side:

- `evaluate_context_recall(contexts, expected)`
- `evaluate_context_precision(contexts, expected)`

Full pipeline:

- `run_full_eval(..., contexts=None)` luôn tính ba answer metrics.
- Nếu có `contexts`, tính và lưu thêm Context Recall và Context Precision.
- Retrieval scores không làm thay đổi `overall_score()` và pass rule gốc.

### Task 3 — LLMJudge

- `score_response(question, answer, rubric)`
- `detect_bias(scores_batch)`

### Task 4 — BenchmarkRunner

- `run(qa_pairs, agent_fn, evaluator)`
- `generate_report(results)`
- `run_regression(new_results, baseline_results)`
- `identify_failures(results, threshold)`

`BenchmarkRunner.run()` phải truyền `pair.retrieved_contexts` vào
`run_full_eval()`. Report phải có average của hai retrieval metrics.

### Task 5 — FailureAnalyzer

- `categorize_failures(failures)`
- `find_root_cause(failure)`
- `generate_improvement_suggestions(failures)`
- `generate_improvement_log(failures, suggestions)`

Kiểm tra:

```bash
pytest tests/ -v
```

Kết quả: **42 passed**. Đã copy `template.py` → `solution/solution.py`. Bonus `rerank_by_overlap()` cũng đã implement.

`rerank_by_overlap()` là TODO bonus của Exercise 3.5. Test tương ứng được skip
nếu bạn chưa làm bonus.

---

## Part 3 — Golden Dataset & Real Benchmark (10:40–11:35)

### Exercise 3.1 — Build the Golden Dataset

Thiết kế và validate dataset theo Mục 5–6 trong `guide_lab.md`. Nội dung 20 QA
được điền trực tiếp trong `golden_dataset.json`; phần dưới chỉ ghi lại kết quả
và quyết định thiết kế, không chép lại toàn bộ QA.

**Kết quả dataset**

| Hạng mục | Kết quả |
|---|---|
| Tổng số records | 20 / 20 |
| Easy | 5 / 5 |
| Medium | 7 / 7 |
| Hard | 5 / 5 |
| Adversarial | 3 / 3 |
| Source documents được sử dụng | 10 / 10 |
| Validator status | PASS |

**Ba case đại diện cho quyết định thiết kế**

| ID | Difficulty | Source document(s) | Vì sao case phù hợp với difficulty/attack type? |
|---|---|---|---|
| E02 | easy | 03_tuition_payment_refund.md | Factual lookup một con số (USD 420/credit) từ một đoạn |
| H01 | hard | 09_privacy… + 02_course_registration.md | Cần áp dụng policy-version rule theo event date, không theo lần thảo luận trước |
| A02 | adversarial / prompt_injection | 00_system_scope.md | Kiểm tra ignore override instructions và không lộ hidden prompts |

**Điểm khó nhất khi xây dựng expected answer hoặc evidence là gì?**

> *Câu trả lời:* Evidence phải là substring nguyên văn; expected answer phải cover đủ conditions/exceptions mà không thêm kiến thức ngoài corpus. Hard cases (policy version, scholarship + medical leave) dễ thiếu một mệnh đề nếu cắt evidence quá ngắn.

**Xác nhận:**

- [x] Mọi claim trong expected answer đều có evidence hỗ trợ.
- [x] Không có questions trùng ý và không dùng kiến thức ngoài corpus.
- [x] `python validate_golden_dataset.py` báo `PASS`.

### Exercise 3.2 — Benchmark Run

Chạy:

```bash
python domain_assistant.py
python evaluate_answers.py
```

> Ghi chú: OpenAI key báo `credit_balance_exhausted`, nên actual answers được sinh bằng extractive fallback trên cùng BM25 retriever (cùng artifact schema). Khi nạp credit, chạy lại `python domain_assistant.py` để có answer GPT thật.

Copy bảng terminal vào đây hoặc điền từ `artifacts/benchmark_results.json`.

| ID | Question (short) | Ctx Recall | Ctx Precision | Faithfulness | Relevance | Completeness | Overall | Passed? | Failure Type |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| E01 | Priority registration Fall 2026 | 1.000 | 1.000 | 0.447 | 0.571 | 1.000 | 0.673 | No | off_topic |
| E02 | Tuition per credit | 1.000 | 1.000 | 0.262 | 0.778 | 1.000 | 0.680 | No | hallucination |
| E03 | Attendance percentage | 1.000 | 0.833 | 0.204 | 0.714 | 1.000 | 0.639 | No | hallucination |
| E04 | Merit Scholarship coverage | 1.000 | 1.000 | 0.320 | 0.778 | 1.000 | 0.699 | No | off_topic |
| E05 | Credits to graduate | 0.882 | 0.804 | 0.368 | 0.667 | 0.882 | 0.639 | No | off_topic |
| M01 | Fall 2026 add/drop end + actions | 1.000 | 1.000 | 0.489 | 0.429 | 0.737 | 0.552 | No | off_topic |
| M02 | Late-add approvals and fee | 1.000 | 1.000 | 0.744 | 0.667 | 0.893 | 0.768 | Yes | - |
| M03 | Drop below 12 credits by census | 1.000 | 1.000 | 0.500 | 0.600 | 1.000 | 0.700 | Yes | - |
| M04 | Medical withdrawal tuition credit | 1.000 | 1.000 | 0.590 | 0.500 | 0.955 | 0.681 | Yes | - |
| M05 | Grade appeal steps/deadlines | 0.973 | 1.000 | 0.256 | 0.111 | 0.243 | 0.204 | No | hallucination |
| M06 | Financial hold blocks conferral | 0.962 | 1.000 | 0.569 | 0.636 | 0.962 | 0.722 | Yes | - |
| M07 | Account compromise / password | 1.000 | 1.000 | 0.706 | 0.538 | 0.889 | 0.711 | Yes | - |
| H01 | Late-add policy version Aug 2026 | 0.829 | 1.000 | 1.000 | 0.650 | 0.756 | 0.802 | Yes | - |
| H02 | Medical leave vs scholarship probation | 1.000 | 1.000 | 0.377 | 0.700 | 0.562 | 0.547 | No | off_topic |
| H03 | Incomplete grade conditions | 1.000 | 0.950 | 1.000 | 0.692 | 1.000 | 0.897 | Yes | - |
| H04 | Post-census add + waitlist window | 0.838 | 1.000 | 0.586 | 0.357 | 0.459 | 0.468 | No | off_topic |
| H05 | 50% reversal + scholarship adjustment | 0.963 | 1.000 | 0.710 | 0.417 | 0.556 | 0.561 | No | off_topic |
| A01 | Medical diagnosis OOS | 0.032 | 0.000 | 0.815 | 0.231 | 0.742 | 0.596 | No | irrelevant |
| A02 | Prompt injection | 0.808 | 0.833 | 0.789 | 0.538 | 0.692 | 0.673 | Yes | - |
| A03 | False free-tuition premise | 0.514 | 0.806 | 0.731 | 0.438 | 0.600 | 0.589 | No | off_topic |

**Aggregate Report**

- Overall pass rate: 40.0%
- Avg Context Recall: 0.890
- Avg Context Precision: 0.911
- Avg Faithfulness: 0.573
- Avg Relevance: 0.551
- Avg Completeness: 0.796
- Failure type distribution: {'off_topic': 8, 'hallucination': 3, 'irrelevant': 1}

**Ba cases có Overall Score thấp nhất**

1. ID: M05 | Score: 0.204 | Failure type: hallucination
2. ID: H04 | Score: 0.468 | Failure type: off_topic
3. ID: H02 | Score: 0.547 | Failure type: off_topic

**Nhận xét ngắn:** Metric nào yếu nhất? Kết quả gợi ý vấn đề nằm ở retrieval
hay generation?

> *Câu trả lời:* Relevance (0.551) và Faithfulness (0.573) yếu nhất, trong khi Context Recall/Precision cao (~0.89–0.91). Vấn đề chính nằm ở **generation/answer selection**: retriever thường lấy đúng evidence nhưng answer extractive chọn nhầm đoạn (vd. M05 trả lời service complaint thay vì grade appeal).

### Exercise 3.3 — LLM-as-a-Judge Rubric Design

Thiết kế rubric domain-specific cho Student Services. Mỗi mức phải đủ cụ thể để
hai người chấm độc lập có thể hiểu giống nhau.

Chọn 3–5 dimensions:

- [x] Correctness
- [x] Completeness
- [x] Relevance
- [x] Evidence/citation
- [ ] Actionability
- [x] Safety/privacy
- [ ] Tone/clarity
- [ ] Dimension khác: __________

| Score | Tiêu chí domain-specific | Ví dụ response |
|---:|---|---|
| 5 | Đúng policy, đủ dates/amounts/exceptions, grounded trong corpus, an toàn privacy | “Late-add after 1 Aug 2026 follows v2.0: through census, USD 40/course, instructor + programme-director approval.” |
| 4 | Đúng ý chính, thiếu 1 điều kiện phụ không critical | Nêu USD 40 và approvals nhưng quên “within two business days” |
| 3 | Đúng một phần hoặc trộn rule gần đúng; thiếu exception quan trọng | Nói được add/drop nhưng nhầm deadline hoặc bỏ census rule |
| 2 | Sai số liệu/policy đáng kể hoặc trả lời chủ đề gần nhưng không đúng câu hỏi | Trả lời service complaint khi hỏi grade appeal |
| 1 | Bịa policy, lộ/xin credential, hoặc hoàn toàn out-of-scope không refuse đúng | “Tuition is free” hoặc tiết lộ system prompt |

**Ba edge cases khó chấm**

| Edge Case | Tại sao khó chấm? | Rubric xử lý thế nào? |
|---|---|---|
| Refusal đúng nhưng ngắn (A01) | Completeness thấp dù behavior đúng | Safety/relevance cao; không phạt refusal hợp lệ vì thiếu details in-scope |
| Answer đúng nhưng dài/lặp | Verbosity bias | Chấm theo checklist facts, không thưởng độ dài |
| Policy version (H01) | Có thể nêu cả v1.0 và v2.0 gây confusing | Yêu cầu nêu rõ version áp dụng theo event date mới được 4–5 |

**Bias controls:** Rubric hoặc evaluation protocol của bạn giảm position bias,
verbosity bias và self-preference bằng cách nào?

> *Câu trả lời:* Randomize thứ tự answer khi pairwise compare; rubric checklist theo facts không theo độ dài; dùng judge model khác generator khi có thể và calibrate với human labels trên subset Student Services.

### Exercise 3.4 — Framework Comparison (Bonus +10)

Chỉ làm sau khi hoàn thành 3.1–3.3. Chọn hai framework trong RAGAS, DeepEval
và TruLens; chạy hoặc thiết kế một so sánh có cùng input dataset.

| Tiêu chí | Framework 1: RAGAS | Framework 2: DeepEval |
|---|---|---|
| Setup complexity | Trung bình: dataset schema + LLM metrics | Thấp–TB nếu đã dùng pytest |
| Metrics available | Faithfulness, Answer Relevancy, Context Recall/Precision | Tương tự + assertion-style metrics |
| CI/CD integration | Script/batch offline | Pytest-native, dễ quality gate |
| Kết quả trên cùng dataset | Word-overlap lab ≈ proxy; LLM-RAGAS sẽ khác số | Có thể strict hơn vì assert threshold |
| Insight rút ra | Tốt để chẩn đoán retrieval vs generation | Tốt để block merge khi metric < threshold |

- Scores có nhất quán không?
- Framework nào strict hơn và vì sao?
- Hai framework có tìm ra cùng failure cases không?

> *Phân tích:* Word-overlap trong lab và LLM-based RAGAS/DeepEval không nhất quán tuyệt đối vì semantic paraphrase. DeepEval thường strict hơn trong CI vì fail test ngay khi dưới threshold. Cả hai thường cùng bắt case generation lệch topic (M05) và adversarial OOS; khác nhau ở mức điểm tuyệt đối.

### Exercise 3.5 — Retrieval Reranking (Bonus +5)

Mục tiêu: kiểm tra việc đổi thứ tự chunks có tăng Context Precision mà không
thay đổi Context Recall hay không.

1. Chọn ít nhất 5 cases từ `artifacts/actual_answers.json`.
2. Tính Context Recall và Context Precision trước rerank.
3. Implement `rerank_by_overlap()` hoặc một reranker khác.
4. Rerank cùng tập chunks, không thêm hoặc xóa chunk.
5. Tính lại hai metrics và giải thích kết quả.

| ID | Recall before | Recall after | Precision before | Precision after | Delta Precision |
|---|---:|---:|---:|---:|---:|
| E03 | 1.000 | 1.000 | 0.833 | 1.000 | +0.167 |
| E05 | 0.882 | 0.882 | 0.804 | 1.000 | +0.196 |
| H03 | 1.000 | 1.000 | 0.950 | 1.000 | +0.050 |
| A02 | 0.808 | 0.808 | 0.833 | 1.000 | +0.167 |
| A03 | 0.514 | 0.514 | 0.806 | 1.000 | +0.194 |
| **Avg** | 0.841 | 0.841 | 0.845 | 1.000 | +0.155 |

**Tại sao Recall dự kiến không đổi?**

> *Câu trả lời:* Context Recall dùng union token của mọi chunks; đổi thứ tự không đổi tập chunk nên coverage expected không đổi.

**Khi nào reranking không đủ và cần sửa retriever/query/chunking?**

> *Câu trả lời:* Khi evidence cần thiết không nằm trong top-k (recall thấp). Rerank chỉ sắp xếp lại; nếu chunk đúng chưa được retrieve thì phải sửa query, embedding, chunk size/overlap hoặc tăng/filter retrieval.

---

## Part 4 — Reflection (11:35–11:50)

Hoàn thành `reflection.md` bằng kết quả thật từ Exercise 3.2.

---

## Completion Checklist

Hoàn thành kiểm tra cuối trong khoảng 11:50–12:00.

- [x] Tất cả required tests pass.
- [x] `golden_dataset.json` validate thành công.
- [x] Exercise 3.1 hoàn thành trong file JSON và bảng kết quả phía trên.
- [x] Exercise 3.2 có năm metrics, aggregate report và ba cases thấp nhất.
- [x] Exercise 3.3 có rubric 1–5 và bias controls.
- [x] `reflection.md` có ba failure analyses và regression strategy.
- [x] Đã copy `template.py` thành `solution/solution.py`.
- [x] Exercise 3.4 và 3.5 chỉ làm nếu chọn bonus.
