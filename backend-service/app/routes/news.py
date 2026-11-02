"""
News API Routes — English News Articles for Language Learning

Proxy endpoints that fetch news from NewsAPI.org (primary) and NewsData.io (fallback).
Articles are AI-graded with CEFR levels and cached via APICacheService.

Phase 2: News Reading Feature.
"""

import logging
import hashlib
import html
import re
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from typing import Optional

import httpx
from urllib.parse import quote
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.safe_http import (
    safe_get as _safe_get,
    safe_stream_get as _safe_stream_get,
    validate_public_url as _validate_safe_public_url,
)
from app.services.api_cache_service import (
    APICacheService,
    QuotaExhaustedError,
    QuotaNearLimitError,
)
from app.services.quota_manager import Priority

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/news", tags=["News"])

NEWSAPI_BASE = "https://newsapi.org/v2"
NEWSDATA_BASE = "https://newsdata.io/api/1"
PUBLIC_NEWS_RSS = {
    "general": "https://feeds.bbci.co.uk/news/world/rss.xml",
    "technology": "https://feeds.bbci.co.uk/news/technology/rss.xml",
    "science": "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
    "health": "https://feeds.bbci.co.uk/news/health/rss.xml",
    "business": "https://feeds.bbci.co.uk/news/business/rss.xml",
    "entertainment": "https://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml",
    "sports": "https://feeds.bbci.co.uk/sport/rss.xml?edition=uk",
    "education": "https://feeds.bbci.co.uk/news/education/rss.xml",
}
# ── CEFR Level Definitions ──────────────────────────────────────
CEFR_LEVELS = {
    "A1": {"label": "Beginner", "color": "#4CAF50", "max_words": 120},
    "A2": {"label": "Elementary", "color": "#8BC34A", "max_words": 200},
    "B1": {"label": "Intermediate", "color": "#FFC107", "max_words": 350},
    "B2": {"label": "Upper Intermediate", "color": "#FF9800", "max_words": 500},
    "C1": {"label": "Advanced", "color": "#FF5722", "max_words": 800},
    "C2": {"label": "Proficiency", "color": "#9C27B0", "max_words": 1500},
}

# ── Curated Categories ──────────────────────────────────────────
NEWS_CATEGORIES = [
    {"id": "technology", "label": "Technology", "icon": "devices"},
    {"id": "science", "label": "Science", "icon": "science"},
    {"id": "health", "label": "Health", "icon": "favorite"},
    {"id": "business", "label": "Business", "icon": "business"},
    {"id": "entertainment", "label": "Entertainment", "icon": "movie"},
    {"id": "sports", "label": "Sports", "icon": "sports"},
    {"id": "general", "label": "World", "icon": "public"},
    {"id": "education", "label": "Education", "icon": "school"},
]


# ============================================================================
# News Articles
# ============================================================================

