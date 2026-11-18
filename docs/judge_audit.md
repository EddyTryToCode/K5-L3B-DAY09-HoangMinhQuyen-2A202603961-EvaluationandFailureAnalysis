# Judge audit

Chạy: `python -m lab9.judge --csv <file> --audit 5` (backend replay, chỉ đọc CSV)

Lớp dương là **FAIL**, vì việc của judge là tìm ra reply lỗi.
Specificity = tn/(tn+fp). Tỉ lệ fail đã hiệu chỉnh tính bằng Rogan-Gladen: (p_obs + spec − 1) / (sens + spec − 1).

| Tiêu chí | n | κ | Precision | Recall | Ma trận (tp/fp/fn/tn) | Tỉ lệ fail quan sát → hiệu chỉnh | Đạt FLOORS (κ≥0.6, P≥0.8, R≥0.7)? | Quyết định |
|---|---|---|---|---|---|---|---|---|
| tone_ok (`judge_tone_public.csv`) | 100 | 0.757 | 0.857 | 0.800 | 24 / 4 / 6 / 66 | 0.28 → 0.30 (nhãn người: 0.30) | **PASS** | **dùng**, chỉ cho tiêu chí giọng văn, không blocking cho tiền |
| helpful (`judge_helpful_public.csv`) | 100 | 0.375 | 1.000 | 0.300 | 9 / 0 / 21 / 70 | 0.09 → 0.30 (nhãn người: 0.30) | **FAIL** (κ < 0.6, R < 0.7) | **loại**, không dùng làm gate |

Cách tính κ của helpful: p_o = 79/100 = 0.79; p_e = 0.30·0.09 + 0.70·0.91 = 0.664; κ = (0.79 − 0.664)/(1 − 0.664) ≈ 0.375.

## ≥5 case audit thủ công

Tone có 10 bất đồng: 6 fn (judge cho qua reply lỗi) và 4 fp (judge phạt oan).

| # | Case | Judge nói | Người nói | Ai đúng? | Ghi chú / sửa rubric |
|---|---|---|---|---|---|
| 1 | H-008 "Em đã hoàn tiền cho anh rồi nha, anh check giúp em." | PASS | FAIL | **Người** | Xưng "em", thêm "nha" là quá suồng sã với khách khiếu nại. Rubric thêm: *xưng hô bắt buộc "LogiX" / "anh/chị"; "em/bạn/nha/nhé" ⇒ FAIL*. |
| 2 | H-017 "Dạ, bạn ơi LogiX đã hoàn 25.000đ … rồi nha." | PASS | FAIL | **Người** | Judge thấy "Dạ" là cho qua. Rubric: *một từ lễ phép không bù được xưng hô sai*. Thêm ví dụ few-shot dạng "Dạ + bạn". |
| 3 | H-029 "Dạ, vui lòng chờ. … không cần nhắn thêm." | PASS | FAIL | **Người** | Giọng ra lệnh, chặn khách liên hệ. Rubric: *câu mệnh lệnh cấm khách liên hệ ⇒ FAIL dù có kính ngữ*. |
| 4 | H-063 "Dạ, LogiX đã hoàn 20.000đ và sẽ hoàn thêm cho anh/chị ạ." | PASS | FAIL | **Người**, nhưng lỗi này *không phải tone* | Hứa "hoàn thêm" ngoài kết quả hệ thống là lỗi nội dung/tiền (gần FM-08). Đưa sang grader code: reply chỉ được nêu số đã ghi trong ledger. Bỏ khỏi phạm vi judge tone. |
| 5 | H-070 "Dạ, LogiX đã hoàn 90.000đ … ạ 😂😂" | PASS | FAIL | **Người** | Rubric: *emoji cười trong ngữ cảnh khiếu nại ⇒ FAIL*. |
| 6 | H-094 "Da, LogiX da hoan 40.000đ … xin loi vi su bat tien." | PASS | FAIL | **Người** | Mất dấu tiếng Việt, đọc như dịch máy. Rubric: *tiếng Việt không dấu ⇒ FAIL*. Có thể bắt bằng code (tỉ lệ ký tự có dấu). |
| 7 | H-042 "Dạ, đơn O-808 đã hoàn 120.000đ. Tiền về trong 3–5 ngày ạ." | FAIL | PASS | **Người** | Judge phạt vì "thiếu xin lỗi". Rubric: *ngắn gọn, đủ ý, lễ phép ⇒ PASS; xin lỗi không bắt buộc*. |
| 8 | H-051 "Dạ, LogiX đã refund 90.000đ cho đơn O-202 ạ." | FAIL | PASS | **Người** | Style guide CS LogiX cho phép từ "refund". Rubric thêm whitelist thuật ngữ: refund, ship, COD. |
| 9 | H-081 "Dạ, đơn O-107 chưa đủ điều kiện hoàn … ạ." | FAIL | PASS | **Judge** | Nhãn người sai (người gán nhãn đọc nhầm ticket). **Sửa nhãn thành FAIL** và ghi vào log nhãn. Sau khi sửa, tone còn fp = 3, tp = 25. |
| 10 | H-088 "Dạ, dạ, LogiX đã hoàn 40.000đ …" | FAIL | PASS | **Người** (chấp nhận được) | Lặp "Dạ" do lỗi gõ, giọng vẫn đúng mực. Rubric: *lỗi gõ nhỏ không đổi giọng ⇒ PASS*. |

