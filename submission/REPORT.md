# Báo cáo nhóm <<XX>>

## 1. Số liệu luyện tập
- F1 theo seed (rule / cross_check / overall): <<seed: ... / ... / ...>>
- Số ứng viên trên lô sạch (`--no-faults`): <<...>>; hàng đợi trên seed luyện tập: <<... ảnh>>
- Ngưỡng đã chọn và cách chọn (không dùng `_private`): <<...>>

## 2. Vì sao báo hết ứng viên làm F1 giảm?
<<Trả lời bằng số của nhóm.>>

## 3. Quyết định và lineage
<<QC v1 a/b, kết luận, vì sao R-021 phải xem lại hoặc train lại.>>

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
<<>>