@router.get("")
async def get_news(
    request: Request,
    category: str = Query("general", description="News category"),
    level: Optional[str] = Query(None, description="CEFR level filter (A1-C2)"),
    page: int = Query(1, ge=1, le=10),
    page_size: int = Query(10, ge=5, le=20),
    q: Optional[str] = Query(None, description="Search query"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get English news articles with CEFR level grading.
    
    Flow:
    1. Fetch from NewsAPI.org (primary) or NewsData.io (fallback)
    2. Estimate CEFR level for each article
    3. Optionally filter by requested level
    4. Cache: Redis 1h, DB 6h
    
    Returns articles with cefrLevel, estimated reading time, and highlighted words.
    """
    if level and level not in CEFR_LEVELS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid CEFR level: {level}. Valid: {list(CEFR_LEVELS.keys())}",
        )
    
    # Build cache key
    cache_parts = [f"cat:{category}", f"p:{page}", f"ps:{page_size}"]
    if level:
        cache_parts.append(f"lv:{level}")
    if q:
        cache_parts.append(f"q:{q}")
    cache_key = f"news:articles:{':'.join(cache_parts)}"
    
    cache_service = APICacheService(db)
    
    try:
        result = await cache_service.get_or_fetch(
            cache_key=cache_key,
            api_name="newsapi",
            fetch_fn=lambda: _fetch_news(
                category=category,
                page=page,
                page_size=page_size,
                query=q,
            ),
            priority=Priority.MEDIUM,
            redis_ttl=3600,      # 1 hour
            db_ttl=21600,        # 6 hours
        )
        
        articles = result.data.get("articles", [])
        
        # Post-process: estimate CEFR level and filter
        for article in articles:
            if "cefr_level" not in article:
                article["cefr_level"] = _estimate_cefr(article)
                article["cefr_info"] = CEFR_LEVELS.get(article["cefr_level"], {})
                article["reading_time_min"] = _estimate_reading_time(article)
                article["highlighted_words"] = _extract_highlight_words(article)
        
        # Filter by level if specified
        if level:
            articles = [a for a in articles if a.get("cefr_level") == level]
        
        # Proxy image URLs to avoid CORS
        base_url = str(request.base_url).rstrip("/")
        api_prefix = settings.API_V1_PREFIX.strip("/")
        news_prefix = router.prefix.strip("/")
        path_prefix = f"{api_prefix}/{news_prefix}".strip("/")
        for a in articles:
            if a.get("image_url"):
                a["image_url"] = f"{base_url}/{path_prefix}/proxy/image?url={quote(a['image_url'])}"
        
        return {
            "articles": articles,
            "total": len(articles),
            "page": page,
            "category": category,
            "source": result.source,
            "is_stale": result.is_stale,
            "categories": NEWS_CATEGORIES,
        }
    except QuotaExhaustedError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e),
            headers={"Retry-After": e.reset_time},
        )
    except QuotaNearLimitError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e),
        )


@router.get("/proxy/image", summary="Proxy news images to bypass CORS")
async def proxy_image(url: str = Query(..., description="The image URL to proxy")):
    """
    Proxy news images to bypass browser CORS on web.
    """
    _validate_public_http_url(url)
        
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await _get_public_url(
                client,
                url,
                headers={"User-Agent": "LexiLingo/1.0 (English learning app; proxy)"},
            )
            if resp.status_code != 200:
                raise HTTPException(
                    status_code=resp.status_code,
                    detail=f"Failed to fetch image: HTTP {resp.status_code}"
                )
            return Response(
                content=resp.content,
                media_type=resp.headers.get("content-type", "image/jpeg"),
                headers={
                    "Cache-Control": "public, max-age=86400",  # Cache for 24h
                }
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error proxying image {url}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to proxy image."
            )


@router.get("/categories")
async def get_categories():
    """Get available news categories with labels and icons."""
    return {"categories": NEWS_CATEGORIES}


# ============================================================================
# Full Article Content (Web Scraping)
# ============================================================================

@router.post("/full-content")
async def get_full_article_content(
    url: str = Body(..., embed=True, description="Original article URL to scrape"),
    db: AsyncSession = Depends(get_db),
):
    """
    Scrape full article text from the original URL.

    NewsAPI free tier truncates content to ~200 characters.
    This endpoint fetches the full article using trafilatura.

    Cache: Redis 24h, DB 7 days (article content doesn't change).
    """
    _validate_public_http_url(url)

    cache_key = f"news:full:{hashlib.md5(url.encode()).hexdigest()[:16]}"
    cache_service = APICacheService(db)

    try:
        result = await cache_service.get_or_fetch(
            cache_key=cache_key,
            api_name="newsapi",
            fetch_fn=lambda: _scrape_full_article(url),
            priority=Priority.LOW,
            redis_ttl=86400,     # 24 hours
            db_ttl=604800,       # 7 days
        )

        return {
            "content": result.data.get("content", ""),
            "source": result.source,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to scrape article from {url}: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch full article content",
        )


async def _scrape_full_article(url: str) -> dict:
    """Fetch and extract full article text from a URL using trafilatura."""
    import asyncio

    try:
        import trafilatura

        async with httpx.AsyncClient(
            timeout=15.0,
            headers={"User-Agent": "Mozilla/5.0 (compatible; LexiLingo/1.0)"},
        ) as client:
            response = await _get_public_url(client, url)
            response.raise_for_status()
            html = response.text

        # trafilatura is synchronous — run in executor
        loop = asyncio.get_event_loop()
        content = await loop.run_in_executor(
            None,
            lambda: trafilatura.extract(
                html,
                include_comments=False,
                include_tables=False,
                no_fallback=False,
            ),
        )

        if not content:
            # Fallback: basic HTML tag stripping
            content = _strip_html_basic(html)

        return {"content": content or ""}

    except ImportError:
        # trafilatura not installed — basic fallback
        logger.warning("trafilatura not installed, using basic HTML extraction")
        async with httpx.AsyncClient(
            timeout=15.0,
            headers={"User-Agent": "Mozilla/5.0 (compatible; LexiLingo/1.0)"},
        ) as client:
            response = await _get_public_url(client, url)
            response.raise_for_status()
            html = response.text

        return {"content": _strip_html_basic(html)}


def _validate_public_http_url(url: str) -> None:
    """Reject malformed/private URL syntax before the pinned network fetch.

    DNS resolution is intentionally performed only by ``safe_http`` at the
    connection step.  Resolving here as well creates a check/use mismatch and
    can incorrectly reject a public CDN host with several addresses.
    """
    _validate_safe_public_url(url)


async def _get_public_url(client: httpx.AsyncClient, url: str, **kwargs) -> httpx.Response:
    """Fetch a public URL, IP-pinned and revalidated on every redirect hop.

    Delegates to app.core.safe_http.safe_get — see that module for why a
    plain "resolve, check, then let httpx resolve again to connect" approach
    (the previous implementation here) is vulnerable to DNS rebinding.
    """
    return await _safe_get(client, url, max_redirects=5, **kwargs)


async def _stream_public_url(
    client: httpx.AsyncClient,
    url: str,
    **kwargs,
) -> httpx.Response:
    """Open a streaming public URL, IP-pinned and revalidated on every
    redirect hop — see _get_public_url / app.core.safe_http for why."""
    return await _safe_stream_get(client, url, max_redirects=5, **kwargs)


def _strip_html_basic(html: str) -> str:
    """Basic HTML to text conversion — fallback when trafilatura is unavailable."""
    import html as html_module

    # Remove script and style tags
    html = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', html, flags=re.DOTALL | re.IGNORECASE)
    # Remove HTML tags (replace with space to preserve word boundaries)
    text = re.sub(r'<[^>]+>', ' ', html)
    # Decode HTML entities (&#x27; → ', &amp; → &, etc.)
    text = html_module.unescape(text)
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    # Take only the main content portion (skip navigation etc.)
    if len(text) > 500:
        return text[:10000]  # Cap at 10k chars
    return text


# ============================================================================
# Article Quiz
# ============================================================================

@router.post("/{article_id}/quiz")
async def get_article_quiz(
    article_id: str,
    article: dict = Body(..., description="Real article context used to build the quiz"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a deterministic comprehension quiz grounded in the supplied article.
    
    Generates 5 questions:
    - 2 comprehension (main idea, detail)
    - 2 vocabulary (word meaning in context)
    - 1 grammar (sentence structure)
    
    The client must send the real title/description/content it displayed.  We
    intentionally reject an ID-only request instead of inventing context.
    """
    quiz_article = _validated_quiz_article(article)
    context_hash = hashlib.sha256(
        (
            quiz_article["title"]
            + "\n"
            + quiz_article["description"]
            + "\n"
            + quiz_article["content"]
        ).encode("utf-8")
    ).hexdigest()[:16]
    cache_key = f"news:quiz:v3:{article_id}:{context_hash}"
    cache_service = APICacheService(db)
    
    try:
        result = await cache_service.get_or_fetch(
            cache_key=cache_key,
            api_name="newsapi",
            fetch_fn=lambda: _generate_quiz(article_id, quiz_article),
            priority=Priority.LOW,
            cost=0,
            redis_ttl=604800,       # 7 days
            db_ttl=31536000,        # 1 year (permanent)
        )
        return {
            "article_id": article_id,
            "quiz": result.data,
            "source": result.source,
        }
    except (QuotaExhaustedError, QuotaNearLimitError) as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e),
        )


def _validated_quiz_article(article: dict) -> dict[str, str]:
    """Bound and validate client-supplied article text before quiz generation."""
    title = str(article.get("title") or "").strip()[:300]
    description = _strip_html_basic(
        str(article.get("description") or "")[:5000]
    )
    content = _strip_html_basic(str(article.get("content") or "")[:20000])
    source_text = " ".join(part for part in (description, content) if part)

    if not title or len(source_text) < 80:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                "The real article text is unavailable or too short for a reliable quiz. "
                "Open the article and load its full content before trying again."
            ),
        )

    sentences = _split_quiz_sentences(source_text)
    if len(sentences) < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="At least two complete source sentences are required for a reliable quiz.",
        )

    return {
        "title": title,
        "description": description,
        "content": content,
    }


