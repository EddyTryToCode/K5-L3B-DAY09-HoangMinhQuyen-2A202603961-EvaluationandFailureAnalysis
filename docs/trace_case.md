# Trace case: từ trace tới quyết định sai đầu tiên

Một trace case trả lời một câu: **bước nào là bước sai đầu tiên**, và test nào sẽ bắt được nó lần sau.

```bash
cd src
python -m lab9.trace_case --shape seeded_regression --claim C-002 --seed 11
python -m lab9.trace_case --shape fixed --claim C-002 --seed 11   # đối chứng
```

Lệnh in ra ba phần: các event trong trace (`reply`, `decision`, `model_override`, `error` …), ledger so với nhãn, và lý do của grader Lab 8.

## Mẫu điền (mỗi bạn 1 case, lấy từ trial đang fail trong report)

| Trường | Nội dung |
|---|---|
| Trial | `<shape> <claim>@<seed>`, run ID trong report |
| Triệu chứng | Grader nào fail; reply nói gì so với ledger ghi gì |
| Bước sai đầu tiên | Số thứ tự event + kind + trích payload (≤1 dòng) |
| Vì sao là bước *đầu tiên* | Các bước trước đó đúng ra sao (dẫn số event) |
| Failure mode | Mã FM-xx trong `docs/failure_taxonomy.md` |
| Đối chứng | Cùng claim@seed trên shape `fixed`: bước đó khác thế nào |
| Regression test | Tên test + grader/assert nào bắt được; đã thấy fail trên variant lỗi và pass trên `fixed` chưa |
| Chưa chắc chắn | Điều trace không chứng minh được |

## Case của mình: `seeded_regression C-007@11` (FM-02)

```bash
python -m lab9.trace_case --shape seeded_regression --claim C-007 --seed 11
python -m lab9.trace_case --shape fixed --claim C-007 --seed 11
```

| Trường | Nội dung |
|---|---|
| Trial | `seeded_regression C-007@11`. Trong report là dòng `E-007@11` của `reports/eval_seeded_regression.json`, run ID `E-seeded_regression-20261118-28db` (sha eval set `28db4d746752`) |
| Triệu chứng | `pass_rate` (Lab 8) FAIL: `status resolved != denied`. `reply_amount_matches_ledger` FAIL: reply nói **35.000đ**, ledger `refund_vnd=0`, `refund_count=0`. Khách được báo đã hoàn tiền nhưng thực tế không có đồng nào |
| Bước sai đầu tiên | **Event 5 `reply`**: `{"text": "Dạ, LogiX đã hoàn 35.000đ cho đơn O-909."}`, kèm `status=resolved` trả về host |
| Vì sao là bước *đầu tiên* | Event 1 `handoff` đúng scope `owner_order_only`. Event 2 `investigator` đọc O-909 đúng (`delay_days=4`, của P-100). Event 3 `quote` 35.000đ theo `SHIP-LATE-03` là đúng: label `proposal_amount=35000`. Event 4 `refund_history` cho 0 lần hoàn trước, cũng đúng. Sau event 4, `issue_refund` bị host từ chối vì approval A-007 hết hạn 2020-01-01 (label `policy_denied=true`, ledger 0). Tới đây hệ thống vẫn đúng. Bước 5 là chỗ agent bỏ qua `ok=false` của host và báo resolved |
| Failure mode | **FM-02** ignore_denied, kéo theo FM-08 (reply nói số tiền ledger không có) |
| Đối chứng | `fixed C-007@11`: event 1–3 giống hệt (quote 35.000đ). Không có `refund_history` vì `pre_deducted` tắt. Host cũng từ chối, nhưng agent trả `status=denied` và reply "chưa đủ điều kiện hoàn theo chính sách hiện hành". Grader Lab 8 PASS |
| Regression test | `tests/test_lab9_trace_case.py::test_trace_case_c007_seeded_regression_is_caught`: chạy shape thật, assert `ReplyMatchesLedger` và `TrialPass` cùng FAIL. `::test_trace_case_c007_fixed_is_clean` assert cả hai PASS trên `fixed`. Metric `reply_amount_matches_ledger` trong `config/metric_spec.yaml` (blocking, min 1.0) bắt case này ở gate |
| Chưa chắc chắn | Trace không ghi event cho kết quả `issue_refund` (`ok=false`, reason). Mình suy ra việc host từ chối từ ledger = 0 và label `policy_denied`, không đọc trực tiếp từ trace. Nên đề xuất thêm event `refund_outcome` vào shape (Lab 10, vì Lab 8 bị khóa). `ApprovalBypass` **không** fire ở case này vì không có tiền đi ra (refund_count 0). Nếu host không chặn thì đây sẽ là approval bypass thật, và chỉ ledger mới cho biết điều đó |

## Quy tắc

- Đọc **ledger trước reply**: reply trôi chảy vẫn có thể đi kèm một khoản hoàn sai.
- "Bước sai đầu tiên" phải dẫn số event cụ thể, không phải "agent bị nhầm".
- Case chỉ hoàn thành khi có regression test chạy được: thêm vào `tests/`, hoặc thành item mới trong eval set với `provenance.from_trace`.
