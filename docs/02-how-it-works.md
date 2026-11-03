# 02 — How it works: the PKCE sign-in flow

This doc explains the mechanism, so you understand *what you are doing* before doing it. The official `mistral-vibe` CLI ships this exact flow in `vibe/setup/auth/` — we replay it with plain HTTP calls.

## The idea in one paragraph

When you run `vibe --setup`, the CLI opens a browser page on `console.mistral.ai`, you log in and approve the device, and behind the curtain the CLI exchanges a PKCE token pair for a fresh **API key provisioned on the Vibe counter**. Nothing in that exchange is CLI-magic: it is four plain HTTPS calls to public console endpoints. Any HTTP client can do it — including a 60-line Python script on a headless server.

## The actors

| Actor | Role |
|---|---|
| Your server / script | Creates the sign-in process, polls, exchanges. Never sees your password. |
| Your browser (any machine) | The only place where account authentication happens. |
| `console.mistral.ai` | Serves the approval page and the sign-in API (`/api/...`). |
| `api.mistral.ai` | The model API the new key will call later. |

## Step 1 — Create the sign-in process

```
POST https://console.mistral.ai/api/vibe/sign-in
Content-Type: application/json

{"code_challenge": "<BASE64URL(SHA256(verifier))>", "code_challenge_method": "S256"}
```

Response (200):

```json
{
  "process_id": "<uuid>",
  "sign_in_url": "https://console.mistral.ai/codestral/cli/authenticate?process_id=<uuid>&complete_token=<opaque>",
  "poll_url": "https://console.mistral.ai/api/vibe/sign-in/poll/<opaque>",
  "expires_at": "<iso8601>"
}
```

The **PKCE pair** (same scheme as OAuth 2.0 RFC 7636, as used by the CLI):

- `code_verifier` = `secrets.token_urlsafe(64)` — a random 86-char ASCII string.
- `code_challenge` = `base64url(sha256(code_verifier))` without padding.

Keep the `code_verifier` for the whole flow: the exchange will fail without the *exact* same value. Losing it means starting a new process.

## Step 2 — The human approves in the browser

Open `sign_in_url` in a browser logged into the Mistral account that owns the Vibe quota. The page shows a device-approval prompt; clicking approve marks the process as completed server-side.

- The link **expires** (observed ~20 min lifetime).
- It is **single-use** for the exchange: one approval = one key provisioning.

## Step 3 — Poll until approved

```
GET https://console.mistral.ai/api/vibe/sign-in/poll/<opaque>
```

Responses:

| Status | Meaning |
|---|---|
| `200 {"status": "pending"}` | Not approved yet — keep polling |
| `200 {"status": "completed", "exchange_token": "<opaque>"}` | Approved! Grab the `exchange_token` |
| `200 {"status": "expired"}` or `410 Gone` | Process expired — restart from step 1 |
| `200 {"status": "denied"}` / `"error"` | Aborted — restart |
| `429` | **Rate-limited.** Poll intervals under ~10 s trigger this |

**Poll every 15 seconds.** The CLI's own service treats fast polling as abuse; at 15 s we never saw a single 429 across hours of polling, at 2 s the flow died within minutes.

## Step 4 — Exchange for the API key

```
POST https://console.mistral.ai/api/vibe/sign-in/<process_id>/exchange
Content-Type: application/json

{"exchange_token": "<from poll>", "code_verifier": "<from step 1>"}
```

Response (200):

```json
{"api_key": "mstr...<45 chars total>"}
```

That key is a **regular Mistral API key** — same shape as a console-created one — but its usage is billed on the **Vibe code usage** counter instead of the API counter.

## Step 5 — Verify it works

```bash
curl -s https://api.mistral.ai/v1/models -H "Authorization: Bearer $KEY" | head
# expect: 200, ~64 models

curl -s https://api.mistral.ai/v1/chat/completions \
  -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
  -d '{"model": "zai-glm-5-3-flash", "messages": [{"role": "user", "content": "ping"}], "max_tokens": 10}'
# expect: 200 with a choice — NOT a 402 quota error
```

Models we verified working through the Vibe key (2026-11-03):

- `zai-glm-5-3-flash`, `zai-glm-5-3`, `zai-glm-5-2`, `zai-glm-latest`
- `deepseek-v4-1-flash-1017` (the only DeepSeek id exposed)
- `mistral-vibe-cli-latest`, `mistral-vibe-cli-with-tools`, `mistral-vibe-cli-fast` (the CLI's own aliases — their 200 responses prove the billing lands on the Vibe counter)
- `codestral-*`, `magistral-*`, `voxtral-mini-latest` (audio transcription works too)

## Why this is legitimate-ish (read before you rely on it)

This is not exploiting a hole: it is the CLI's own first-party flow, replayed without the CLI. You authenticate as yourself, Mistral provisions a key to *you*, on *your* plan's counter. What may change without notice: endpoint paths, the 20-min expiry, rate-limit thresholds, or Mistral deciding to bind the key to CLI user-agents. Nothing here bypasses the plan's monthly quota — it just spends the *right* counter.