# ============================================================================
# Internal Functions
# ============================================================================

async def _fetch_news(
    category: str = "general",
    page: int = 1,
    page_size: int = 10,
    query: Optional[str] = None,
) -> dict:
    """
    Fetch news from NewsAPI.org, NewsData.io, then a public BBC RSS feed.
    
    Returns normalized article list.
    """
    # Try NewsAPI.org first
    if settings.NEWSAPI_KEY:
        try:
            return await _fetch_from_newsapi(category, page, page_size, query)
        except Exception as e:
            logger.warning(f"NewsAPI.org failed, trying fallback: {e}")
    
    # Fallback: NewsData.io
    if settings.NEWSDATA_KEY:
        try:
            return await _fetch_from_newsdata(category, page, page_size, query)
        except Exception as e:
            logger.warning(f"NewsData.io failed, trying public RSS: {e}")

    # Public RSS is a real, attributable source and does not need a paid key.
    # It is deliberately last so configured providers retain their pagination.
    try:
        return await _fetch_from_public_rss(category, page, page_size, query)
    except Exception as e:
        logger.error(f"Public news RSS failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="News sources are temporarily unavailable.",
        ) from e


def _rss_text(item: ET.Element, tag: str) -> str:
    node = item.find(tag)
    return (node.text or "").strip() if node is not None else ""


