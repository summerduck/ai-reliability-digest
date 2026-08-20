# AI Reliability Weekly

**Issue archive:** <https://summerduck.github.io/ai-reliability-digest/>

Personal weekly news digest for the **AI Reliability & Test Automation Engineer** field.
Every Monday morning a GitHub Actions job pulls ~45 curated RSS feeds, has Claude rank every
article against the target role profile, writes an analyst-style briefing (top stories, quick
hits, weekly trends, career implications), and emails it via Gmail.

## How it works

```
feeds.yaml ──▶ fetch (feedparser, 7-day window, failures collected)
           ──▶ rank    (claude-haiku-4-5, batched, 0–10 relevance scores)
           ──▶ analyze (claude-sonnet-5, structured output → Digest)
           ──▶ render  (HTML email)
           ──▶ send    (Gmail SMTP)
```

- A broken feed never kills the issue — it's listed at the bottom of the email.
- A quiet week still sends a (short) email, marked "quiet week".
- Cost: roughly $0.5–0.8 per issue.

## One-time setup

1. **Anthropic API key** — create at <https://console.anthropic.com> (Settings → API keys).
2. **Gmail app password** — enable 2FA on your Google account, then create an app password
   at <https://myaccount.google.com/apppasswords>.
3. **GitHub Secrets** — in this repo: Settings → Secrets and variables → Actions → New repository secret:

   | Secret | Value |
   |---|---|
   | `ANTHROPIC_API_KEY` | your Anthropic key |
   | `GMAIL_ADDRESS` | your Gmail address (sender and default recipient) |
   | `GMAIL_APP_PASSWORD` | the 16-character app password |

4. **First run** — Actions tab → "Weekly digest" → Run workflow (tick *dry run* to get the
   HTML as an artifact without sending, or untick to send a real email).

## Schedule

`.github/workflows/digest.yml` runs Mondays at `0 5 * * 1` (05:00 UTC = 08:00 UTC+3 / 07:00 UTC+2).
GitHub cron is always UTC — edit that one line to shift the time.

## Local development

```bash
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/pytest                          # run tests (all LLM/SMTP calls mocked)
.venv/bin/ruff check src tests            # lint
ANTHROPIC_API_KEY=... .venv/bin/python -m digest.main --dry-run   # real run → digest.html
```

## Tuning

- `feeds.yaml` — add/remove sources (name, url, category).
- `src/digest/config.py` — models, relevance threshold, window, batch sizes, and the
  `TARGET_ROLE_PROFILE` text that drives ranking and analysis.
