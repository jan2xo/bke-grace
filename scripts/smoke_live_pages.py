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


# Verify legacy hardcoded URLs at the Cloudflare edge without changing the domain.
class StopRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

opener = urllib.request.build_opener(StopRedirect())
for name in ("renderdock", "airstack"):
    legacy = f"https://jl-bke.com/api/graceperiod/{name}"
    target = f"{BASE}/api/graceperiod/{name}"
    try:
        with opener.open(urllib.request.Request(legacy), timeout=8) as response:
            raise SystemExit(f"FAIL {legacy}: expected exact 302 redirect but got HTTP {response.status}")
    except urllib.error.HTTPError as exc:
        assert exc.code == 302, f"FAIL {legacy}: expected 302, got {exc.code}"
        assert exc.headers.get("Location") == target, f"FAIL {legacy}: unexpected redirect destination"
    with urllib.request.urlopen(urllib.request.Request(legacy), timeout=8) as response:
        assert response.status == 200 and response.geturl() == target
        assert "application/json" in response.headers.get("Content-Type", "").lower()
        assert "no-store" in response.headers.get("Cache-Control", "").lower()
        payload = json.loads(response.read())
        assert payload == {"grace": True} and type(payload["grace"]) is bool
    print(f"PASS legacy /api/graceperiod/{name}: exact 302 to Pages -> 200 JSON true, no-store")
