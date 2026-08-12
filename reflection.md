# Day 14 — Reflection

## Evaluation Report & Failure Analysis

Dùng kết quả thật trong `artifacts/benchmark_results.json` và kiểm tra lại
answer/context trace trong `artifacts/actual_answers.json` trước khi kết luận.

> Ghi chú chạy: OpenAI báo hết credit nên actual answers dùng extractive fallback
> trên cùng BM25 retriever. Phân tích dưới đây dựa trên artifact đó.

---

## 1. Benchmark Results Summary

**Overall pass rate:** 40.0%

| Metric | Average | Min | Max | Nhận xét |
|---|---:|---:|---:|---|
| Context Recall | 0.890 | 0.032 | 1.000 | Retrieval coverage tốt trên hầu hết in-scope cases |
| Context Precision | 0.911 | 0.000 | 1.000 | Ranking khá tốt; A01 thấp vì OOS |
| Faithfulness | 0.573 | 0.204 | 1.000 | Answer đôi khi lấy đoạn không khớp gold context |
| Relevance | 0.551 | 0.111 | 0.778 | Yếu nhất — lệch intent/topic |
| Completeness | 0.796 | 0.243 | 1.000 | Tốt hơn khi extract đúng đoạn |
| Overall Score | 0.640 | 0.204 | 0.897 | Pass rate 8/20 |

**Score interpretation**

- Metrics/cases ở mức Good (0.8–1.0): Context Recall/Precision trung bình; H01/H03 overall
- Metrics/cases ở mức Needs Work (0.6–0.8): Nhiều Easy cases overall ~0.64–0.70
- Metrics/cases ở mức Significant Issues (<0.6): M05, H04, H02, A01, A03, M01, H05

**Failure type distribution**

| Failure Type | Count | Percentage |
|---|---:|---:|
| hallucination | 3 | 25% of failures (3/12) |
| irrelevant | 1 | 8% |
| incomplete | 0 | 0% |
| off_topic | 8 | 67% |
| refusal | 0 | 0% |

**Chẩn đoán tổng quan:** Vấn đề chính nằm ở retrieval, generation hay cả hai?
Dùng ít nhất hai metrics để bảo vệ kết luận.

> *Câu trả lời:* Chủ yếu **generation/answer selection**. Avg Context Recall 0.89 và Context Precision 0.91 cho thấy retriever thường có evidence; Faithfulness 0.57 và Relevance 0.55 cho thấy câu trả lời chọn/paraphrase sai đoạn hoặc thiếu focus vào question (điển hình M05).

---

## 2. Top 3 Worst Failures — 5 Whys

Phân loại failure trước khi đề xuất fix. Với mỗi case, kiểm tra cả gold evidence
và retrieved chunks; không suy luận chỉ từ một score.

### Failure 1

**ID và question:**

> *Điền:* M05 — What steps and deadlines apply before filing a formal grade appeal?

**Expected answer:**

> *Điền:* Request clarification from instructor within 5 business days; formal grade appeal within 10 business days with permitted grounds; disagreement with academic judgement alone is not enough.

**Actual answer:**

> *Điền:* Trả lời về **service complaint** (5 business days response, formal complaint 20 business days) thay vì grade appeal.

**Scores:** Context Recall: 0.973 | Context Precision: 1.000 | Faithfulness: 0.256 |
Relevance: 0.111 | Completeness: 0.243 | Overall: 0.204

**Evidence inspection:** Retriever lấy đúng/thiếu/thừa chunks nào?

> *Câu trả lời:* Retriever lấy được chunks từ appeals document (recall/precision cao), nhưng generator/extractive chọn đoạn service complaint đứng gần grade-appeal text → answer sai topic.

| Level | Question | Answer |
|---|---|---|
| Symptom | Overall rất thấp, failure=hallucination | Answer nói complaint thay vì grade appeal |
| Why 1 | Tại sao symptom xảy ra? | Answer không grounded vào đúng đoạn grade-appeal |
| Why 2 | Tại sao nguyên nhân trên xảy ra? | Chunk/complaint và grade appeal cùng document; selection kém |
| Why 3 | Tại sao vấn đề đó chưa được ngăn chặn? | Không có intent check “grade appeal vs complaint” |
| Why 4 | Tại sao cơ chế hiện tại chưa phát hiện hoặc xử lý được? | Không có faithfulness/citation gate trước khi trả lời |
| Why 5 | Root cause có thể hành động được là gì? | Thiếu prompt constraint + post-check relevance với question terms |

**Root cause từ `find_root_cause()`:**

> *Paste output:* Answer does not address the question — improve prompt clarity

**Bạn đồng ý hay không? Dẫn evidence từ trace:**

> *Câu trả lời:* Đồng ý. Relevance 0.111 và actual answer mở đầu bằng “A service complaint...” trong khi question hỏi grade appeal.

**Proposed fix cụ thể:**

