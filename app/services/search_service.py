import urllib.parse
from typing import List, Optional
import httpx
from app.core.config import PLATFORMS, ProfileResult, SearchResponse

def generate_google_dork_url(dork_query: str) -> str:
    encoded = urllib.parse.quote(dork_query)
    return f"https://www.google.com/search?q={encoded}"

def format_platform_urls(platform_key: str, query: str) -> ProfileResult:
    config = PLATFORMS[platform_key]
    clean_query = query.strip()
    encoded_query = urllib.parse.quote(clean_query)

    # Generate Google Dork
    dork = config.google_dork_template.format(query=clean_query)
    dork_url = generate_google_dork_url(dork)

    # Generate Direct Platform Search URL
    parts = clean_query.split()
    first_name = urllib.parse.quote(parts[0]) if parts else ""
    last_name = urllib.parse.quote(" ".join(parts[1:])) if len(parts) > 1 else ""

    direct_url = config.direct_search_url_template.format(
        query=encoded_query,
        first_name=first_name,
        last_name=last_name
    )

    # Candidate profile URL if single token (potential username/handle)
    candidate_url = None
    if " " not in clean_query and config.profile_url_template:
        candidate_url = config.profile_url_template.format(username=urllib.parse.quote(clean_query.lstrip("@")))

    return ProfileResult(
        platform=config.name,
        domain=config.domain,
        search_url=direct_url,
        profile_candidate_url=candidate_url,
        google_dork=dork,
        google_dork_url=dork_url,
        status="generated"
    )

async def check_candidate_url(candidate_url: Optional[str]) -> Optional[str]:
    if not candidate_url:
        return None
    try:
        async with httpx.AsyncClient(timeout=3.0, follow_redirects=True) as client:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ProfScope OSINT Tool"}
            response = await client.head(candidate_url, headers=headers)
            if response.status_code == 200:
                return "exists"
            elif response.status_code == 404:
                return "not_found"
            else:
                return "unverified"
    except Exception:
        return "unverified"

async def perform_search(query: str, platforms: Optional[List[str]] = None, check_status: bool = False) -> SearchResponse:
    target_platforms = platforms if platforms else list(PLATFORMS.keys())
    results: List[ProfileResult] = []

    for key in target_platforms:
        key_lower = key.lower()
        if key_lower in PLATFORMS:
            res = format_platform_urls(key_lower, query)
            if check_status and res.profile_candidate_url:
                status = await check_candidate_url(res.profile_candidate_url)
                if status:
                    res.status = status
            results.append(res)

    return SearchResponse(query=query, results=results)