def _rss_published_at(value: str) -> str:
    if not value:
        return ""
    try:
        return parsedate_to_datetime(value).isoformat()
    except (TypeError, ValueError):
        return value


async def _fetch_from_public_rss(
    category: str,
    page: int,
    page_size: int,
    query: Optional[str],
) -> dict:
    """Read normalized articles from BBC's public RSS feeds.

    RSS only exposes publisher-provided title/summary/link metadata. Full text is
    fetched later by the existing full-content endpoint, so no article text is
    invented or mislabeled as publisher content.
    """
    feed_url = PUBLIC_NEWS_RSS.get(category, PUBLIC_NEWS_RSS["general"])
    async with httpx.AsyncClient(
        timeout=15.0,
        headers={"User-Agent": "LexiLingo/1.0 (English learning app)"},
        follow_redirects=True,
    ) as client:
        response = await client.get(feed_url)
        response.raise_for_status()

    root = ET.fromstring(response.content)
    normalized = []
    query_lower = (query or "").strip().lower()
    media_ns = "{http://search.yahoo.com/mrss/}"

    for item in root.findall(".//item"):
        title = html.unescape(_rss_text(item, "title"))
        description = html.unescape(
            re.sub(r"<[^>]+>", " ", _rss_text(item, "description"))
        )
        description = re.sub(r"\s+", " ", description).strip()
        link = _rss_text(item, "link") or _rss_text(item, "guid")
        if not title or not link:
            continue
        if query_lower and query_lower not in f"{title} {description}".lower():
            continue

        thumbnail = item.find(f"{media_ns}thumbnail")
        image_url = thumbnail.get("url", "") if thumbnail is not None else ""
        if not image_url:
            enclosure = item.find("enclosure")
            if enclosure is not None and enclosure.get("type", "").startswith("image/"):
                image_url = enclosure.get("url", "")

        normalized.append({
            "id": hashlib.md5(f"{link}{title}".encode()).hexdigest()[:12],
            "title": title,
            "description": description,
            "content": description,
            "url": link,
            "image_url": image_url,
            "source_name": "BBC News",
            "author": "BBC News",
            "published_at": _rss_published_at(_rss_text(item, "pubDate")),
            "category": category,
            "provider": "bbc_rss",
        })

    start = (page - 1) * page_size
    return {
        "articles": normalized[start:start + page_size],
        "total_results": len(normalized),
    }


