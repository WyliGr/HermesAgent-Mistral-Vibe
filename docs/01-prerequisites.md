# 01 â€” Prerequisites

Everything you need before running the flow.

## 1. A Mistral subscription with a Vibe counter

The whole trick relies on Mistral plans that ship **two separate monthly counters**:

| Counter | Typical size (Education plan, 2026-11) | Billed by |
|---|---|---|
| `API usage` | ~12.75â‚¬ / $15 | every call with a **standard** API key |
| `Vibe code usage` | ~127â‚¬ / $100+ | calls made by the `mistral-vibe` CLI â€” **and by any client holding a Vibe-provisioned key** |

Check yours at [console.mistral.ai](https://console.mistral.ai) â€” the plan page shows both counters. If your plan has no Vibe counter, this flow still works but everything lands on the small API counter (pointless).

## 2. Tools

- **Python 3.10+** on the machine that will run the sign-in (only stdlib needed by [the script](../scripts/vibe_signin.py)).
- **`uv`** *(optional but recommended)* â€” only if you want the official CLI installed to cross-check (`uv tool install mistral-vibe`). The flow itself does not require the CLI at runtime; we replay its HTTP calls.
- **A browser** on any machine, **already logged into the Mistral account that owns the Vibe quota**. The approval click happens there. Headless servers work fine: the URL opens on your laptop, the script polls from the server.

## 3. Account access notes

- The sign-in URL is validated against `console.mistral.ai` origins â€” open it in the browser profile where the target account is logged in, or log in when prompted.
- One sign-in process = one approval. Links **expire** (~20 min) and single-use: if the script dies before the exchange, just start a new process.
- The provisioned key is a **regular Mistral API key** (45 chars, `mstr...` prefix observed). Its calls are billed on the **Vibe** counter. It has the same model catalog as the CLI: hosted GLM / DeepSeek / Codestral / Magistral plus the standard Mistral models (64 models observed).

## 4. Where the key will live (Hermes case)

If your goal is wiring this into [Hermes Agent](https://github.com/NousResearch/hermes-agent), you will ultimately:

1. put the key in `MISTRAL_API_KEY` inside `~/.hermes/.env` (backup the old one first!),
2. route models/channels to `provider: mistral`,
3. restart the gateway from an **external** shell (never from inside an agent session â€” the self-restart guard blocks it).

Details in [04-hermes-integration.md](04-hermes-integration.md).
