#!/usr/bin/env python3
"""Live GET proof for the two strict JSON endpoints hosted by Cloudflare Pages."""
import json
import time
import urllib.error
import urllib.request

BASE = "https://bke-grace.pages.dev"
for name in ("renderdock", "airstack"):
    path = f"/api/graceperiod/{name}"
    last_error = None
    for attempt in range(4):
        try:
            request = urllib.request.Request(BASE + path, headers={"User-Agent": "bke-grace-exact-contract-smoke/1"})
            with urllib.request.urlopen(request, timeout=8) as response:
                status = response.status
                raw = response.read()
                mime = response.headers.get("Content-Type", "").lower()
                cache = response.headers.get("Cache-Control", "").lower()
            assert status == 200, f"{path}: HTTP {status}"
            assert "application/json" in mime, f"{path}: wrong content type {mime}"
            assert "no-store" in cache, f"{path}: cache-control must be no-store"
            payload = json.loads(raw)
            assert payload == {"grace": True} and type(payload["grace"]) is bool
            assert raw.strip() == b'{"grace":true}', f"{path}: exact JSON body changed"
            print(f"PASS {path}: 200 JSON exact true, no-store")
            break
        except (AssertionError, urllib.error.URLError, TimeoutError, ValueError) as exc:
            last_error = exc
            if attempt < 3:
                time.sleep(3)
    else:
        raise SystemExit(f"FAIL {path}: {last_error}")

try:
    with urllib.request.urlopen(BASE + "/api/graceperiod/unknown", timeout=8) as response:
        raise SystemExit(f"FAIL unknown Grace path: returned HTTP {response.status} instead of 404")
except urllib.error.HTTPError as exc:
    # Cloudflare can reject unrecognized paths at the edge with 403 before the
    # site's 404 fallback; either status refuses Grace and is safe.
    assert exc.code in (403, 404), f"Unexpected status for unknown path: {exc.code}"
    print(f"PASS unknown path: HTTP {exc.code}, denied")