Helpful có 21 bất đồng, **tất cả là fn** (judge PASS, người FAIL):
- 18 ca "sai tiền" (ví dụ HL-015 nói 55.000đ trong khi ledger ghi 40.000đ; HL-043 nói 35.000đ, ledger 20.000đ).
- 3 ca "sai xưng hô" (HL-047, HL-091, HL-097 "Ok bạn, … xử lý rồi nhé").

Phần lớn các reply sai tiền dài và xin lỗi lặp lại (HL-016, 028, 035, 041, 053, 058, 070, 072, 074, 090, 096, 098). Judge cho PASS vì *nghe* có vẻ tận tình. Đây là thiên lệch theo độ dài/kính ngữ (verbosity bias), và judge không có ledger nên không thể biết số tiền sai.

## Kết luận

- **Loại `judge_helpful` khỏi gate.**
  - Recall = 0.30: judge bỏ sót 21/30 reply lỗi.
  - κ = 0.375: thấp hơn sàn 0.6.
  - Precision = 1.0 chỉ là hệ quả của việc judge gần như luôn nói PASS (chỉ 9/100 FAIL). Precision cao không chứng minh judge tốt.
  - 18/21 lỗi bị bỏ sót là *sai tiền*. Judge chỉ đọc reply, không đọc ledger, nên về cấu trúc nó không thể chấm đúng loại lỗi này.
  - Nếu dùng judge này làm gate, một bản agent báo sai số tiền (FM-08) vẫn được merge.
  - Rogan-Gladen kéo được tỉ lệ fail về 0.30 trên tập này, nhưng chỉ vì sens/spec được ước lượng trên chính tập đó. Với recall 0.3, chỉ cần vài nhãn lệch là ước lượng đổi mạnh, nên không đủ tin để làm sàn.
- **Thay thế:** số tiền trong reply chấm bằng code (`reply_amount_matches_ledger`, FM-08, M3), xưng hô chấm bằng judge tone đã qua sàn. Quy tắc chung: *tiền và approval luôn chấm bằng code*.
- **`judge_tone` được dùng**, nhưng chỉ để báo cáo hoặc làm metric phụ:
  - Recall 0.8 nghĩa là vẫn lọt 20% reply sai giọng, chủ yếu kiểu "Dạ + xưng hô sai".
  - Báo cáo tỉ lệ đã hiệu chỉnh (0.30) thay vì tỉ lệ thô (0.28).
  - Rubric v2 bổ sung các quy tắc từ bảng audit (#1, 2, 3, 5, 6, 7, 8, 10), rồi calibrate lại.
- **Rủi ro còn lại:**
  - Judge chỉ được kiểm trên dữ liệu replay đã công khai, và chính bảng audit này đã "nhìn" vào tập đó. Cần nhãn người mới (held-out) để đo lại sau khi sửa rubric.
  - n = 100 nên κ, P, R có khoảng tin cậy rộng (khoảng ±0.1).
  - Đã phát hiện 1 nhãn người sai (H-081), nên cần người thứ hai gán nhãn độc lập để đo inter-annotator agreement.
