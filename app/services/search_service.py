import re
import urllib.parse
from typing import List, Optional, Tuple, Dict, Any
import httpx
from app.core.config import PLATFORMS, ProfileResult, SearchResponse, DiscoveredUserProfile

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ProfScope OSINT Discovery Tool"
}

def extract_target_from_input(raw_input: str) -> Tuple[str, bool]:
    clean_input = raw_input.strip()
    if not (clean_input.startswith("http://") or clean_input.startswith("https://") or "www." in clean_input or ".com" in clean_input):
        return clean_input, False

    url_to_parse = clean_input
    if not (url_to_parse.startswith("http://") or url_to_parse.startswith("https://")):
        url_to_parse = "https://" + url_to_parse

    try:
        parsed = urllib.parse.urlparse(url_to_parse)
        path_parts = [p for p in parsed.path.split("/") if p]

        if "stackoverflow.com" in parsed.netloc:
            if len(path_parts) >= 3 and path_parts[0] == "users":
                return path_parts[2], True
            elif len(path_parts) >= 2 and path_parts[0] == "users":
                return path_parts[1], True

        if "linkedin.com" in parsed.netloc:
            if len(path_parts) >= 2 and path_parts[0] == "in":
                return path_parts[1], True

        if "medium.com" in parsed.netloc:
            if path_parts:
                return path_parts[0].lstrip("@"), True

        if path_parts:
            extracted = path_parts[0].lstrip("@")
            if extracted not in ["search", "users", "pub", "dir", "in"]:
                return extracted, True

    except Exception:
        pass

    return clean_input, True

def generate_google_dork_url(dork_query: str) -> str:
    encoded = urllib.parse.quote(dork_query)
    return f"https://www.google.com/search?q={encoded}"

def format_platform_urls(platform_key: str, query: str) -> ProfileResult:
    config = PLATFORMS[platform_key]
    clean_query = query.strip()
    encoded_query = urllib.parse.quote(clean_query)

    dork = config.google_dork_template.format(query=clean_query)
    dork_url = generate_google_dork_url(dork)

    parts = clean_query.split()
    first_name = urllib.parse.quote(parts[0]) if parts else ""
    last_name = urllib.parse.quote(" ".join(parts[1:])) if len(parts) > 1 else ""

    direct_url = config.direct_search_url_template.format(
        query=encoded_query,
        first_name=first_name,
        last_name=last_name
    )

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

async def search_github_profiles(target: str) -> List[DiscoveredUserProfile]:
    profiles = []
    try:
        url = f"https://api.github.com/search/users?q={urllib.parse.quote(target)}&per_page=10"
        async with httpx.AsyncClient(timeout=4.0) as client:
            res = await client.get(url, headers=HEADERS)
            if res.status_code == 200:
                items = res.json().get("items", [])
                for item in items:
                    login = item.get("login")
                    dork = f'site:github.com "{login}"'
                    profiles.append(DiscoveredUserProfile(
                        platform="GitHub",
                        display_name=login,
                        username=login,
                        avatar_url=item.get("avatar_url"),
                        profile_url=item.get("html_url") or f"https://github.com/{login}",
                        search_url=f"https://github.com/search?q={urllib.parse.quote(login)}&type=users",
                        google_dork=dork,
                        google_dork_url=generate_google_dork_url(dork),
                        extra_info=f"Type: {item.get('type', 'User')}"
                    ))
    except Exception:
        pass
    return profiles

async def search_gitlab_profiles(target: str) -> List[DiscoveredUserProfile]:
    profiles = []
    try:
        url = f"https://gitlab.com/api/v4/users?search={urllib.parse.quote(target)}&per_page=10"
        async with httpx.AsyncClient(timeout=4.0) as client:
            res = await client.get(url, headers=HEADERS)
            if res.status_code == 200:
                users = res.json()
                if isinstance(users, list):
                    for u in users:
                        username = u.get("username")
                        name = u.get("name") or username
                        dork = f'site:gitlab.com "{username}"'
                        profiles.append(DiscoveredUserProfile(
                            platform="GitLab",
                            display_name=name,
                            username=username,
                            avatar_url=u.get("avatar_url"),
                            profile_url=u.get("web_url") or f"https://gitlab.com/{username}",
                            search_url=f"https://gitlab.com/search?search={urllib.parse.quote(username)}",
                            google_dork=dork,
                            google_dork_url=generate_google_dork_url(dork),
                            location=u.get("location"),
                            extra_info=f"State: {u.get('state', 'active')}"
                        ))
    except Exception:
        pass
    return profiles

async def search_stackoverflow_profiles(target: str) -> List[DiscoveredUserProfile]:
    profiles = []
    try:
        url = f"https://api.stackexchange.com/2.3/users?inname={urllib.parse.quote(target)}&site=stackoverflow&pagesize=10"
        async with httpx.AsyncClient(timeout=4.0) as client:
            res = await client.get(url, headers=HEADERS)
            if res.status_code == 200:
                items = res.json().get("items", [])
                for item in items:
                    display_name = item.get("display_name")
                    rep = item.get("reputation", 0)
                    dork = f'site:stackoverflow.com/users "{display_name}"'
                    profiles.append(DiscoveredUserProfile(
                        platform="Stack Overflow",
                        display_name=display_name,
                        username=display_name,
                        avatar_url=item.get("profile_image"),
                        profile_url=item.get("link") or f"https://stackoverflow.com/users/{item.get('user_id')}",
                        search_url=f"https://stackoverflow.com/users?search={urllib.parse.quote(display_name)}",
                        google_dork=dork,
                        google_dork_url=generate_google_dork_url(dork),
                        location=item.get("location"),
                        extra_info=f"Reputation: {rep}"
                    ))
    except Exception:
        pass
    return profiles

async def fetch_all_discovered_profiles(target: str) -> List[DiscoveredUserProfile]:
    profiles: List[DiscoveredUserProfile] = []
    gh = await search_github_profiles(target)
    gl = await search_gitlab_profiles(target)
    so = await search_stackoverflow_profiles(target)
    profiles.extend(gh)
    profiles.extend(gl)
    profiles.extend(so)
    return profiles

async def check_candidate_url(candidate_url: Optional[str]) -> Optional[str]:
    if not candidate_url:
        return None
    try:
        async with httpx.AsyncClient(timeout=3.0, follow_redirects=True) as client:
            response = await client.head(candidate_url, headers=HEADERS)
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

    discovered_profiles = await fetch_all_discovered_profiles(target)

    return SearchResponse(
        raw_query=query,
        extracted_target=target,
        is_url=is_url,
        discovered_profiles=discovered_profiles,
        results=results
    )
