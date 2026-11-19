# Báo cáo nhóm 13

## 1. Số liệu luyện tập
- F1 theo seed, đo bằng `scripts/score_findings.py` chế độ học viên (chỉ in F1 làm tròn 1 chữ số; nhóm không đọc `_private`, không dùng `--truth-dir`):

  | Lô | Lỗi luật validator báo | Ứng viên đối chiếu | F1 rule | F1 cross_check | F1 overall |
  |---|---:|---:|---:|---:|---:|
  | r13007 (seed luyện tập, sau review mắt) | 12 | 10 | ≈ 1.0 | ≈ 1.0 | ≈ 1.0 |
  | r11 (seed phụ) | 13 | 8 | ≈ 1.0 | (không review) | — |
  | r22 (seed phụ) | 9 | 9 | ≈ 1.0 | (không review) | — |
  | clean (seed 5, pool calib, `--no-faults`) | 0 | 1 | 1.0 | 1.0 | 1.0 |
  | r99 (`--opaque`, diễn tập đề ẩn, tên `img_xxxx`) | 11 | 10 | ≈ 1.0 | (không review) | — |

  Seed phụ chỉ dùng để kiểm luật và kiểm công cụ; nhóm chỉ review bằng mắt trên seed luyện tập 13007.
- Số ứng viên trên lô sạch (`--no-faults`): **1** ứng viên (class_swap, lệch tự nhiên). Hàng đợi trên seed luyện tập: **10 ảnh** (2 ảnh/người cho 5 thành viên); sau khi xem ảnh: 7 `confirmed`, 3 `rejected`.
- Ngưỡng đã chọn và cách chọn (không dùng `_private`): chỉnh trên **lô sạch** (mọi ứng viên ở đó là lệch tự nhiên của COCO) và bằng cách **mở ảnh** các ứng viên ở seed luyện tập, sao cho hàng đợi đủ nhỏ để 5 người xem hết trong khoảng 20 phút. Không thử–sai theo điểm của `score_findings.py`.
  - `class_swap` / `category_swap`: IoU $\ge 0.70$ giữa box detection và mask segment nhưng nhãn 2 nguồn bất đồng.
  - `instance_merge`: Tận dụng tín hiệu chênh lệch số lượng cá thể giữa 2 nguồn (`det_count > pan_count` cho cùng một lớp) kết hợp điều kiện bbox segment panoptic bao trùm tâm của $\ge 2$ box detection tách biệt (IoU giữa 2 box $< 0.20$).
  - `bbox_drift`: Box detection và segment cùng lớp có độ lệch tâm $\ge 18\%$ kích thước tối thiểu của box và $0.30 \le \text{IoU} \le 0.68$.
  - `missing_box`: Segment thing trong panoptic có diện tích lớn ($\ge 1\%$ diện tích ảnh và $\ge 1500$ px), nhưng không có box detection nào khớp ($\max \text{IoU} < 0.10$).

## 2. Vì sao báo hết ứng viên làm F1 giảm?
- Trong dữ liệu COCO thực tế, sự bất đồng tự nhiên giữa bounding box và segmentation mask là rất phổ biến (vật thể bị che khuất, các đối tượng chen chúc trong đám đông, ranh giới giữa các đồ vật gần nhau như spoon/fork hay sandwich/hotdog).
- Điểm đánh giá là điểm điều hoà $F_1 = \frac{2 \times \text{TP}}{2 \times \text{TP} + \text{FP} + \text{FN}}$, nghĩa là **báo thừa (FP) bị phạt nặng tương đương bỏ sót (FN)**.
- Nếu tự động báo toàn bộ ứng viên nghi vấn mà không mở ảnh review bằng mắt:
  - Số lượng False Positive (FP) sẽ tăng mạnh do đưa nhầm các ca lệch tự nhiên thành lỗi gán nhãn.
  - Ứng viên còn mang **sai loại**: crosscheck chỉ thấy hai nguồn bất đồng nên ghi `class_swap`, phải mở ảnh mới biết bên nào sai. Báo sai loại bị tính hai lần: một FP (`class_swap`) và một FN (`category_swap`).
- **Số đo của nhóm** (cùng validator, chỉ khác bước xem ảnh):

  | Lô | Nhận hết ứng viên, không xem ảnh: F1 overall / cross_check | Chỉ nhận dòng `confirmed` sau khi xem ảnh: F1 overall / cross_check |
  |---|---|---|
  | r13007 | ≈ 0.9 / ≈ 0.7 | ≈ 1.0 / ≈ 1.0 |
  | r11 | ≈ 0.8 / ≈ 0.5 | (không review) |
  | r22 | ≈ 0.7 / ≈ 0.5 | (không review) |
  | r99 (`--opaque`) | ≈ 0.8 / ≈ 0.6 | (không review) |

  Ở r13007, 3/10 ứng viên là lệch tự nhiên khi mở ảnh: `000000003845` (nĩa nằm chồng lên muỗng, cả hai nguồn đều có fork và spoon), `000000009914` (detection có thêm box hot dog trùng box sandwich), `000000022705` (người che tủ lạnh). Ngoài ra `000000010363` là lỗi của **panoptic** (ảnh là mèo, panoptic ghi dog) nên phải ghi `category_swap`, không phải `class_swap` như crosscheck đề xuất. Nhận hết ứng viên sẽ biến những ca này thành FP/FN, nên F1 cross_check giảm từ ≈ 1.0 xuống ≈ 0.7.

