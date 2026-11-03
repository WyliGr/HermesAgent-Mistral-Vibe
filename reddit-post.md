# Stop burning your cheap AI plan. Use its 10× bigger plan instead. (works with any agent)

## TL;DR

Your AI subscription probably has **two separate usage pools**: the tiny "API" one your agent burns, and a huge "included tooling" one sitting idle. On my Mistral plan: €12.75/month of API usage vs **€127.50/month of "Vibe" usage** (their coding-tool pool). I made my self-hosted agent [**Hermes**](https://github.com/NousResearch/hermes-agent) spend the big pool instead — same models, same API, 10× the budget. **Full guide + working script:** [github.com/WyliGr/HermesAgent-Mistral-Vibe](https://github.com/WyliGr/HermesAgent-Mistral-Vibe)

## The story

I run my personal AI agent on my own server. For privacy reasons I wanted a European provider, so I picked Mistral's student plan. Great choice — until my agent ate the **entire month of API credit in about a day**. Long agent conversations re-send the whole history on every call, and agent loops are hungry.

Then I looked at my subscription page: next to the tiny "API usage" bar (now dead) sat a **massive unused "Vibe" bar** — the pool that's supposed to power Mistral's coding CLI only.

## The discovery

The official CLI's sign-in is just a standard **PKCE device flow**: the CLI asks Mistral for a login URL, you approve it in a browser, and Mistral hands back — wait for it — **a plain API key**. The only special thing about it is *which pool it bills*.

So I read the CLI's Python source, extracted the 4 HTTP calls it makes, and replayed them with a ~100-line script that runs on a headless server:

1. `POST /vibe/sign-in` → get a login URL (valid ~20 min)
2. You click "approve" in your browser (the only human step)
3. Script polls every 15 s → gets an `exchange_token`
4. `POST .../exchange` → **API key that bills the big pool**

Key insight: **it's not an exploit**. You authenticate as yourself, Mistral issues a key to you, on your own plan's pool. It's the CLI's own flow, just without the CLI.

## Does it actually work?

Yes. My agent now chats through Mistral's hosted models (`GLM 5.3 Flash`, `DeepSeek v4.1 Flash`, Codestral, Magistral…) and the big pool moves instead of the tiny one. I verified: model list, chat completions, even **voice transcription** — all billed on the big pool. If it ever runs dry, one file copy switches me back to the standard key.

## What's in the repo

- **Step-by-step guide** for the sign-in flow (every HTTP call, every pitfall)
- **A ready-to-run script** — standard library only, no dependencies
- **Agent instructions**: a copy-paste block for your agent that makes *it* do the whole migration (it reads the guide itself)
- **Troubleshooting** from my own failures: rate limits (poll every 15 s, not 2 s!), expired links, headless-TUI traps

## The general lesson

Whatever your subscription (Mistral or otherwise): **check your usage page for a second, bigger pool**. Tooling-included pools are often 5–10× the API pool, and if the vendor's own tool mints API keys against it, those keys usually work anywhere an API key goes.

## Links

- Guide + script: [github.com/WyliGr/HermesAgent-Mistral-Vibe](https://github.com/WyliGr/HermesAgent-Mistral-Vibe)
- The agent I run: [Hermes Agent](https://github.com/NousResearch/hermes-agent) (open source, self-hosted)

*Not affiliated with Mistral. Your plan's terms are yours to read — the flow uses the vendor's own first-party endpoints with your own account.*
