# Static Grace deployment and two-path legacy cutover

Intent: temporarily serve exact legacy `GET /api/graceperiod/renderdock` and `GET /api/graceperiod/airstack` contracts while the office transitions to paid licensing. **This is a public, product-wide grace override** — every compatible desktop client receives `{"grace":true}` on startup. It does not select one office or purchaser. Disable promptly after entitlements are in effect.

## Static source (this repository)
- Cloudflare Pages project: `bke-grace`
- GitHub source: `jan2xo/bke-grace`, production branch `main`, output directory `public`, no build command, zero Pages Functions/Worker code.
- `public/_redirects` internally rewrites exact extensionless URLs to static `.json` files with HTTP 200.
- `public/_headers` ensures `Cache-Control: no-store`, `Content-Type: application/json`, and `X-Content-Type-Options: nosniff`.
- Both JSON files contain exactly `{"grace":true}`. Any other state or parsing error is denied by existing desktop clients.

## Cloudflare legacy hostname — minimal two-path router

Do **not** replace the apex `jl-bke.com` DNS record or attach that entire hostname to Pages while the old VPS is live. Cloudflare zone `jl-bke.com` has unrelated paths and may still serve installed-client or recovery requests. Instead, add a zone-level **Single Redirects** ruleset at phase `http_request_dynamic_redirect` with two exact-path rules:

1. `http.host eq "jl-bke.com" and http.request.method eq "GET" and http.request.uri.path eq "/api/graceperiod/renderdock"` → HTTP 302 to `https://bke-grace.pages.dev/api/graceperiod/renderdock`.
2. Same for `airstack`.

These are temporary redirects, not site-wide rewrites. `.NET HttpClient` follows redirects by default; nevertheless, confirm the shipped 2-second timeout can follow and parse each 200 JSON response. Redirects must not match unrelated APIs, other hosts, or the admin mutation path. All original hostname requests still arrive at Cloudflare without requiring the VPS for those two paths.

## Verification before and after cutover

Verify Cloudflare Pages production deployment at immutable GitHub main SHA (source proof and deployed behavior are separate):

```sh
curl -i https://bke-grace.pages.dev/api/graceperiod/renderdock
curl -i https://bke-grace.pages.dev/api/graceperiod/airstack
curl -i https://bke-grace.pages.dev/api/graceperiod/unknown
```

Expect 200, JSON content type, no-store, exact body `{"grace":true}` on known paths; 404 on unknown path. After adding the **two precise Cloudflare Redirect Rules**, run:

```sh
curl -i https://jl-bke.com/api/graceperiod/renderdock
curl -iL https://jl-bke.com/api/graceperiod/renderdock
curl -iL https://jl-bke.com/api/graceperiod/airstack
curl -i https://jl-bke.com/licensing-agent
```

First response should be a 302 to Pages; redirected GET should return 200 with exact JSON. Confirm unrelated `/licensing-agent` remains routed as it was prior to this change.

## Revoke and retire

After normal paid entitlements are verified, replace both files with `{"grace":false}`, certify, merge and wait for Pages deployment, or remove the two Single Redirect rules and disable legacy Grace on its original authority. To avoid unplanned global gratis usage, do not leave `true` indefinitely. Restoring the original two-route traffic requires removing only the two Cloudflare rules. **Do not destroy the VPS based on Grace-only evidence:** the Agent may still rely on other `jl-bke.com` platform paths.

This repository is an intentionally temporary transport compatibility layer, not the permanent Digital Solutions licensing authority.