> *Câu trả lời:* Thêm instruction: distinguish grade appeal vs service complaint; require citing the matching subsection; reject answers whose key entities mismatch the question.

### Failure 2

**ID và question:**

> *Điền:* H04 — After census, can a student still add a course, and how does the waitlist offer window work before census?

**Expected answer:**

> *Điền:* After census only for documented administrative error; waitlist offers 24 hours to first eligible student; waitlist does not override prerequisite/hold rules.

**Actual answer:**

> *Điền:* Mô tả add/drop + waitlist 24h nhưng **thiếu** rule “after census only administrative error”.

**Scores:** Context Recall: 0.838 | Context Precision: 1.000 | Faithfulness: 0.586 |
Relevance: 0.357 | Completeness: 0.459 | Overall: 0.468

**Evidence inspection:**

> *Câu trả lời:* Có chunk waitlist và registration; phần after-census add restriction có trong corpus nhưng không được đưa vào answer đầy đủ → incomplete/off_topic theo heuristic.

| Level | Question | Answer |
|---|---|---|
| Symptom | Vấn đề quan sát được là gì? | Missing post-census constraint; overall < 0.5 |
| Why 1 | Tại sao symptom xảy ra? | Answer chỉ cover nửa câu hỏi (waitlist) |
| Why 2 | Tại sao nguyên nhân trên xảy ra? | Multi-part question; generator dừng sớm |
| Why 3 | Tại sao vấn đề đó chưa được ngăn chặn? | Không enforce “answer every part” |
| Why 4 | Tại sao cơ chế hiện tại chưa phát hiện hoặc xử lý được? | Completeness check chỉ chạy offline sau |
| Why 5 | Root cause có thể hành động được là gì? | Thiếu multi-constraint answering + checklist |

**Root cause và proposed fix:**

> *Câu trả lời:* `find_root_cause()` → improve prompt clarity. Fix: split multi-part questions in prompt (“Part A/Part B”) và verify mỗi phần có sentence tương ứng trước khi return.

### Failure 3

**ID và question:**

> *Điền:* H02 — How does an approved medical leave interact with Merit Scholarship probation and renewal?

**Expected answer:**

> *Điền:* Medical leave pauses scholarship up to two regular terms and does not consume probation; first academic failure → one-term probation with award still active.

**Actual answer:**

> *Điền:* Nêu đúng pause + không consume probation, nhưng lệch sang voluntary leave deferral; thiếu chi tiết probation remains active.

**Scores:** Context Recall: 1.000 | Context Precision: 1.000 | Faithfulness: 0.377 |
Relevance: 0.700 | Completeness: 0.562 | Overall: 0.547

**Evidence inspection:**

> *Câu trả lời:* Retrieval đủ (recall/precision = 1.0). Generation chọn thêm voluntary-leave sentences làm giảm faithfulness/completeness so với expected.

| Level | Question | Answer |
|---|---|---|
| Symptom | Vấn đề quan sát được là gì? | Partial answer; faithfulness thấp dù retrieval tốt |
| Why 1 | Tại sao symptom xảy ra? | Answer lẫn rule liên quan nhưng không phải trọng tâm |
| Why 2 | Tại sao nguyên nhân trên xảy ra? | Top chunks chứa nhiều scholarship rules |
| Why 3 | Tại sao vấn đề đó chưa được ngăn chặn? | Không rank sentences theo overlap với question constraints |
| Why 4 | Tại sao cơ chế hiện tại chưa phát hiện hoặc xử lý được? | Offline metrics bắt sau, không có online filter |
| Why 5 | Root cause có thể hành động được là gì? | Cần sentence-level rerank/filtering theo question entities |

**Root cause và proposed fix:**

> *Câu trả lời:* `find_root_cause()` → Context is missing or irrelevant — improve retrieval (heuristic vì faithfulness thấp nhất). Một phần đúng ở sentence selection; fix thực tế: sentence rerank + require covering “probation” and “pauses” jointly.

---

## 3. Failure Clustering

Một root cause có thể tạo ra nhiều failures. Nhóm theo nguyên nhân có thể sửa,
không chỉ nhóm theo tên metric.

| Cluster | Root Cause | Failure IDs | Priority |
|---|---|---|---|
| 1 | Answer selection/topic confusion trong cùng document | M05, E02, E03 | High |
| 2 | Multi-part question thiếu constraint | H04, H05, M01 | High |
| 3 | Adversarial/false premise handling còn yếu về relevance scoring | A01, A03 | Medium |

**Nếu chỉ được sửa một cluster, bạn chọn cluster nào và vì sao?**

> *Câu trả lời:* Cluster 1 — sửa intent/topic selection mang lại impact lớn nhất vì nhiều failures “hallucination/off_topic” xảy ra dù retrieval đã tốt.

---

## 4. Improvement Log

Paste output của `generate_improvement_log()`:

