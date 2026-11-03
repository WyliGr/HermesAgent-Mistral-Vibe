# Agent prompt — switch this Hermes to the Mistral Vibe quota

> Usage: give this whole file to a Hermes agent (paste it in a fresh session, or
> `hermes chat -q "$(cat PROMPT.md)"`). The agent executes the plan autonomously
> and only comes back to you for the browser approval and the gateway restart.
> All technical details live in [docs/](docs/) — this file is the mission brief.

---

## Your goal

My Hermes runs on a Mistral subscription that carries **two separate monthly counters**:

- `API usage` — small (the one currently burning / already 402).
- `Vibe code usage` — ~10× bigger, normally reserved to the official `mistral-vibe` CLI.

The CLI's browser sign-in provisions a **regular Mistral API key billed on the Vibe counter**. Your mission: provision that key headlessly, wire it into my Hermes (`MISTRAL_API_KEY`), route my Discord channels to Vibe-billed models, and verify everything with real API calls. Full background: [docs/02-how-it-works.md](docs/02-how-it-works.md), walkthrough: [docs/03-step-by-step.md](docs/03-step-by-step.md).

## Hard rules — never break these

1. **Never print, echo or log the API key or any token** (`complete_token`, `exchange_token`, the key itself). Mask them as `[REDACTED]` everywhere, including Discord messages and log reads. Length + prefix only (`45 chars, mstr...`).
2. **Backup before touching `.env`**: `cp ~/.hermes/.env ~/.hermes/.env.bak-pre-vibe` (chmod 600) — first time only.
3. **Never restart the gateway yourself.** A restart from inside an agent session kills the session and is guard-blocked. When a restart is needed, hand me the exact command (`systemctl --user restart hermes-gateway`) and wait.
4. **One sign-in process at a time**, one log file. Poll **every 15 s minimum** — faster polls get 429-rate-limited and poison the flow.
5. **Verify with real calls, not assumptions**: every model you route must return HTTP 200 on the new key before you commit it to config.
6. If the same step fails twice for the same reason, stop and report — do not improvise a third variant.

## Procedure

### Phase 1 — Diagnose (no side effects)

- Grep `~/.hermes/logs/agent.log*` for the provider's model usage and any 402/quota errors; estimate the burn rate.
- Confirm current config: `hermes config get model` and the channel overrides under `platforms.discord.channel_overrides`.
- Report: current provider, burn, and the plan (counters) before touching anything.

### Phase 2 — Provision the Vibe key

- Copy [scripts/vibe_signin.py](scripts/vibe_signin.py) from this repo to the server (stdlib only, Python 3.10+).
- Run it in the background; capture the printed `SIGN_IN_URL`.
- Send me the URL with: "open it in a browser **logged into the Mistral account that owns the Vibe quota**, approve within ~20 min".
- The script polls (15 s) and exchanges automatically; it prints the key length when done. Do not run a second instance while waiting.

### Phase 3 — Wire the key in

- Verify the key works **before** installing it: `GET https://api.mistral.ai/v1/models` (expect 200, ~64 models) and one `chat/completions` call (expect 200, no 402).
- Backup `.env`, replace the `MISTRAL_API_KEY` value.
- Note: the STT re-reads `.env` per call (works immediately); chat models are cached at boot (need the restart in Phase 5).

### Phase 4 — Route channels

- Ask me **which channels** get which model (e.g. `zai-glm-5-3-flash` for chat channels, `deepseek-v4-1-flash-1017` for coding ones) — or propose a default and wait for my go.
- Apply per channel: `hermes config set platforms.discord.channel_overrides.<ID>.model <model>` and `.provider mistral`.
- Verify each with `hermes config get platforms.discord.channel_overrides.<ID>`.

### Phase 5 — Restart handoff

- Tell me to run `systemctl --user restart hermes-gateway` from an **external shell** (SSH/console — not you).
- After my confirmation, verify: overrides active, test message in each routed channel, no 402 in fresh logs.

### Phase 6 — Report

Summarize: what was diagnosed, the key provisioning (no secrets), the channel routing table, verification results, the rollback path (`cp ~/.hermes/.env.bak-pre-vibe ~/.hermes/.env` + restart), and which counter now burns.

## Failure handling

| Symptom | Cause | Fix |
|---|---|---|
| 429 on poll | polling too fast | 15 s interval, restart a fresh process |
| `410 Gone` / `expired` | 20-min link lifetime elapsed | new sign-in process |
| exchange fails | `code_verifier` lost/mismatched | fresh process, keep the pair for the whole flow |
| 402 after swap | wrong key installed or Vibe counter dry | check which key is in `.env` (length/prefix), check console counters |
| `vibe --setup` spinner/cancel | TUI needs a TTY | ignore the CLI's TUI, use the HTTP flow |
| overrides inert after config set | gateway not restarted | Phase 5 handoff |

## Done when

- [ ] Vibe key provisioned and stored (never displayed).
- [ ] `MISTRAL_API_KEY` swapped, backup exists.
- [ ] Every routed channel returns real 200 responses through the new key.
- [ ] Gateway restarted by the human, overrides verified live.
- [ ] Report delivered with rollback path.
