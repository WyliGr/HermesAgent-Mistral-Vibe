# INSTRUCTIONS.md — mission brief for your Hermes agent

You are a Hermes agent. Your human just handed you this repository and asked you
to switch **this Hermes instance** to the Mistral **Vibe** quota. This file is
your complete mission. Read it whole, then the docs it references, then execute.

## Context (read first, 2 minutes)

- The Mistral plan on this machine carries **two separate monthly counters**:
  `API usage` (small, the one currently burning) and `Vibe code usage`
  (~10× bigger, normally reserved to the official `mistral-vibe` CLI).
- The CLI's browser sign-in provisions a **regular Mistral API key billed on the
  Vibe counter**. You will provision that key headlessly, wire it into this
  Hermes, route the chat channels to it, and verify with real API calls.
- Technical background: [docs/02-how-it-works.md](docs/02-how-it-works.md)
  (endpoints, payloads, rate limits). Walkthrough:
  [docs/03-step-by-step.md](docs/03-step-by-step.md). Hermes specifics:
  [docs/04-hermes-integration.md](docs/04-hermes-integration.md). Failure modes:
  [docs/05-troubleshooting.md](docs/05-troubleshooting.md).

## Hard rules — never break these

1. **Never print, echo or log the API key or any token** (`complete_token`,
   `exchange_token`, the key itself). Mask them as `[REDACTED]` everywhere,
   including chat messages and log excerpts. Length + prefix only
   (observed: 45 chars, `mstr...`).
2. **Backup before touching the env file**: `cp <hermes-home>/.env
   <hermes-home>/.env.bak-pre-vibe` (chmod 600) — first time only.
   Resolve the real home from `$HERMES_HOME` when set, else `~/.hermes`.
3. **Never restart the gateway yourself.** A restart from inside an agent
   session kills the session and is guard-blocked. When a restart is needed,
   hand the human the exact command (`systemctl --user restart hermes-gateway`
   or their equivalent service command) and wait for their confirmation.
4. **One sign-in process at a time**, one log file. Poll **every 15 s minimum**
   — faster polls get 429-rate-limited and poison the flow.
5. **Verify with real calls, not assumptions**: every model you route must
   return HTTP 200 on the new key before it goes into any config.
6. If the same step fails twice for the same reason, stop and report — do not
   improvise a third variant.

## Phase 0 — Orientation (no side effects)

- Confirm this host actually runs Hermes: `hermes --version` (or find
  `~/.hermes/config.yaml`). If it does not, stop and report.
- Read the current config: `hermes config get model` and
  `hermes config get platforms.discord.channel_overrides` (if Discord is used).
- Grep `<hermes-home>/logs/agent.log*` for the mistral provider's usage and any
  402/quota errors; estimate the burn rate.
- Report to the human: current provider/model, burn observed, and the plan
  (which counter is which) before touching anything.

## Phase 1 — Provision the Vibe key

- Copy [scripts/vibe_signin.py](scripts/vibe_signin.py) to the server
  (stdlib only, Python 3.10+). Run it in the background; capture the printed
  `SIGN_IN_URL`.
- Send the human the URL with: "open it in a browser **logged into the Mistral
  account that owns the Vibe quota**, approve within ~20 min".
- The script polls (15 s) and exchanges automatically; it prints the key length
  when done. Do not run a second instance while waiting. If the link expires
  (`410`/`expired`), start a fresh process — never reuse a dead one.
- On success, keep the key material ONLY in a root-owned file (e.g.
  `<hermes-home>/vibe-key`, chmod 600) until Phase 2.

## Phase 2 — Wire the key in

- Verify the key **before** installing it:
  `GET https://api.mistral.ai/v1/models` (expect 200, ~64 models) and one
  `chat/completions` call (expect 200, no 402).
- Backup the env file, then replace the `MISTRAL_API_KEY` value with the new key.
- Note: the STT re-reads the env file per call (works immediately); chat models
  are cached at boot (need the restart in Phase 4).

## Phase 3 — Route the chat channels

- Ask the human **which channels** get which model (example split observed in
  the wild: `zai-glm-5-3-flash` for chat channels, `deepseek-v4-1-flash-1017`
  for coding ones). Propose a default if they have no opinion, and wait for
  their go.
- Apply per channel (Discord case):
  `hermes config set platforms.discord.channel_overrides.<ID>.model <model>`
  and `...provider mistral`. Verify each with `hermes config get`.
- If this Hermes does not use Discord, the generic equivalent is
  `hermes config set model.provider mistral` (+ `model.default <model>`) —
  same restart discipline.

## Phase 4 — Restart handoff

- Tell the human to run the gateway restart from an **external shell**
  (SSH/console — never from inside an agent session).
- After their confirmation, verify: overrides active, a test message in each
  routed channel, no 402 in fresh logs.

## Phase 5 — Report

Summarize: what was diagnosed, the key provisioning (no secrets), the channel
routing table, verification results, the rollback path
(`cp <hermes-home>/.env.bak-pre-vibe <hermes-home>/.env` + restart), and which
counter now burns.

## Failure handling

| Symptom | Cause | Fix |
|---|---|---|
| 429 on poll | polling too fast | 15 s interval, restart a fresh process |
| `410 Gone` / `expired` | 20-min link lifetime elapsed | new sign-in process |
| exchange fails | `code_verifier` lost/mismatched | fresh process, keep the pair for the whole flow |
| 402 after swap | wrong key installed or Vibe counter dry | check which key is in the env file (length/prefix), check console counters |
| `vibe --setup` spinner/cancel | TUI needs a TTY | ignore the CLI's TUI, use the HTTP flow |
| overrides inert after config set | gateway not restarted | Phase 4 handoff |

## Done when

- [ ] Vibe key provisioned and stored (never displayed).
- [ ] `MISTRAL_API_KEY` swapped, backup exists.
- [ ] Every routed channel returns real 200 responses through the new key.
- [ ] Gateway restarted by the human, overrides verified live.
- [ ] Report delivered with rollback path.
