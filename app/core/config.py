from typing import List, Dict, Optional
from pydantic import BaseModel, Field

class PlatformConfig(BaseModel):
    name: str
    domain: str
    direct_search_url_template: str
    profile_url_template: Optional[str] = None
    google_dork_template: str

PLATFORMS: Dict[str, PlatformConfig] = {
    "linkedin": PlatformConfig(
        name="LinkedIn",
        domain="linkedin.com",
        direct_search_url_template="https://www.linkedin.com/pub/dir?firstName={first_name}&lastName={last_name}",
        profile_url_template="https://www.linkedin.com/in/{username}",
        google_dork_template='site:linkedin.com/in/ "{query}"'
    ),
    "github": PlatformConfig(
        name="GitHub",
        domain="github.com",
        direct_search_url_template="https://github.com/search?q={query}&type=users",
        profile_url_template="https://github.com/{username}",
        google_dork_template='site:github.com "{query}"'
    ),
    "gitlab": PlatformConfig(
        name="GitLab",
        domain="gitlab.com",
        direct_search_url_template="https://gitlab.com/search?search={query}",
        profile_url_template="https://gitlab.com/{username}",
        google_dork_template='site:gitlab.com "{query}"'
    ),
    "stackoverflow": PlatformConfig(
        name="Stack Overflow",
        domain="stackoverflow.com",
        direct_search_url_template="https://stackoverflow.com/users?search={query}",
        profile_url_template="https://stackoverflow.com/users/{username}",
        google_dork_template='site:stackoverflow.com/users "{query}"'
    ),
    "medium": PlatformConfig(
        name="Medium",
        domain="medium.com",
        direct_search_url_template="https://medium.com/search?q={query}",
        profile_url_template="https://medium.com/@{username}",
        google_dork_template='site:medium.com "@ {query}"'
    )
}

class DiscoveredUserProfile(BaseModel):
    platform: str
    display_name: str
    username: str
    avatar_url: Optional[str] = None
    profile_url: str
    search_url: Optional[str] = None
    google_dork: Optional[str] = None
    google_dork_url: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    extra_info: Optional[str] = None

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Target name or username to search")
    platforms: Optional[List[str]] = Field(default=None, description="Optional list of target platforms")

class ProfileResult(BaseModel):
    platform: str
    domain: str
    search_url: str
    profile_candidate_url: Optional[str] = None
    google_dork: str
    google_dork_url: str
    status: str = "generated"  # candidate, generated, exists, etc.

class SearchResponse(BaseModel):
    raw_query: str
    extracted_target: str
    is_url: bool
    discovered_profiles: List[DiscoveredUserProfile] = []
    results: List[ProfileResult]