async def _fetch_from_newsapi(
    category: str,
    page: int,
    page_size: int,
    query: Optional[str],
) -> dict:
    """Fetch from NewsAPI.org and normalize to common format."""
    params = {
        "apiKey": settings.NEWSAPI_KEY,
        "language": "en",
        "pageSize": page_size,
        "page": page,
    }
    
    if query:
        # Use /everything endpoint for search
        params["q"] = query
        params["sortBy"] = "relevancy"
        endpoint = f"{NEWSAPI_BASE}/everything"
    else:
        # Use /top-headlines for category browsing
        params["category"] = category
        params["country"] = "us"
        endpoint = f"{NEWSAPI_BASE}/top-headlines"
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(endpoint, params=params)
        response.raise_for_status()
        data = response.json()
    
    if data.get("status") != "ok":
        raise Exception(f"NewsAPI error: {data.get('message', 'Unknown')}")
    
    articles = []
    for item in data.get("articles", []):
        # Skip articles with [Removed] content
        if item.get("title") == "[Removed]" or not item.get("content"):
            continue
        
        article_id = hashlib.md5(
            (item.get("url", "") + item.get("title", "")).encode()
        ).hexdigest()[:12]
        
        articles.append({
            "id": article_id,
            "title": item.get("title", ""),
            "description": item.get("description", ""),
            "content": re.sub(r'\s*\[\+\d+ chars\]$', '', item.get("content", "")),
            "url": item.get("url", ""),
            "image_url": item.get("urlToImage", ""),
            "source_name": item.get("source", {}).get("name", ""),
            "author": item.get("author", ""),
            "published_at": item.get("publishedAt", ""),
            "category": category,
            "provider": "newsapi",
        })
    
    return {
        "articles": articles,
        "total_results": data.get("totalResults", 0),
    }


async def _fetch_from_newsdata(
    category: str,
    page: int,
    page_size: int,
    query: Optional[str],
) -> dict:
    """Fetch from NewsData.io (fallback) and normalize to common format."""
    params = {
        "apikey": settings.NEWSDATA_KEY,
        "language": "en",
        "size": min(page_size, 10),  # NewsData free tier limit
    }
    
    if query:
        params["q"] = query
    if category and category != "general":
        params["category"] = category
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(f"{NEWSDATA_BASE}/news", params=params)
        response.raise_for_status()
        data = response.json()
    
    if data.get("status") != "success":
        raise Exception(f"NewsData error: {data.get('message', 'Unknown')}")
    
    articles = []
    for item in data.get("results", []):
        article_id = hashlib.md5(
            (item.get("link", "") + item.get("title", "")).encode()
        ).hexdigest()[:12]
        
        articles.append({
            "id": article_id,
            "title": item.get("title", ""),
            "description": item.get("description", ""),
            "content": item.get("content", "") or item.get("description", ""),
            "url": item.get("link", ""),
            "image_url": item.get("image_url", ""),
            "source_name": item.get("source_id", ""),
            "author": item.get("creator", [""])[0] if item.get("creator") else "",
            "published_at": item.get("pubDate", ""),
            "category": category,
            "provider": "newsdata",
        })
    
    return {
        "articles": articles,
        "total_results": data.get("totalResults", 0),
    }


