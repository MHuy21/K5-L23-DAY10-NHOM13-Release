# Dùng AI

<<<<<<< HEAD
| # | Ai dùng | Công cụ | Prompt (tóm tắt) | AI sai ở đâu | Nhóm kiểm lại thế nào |
|---|---|---|---|---|---|
| 1 | Quân — phần Validator luật | Codex | Đọc hướng dẫn repo và phân công; phân tích Validator luật; triển khai P1a/P1b/P1c với seed 13007: loader, CLI, 7 luật và stub panoptic/crosscheck. | Codex dùng `py` theo tài liệu nhưng launcher trong phiên công cụ không tìm thấy Python; chuyển sang đường dẫn Python 3.12 có sẵn. Lần chạy test đầu bị sandbox chặn thư mục tạm; chạy lại có cấp quyền thì đạt. Chưa có kết luận lỗi thuật toán từ review của người dùng. | Codex chạy 10 kiểm thử tổng hợp đạt; seed 13007 ghi nhận 9 lỗi luật; lô sạch calib 50 ảnh có 0 lỗi luật. Kiểm hash xác nhận v1 giữ nguyên. Không đọc đáp án, không dò điểm. Panoptic/crosscheck còn stub; chưa đánh giá đủ 9 luật. Quân cần đọc code và tự kiểm lại trước vấn đáp. |
=======
| # | Ai dùng | Công cụ | Prompt (tóm tắt)                  | AI sai ở đâu                                                                     | Nhóm kiểm lại thế nào |
|---|---|---|-----------------------------------|----------------------------------------------------------------------------------|---|
| 1 | Phúc | Claude Code | Hướng dẫn làm phần được phân công | AI ban đầu viết view.py bắt buộc tham số CLI nên bấm Run trong IDE bị lỗi, sau đó đã bổ sung fallback tự nhận diện | Chạy thử trên seed 13007: `score_findings.py` truy vết F1 ≈ 1.0; mở ảnh 000000000139 kiểm viewer; TODO thử trên lô sạch và seed phụ |
>>>>>>> 989b389 (P5: truy vet ticket (tier_a, tier_b, notify); REPORT muc 5)
