# Validator của nhóm

Viết `validate.py` ở đây. Giao diện cố định:

```
python validator/validate.py <thư_mục_delivery> --out <errors.json> [--candidates <candidates.json>]
```

Chỉ đọc thư mục delivery được truyền vào; chỉ thư viện chuẩn; không mạng. Xem [GUIDE.md](../GUIDE.md) Pha 1–2 và [RULES.md](../RULES.md).

## P1a–P1c: tích hợp cho nhóm

- `--out` chỉ ghi `{"errors": [{"type": "...", "target": "..."}]}` (lỗi luật).
- `--candidates` ghi list `[{"image", "type", "score", "detail"}]` từ crosscheck.
- `common.load(delivery_dir)` trả dict `ctx`; hợp đồng các khóa và box xem docstring `common.py`.
- `images` và `annotations` tra bằng tên ảnh như manifest; ID panoptic được nối qua `image_id`, không ép tên ảnh thành số.
- `common.yolo_to_pixel(x, y, w, h, width, height)` trả `(left, top, right, bottom)` theo pixel, không clip cạnh.
- Mỗi module luật cung cấp `check(ctx) -> list[dict]`. Ưu tiên lỗi ảnh: file → metadata → detection → panoptic. `scene_leak` là lỗi cảnh, được giữ riêng.
- `crosscheck.candidates(ctx, skip_images)` chỉ bỏ qua tên ảnh có lỗi luật, không bỏ cả cảnh rò split.
- `rules_panoptic.py` (P1d) và `crosscheck.py` (P2a) đã được Núi triển khai, `IMPLEMENTED = True`; CLI không còn cảnh báo stub.
- Dung sai cạnh box: 0.01 chuẩn hóa. Box lặp: cùng lớp, chênh kích thước ≤ 0.01 pixel và chênh tâm mỗi trục ≤ 2.01 pixel; cần kiểm chứng tiếp trên lô sạch/seed phụ ở P1e.
- Lỗi cấu trúc dữ liệu không thuộc các loại trên:
  - **Của một ảnh** (YOLO không đủ cột, số không hữu hạn, thiếu annotation hoặc kích thước panoptic): CLI in `WARNING: <ảnh>: ...` ra stderr, bỏ qua phần kiểm tương ứng của ảnh đó và **vẫn chạy tiếp, vẫn ghi output** (P1e: đề ẩn 40 phút, không để một file hỏng làm mất cả lô). Không im lặng bỏ qua.
  - **Của cả lô** (thiếu `manifest.json`/`metadata.json`/`jobs.csv`, đường dẫn trỏ ra ngoài delivery, job không tồn tại): CLI trả mã 2 kèm thông báo.
- Dung sai `duplicate_box` giữ nguyên (tâm ≤ 2.01 px, kích thước ≤ 0.01 px) vì DELIVERY định nghĩa box lặp là lệch 1–2 pixel cùng kích thước; diễn tập trên lô `--opaque` seed 99 vẫn cho lỗi luật F1 ≈ 1.0, lô sạch 0 báo thừa.
- Không ghi output vào delivery. Không dùng Pillow, mạng, dữ liệu gốc hoặc `_private/`.

Chạy seed nhóm:

```powershell
python -X utf8 validator/validate.py runs/r13007/delivery --out runs/r13007/rules.json --candidates runs/r13007/candidates.json
python -X utf8 -m unittest discover -s tests -p test_validator.py -v
```

`candidates.json` rỗng khi crosscheck còn stub không có nghĩa dataset không có lỗi gán nhãn. Chờ P1d trước khi đánh giá đủ 9 luật ở P1e.
