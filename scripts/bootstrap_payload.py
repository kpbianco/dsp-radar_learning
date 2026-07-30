#!/usr/bin/env python3
from __future__ import annotations
import base64, hashlib, io, tarfile
from pathlib import Path
root = Path(__file__).resolve().parents[1]
parts = sorted((root / "scripts").glob("bootstrap_payload.part*.b64"))
chunks = []
for part in parts:
    chunk = "".join(part.read_text().split())
    if part.name == "bootstrap_payload.part11.b64" and len(chunk) == 4499:
        chunk = chunk[:3119] + "Q" + chunk[3119:]
    chunks.append(chunk)
payload = "".join(chunks)
expected = "77a6e1aff573859a8844f936e618f40063fb32d2af1cc0f11ca66dc042f6d074"
actual = hashlib.sha256(payload.encode()).hexdigest()
if actual != expected:
    raise SystemExit(f"payload checksum mismatch: {actual}")
with tarfile.open(fileobj=io.BytesIO(base64.b64decode(payload)), mode="r:gz") as archive:
    archive.extractall(root)
(root / ".github/workflows/bootstrap-harness.yml").unlink(missing_ok=True)
(root / "scripts/bootstrap_payload.py").unlink(missing_ok=True)
for part in (root / "scripts").glob("bootstrap_payload.part*.b64"):
    part.unlink()
print("Extracted DSP/radar tutor harness")
