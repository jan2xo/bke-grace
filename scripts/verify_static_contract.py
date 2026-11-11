#!/usr/bin/env python3
"""Source contract for BKE's temporary, serverless, product-wide Grace GET."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "public"
EXPECTED = ("renderdock", "airstack")
EXPECTED_REDIRECTS = [
    f"/api/graceperiod/{name} /api/graceperiod/{name}.json 200"
    for name in EXPECTED
]
for name in EXPECTED:
    file = STATIC / "api" / "graceperiod" / f"{name}.json"
    raw = file.read_bytes()
    assert raw == b'{"grace":true}\n', f"{name}: exact one-property JSON boolean true required"
    data = json.loads(raw)
    assert set(data) == {"grace"} and type(data["grace"]) is bool and data["grace"] is True
actual_json = sorted(p.name for p in (STATIC / "api" / "graceperiod").iterdir())
assert actual_json == ["airstack.json", "renderdock.json"], "Only two public Grace JSON assets permitted"
redirects = [
    line.strip() for line in (STATIC / "_redirects").read_text().splitlines()
    if line.strip() and not line.startswith("#")
]
assert redirects == EXPECTED_REDIRECTS, "Cloudflare Pages must preserve both extensionless routes with 200 rewrites"
headers = (STATIC / "_headers").read_text()
assert "/api/graceperiod/*" in headers
assert "Cache-Control: no-store" in headers
assert "Content-Type: application/json" in headers
assert "X-Content-Type-Options: nosniff" in headers
assert (STATIC / "404.html").is_file(), "Do not return index.html as a successful unknown route"
for child in STATIC.rglob("*"):
    assert not child.is_file() or child.suffix not in {".js", ".ts", ".wasm"}, "No runtime code in the static site"
assert not (ROOT / "functions").exists(), "No Pages Functions/Workers allowed"
assert not (STATIC / "_worker.js").exists()
print("STATIC GRACE CONTRACT PASS: two exact one-property boolean JSON files, extensionless routes, no-store, no runtime.")
