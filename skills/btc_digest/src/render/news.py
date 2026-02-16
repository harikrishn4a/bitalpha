"""News from RSS feeds. Returns headlines with links or 'News disabled'."""
import feedparser
from ..config import RSS_FEEDS


def fetch_headlines(max_items: int = 3) -> list[tuple[str, str]]:
    """Fetch top headlines from RSS_FEEDS. Returns [(title, link), ...]."""
    if not RSS_FEEDS:
        return []
    out = []
    for url in RSS_FEEDS[:5]:
        try:
            fp = feedparser.parse(url, request_headers={"User-Agent": "btc_digest/1.0"})
            for e in fp.entries[:2]:
                title = getattr(e, "title", "") or ""
                link = getattr(e, "link", "") or ""
                if title:
                    out.append((title[:120], link))
        except Exception:
            pass
        if len(out) >= max_items:
            break
    return out[:max_items]
