"""Delivery-only loader shared by rule checks and panoptic crosschecking.

Image keys are manifest keys (opaque strings, never COCO numeric IDs).
ctx keys: root, manifest, meta, jobs, classes, panoptic, images,
annotations, categories, detections. images/annotations are keyed by image name;
categories by category ID. detections[name] is a list of dictionaries with
class_id, xywh (normalized), xyxy (normalized), xyxy_px and line.
"""

import csv
import json
import math
from pathlib import Path


def delivery_path(root, relative):
    """Resolve an input path without allowing reads outside delivery."""
    root = Path(root).resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f"Path outside delivery: {relative}")
    return path


def yolo_to_xyxy(x, y, w, h):
    return (x - w / 2, y - h / 2, x + w / 2, y + h / 2)


def yolo_to_pixel(x, y, w, h, width, height):
    """Return pixel (left, top, right, bottom), without clipping bad boxes."""
    left, top, right, bottom = yolo_to_xyxy(x, y, w, h)
    return (left * width, top * height, right * width, bottom * height)


def read_yolo(path, width, height):
    boxes = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip():
            continue
        values = line.split()
        if len(values) != 5:
            raise ValueError(f"{path}:{line_no}: expected 5 YOLO fields")
        try:
            c, x, y, w, h = map(float, values)
        except ValueError as exc:
            raise ValueError(f"{path}:{line_no}: invalid YOLO number") from exc
        if not all(math.isfinite(v) for v in (c, x, y, w, h)):
            raise ValueError(f"{path}:{line_no}: non-finite YOLO number")
        boxes.append({"class_id": int(c) if c.is_integer() else c,
                      "xywh": (x, y, w, h), "xyxy": yolo_to_xyxy(x, y, w, h),
                      "xyxy_px": yolo_to_pixel(x, y, w, h, width, height),
                      "line": line_no})
    return boxes


def load(delivery_dir):
    root = Path(delivery_dir).resolve()

    def read_json(relative):
        return json.loads(delivery_path(root, relative).read_text(encoding="utf-8-sig"))

    manifest = read_json("manifest.json")["items"]
    meta = {m["image"]: m for m in read_json("metadata.json")["items"]}
    with delivery_path(root, "jobs.csv").open(encoding="utf-8-sig", newline="") as f:
        jobs = {row["job_id"]: row for row in csv.DictReader(f)}
    classes = {}
    for line in delivery_path(root, "classes.txt").read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            class_id, name = line.split(maxsplit=1)
            classes[int(class_id)] = name.strip()
    panoptic = read_json("panoptic.json")
    image_by_file = {Path(im["file_name"]).name: im for im in panoptic["images"]}
    ann_by_id = {ann["image_id"]: ann for ann in panoptic["annotations"]}
    images, annotations, detections, warnings = {}, {}, {}, []
    for name, item in manifest.items():
        # Validate all manifest input paths, even when a module does not read them yet.
        # Path escapes stay fatal: the validator must never read outside delivery.
        for key in ("image", "label", "mask"):
            delivery_path(root, item[key])
        jobs[meta[name]["job_id"]]  # Fail explicitly on broken metadata references.
        # P1e: one broken image must not stop the whole delivery (hidden test is 40 minutes).
        # Record a warning, keep empty data for that image, and continue with the others.
        image = image_by_file.get(Path(item["image"]).name)
        if image is None or image.get("width", 0) <= 0 or image.get("height", 0) <= 0:
            warnings.append(f"{name}: no valid panoptic image dimensions; skipped detection/panoptic checks")
            annotations[name] = {"segments_info": []}
            detections[name] = []
            continue
        images[name] = image
        if image["id"] in ann_by_id:
            annotations[name] = ann_by_id[image["id"]]
        else:
            warnings.append(f"{name}: no panoptic annotation; panoptic checks see no segments")
            annotations[name] = {"image_id": image["id"], "segments_info": []}
        try:
            detections[name] = read_yolo(delivery_path(root, item["label"]),
                                         image["width"], image["height"])
        except (OSError, ValueError) as exc:
            warnings.append(f"{name}: unreadable label ({exc}); detection checks skipped for this image")
            detections[name] = []
    return {"root": root, "manifest": manifest, "meta": meta, "jobs": jobs,
            "classes": classes, "panoptic": panoptic, "images": images,
            "annotations": annotations, "categories": {c["id"]: c for c in panoptic["categories"]},
            "detections": detections, "warnings": warnings}