def _estimate_cefr(article: dict) -> str:
    """
    Estimate CEFR level from article text using heuristics.
    
    Factors: word count, average word length, sentence complexity.
    In production, replace with AI grading via /ai/grade_text endpoint.
    """
    content = article.get("content", "") or article.get("description", "")
    if not content:
        return "B1"  # Default middle level
    
    words = content.split()
    word_count = len(words)
    
    if word_count == 0:
        return "B1"
    
    avg_word_length = sum(len(w) for w in words) / word_count
    
    # Long words + many words → harder
    # Short words + fewer words → easier
    complexity_score = (avg_word_length - 3) * 10 + (word_count / 50)
    
    if complexity_score < 10:
        return "A1"
    elif complexity_score < 20:
        return "A2"
    elif complexity_score < 35:
        return "B1"
    elif complexity_score < 50:
        return "B2"
    elif complexity_score < 70:
        return "C1"
    else:
        return "C2"


def _estimate_reading_time(article: dict) -> int:
    """Estimate reading time in minutes (avg 200 wpm for ESL learners)."""
    content = article.get("content", "") or article.get("description", "")
    word_count = len(content.split()) if content else 0
    return max(1, round(word_count / 150))  # 150 wpm for ESL


def _extract_highlight_words(article: dict) -> list[str]:
    """
    Extract potentially challenging vocabulary words to highlight.
    
    Simple heuristic: words longer than 7 characters that aren't common.
    In production, use AI NLP analysis.
    """
    COMMON_LONG_WORDS = {
        "something", "everything", "everyone", "someone", "position",
        "important", "different", "national", "international", "according",
        "government", "president", "countries", "continue", "following",
        "including", "community", "available", "together", "possible",
        "information", "development", "education", "technology", "experience",
        "questions", "companies", "beginning", "financial", "political",
    }
    
    content = article.get("content", "") or article.get("description", "")
    if not content:
        return []
    
    import re
    words = re.findall(r'\b[a-zA-Z]+\b', content)
    
    highlights = set()
    for word in words:
        lower = word.lower()
        if len(lower) > 7 and lower not in COMMON_LONG_WORDS:
            highlights.add(lower)
    
    return sorted(list(highlights))[:10]  # Max 10 highlighted words


