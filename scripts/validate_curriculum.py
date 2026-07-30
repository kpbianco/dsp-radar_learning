#!/usr/bin/env python3
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
manifest_path = ROOT / "curriculum" / "modules.json"
errors: list[str] = []
try:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
except Exception as exc:
    print(f"invalid curriculum manifest: {exc}", file=sys.stderr)
    raise SystemExit(1)
modules = manifest.get("modules", [])
if manifest.get("schema_version") != 1: errors.append("schema_version must be 1")
if manifest.get("module_count") != 84: errors.append("module_count must be 84")
if len(modules) != 84: errors.append(f"expected 84 module entries, found {len(modules)}")
expected = list(range(1, 85))
actual = [m.get("number") for m in modules]
if actual != expected: errors.append("module numbers must be contiguous 1..84")
ids = [m.get("id") for m in modules]
if len(set(ids)) != len(ids): errors.append("module ids must be unique")
folders = [m.get("folder") for m in modules]
if len(set(folders)) != len(folders): errors.append("module folders must be unique")
required = ["id", "title", "phase", "phase_title", "guiding_question", "folder", "status", "implementation_batch"]
for m in modules:
    mid = m.get("id", "<unknown>")
    for key in required:
        if not m.get(key): errors.append(f"{mid}: missing {key}")
    if not re.fullmatch(r"P\d{2}", str(mid)): errors.append(f"{mid}: invalid id")
    folder = ROOT / str(m.get("folder", ""))
    for name in ["README.md"]:
        if not (folder / name).is_file(): errors.append(f"{mid}: missing {name}")
    if m.get("status") == "implemented":
        for name in ["experiment.m", "lesson.md", "walkthrough.md", "checks.md"]:
            p = folder / name
            if not p.is_file(): errors.append(f"{mid}: implemented but missing {name}")
            elif "TODO" in p.read_text(encoding="utf-8", errors="replace"): errors.append(f"{mid}: TODO remains in {name}")
    elif m.get("status") != "scaffolded": errors.append(f"{mid}: invalid status")
if sum(m.get("status") == "implemented" for m in modules) < 1:
    errors.append("at least one reference module must be implemented")
if errors:
    print("Curriculum validation failed:", file=sys.stderr)
    for e in errors: print(f"- {e}", file=sys.stderr)
    raise SystemExit(1)
print(f"Curriculum validation passed: {len(modules)} modules, {sum(m['status']=='implemented' for m in modules)} implemented.")
