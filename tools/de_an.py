#!/usr/bin/env python3
"""Chạy đề ẩn (40 phút) bằng 2 lệnh, chỉ gọi lại công cụ sẵn có của nhóm.

  # 1) Sau khi giải nén de_an.zip ra delivery/ ở gốc repo:
  py -X utf8 tools/de_an.py prepare                     # chia hàng đợi cho 5 người
  py -X utf8 tools/de_an.py prepare --names huy         # làm một mình: mọi ứng viên vào 1 file

  # 2) Mọi người mở ảnh trong runs/de_an/view/, điền work/de_an_review_<ten>.csv
  #    (verdict confirmed/rejected, note >= 20 ký tự nói rõ thấy gì; panoptic sai -> type category_swap)

  # 3) Gộp + chốt + tự kiểm:
  py -X utf8 tools/de_an.py finish

prepare: validator/validate.py -> runs/de_an/rules.json + submission/de_an/candidates.json
         tools/trace_query.py  -> submission/de_an/trace.json
         tools/split_queue.py  -> work/de_an_review_<ten>.csv
         tools/view.py         -> runs/de_an/view/*.png (cần Pillow; lỗi viewer không chặn các bước khác)
finish:  tools/merge_parts.py  -> submission/de_an/review_log.csv
         scripts/merge_review.py -> submission/de_an/errors.json
         rồi tự kiểm định dạng theo RUBRIC mục 1-2-4 (không có _private nên không chấm được F1).

KHÔNG commit thư mục delivery/ (đã có trong .gitignore). AI không điền verdict review.
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAMES = ["huy", "quan", "nui", "phuc", "dat"]
SEMANTIC = {"class_swap", "bbox_drift", "missing_box", "category_swap", "instance_merge"}


def run(*args: str, required: bool = True) -> bool:
    cmd = [sys.executable, "-X", "utf8", *args]
    print("+", " ".join(args), flush=True)
    ok = subprocess.run(cmd, cwd=ROOT).returncode == 0
    if not ok and required:
        raise SystemExit(f"Lỗi ở bước: {' '.join(args)}")
    return ok


def prepare(a) -> None:
    delivery = Path(a.delivery)
    if not (delivery / "manifest.json").is_file():
        raise SystemExit(f"Không thấy {delivery}/manifest.json. Giải nén de_an.zip ra delivery/ ở gốc repo trước.")
    a.run_dir.mkdir(parents=True, exist_ok=True)
    a.sub_dir.mkdir(parents=True, exist_ok=True)
    rules, cands = a.run_dir / "rules.json", a.sub_dir / "candidates.json"
    run("validator/validate.py", str(delivery), "--out", str(rules), "--candidates", str(cands))
    run("tools/trace_query.py", str(delivery), "--out", str(a.sub_dir / "trace.json"))
    run("tools/split_queue.py", str(cands), "--prefix", "de_an_review", "--out-dir", str(a.work_dir), "--names", *a.names)
    if not run("tools/view.py", str(delivery), "--candidates", str(cands), "--out-dir", str(a.run_dir / "view"), required=False):
        print("CHÚ Ý: viewer lỗi (thiếu Pillow?). Vẫn mở ảnh gốc trong delivery/images/ để review.")
    n_rules = len(json.loads(rules.read_text(encoding="utf-8"))["errors"])
    n_cand = len(json.loads(cands.read_text(encoding="utf-8")))
    print(f"\nXONG prepare: {n_rules} lỗi luật, {n_cand} ứng viên cần xem ảnh.")
    print(f"Ảnh review: {a.run_dir / 'view'}  |  File điền: {a.work_dir}/de_an_review_<ten>.csv")


def finish(a) -> int:
    parts = [str(a.work_dir / f"de_an_review_{n}.csv") for n in a.names if (a.work_dir / f"de_an_review_{n}.csv").is_file()]
    if not parts:
        raise SystemExit(f"Không thấy file review nào trong {a.work_dir}")
    review, errors_path = a.sub_dir / "review_log.csv", a.sub_dir / "errors.json"
    run("tools/merge_parts.py", *parts, "--out", str(review))
    run("scripts/merge_review.py", "--rules", str(a.run_dir / "rules.json"), "--review", str(review), "--out", str(errors_path))

    problems = []
    errors = json.loads(errors_path.read_text(encoding="utf-8"))["errors"]
    with review.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    confirmed = {(r["type"].strip(), r["image"].strip()) for r in rows
                 if r["verdict"].strip() == "confirmed" and len(r["note"].strip()) >= 20}
    for e in errors:
        if e["type"] in SEMANTIC and (e["type"], e["target"]) not in confirmed:
            problems.append(f"lỗi gán nhãn {e['type']} {e['target']} không có dòng confirmed (note >= 20 ký tự): sẽ bị bỏ khi chấm")
    pending = 0
    for p in parts:
        with open(p, encoding="utf-8-sig", newline="") as f:
            pending += sum(1 for r in csv.DictReader(f) if not (r.get("verdict") or "").strip())
    if pending:
        problems.append(f"{pending} ứng viên chưa điền verdict (chưa xem ảnh)")
    trace = json.loads((a.sub_dir / "trace.json").read_text(encoding="utf-8"))
    for k in ("tier_a", "tier_b", "notify"):
        if not isinstance(trace.get(k), list):
            problems.append(f"trace.json thiếu khoá {k}")
    if not trace.get("tier_a") or not trace.get("notify"):
        problems.append("trace.json: tier_a hoặc notify đang rỗng")
    for name in ("errors.json", "candidates.json", "review_log.csv", "trace.json"):
        if not (a.sub_dir / name).is_file():
            problems.append(f"thiếu {a.sub_dir / name}")

    sem = sum(1 for e in errors if e["type"] in SEMANTIC)
    print(f"\nerrors.json: {len(errors)} lỗi ({len(errors) - sem} luật, {sem} gán nhãn); "
          f"review_log: {len(rows)} dòng; trace: tier_a {len(trace.get('tier_a', []))}, "
          f"tier_b {len(trace.get('tier_b', []))}, notify {len(trace.get('notify', []))}")
    if problems:
        print("CẦN XỬ LÝ:")
        for p in problems:
            print("  -", p)
        return 1
    print("SẴN SÀNG COMMIT: git add submission/de_an/ work/de_an_review_*.csv  (KHÔNG add delivery/)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("step", choices=["prepare", "finish"])
    ap.add_argument("--delivery", default="delivery")
    ap.add_argument("--names", nargs="+", default=NAMES, help="người review (mặc định 5 người)")
    ap.add_argument("--run-dir", type=Path, default=ROOT / "runs" / "de_an", help="file nháp, không commit")
    ap.add_argument("--sub-dir", type=Path, default=ROOT / "submission" / "de_an")
    ap.add_argument("--work-dir", type=Path, default=ROOT / "work")
    a = ap.parse_args()
    if a.step == "prepare":
        prepare(a)
        return 0
    return finish(a)


if __name__ == "__main__":
    raise SystemExit(main())
