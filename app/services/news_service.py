from __future__ import annotations

import html
import re
from typing import Dict, List

import feedparser
import requests


class NewsService:
    CATEGORY_QUERIES = {
        "Large Cap": "large cap mutual fund india OR bluechip fund OR equity mutual fund",
        "Mid Cap": "mid cap mutual fund india OR midcap SIP OR mutual fund returns",
        "Small Cap": "small cap mutual fund india OR smallcap fund OR high growth mutual fund",
        "Hybrid": "hybrid mutual fund india OR balanced advantage fund OR asset allocation fund",
    }

    def __init__(
        self,
        topic: str = "mutual fund india",
        page_size: int = 7,
        api_key: str = "",
        api_provider: str = "newsapi",
        language: str = "en",
    ):
        self.topic = topic
        self.page_size = max(int(page_size), 1)
        self.api_key = api_key.strip()
        self.api_provider = api_provider.lower().strip() or "newsapi"
        self.language = language
        self.status_message = ""
        self.api_error_message = ""

    def _build_rss_url(self, query: str) -> str:
        encoded_query = requests.utils.quote(query)
        return f"https://news.google.com/rss/search?q={encoded_query}&hl=en-IN&gl=IN&ceid=IN:en"

    def _build_api_request(self, query: str) -> tuple[str, Dict[str, str | int]]:
        if self.api_provider == "gnews":
            return (
                "https://gnews.io/api/v4/search",
                {
                    "q": query,
                    "lang": self.language,
                    "max": self.page_size,
                    "sortby": "publishedAt",
                    "apikey": self.api_key,
                },
            )

        return (
            "https://newsapi.org/v2/everything",
            {
                "q": query,
                "language": self.language,
                "pageSize": self.page_size,
                "sortBy": "publishedAt",
                "searchIn": "title,description",
                "apiKey": self.api_key,
            },
        )

    @staticmethod
    def _clean_summary(text: str) -> str:
        plain_text = re.sub(r"<[^>]+>", "", text or "")
        return html.unescape(plain_text).strip() or "Click to read the full article."

    @staticmethod
    def _format_published(value: str) -> str:
        return value.replace("T", " ").replace("Z", " UTC") if value else "Recently updated"

    @staticmethod
    def _normalize_text(text: str) -> str:
        cleaned = (text or "").lower().strip()
        cleaned = re.split(r"\s+-\s+", cleaned)[0]
        cleaned = re.sub(r"[^a-z0-9\s]", " ", cleaned)
        return re.sub(r"\s+", " ", cleaned).strip()

    def _article_key(self, article: Dict[str, str]) -> str:
        title_key = self._normalize_text(article.get("title", ""))
        link_key = (article.get("link", "") or "").split("?")[0].strip().lower()
        return f"{title_key}|{link_key}"

    @staticmethod
    def _is_relevant(article: Dict[str, str]) -> bool:
        haystack = " ".join(
            [
                article.get("title", ""),
                article.get("summary", ""),
                article.get("category", ""),
            ]
        ).lower()
        keywords = [
            "mutual fund",
            "fund",
            "sip",
            "amc",
            "asset allocation",
            "scheme",
            "bluechip",
            "hybrid",
            "equity",
            "debt",
            "large cap",
            "mid cap",
            "small cap",
        ]
        return any(keyword in haystack for keyword in keywords)

    def _unique_articles(
        self,
        articles: List[Dict[str, str]],
        used_keys: set[str] | None = None,
    ) -> List[Dict[str, str]]:
        unique_articles: List[Dict[str, str]] = []
        local_seen = set()

        for article in articles:
            if not self._is_relevant(article):
                continue

            article_key = self._article_key(article)
            if not article_key or article_key in local_seen:
                continue
            if used_keys is not None and article_key in used_keys:
                continue

            local_seen.add(article_key)
            if used_keys is not None:
                used_keys.add(article_key)
            unique_articles.append(article)

            if len(unique_articles) >= self.page_size:
                break

        return unique_articles

    def _fetch_from_api(self, query: str, category: str) -> List[Dict[str, str]]:
        if not self.api_key:
            return []

        try:
            url, params = self._build_api_request(query)
            response = requests.get(
                url,
                params=params,
                timeout=10,
                headers={"User-Agent": "Mozilla/5.0"},
            )

            if not response.ok:
                try:
                    payload = response.json()
                    message = payload.get("message") or payload.get("error") or str(payload)
                except ValueError:
                    message = response.text[:200]

                self.api_error_message = message
                return []

            payload = response.json()
            articles: List[Dict[str, str]] = []

            for item in payload.get("articles", []):
                source_info = item.get("source") or {}
                articles.append(
                    {
                        "title": (item.get("title") or "Untitled news").strip(),
                        "summary": self._clean_summary(item.get("description") or item.get("content") or ""),
                        "link": item.get("url") or "#",
                        "published": self._format_published(item.get("publishedAt", "")),
                        "source": source_info.get("name", self.api_provider.title()),
                        "category": category,
                    }
                )

            return self._unique_articles(articles)
        except (requests.RequestException, ValueError) as exc:
            self.api_error_message = str(exc)
            return []

    def _fetch_from_rss(self, query: str, category: str) -> List[Dict[str, str]]:
        try:
            response = requests.get(
                self._build_rss_url(query),
                timeout=10,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            response.raise_for_status()
            feed = feedparser.parse(response.content)

            articles: List[Dict[str, str]] = []
            for entry in feed.entries:
                source_info = getattr(entry, "source", {}) or {}
                articles.append(
                    {
                        "title": getattr(entry, "title", "Untitled news").strip(),
                        "summary": self._clean_summary(getattr(entry, "summary", "")),
                        "link": getattr(entry, "link", "#"),
                        "published": getattr(entry, "published", "Recently updated"),
                        "source": source_info.get("title", "Google News"),
                        "category": category,
                    }
                )

            return self._unique_articles(articles)
        except requests.RequestException:
            return []

    def _fetch_articles(self, query: str, category: str) -> List[Dict[str, str]]:
        api_articles = self._fetch_from_api(query, category)
        rss_articles = self._fetch_from_rss(query, category)
        return self._unique_articles(api_articles + rss_articles)

    def get_news_by_category(self) -> Dict[str, List[Dict[str, str]]]:
        categorized_news: Dict[str, List[Dict[str, str]]] = {}
        used_keys: set[str] = set()
        self.status_message = ""
        self.api_error_message = ""

        for category, query in self.CATEGORY_QUERIES.items():
            live_articles = self._fetch_articles(query, category)
            categorized_news[category] = self._unique_articles(live_articles, used_keys)

        if self.api_key and self.api_error_message:
            self.status_message = (
                f"{self.api_provider.title()} API could not be used: {self.api_error_message}. "
                "Showing only the live feed results that are currently available."
            )
        elif not any(categorized_news.values()):
            self.status_message = "No live mutual-fund news is available right now. Please try refreshing later."

        return categorized_news

    @staticmethod
    def _fallback_articles(category: str) -> List[Dict[str, str]]:
        common_sources = {
            "amfi": "https://www.amfiindia.com/",
            "sebi": "https://www.sebi.gov.in/",
            "et": "https://economictimes.indiatimes.com/mf",
            "moneycontrol": "https://www.moneycontrol.com/news/business/personal-finance/",
            "valueresearch": "https://www.valueresearchonline.com/funds/",
            "morningstar": "https://www.morningstar.in/",
            "nse": "https://www.nseindia.com/market-data/mutual-funds",
        }

        fallback_map = {
            "Large Cap": [
                {
                    "title": "Large-cap funds remain a preferred choice for stability-focused investors",
                    "summary": "Investors continue to track bluechip allocations, fund manager strategy shifts, and defensive sector exposure.",
                    "link": common_sources["et"],
                    "published": "Backup update",
                    "source": "Economic Times",
                    "category": "Large Cap",
                },
                {
                    "title": "Bluechip mutual fund portfolios see renewed attention after quarterly earnings",
                    "summary": "Large-cap scheme positioning around banking, IT, and FMCG remains a key discussion area.",
                    "link": common_sources["moneycontrol"],
                    "published": "Backup update",
                    "source": "Moneycontrol",
                    "category": "Large Cap",
                },
                {
                    "title": "Investors compare expense ratios and Sharpe scores in large-cap schemes",
                    "summary": "Performance consistency and downside protection remain the focus for long-term SIP investors.",
                    "link": common_sources["valueresearch"],
                    "published": "Backup update",
                    "source": "Value Research",
                    "category": "Large Cap",
                },
                {
                    "title": "Fund houses rebalance large-cap allocations as valuations stretch",
                    "summary": "Analysts are watching whether market leaders can continue earnings momentum into the next quarter.",
                    "link": common_sources["morningstar"],
                    "published": "Backup update",
                    "source": "Morningstar",
                    "category": "Large Cap",
                },
                {
                    "title": "SIP investors seek resilience through diversified large-cap exposure",
                    "summary": "Disciplined investing in established companies remains a common wealth-building strategy.",
                    "link": common_sources["amfi"],
                    "published": "Backup update",
                    "source": "AMFI",
                    "category": "Large Cap",
                },
                {
                    "title": "Market experts review how large-cap funds behave during volatility spikes",
                    "summary": "Large companies often offer steadier participation when equity markets become uncertain.",
                    "link": common_sources["nse"],
                    "published": "Backup update",
                    "source": "NSE",
                    "category": "Large Cap",
                },
                {
                    "title": "Regulatory disclosures help investors compare top large-cap mutual fund strategies",
                    "summary": "Scheme documents and monthly factsheets remain important for informed fund selection.",
                    "link": common_sources["sebi"],
                    "published": "Backup update",
                    "source": "SEBI",
                    "category": "Large Cap",
                },
            ],
            "Mid Cap": [
                {
                    "title": "Mid-cap mutual funds draw interest as investors look for growth beyond bluechips",
                    "summary": "Mid-sized companies can offer stronger upside, though risk and volatility stay higher than large caps.",
                    "link": common_sources["et"],
                    "published": "Backup update",
                    "source": "Economic Times",
                    "category": "Mid Cap",
                },
                {
                    "title": "Fund managers track earnings quality before increasing mid-cap exposure",
                    "summary": "Balance sheet strength and management execution remain central to mid-cap stock selection.",
                    "link": common_sources["moneycontrol"],
                    "published": "Backup update",
                    "source": "Moneycontrol",
                    "category": "Mid Cap",
                },
                {
                    "title": "SIP investors review mid-cap funds for long-term alpha potential",
                    "summary": "Analysts recommend staying invested with realistic return expectations and proper time horizon.",
                    "link": common_sources["valueresearch"],
                    "published": "Backup update",
                    "source": "Value Research",
                    "category": "Mid Cap",
                },
                {
                    "title": "Portfolio diversification remains key when choosing mid-cap mutual fund schemes",
                    "summary": "Over-concentration can increase risk in fast-moving market segments.",
                    "link": common_sources["amfi"],
                    "published": "Backup update",
                    "source": "AMFI",
                    "category": "Mid Cap",
                },
                {
                    "title": "Research platforms highlight valuation discipline in mid-cap fund selections",
                    "summary": "Buying growth at reasonable prices is still a central theme in this category.",
                    "link": common_sources["morningstar"],
                    "published": "Backup update",
                    "source": "Morningstar",
                    "category": "Mid Cap",
                },
                {
                    "title": "Investors compare rolling returns before entering mid-cap mutual funds",
                    "summary": "Looking at multi-year performance can offer a clearer picture than short-term returns alone.",
                    "link": common_sources["nse"],
                    "published": "Backup update",
                    "source": "NSE",
                    "category": "Mid Cap",
                },
                {
                    "title": "Risk disclosures matter more when evaluating aggressive mid-cap allocations",
                    "summary": "Investors are advised to align mid-cap exposure with goals, age, and volatility tolerance.",
                    "link": common_sources["sebi"],
                    "published": "Backup update",
                    "source": "SEBI",
                    "category": "Mid Cap",
                },
            ],
            "Small Cap": [
                {
                    "title": "Small-cap mutual funds stay in focus for high-risk, high-growth investors",
                    "summary": "Smaller companies can generate strong returns but often experience sharper drawdowns.",
                    "link": common_sources["et"],
                    "published": "Backup update",
                    "source": "Economic Times",
                    "category": "Small Cap",
                },
                {
                    "title": "Analysts warn that small-cap fund selection needs patience and risk discipline",
                    "summary": "Time horizon and volatility tolerance are critical before starting a small-cap SIP.",
                    "link": common_sources["moneycontrol"],
                    "published": "Backup update",
                    "source": "Moneycontrol",
                    "category": "Small Cap",
                },
                {
                    "title": "Fund houses review liquidity and valuations in small-cap portfolios",
                    "summary": "Liquidity conditions can materially affect performance during rapid market moves.",
                    "link": common_sources["valueresearch"],
                    "published": "Backup update",
                    "source": "Value Research",
                    "category": "Small Cap",
                },
                {
                    "title": "Small-cap funds may suit investors with long holding periods and staggered entries",
                    "summary": "Systematic investing can help manage timing risk in more volatile segments.",
                    "link": common_sources["amfi"],
                    "published": "Backup update",
                    "source": "AMFI",
                    "category": "Small Cap",
                },
                {
                    "title": "Market commentators revisit risk-reward balance in small-cap mutual fund bets",
                    "summary": "Selection quality and diversification remain essential in this category.",
                    "link": common_sources["morningstar"],
                    "published": "Backup update",
                    "source": "Morningstar",
                    "category": "Small Cap",
                },
                {
                    "title": "Retail investors seek clarity on valuation comfort before adding small-cap exposure",
                    "summary": "Experts often suggest using gradual SIP routes instead of large lump-sum entries.",
                    "link": common_sources["nse"],
                    "published": "Backup update",
                    "source": "NSE",
                    "category": "Small Cap",
                },
                {
                    "title": "Investor education remains vital when navigating small-cap mutual fund cycles",
                    "summary": "Understanding cycles helps investors avoid emotional decisions during corrections.",
                    "link": common_sources["sebi"],
                    "published": "Backup update",
                    "source": "SEBI",
                    "category": "Small Cap",
                },
            ],
            "Hybrid": [
                {
                    "title": "Hybrid mutual funds gain traction among investors seeking balanced risk",
                    "summary": "These schemes mix equity and debt to smooth returns across changing market cycles.",
                    "link": common_sources["et"],
                    "published": "Backup update",
                    "source": "Economic Times",
                    "category": "Hybrid",
                },
                {
                    "title": "Balanced advantage funds stay relevant as investors seek flexible asset allocation",
                    "summary": "Dynamic allocation strategies aim to reduce extreme portfolio swings.",
                    "link": common_sources["moneycontrol"],
                    "published": "Backup update",
                    "source": "Moneycontrol",
                    "category": "Hybrid",
                },
                {
                    "title": "Hybrid schemes help first-time investors start with moderated equity exposure",
                    "summary": "For some investors, blended portfolios can feel more comfortable than pure equity funds.",
                    "link": common_sources["valueresearch"],
                    "published": "Backup update",
                    "source": "Value Research",
                    "category": "Hybrid",
                },
                {
                    "title": "Analysts study how hybrid funds respond to rate changes and equity volatility",
                    "summary": "Debt quality and rebalancing process remain important evaluation points.",
                    "link": common_sources["morningstar"],
                    "published": "Backup update",
                    "source": "Morningstar",
                    "category": "Hybrid",
                },
                {
                    "title": "Investors compare aggressive and conservative hybrid funds before allocation shifts",
                    "summary": "Scheme mandates differ significantly, making category understanding essential.",
                    "link": common_sources["amfi"],
                    "published": "Backup update",
                    "source": "AMFI",
                    "category": "Hybrid",
                },
                {
                    "title": "Asset allocation remains the core theme in hybrid mutual fund recommendations",
                    "summary": "Hybrid funds can play a stabilizing role around goals and income needs.",
                    "link": common_sources["nse"],
                    "published": "Backup update",
                    "source": "NSE",
                    "category": "Hybrid",
                },
                {
                    "title": "Regulatory disclosures help compare debt-equity mix across hybrid schemes",
                    "summary": "Reviewing scheme documents can reveal how risk is managed across market conditions.",
                    "link": common_sources["sebi"],
                    "published": "Backup update",
                    "source": "SEBI",
                    "category": "Hybrid",
                },
            ],
        }

        return fallback_map.get(category, fallback_map["Large Cap"])
