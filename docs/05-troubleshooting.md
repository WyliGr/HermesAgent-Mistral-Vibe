# 05 — Troubleshooting

Every failure mode we hit during the 2026-11-03 run, with the fix that worked.

## HTTP 429 while polling

The poll endpoint rate-limits aggressively. Intervals under ~10 s produce 429s within minutes; at **15 s** we never saw one across hours.

- Fix: poll every 15 s, and treat a 429 as "slow down", not "retry immediately".
- Never run two pollers on the same process — the second one's failures look like flow failures.

## Link expired / process died mid-flow

Sign-in links live ~20 minutes. If the script (or the human) is too slow:

- `410 Gone` on poll → process expired, start over from step 1.
- Script crashed after approval but before the exchange → the `exchange_token` from the last successful poll is still valid: re-run with the same `process_id`/`exchange_token`, or just start a fresh process.

## "Setup cancelled" from `vibe --setup`

The TUI cannot run headless (no TTY). Ignore the CLI's TUI entirely and use the HTTP flow — that is what [scripts/vibe_signin.py](../scripts/vibe_signin.py) does.

## 402 / quota errors on chat calls

Two separate counters exist:

- **API usage** — small, what a standard API key spends.
- **Vibe code usage** — big, what the CLI-provisioned key spends.

If chat calls 402 with the Vibe key: check the key in `.env` is actually the Vibe one (45 chars), and check the counter on the console. If the Vibe counter is dry, the point of this whole setup is gone — either wait for the monthly reset or fall back to the standard key.

## "Missing API key" from the exchange

The exchange step needs the *exact* `code_verifier` generated in step 1. If the script restarted in between, the pair is lost — start a fresh sign-in process. Also: the exchange is single-use, a second call with the same token fails.

## Encoding glitches in chat messages

If your bot sends Discord/Slack messages through shell heredocs, non-ASCII text can arrive mangled (we had Chinese characters corrupt mid-message). Write the message to a file and send that file instead of piping through heredocs.

## Nothing works / gateway ignores the new key

- The gateway caches chat models at boot: a `.env` edit needs `systemctl --user restart hermes-gateway` from an **external** shell (never from inside an agent session — the self-restart guard blocks it).
- After restart, `hermes config get platforms.discord.channel_overrides.<CHANNEL_ID>` shows the effective `model`/`provider` per channel.
- Test with a tiny real call before blaming the flow:

```bash
curl -s https://api.mistral.ai/v1/chat/completions \
  -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
  -d '{"model": "zai-glm-5-3-flash", "messages": [{"role": "user", "content": "ping"}], "max_tokens": 10}'
```
