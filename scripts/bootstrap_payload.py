#!/usr/bin/env python3
from __future__ import annotations
import base64, io, tarfile
from pathlib import Path
root = Path(__file__).resolve().parents[1]
payload = "".join(p.read_text().strip() for p in sorted((root / "scripts").glob("bootstrap_payload.part*.b64")))
with tarfile.open(fileobj=io.BytesIO(base64.b64decode(payload)), mode="r:gz") as archive:
    archive.extractall(root)
(root / ".github/workflows/bootstrap-harness.yml").unlink(missing_ok=True)
(root / "scripts/bootstrap_payload.py").unlink(missing_ok=True)
for part in (root / "scripts").glob("bootstrap_payload.part*.b64"):
    part.unlink()
print("Extracted DSP/radar tutor harness")
