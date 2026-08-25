import re
import urllib.parse
from typing import List, Optional, Tuple
import httpx
from app.core.config import PLATFORMS, ProfileResult, SearchResponse

def extract_target_from_input(raw_input: str) -> Tuple[str, bool]:
    clean_input = raw_input.strip()
    if not (clean_input.startswith("http://") or clean_input.startswith("https://") or "www." in clean_input or ".com" in clean_input):
        return clean_input, False

    # Try parsing URL
    url_to_parse = clean_input
    if not (url_to_parse.startswith("http://") or url_to_parse.startswith("https://")):
        url_to_parse = "https://" + url_to_parse

    try:
        parsed = urllib.parse.urlparse(url_to_parse)
        path_parts = [p for p in parsed.path.split("/") if p]

        # StackOverflow: /users/12888115/kofi -> kofi
        if "stackoverflow.com" in parsed.netloc:
            if len(path_parts) >= 3 and path_parts[0] == "users":
                return path_parts[2], True
            elif len(path_parts) >= 2 and path_parts[0] == "users":
                return path_parts[1], True

        # LinkedIn: /in/john-doe -> john-doe
        if "linkedin.com" in parsed.netloc:
            if len(path_parts) >= 2 and path_parts[0] == "in":
                return path_parts[1], True

        # Medium: /@username -> username
        if "medium.com" in parsed.netloc:
            if path_parts:
                return path_parts[0].lstrip("@"), True

        # GitHub / GitLab / generic path
        if path_parts:
            extracted = path_parts[0].lstrip("@")
            # Avoid extracting generic paths like 'search', 'users' if standalone
            if extracted not in ["search", "users", "pub", "dir", "in"]:
                return extracted, True

    except Exception:
        pass

    # Fallback if parsing fails or non-matching URL path
    return clean_input, True

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

    # Candidate profile URL if single token (potential username/handle) and not a full URL
    candidate_url = None
    if " " not in clean_query and not clean_query.startswith("http://") and not clean_query.startswith("https://") and config.profile_url_template:
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
    target, is_url = extract_target_from_input(query)
    target_platforms = platforms if platforms else list(PLATFORMS.keys())
    results: List[ProfileResult] = []

    for key in target_platforms:
        key_lower = key.lower()
        if key_lower in PLATFORMS:
            res = format_platform_urls(key_lower, target)
            if check_status and res.profile_candidate_url:
                status = await check_candidate_url(res.profile_candidate_url)
                if status:
                    res.status = status
            results.append(res)

    return SearchResponse(
        raw_query=query,
        extracted_target=target,
        is_url=is_url,
        results=results
    )