async def _generate_quiz(article_id: str, article: dict | None = None) -> dict:
    """
    Generate a comprehension quiz for an article.

    This deterministic generator keeps the route useful even when the AI
    service is unavailable. A future AI-backed generator can replace this
    helper as long as it preserves the response contract below.
    """
    if not article:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Real article context is required to generate a quiz.",
        )
    context = _build_quiz_context(article_id, article)
    topic = context["topic"]
    sentences = context["sentences"]
    keywords = context["highlight_words"]

    main_sentence = sentences[0]
    detail_sentence = sentences[1]
    support_sentence = sentences[2] if len(sentences) > 2 else detail_sentence
    first_word, first_word_sentence = _keyword_in_source(sentences, keywords, 0)
    second_word, second_word_sentence = _keyword_in_source(
        sentences,
        [word for word in keywords if word.lower() != first_word.lower()],
        1,
    )
    all_distractors = _extract_quiz_keywords(" ".join(sentences), topic)

    return {
        "questions": [
            {
                "id": 1,
                "type": "comprehension",
                "question": "Which statement is explicitly supported by the article?",
                "options": _unique_options(
                    [
                        _shorten(main_sentence, 110),
                        f"The article gives no information about {topic}.",
                        "The article says that every event described is fictional.",
                        "The article replaces its subject with an unrelated travel diary.",
                    ]
                ),
                "correct_index": 0,
                "explanation": (
                    f"The correct answer reproduces this source sentence: “{_shorten(main_sentence, 180)}” "
                    "The other choices add claims that do not appear in the source, so they "
                    "cannot be supported by the article."
                ),
            },
            {
                "id": 2,
                "type": "comprehension",
                "question": "Which supporting detail is mentioned in the article?",
                "options": _unique_options(
                    [
                        f"The article says that {topic} happened without any context.",
                        _shorten(detail_sentence, 110),
                        "The article says the topic was cancelled before it began.",
                        "The article says readers should ignore the main event.",
                    ]
                ),
                "correct_index": 1,
                "explanation": (
                    f"The correct answer comes directly from the source: “{_shorten(detail_sentence, 180)}” "
                    "The other options either remove the article's context or introduce actions "
                    "that the source never states."
                ),
            },
            {
                "id": 3,
                "type": "vocabulary",
                "question": (
                    "Which word from the article exactly completes this sentence?\n"
                    f"{_cloze_source_sentence(first_word_sentence, first_word)}"
                ),
                "options": _cloze_options(first_word, all_distractors, 2),
                "correct_index": 2,
                "explanation": (
                    f"The source sentence reads: “{_shorten(first_word_sentence, 180)}” "
                    f"Therefore “{first_word}” is the exact contextual answer. The other words "
                    "are not used in this position in the article, even if they occur elsewhere."
                ),
            },
            {
                "id": 4,
                "type": "vocabulary",
                "question": (
                    "Which word from the article exactly completes this sentence?\n"
                    f"{_cloze_source_sentence(second_word_sentence, second_word)}"
                ),
                "options": _cloze_options(second_word, all_distractors, 0),
                "correct_index": 0,
                "explanation": (
                    f"The source sentence reads: “{_shorten(second_word_sentence, 180)}” "
                    f"The author uses “{second_word}” in that exact place. The remaining choices "
                    "do not match the recorded wording and therefore are not evidence-based answers."
                ),
            },
            {
                "id": 5,
                "type": "grammar",
                "question": "Which sentence structure is correct?",
                "options": _unique_options(
                    [
                        f"{topic} are explains by the article.",
                        f"The article explain {topic}.",
                        f"Readers learning about {topic} yesterday important.",
                        _shorten(support_sentence, 120),
                    ]
                ),
                "correct_index": 3,
                "explanation": (
                    f"The correct option is the complete source sentence: “{_shorten(support_sentence, 180)}” "
                    "It contains a subject and a correctly formed predicate. Option 1 has an "
                    "agreement/verb-form error (“are explains”); option 2 needs “explains”; "
                    "option 3 is a fragment without a finite main verb."
                ),
            },
        ],
        "total_questions": 5,
        "xp_reward": 15,
        "source": context["source"],
    }


def _build_quiz_context(article_id: str, article: dict) -> dict:
    """Build safe article context for deterministic quiz generation."""
    title = str(article.get("title") or "").strip()
    description = str(article.get("description") or "").strip()
    content = str(article.get("content") or "").strip()
    body_parts = [part for part in (description, content) if part]
    raw_text = " ".join(dict.fromkeys(body_parts))
    topic = title or _humanize_article_id(article_id)

    sentences = _split_quiz_sentences(raw_text)
    if len(sentences) < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="The article does not contain enough complete sentences for a reliable quiz.",
        )

    highlight_words = _extract_highlight_words(article)
    extracted_keywords = _extract_quiz_keywords(raw_text, topic)
    highlight_words = list(dict.fromkeys(highlight_words + extracted_keywords))

    return {
        "topic": _shorten(topic, 80),
        "sentences": sentences[:6],
        "highlight_words": highlight_words[:12],
        "source": "article_context",
    }


def _keyword_in_source(
    sentences: list[str], preferred: list[str], fallback_sentence_index: int
) -> tuple[str, str]:
    """Choose a keyword and the real sentence that contains it."""
    for word in preferred:
        pattern = re.compile(rf"\b{re.escape(word)}\b", re.IGNORECASE)
        for sentence in sentences:
            if pattern.search(sentence):
                return word.lower(), sentence

    sentence = sentences[min(fallback_sentence_index, len(sentences) - 1)]
    return _topic_keyword(sentence), sentence


