# 03 — Step by step: provision the key and plug it into Hermes

Zero-to-working walkthrough, tested end to end on 2026-11-03 on a self-hosted Hermes (Ubuntu 24.04 VM, gateway as systemd user unit).

## 0. What you need

- A Mistral plan **with a Vibe counter** (Education plan does; check console.mistral.ai).
- Python 3.10+ on the server that runs Hermes.
- A browser somewhere, **logged into the Mistral account that owns the Vibe quota** — the approval click happens there.
- 5 minutes.

## 1. Run the headless sign-in

Save [scripts/vibe_signin.py](../scripts/vibe_signin.py) anywhere on the server and run it:

```bash
python3 vibe_signin.py
```

It prints:

```
[hh:mm:ss] SIGN_IN_URL: https://console.mistral.ai/codestral/cli/authenticate?process_id=...
[hh:mm:ss] poll_hint: https://console.mistral.ai/api/vibe/sign-in/poll/...
```

## 2. Approve in the browser

Open the printed `SIGN_IN_URL` in a browser **logged into the right Mistral account** and approve the device prompt. Do it within ~20 minutes (link expiry observed).

## 3. Grab the key

The script finishes with:

```
[hh:mm:ss] browser sign-in completed, exchanging...
[hh:mm:ss] Obtained vibe API key (length) 45
[hh:mm:ss] WROTE_KEY to /root/.vibe/.env and /root/.hermes/vibe-key
```

(Reproduce whatever your setup needs: the script's job is only to hand you the 45-char key.)

## 4. Put the key in Hermes

⚠️ **Back up the previous key first** — if the Vibe counter ever runs dry, one `cp` rolls you back:

```bash
cp /root/.hermes/.env /root/.hermes/.env.bak-pre-vibe   # only needed the first time
# replace the MISTRAL_API_KEY=... line in /root/.hermes/.env with the new key
```

- The **STT** (voice) re-reads `.env` on every call → works immediately, no restart.
- The **chat models** are cached by the gateway → needs the restart in step 6.

## 5. Route channels to the Vibe key

Per-channel overrides, set with the CLI (never hand-edit the YAML):

```bash
hermes config set platforms.discord.channel_overrides.<CHANNEL_ID>.model zai-glm-5-3-flash
hermes config set platforms.discord.channel_overrides.<CHANNEL_ID>.provider mistral
```

Models we validated at 200 through the Vibe key: `zai-glm-5-3-flash` (fast), `zai-glm-5-3`, `deepseek-v4-1-flash-1017`, plus `codestral-*`, `magistral-*`, `voxtral-mini-latest` (audio transcription).

## 6. Restart the gateway (external shell!)

```bash
systemctl --user restart hermes-gateway
```

Never trigger that from inside an agent session — the self-restart guard blocks it by design.

## 7. Verify

- `hermes config get platforms.discord.channel_overrides.<CHANNEL_ID>` → shows the new `model`/`provider`.
- Send a test message in each routed channel.
- Optionally `curl -s https://api.mistral.ai/v1/models -H "Authorization: Bearer $KEY" | python3 -m json.tool | grep -c '"id"'` → expect ~64 models.
- Watch the Vibe counter (not the API one) move on console.mistral.ai.