## 3. Quyết định và lineage
- **QC v1 = 19/250 = 7,6%** (lô `lab250_a13aacb20205`, seed 13007). Tử số là số **target khác nhau** trong `errors.json`: mỗi ảnh mang nhiều nhất một lỗi, `scene_leak` tính một lần theo cảnh. Gồm 12 lỗi luật (wrong_hash 2, invalid_class 2, duplicate_box 2, bbox_out_of_bounds 1, guideline_mismatch 1, scene_leak 1, invalid_category_id 2, thing_overlap 1) và 7 lỗi gán nhãn đã `confirmed` sau khi xem ảnh (trên 10 ứng viên; 3 ứng viên `rejected` là lệch tự nhiên).
- **Kết luận v1: HOLD.** 7,6% > ngưỡng 2% của Day 7. Chỉ riêng lỗi luật đã là 12/250 = 4,8% > 2%, nên kết luận không phụ thuộc vào kết quả review. Ngưỡng tính theo **tỉ lệ ảnh lỗi** (không theo số lỗi) để so được giữa các lô khác kích thước và để một ảnh nhiều lỗi không bị đếm nhiều lần.
- **Lineage** (`runs/lineage.jsonl`, chép sang `submission/lineage.jsonl`): `inject` → `train R-021` trên v1 → `decision HOLD` cho v1. `lineage.py impact --release-id lab250_a13aacb20205` trả về `R-021: affected=True action=review_or_retrain`. Lô v2 sẽ được ghi `release` với `--parent lab250_a13aacb20205` sau khi bàn giao.
- **Vì sao R-021 phải xem lại hoặc train lại:** R-021 đã học trọng số từ v1, nên sửa dataset (ra v2) **không** tự sửa model đã train.
  - Model đã học từ nhãn sai: box gán nhầm lớp, box lệch, box lặp, vật thiếu box. Ticket của team AI (bỏ sót `cup` bị che) cũng cho thấy ảnh hưởng của các job theo guideline cũ v1.2.
  - Lô có cảnh bị rò giữa train và val (`scene_leak`), nên chỉ số validation của R-021 có thể bị **thổi phồng**.
  - Cần đánh giá lại R-021 trên tập val sạch (không rò cảnh) và train lại trên v2 sau khi các ảnh rework được gán lại.

## 4. Hash chứng minh gì, không chứng minh gì?
<<>>

## 5. Truy vết
Ticket nêu lớp `cup` và hai cảnh scene_342, scene_675; changelog cho biết v1.3 đổi quy tắc `cup` (vật bị che/cắt mép vẫn phải gán box). `tools/trace_query.py` đọc lớp và cảnh từ hai file này bằng code (không gõ cứng).
- **Tập nền:** ảnh thuộc job có guideline cũ (khác v1.3) **theo `jobs.csv`** và có ít nhất một box detection lớp `cup` trong `labels/`.
- **tier_a:** tập nền nằm trong cảnh ticket nêu; **tier_b:** phần còn lại của tập nền (chưa ai báo).
- **notify:** annotator và reviewer của các job chứa ảnh tier_a + tier_b.
- **Vì sao theo job:** `guideline_version` ghi ở từng ảnh có thể chính là lỗi `guideline_mismatch`; người gán nhãn làm theo guideline của job họ nhận, nên job mới là căn cứ đúng.
- Kết quả seed 13007: tier_a = 3 ảnh, tier_b = 4 ảnh, notify = A04, Q02; `score_findings.py` báo truy vết F1 ≈ 1.0 (tier_a, tier_b, notify).

## 6. Bug hoặc điểm chưa rõ trong lab (nếu có)
- **`release_id` của cùng một seed khác nhau giữa các máy.** `release_id` là sha256 của byte trong `manifest.json` + `metadata.json`. Có hai nguồn làm byte khác nhau dù nội dung lô y hệt:
  - `scripts/pngutil.py` nén mask bằng `zlib`. Python 3.14 trên Windows dùng zlib-ng, nên byte PNG khác bản zlib thường, và `mask_sha256` trong manifest đổi theo.
  - `Path.write_text` ghi JSON xuống dòng CRLF trên Windows, LF trên macOS/Linux.
  - Nhóm đã kiểm trên cùng một máy: seed 13007 tạo bằng Python 3.14.10 ra `lab250_a13aacb20205`, bằng Python 3.12.10 ra `lab250_0a6eeec065f8`. Ảnh, nhãn, metadata, jobs, ticket giống hệt; 241 mask khác byte nhưng giống từng pixel.
  - Hệ quả: người chấm tạo lại lô bằng `export_submission.py --import` trên môi trường khác có thể ra `release_id` khác, làm `check_handover.py` không tìm thấy thư mục `<release_id>_v2` (H4) và lineage không khớp (H12, H14). **Lô chính thức của nhóm được tạo bằng Python 3.14.10 trên Windows 11.** Nhóm không sửa `scripts/`; điểm này cần báo giảng viên để chấm trên cùng môi trường.
