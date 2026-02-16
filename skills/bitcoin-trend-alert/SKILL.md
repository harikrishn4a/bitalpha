---
name: bitcoin-trend-alert
description: Monitors BTC trends with extensive web scraping (X, Reddit, news), generates educational 1-2-3 digest, sends Telegram alerts. Invoke via /bitcoin-trend-alert or /btc.
metadata: { "openclaw": { "emoji": "₿" } }
---

# Bitcoin Trend Alert

Educational BTC assistant for Singapore retail investors. Neutral, MAS-risk aware. Uses extensive web scraping.

## Workflow

### 1. Price + sentiment

```bash
curl -s "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd,sgd"
```

For 24h/7d change: https://api.coingecko.com/api/v3/coins/bitcoin (market_data). Fear and Greed: https://api.alternative.me/fng/?limit=1

### 2. News (web_fetch / browse)

CoinDesk, CoinTelegraph, CryptoPanic, The Block. Extract headlines, summarize narrative.

### 3. X (Twitter) - extensive coverage

- web_search: "bitcoin site:x.com" or "bitcoin trending Twitter"
- web_fetch Nitter: https://nitter.privacydev.net/search?f=tweets&q=bitcoin (fallback if web_search insufficient)
- Extract: trending topics, influencer takes, sentiment shift. Cite sources.

### 4. Reddit

web_fetch or browse: https://old.reddit.com/r/bitcoin/.json?limit=25, https://old.reddit.com/r/cryptocurrency/hot

### 5. Detect trend

If 24h/7d move >5%, Fear and Greed extreme, or strong X/Reddit signal, generate digest.

### 6. Generate 1-2-3 digest

- What is being observed? (pattern, X/Reddit trends)
- Why? (news + social narrative)
- Last observed? Past outcome? Expectations.

### 7. Send digest

```bash
openclaw message send --channel telegram --target 737798118 --message "{digest}"
```

- Cite sources (X, Reddit, news sites). SGD focus.
- End with: "Informational only—high risk per MAS."