def _cloze_source_sentence(sentence: str, word: str) -> str:
    """Blank one exact source word without changing the rest of the sentence."""
    return re.sub(
        rf"\b{re.escape(word)}\b",
        "_____",
        _shorten(sentence, 180),
        count=1,
        flags=re.IGNORECASE,
    )


def _cloze_options(correct: str, candidates: list[str], correct_index: int) -> list[str]:
    """Build stable cloze options while keeping the declared answer index."""
    wrong = [
        word.lower()
        for word in candidates + ["article", "reader", "report", "context"]
        if word.lower() != correct.lower()
    ]
    wrong = list(dict.fromkeys(wrong))[:3]
    options = wrong.copy()
    options.insert(correct_index, correct.lower())
    return options[:4]


def _humanize_article_id(article_id: str) -> str:
    """Convert a cache-safe article ID into a readable fallback topic."""
    cleaned = re.sub(r"[_\-]+", " ", article_id).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned or "this news article"


def _split_quiz_sentences(text: str) -> list[str]:
    """Extract readable sentences for quiz options."""
    candidates = re.split(r"(?<=[.!?])\s+", text)
    sentences: list[str] = []
    for candidate in candidates:
        cleaned = re.sub(r"\s+", " ", candidate).strip(" .")
        if len(cleaned.split()) >= 4:
            sentences.append(f"{cleaned}.")
    if sentences:
        return sentences

    cleaned = re.sub(r"\s+", " ", text).strip(" .")
    return [f"{cleaned}."] if cleaned else []


def _extract_quiz_keywords(text: str, topic: str) -> list[str]:
    """Extract stable fallback keywords when highlighted words are unavailable."""
    stop_words = {
        "about", "article", "because", "between", "could", "every", "focuses",
        "important", "learning", "matters", "readers", "should", "their",
        "there", "these", "those", "through", "understand", "useful", "which",
    }
    words = re.findall(r"\b[a-zA-Z][a-zA-Z\-]{4,}\b", f"{text} {topic}")
    keywords: list[str] = []
    for word in words:
        lower = word.lower()
        if lower in stop_words or lower in keywords:
            continue
        keywords.append(lower)
        if len(keywords) == 4:
            break
    return keywords or [_topic_keyword(topic)]


def _topic_keyword(text: str) -> str:
    """Return a readable keyword from arbitrary text."""
    words = re.findall(r"\b[a-zA-Z][a-zA-Z\-]{3,}\b", text)
    if not words:
        return "topic"
    return max((word.lower() for word in words), key=len)


def _vocabulary_definition(word: str, topic: str) -> str:
    """Return a useful beginner-friendly definition for common news terms."""
    definitions = {
        "electricity": "power used by lights, machines, and buildings",
        "installed": "put something in place so it can be used",
        "panels": "flat pieces of equipment used to collect or display something",
        "project": "a planned piece of work with a clear goal",
        "reduces": "makes something smaller or lower",
        "renewable": "able to be replaced naturally and used again",
        "science": "the study of how the world works",
        "students": "people who are learning at school or in a course",
        "support": "help something work or become stronger",
        "teachers": "people who help students learn",
    }
    return definitions.get(
        word.lower(),
        f"a key idea connected to {topic}",
    )


def _unique_options(options: list[str]) -> list[str]:
    """Ensure quiz options are unique while preserving the correct index."""
    seen: set[str] = set()
    unique: list[str] = []
    fillers = [
        "A background detail that is not the best answer",
        "A different idea not supported by the article",
        "A general statement that misses the article's focus",
        "A confusing option with no clear connection",
    ]
    for option in options + fillers:
        normalized = option.strip()
        key = normalized.lower()
        if normalized and key not in seen:
            unique.append(normalized)
            seen.add(key)
        if len(unique) == 4:
            return unique
    return unique[:4]


def _shorten(text: str, max_length: int) -> str:
    """Shorten long generated options without cutting in the middle of a word."""
    cleaned = re.sub(r"\s+", " ", text).strip()
    if len(cleaned) <= max_length:
        return cleaned
    truncated = cleaned[: max_length - 1].rsplit(" ", 1)[0].strip()
    return f"{truncated}."
