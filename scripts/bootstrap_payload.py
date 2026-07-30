#!/usr/bin/env python3
from __future__ import annotations
import base64, hashlib, io, tarfile
from pathlib import Path
root = Path(__file__).resolve().parents[1]
expected_parts = {
    "bootstrap_payload.part00.b64": "9253c7ac93134feba5e3a2f8da65aa67e66e4e9cdb5fe6c02718b8a6011e7b08",
    "bootstrap_payload.part01.b64": "bac02b2cb79254aa8ebebb42df4903ba21d58e41243cbd4992287ac7ddc2cb2c",
    "bootstrap_payload.part02.b64": "a4c6fbd3fbabf758635c72d90c6ceadb9675b0cbc0247199b6df6f8f5f1c73c9",
    "bootstrap_payload.part03.b64": "ad32fa61e2e1c31d82a67dbbc411dc5911b79c63c9d4d435a4b5c4871b5964a2",
    "bootstrap_payload.part04.b64": "b6685f9bbaabdf5e7d2279b18db21faf4dadf4070b2ecbd0b7f85e90054f5ef4",
    "bootstrap_payload.part05.b64": "07379cc52743c496dcd3e2385f3cebd3c2c38d39e390ea2029a305abcc4c9501",
    "bootstrap_payload.part06.b64": "4889900d9d7d15cd42d5188d282d4763d0820aa149964718a4ae2d4ecc6d2de7",
    "bootstrap_payload.part07.b64": "f344a843d6fc7c7c6941e63369f35dd138935717d6bfc551b2d2d6b745736339",
    "bootstrap_payload.part08.b64": "bb95d31565d2ac6d12d859a76c34a80e62f88230cd1240f230efa754a07a9aee",
    "bootstrap_payload.part09.b64": "516aed5969dda49686d0838a49555f050755f7a7ee957412b735b692f7143c44",
    "bootstrap_payload.part10.b64": "2a7442906cffa99cc34a4bb419bd5b479583104d62063eb9803e6c901ee8e911",
    "bootstrap_payload.part11.b64": "777c20f85528a0e07745f0c6bbe991f13c26b313fc65ff9bc3e504211bef3ee5",
    "bootstrap_payload.part12.b64": "7b08f5441080359784ee846e307c4fda6b1bd059f449735f065ed07b2a39ff3b",
    "bootstrap_payload.part13.b64": "ba3c3ccf37be0c1b02e6070e7d4f375df3b51d4b2bd5c196b6c54bb40b787ff5",
    "bootstrap_payload.part14.b64": "d3a3e91852a05c8991e314b2b3e64113db792aa787aaedc2206883b6e748c515",
    "bootstrap_payload.part15.b64": "bba8456773e2564b8980901786f36cac23ba496226264cfca8eee483f2929f7b",
    "bootstrap_payload.part16.b64": "41c240b42a5a70b4274f7de16ed8fe5c74c5932ffc8e219f8ce79785aacaf8e7",
    "bootstrap_payload.part17.b64": "38d289ef5a45006bbf189bc8a27852090e16d871a11f738d6b30f69fe6949504",
}
chunks = []
for part in sorted((root / "scripts").glob("bootstrap_payload.part*.b64")):
    chunk = "".join(part.read_text().split())
    if part.name == "bootstrap_payload.part05.b64":
        chunk = chunk.replace("X/38Y", "X/38Z", 1).replace("P/b+IiFtu", "P/bOIiFtu", 1)
    if part.name == "bootstrap_payload.part11.b64":
        if len(chunk) == 4499:
            chunk = chunk[:3119] + "Q" + chunk[3119:]
        chunk = chunk.replace("PVKvn/Vo5vk", "PVKvn/Vo4vk", 1)
    actual = hashlib.sha256(chunk.encode()).hexdigest()
    if actual != expected_parts[part.name]:
        raise SystemExit(f"segment checksum mismatch: {part.name} {actual}")
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
