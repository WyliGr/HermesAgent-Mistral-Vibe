#!/usr/bin/env python3
"""Headless Mistral Vibe sign-in (stdlib only).

Replays the official `mistral-vibe` CLI PKCE flow with plain HTTP calls:

1. POST /api/vibe/sign-in          -> process_id + sign_in_url + poll_url
2. Human approves in the browser at sign_in_url (you have ~20 min)
3. GET  poll_url every 15 s        -> {"status": "pending"} ... then
                                      {"status": "completed", "exchange_token": "..."}
4. POST /api/vibe/sign-in/<id>/exchange
   {"exchange_token", "code_verifier"} -> {"api_key": "mstr..."}

The key is a regular Mistral API key billed on the Vibe code usage counter.
Tested 2026-11-03 with an Education-plan account (64 models visible).
"""

from __future__ import annotations

import base64
import hashlib
import json
import secrets
import time
import urllib.error
import urllib.request

API_BASE = "https://console.mistral.ai/api"
POLL_INTERVAL_S = 15
DEADLINE_S = 20 * 60


def generate_pkce_pair() -> tuple[str, str]:
    """(code_verifier, code_challenge) — same scheme as OAuth 2.0 RFC 7636."""
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return verifier, challenge


def http_json(method: str, url: str, payload: dict | None = None) -> dict:
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "vibe-signin/1.0")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as err:
        raise RuntimeError(f"{method} {url} -> HTTP {err.code}: {err.read().decode()[:300]}") from err


def main() -> None:
    verifier, challenge = generate_pkce_pair()
    process = http_json("POST", f"{API_BASE}/vibe/sign-in",
                        {"code_challenge": challenge, "code_challenge_method": "S256"})
    process_id = process["process_id"]
    print(f"process_id: {process_id}")
    print(f"Open in a browser logged into the Vibe-quota account, then approve:\n{process['sign_in_url']}")

    exchange_token = None
    deadline = time.monotonic() + DEADLINE_S
    while exchange_token is None:
        time.sleep(POLL_INTERVAL_S)
        poll = http_json("GET", process["poll_url"])
        status = poll.get("status")
        print(f"[{time.strftime('%H:%M:%S')}] poll status: {status}")
        if status == "completed":
            exchange_token = poll["exchange_token"]
        elif status in {"pending"}:
            continue
        elif status in {"expired", "denied", "error"}:
            raise SystemExit(f"sign-in process reached terminal state: {status}")
        if time.monotonic() > deadline:
            raise SystemExit("deadline (20 min) reached without approval")

    exchange = http_json(
        "POST",
        f"{API_BASE}/vibe/sign-in/{process_id}/exchange",
        {"exchange_token": exchange_token, "code_verifier": verifier},
    )
    api_key = exchange.get("api_key")
    if not api_key:
        raise SystemExit(f"exchange returned no api_key: {list(exchange)}")
    print(f"API key obtained (length {len(api_key)}).")
    print("Store it as MISTRAL_API_KEY wherever your client reads its Mistral credentials.")


if __name__ == "__main__":
    main()