```text
| Failure ID | Type | Root Cause | Suggested Fix | Status |
|------------|------|------------|---------------|--------|
| F001 | off_topic | Context is missing or irrelevant — improve retrieval | Implement hallucination checker to filter unsupported claims | Open |
| F002 | hallucination | Context is missing or irrelevant — improve retrieval | Clarify prompts and add intent checks so answers address the question | Open |
| F003 | hallucination | Context is missing or irrelevant — improve retrieval | Tighten intent detection and topic routing to reduce off-topic replies | Open |
| F004 | off_topic | Context is missing or irrelevant — improve retrieval |  | Open |
| F005 | off_topic | Context is missing or irrelevant — improve retrieval |  | Open |
| F006 | off_topic | Answer does not address the question — improve prompt clarity |  | Open |
| F007 | hallucination | Answer does not address the question — improve prompt clarity |  | Open |
| F008 | off_topic | Context is missing or irrelevant — improve retrieval |  | Open |
| F009 | off_topic | Answer does not address the question — improve prompt clarity |  | Open |
| F010 | off_topic | Answer does not address the question — improve prompt clarity |  | Open |
| F011 | irrelevant | Answer does not address the question — improve prompt clarity |  | Open |
| F012 | off_topic | Answer does not address the question — improve prompt clarity |  | Open |
```

**Ba improvement suggestions ưu tiên**

1. Implement hallucination checker to filter unsupported claims
2. Clarify prompts and add intent checks so answers address the question
3. Tighten intent detection and topic routing to reduce off-topic replies

Với mỗi suggestion, nêu metric dự kiến thay đổi và cách đo lại.

| Suggestion | Target metric | Verification method |
|---|---|---|
| Hallucination checker / citation gate | Faithfulness | Re-run evaluate_answers.py; avg faithfulness + fewer hallucination labels |
| Prompt clarity + answer-every-part | Completeness, Relevance | Compare H04/H05/M01 overall before/after |
| Intent/topic routing | Relevance, off_topic count | Failure type distribution; M05 must pass |

---

## 5. Regression Testing Strategy

**Câu 1: Khi nào chạy `run_regression()` trong production workflow?**

> *Câu trả lời:* Mỗi PR đổi prompt, retriever, chunking, model, hoặc guardrail; và trước demo/release như quality gate so với baseline artifact.

**Câu 2: Threshold drop 0.05 có phù hợp Student Services không? Vì sao?**

> *Câu trả lời:* Phù hợp làm alert mặc định. Với Faithfulness/safety có thể chặt hơn (0.02–0.03) vì sai policy học phí/học bổng rủi ro cao; Relevance có thể giữ 0.05 vì paraphrase làm score dao động.

**Câu 3: Metric/failure nào phải block deployment, metric nào chỉ alert?**

> *Câu trả lời:* Block: Faithfulness < 0.70, bất kỳ increase hallucination/privacy leak trên adversarial set. Alert: Context Precision nhỏ drop, Completeness borderline, latency/cost.

**Câu 4: Điền evaluation stages vào flow.**

```text
Code/prompt/retrieval change → [offline golden eval] → [regression vs baseline] → [human spot-check high-risk] → Deploy
```

> *Giải thích:* Offline đảm bảo metrics; regression phát hiện drop > 0.05; human review cho adversarial/privacy trước khi ship.

---

## 6. Continuous Improvement Loop

```text
Evaluate → Analyze → Improve → Augment benchmark → Repeat
```

| Priority | Action | Metric dự kiến cải thiện | Expected impact |
|---:|---|---|---|
| 1 | Intent routing grade-appeal vs complaint | Relevance, Faithfulness | Fix M05-class failures |
| 2 | Multi-part answer checklist | Completeness | Nâng H04/H05 |
| 3 | Sentence-level rerank before answer | Faithfulness, Context Precision | Ít chọn đoạn nhiễu |

**Hai hoặc ba failure cases nào cần thêm vào benchmark ở vòng tiếp theo?**

> *Câu trả lời:* (1) Grade appeal vs complaint near-miss, (2) Multi-deadline question (add/drop + census + refund), (3) Scholarship + medical leave + probation combo tương tự H02 với wording khác.

---

## 7. Final Reflection

**Điều gì trong kết quả benchmark trái với dự đoán ban đầu của bạn?**

> *Câu trả lời:* Easy cases không hẳn dễ pass: retrieval gần như hoàn hảo nhưng extractive/generation vẫn fail faithfulness vì lấy thừa context. Ngược lại một số Hard (H01/H03) pass vì evidence tập trung và overlap cao.

**Word-overlap heuristics trong lab có giới hạn gì? Nếu đưa hệ thống vào
production, bạn sẽ thay hoặc bổ sung metric nào?**

> *Câu trả lời:* Không hiểu paraphrase/synonym; phạt refusal đúng; không đo safety sâu. Production nên dùng LLM-based Faithfulness/Answer Relevancy (RAGAS/DeepEval), plus human/LLM judge trên safety/privacy, và citation exact-match cho dates/amounts.
