import re
import urllib.parse
from typing import Dict, Any, Optional
import httpx

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ProfScope OSINT Crawler"
}

async def fetch_github_profile(username: str) -> Dict[str, Any]:
    url = f"https://api.github.com/users/{urllib.parse.quote(username)}"
    async with httpx.AsyncClient(timeout=5.0) as client:
        res = await client.get(url, headers=HEADERS)
        if res.status_code == 200:
            data = res.json()
            return {
                "platform": "GitHub",
                "username": username,
                "name": data.get("name") or username,
                "bio": data.get("bio") or "No bio provided.",
                "location": data.get("location") or "Unknown",
                "avatar_url": data.get("avatar_url"),
                "profile_url": data.get("html_url"),
                "metrics": {
                    "Public Repos": data.get("public_repos", 0),
                    "Followers": data.get("followers", 0),
                    "Following": data.get("following", 0)
                }
            }
        return {"platform": "GitHub", "username": username, "error": f"Profile not found or inaccessible (HTTP {res.status_code})"}

async def fetch_gitlab_profile(username: str) -> Dict[str, Any]:
    url = f"https://gitlab.com/api/v4/users?username={urllib.parse.quote(username)}"
    async with httpx.AsyncClient(timeout=5.0) as client:
        res = await client.get(url, headers=HEADERS)
        if res.status_code == 200:
            users = res.json()
            if users and isinstance(users, list):
                data = users[0]
                return {
                    "platform": "GitLab",
                    "username": username,
                    "name": data.get("name") or username,
                    "bio": data.get("bio") or "No bio provided.",
                    "location": data.get("location") or "Unknown",
                    "avatar_url": data.get("avatar_url"),
                    "profile_url": data.get("web_url"),
                    "metrics": {
                        "State": data.get("state", "active")
                    }
                }
        return {"platform": "GitLab", "username": username, "error": f"Profile not found (HTTP {res.status_code})"}

async def fetch_stackoverflow_profile(username: str) -> Dict[str, Any]:
    url = f"https://api.stackexchange.com/2.3/users?inname={urllib.parse.quote(username)}&site=stackoverflow"
    async with httpx.AsyncClient(timeout=5.0) as client:
        res = await client.get(url, headers=HEADERS)
        if res.status_code == 200:
            items = res.json().get("items", [])
            for item in items:
                if item.get("display_name", "").lower() == username.lower() or str(item.get("user_id")) == username:
                    return {
                        "platform": "Stack Overflow",
                        "username": item.get("display_name"),
                        "name": item.get("display_name"),
                        "bio": f"Reputation: {item.get('reputation', 0)}",
                        "location": item.get("location") or "Unknown",
                        "avatar_url": item.get("profile_image"),
                        "profile_url": item.get("link"),
                        "metrics": {
                            "Reputation": item.get("reputation", 0),
                            "Gold Badges": item.get("badge_counts", {}).get("gold", 0),
                            "Silver Badges": item.get("badge_counts", {}).get("silver", 0),
                            "Bronze Badges": item.get("badge_counts", {}).get("bronze", 0)
                        }
                    }
            if items:
                item = items[0]
                return {
                    "platform": "Stack Overflow",
                    "username": item.get("display_name"),
                    "name": item.get("display_name"),
                    "bio": f"Reputation: {item.get('reputation', 0)}",
                    "location": item.get("location") or "Unknown",
                    "avatar_url": item.get("profile_image"),
                    "profile_url": item.get("link"),
                    "metrics": {
                        "Reputation": item.get("reputation", 0)
                    }
                }
        return {"platform": "Stack Overflow", "username": username, "error": f"Profile not found (HTTP {res.status_code})"}

async def fetch_opengraph_profile(platform_name: str, target_url: str, username: str) -> Dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
            res = await client.get(target_url, headers=HEADERS)
            if res.status_code == 200:
                html = res.text
                og_title = re.search(r'<meta\s+property=["\']og:title["\']\s+content=["\']([^"\']+)["\']', html, re.I)
                og_desc = re.search(r'<meta\s+property=["\']og:description["\']\s+content=["\']([^"\']+)["\']', html, re.I)
                og_image = re.search(r'<meta\s+property=["\']og:image["\']\s+content=["\']([^"\']+)["\']', html, re.I)

                title_val = og_title.group(1) if og_title else username
                desc_val = og_desc.group(1) if og_desc else "Public profile."
                img_val = og_image.group(1) if og_image else None

                return {
                    "platform": platform_name,
                    "username": username,
                    "name": title_val,
                    "bio": desc_val,
                    "location": "Public Profile",
                    "avatar_url": img_val,
                    "profile_url": target_url,
                    "metrics": {
                        "Status": "Publicly Accessible"
                    }
                }
    except Exception as e:
        pass
    return {
        "platform": platform_name,
        "username": username,
        "name": username,
        "bio": f"Public profile link for {username}",
        "location": "Public Profile",
        "avatar_url": None,
        "profile_url": target_url,
        "metrics": {
            "Status": "Link Generated"
        }
    }

async def crawl_profile_info(platform: str, username: str) -> Dict[str, Any]:
    p_lower = platform.lower()
    if p_lower == "github":
        return await fetch_github_profile(username)
    elif p_lower == "gitlab":
        return await fetch_gitlab_profile(username)
    elif p_lower == "stackoverflow":
        return await fetch_stackoverflow_profile(username)
    elif p_lower == "linkedin":
        url = f"https://www.linkedin.com/in/{urllib.parse.quote(username)}"
        return await fetch_opengraph_profile("LinkedIn", url, username)
    elif p_lower == "medium":
        url = f"https://medium.com/@{urllib.parse.quote(username.lstrip('@'))}"
        return await fetch_opengraph_profile("Medium", url, username)
    else:
        return {"platform": platform, "username": username, "error": "Unsupported platform"}
