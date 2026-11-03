# 04 — Hermes integration: per-channel routing

The Hermes side of the setup: how the Vibe key lands in the `.env`, and how individual Discord channels get routed to Vibe-billed models while others stay on other providers.

## 1. Key storage

`/root/.hermes/.env` carries the standard `MISTRAL_API_KEY=...` line — replace its value with the Vibe-provisioned key (backup the old line first, one `cp` away from rollback). The STT re-reads `.env` at every call, so voice transcription switches instantly; the chat models are cached at boot and need the gateway restart from step 6.

## 2. Per-channel overrides

Routing is a map of channel ID → model + provider, set through the CLI (never hand-edit the YAML):

```bash
hermes config set platforms.discord.channel_overrides.<CHANNEL_ID>.model zai-glm-5-3-flash
hermes config set platforms.discord.channel_overrides.<CHANNEL_ID>.provider mistral
```

Models we validated at 200 through the Vibe key: `zai-glm-5-3-flash` (fast), `zai-glm-5-3`, `deepseek-v4-1-flash-1017`, plus `codestral-*`, `magistral-*`, `voxtral-mini-latest` (audio transcription).

## 3. Restart discipline

The chat models are cached at boot: a `.env` edit or an override change needs a gateway restart from an **external** shell (never from inside an agent session — the self-restart guard blocks it):

```bash
systemctl --user restart hermes-gateway
```

## 4. Verify

- `hermes config get platforms.discord.channel_overrides.<CHANNEL_ID>` → shows the effective `model`/`provider`.
- Send a test message in each routed channel.
- Optionally `curl -s https://api.mistral.ai/v1/models -H "Authorization: Bearer $KEY" | python3 -m json.tool | grep -c '"id"'` → expect ~64 models.
- Watch the Vibe counter (not the API one) move on console.mistral.ai.
