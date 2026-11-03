# Mistral AI as Hermes Agent AI Provider

Mistral AI is a **French AI Provider** specialized in **Sovreignty**. They provide their own AI Models like Large 4 aka *"Le Chonk"* and recently they host some chinese Open-weight (*GLM 5.3 Flash, GLM 5.3 and Deepseek v4.1 Flash*) that they provide in their Vibe code plan and API.

Since **Hermes** is my personnal assistant, I need to have some privacy and sovreignty about my data. I don't want to trust random providers with data retention or with crappy privacy policies.

So I took a Mistral AI subscription. The student one that provide 12.75€ of API usage. But I destroyed the quota in only one day with Hermes.

But in the student subscription, Mistral provide 127.50€ of Vibe usage. (Using their CLI or  Web UI). 

**Can't I use the Vibe Usage on Hermes instead of the highly limited API ?**

**Yes — and this repo documents exactly how.** 🎉

The Mistral plan carries **two separate monthly counters**: the small API one (12.75€/mo here) and a much bigger **Vibe code usage** one (127.50€/mo here). The Vibe counter is normally reserved to the official `mistral-vibe` CLI and the web UI — but the key it provisions is a plain Mistral API key. By replaying the CLI's PKCE sign-in flow headlessly, you can provision that Vibe-billed key yourself and plug it into anything: Hermes, OpenWebUI, a raw `curl`, your own agents.

## Repository map

| File | Content |
|---|---|
| [docs/01-prerequisites.md](docs/01-prerequisites.md) | What you need before starting (plan, tools, account access) |
| [docs/02-how-it-works.md](docs/02-how-it-works.md) | The PKCE sign-in flow, every endpoint, request/response shapes |
| [docs/03-step-by-step.md](docs/03-step-by-step.md) | Full walkthrough: provision the key, verify it, plug it into Hermes |
| [docs/04-hermes-integration.md](docs/04-hermes-integration.md) | Hermes-specific wiring: `.env`, per-channel model routing, restart discipline |
| [docs/05-troubleshooting.md](docs/05-troubleshooting.md) | Every pitfall we hit: 429s, expired links, zombie pollers, headless TUI |
| [scripts/vibe_signin.py](scripts/vibe_signin.py) | Dependency-free headless sign-in script (stdlib only) |

## TL;DR (5 lines)

1. Run the [sign-in script](scripts/vibe_signin.py) (Python 3.10+, stdlib only) — it prints a `console.mistral.ai` URL.
2. Open that URL in a browser **logged into the Mistral account that owns the Vibe quota**, approve.
3. The script polls until approval, exchanges PKCE tokens, and receives a **Vibe-billed API key**.
4. Put the key wherever a Mistral key belongs (`MISTRAL_API_KEY`, provider `mistral`).
5. Chat calls are now billed on the Vibe counter, not the 12€ API one.

> ⚠️ Key hygiene: treat the provisioned key like a password. Store it in a `chmod 600` file and never echo it in chat, logs or screenshots.

---

Everything below was observed live on **2026-11-03** with an Education-plan account. Prices and quotas are the ones at that date — re-check yours on [console.mistral.ai](https://console.mistral.ai). Model catalog seen through the Vibe key: 64 models, including hosted GLM 5.3 (Flash and not), DeepSeek v4.1 Flash, Codestral, Magistral and the standard Mistral lineup.
