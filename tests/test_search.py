import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.search_service import format_platform_urls, generate_google_dork_url, extract_target_from_input

client = TestClient(app)

def test_extract_target_from_input():
    # Plain text query
    target, is_url = extract_target_from_input("octocat")
    assert target == "octocat"
    assert is_url is False

    # Full name query
    target, is_url = extract_target_from_input("John Doe")
    assert target == "John Doe"
    assert is_url is False

    # StackOverflow URL
    target, is_url = extract_target_from_input("https://stackoverflow.com/users/12888115/kofi")
    assert target == "kofi"
    assert is_url is True

    # LinkedIn URL
    target, is_url = extract_target_from_input("https://linkedin.com/in/jane-doe")
    assert target == "jane-doe"
    assert is_url is True

def test_google_dork_url_generation():
    url = generate_google_dork_url('site:linkedin.com/in/ "John Doe"')
    assert "google.com/search?q=" in url
    assert "site%3Alinkedin.com" in url or "site:linkedin.com" in url

def test_format_platform_urls_single_name():
    res = format_platform_urls("github", "octocat")
    assert res.platform == "GitHub"
    assert res.profile_candidate_url == "https://github.com/octocat"
    assert "github.com/search" in res.search_url
    assert 'site:github.com "octocat"' in res.google_dork

def test_format_platform_urls_full_name():
    res = format_platform_urls("linkedin", "Jane Doe")
    assert res.platform == "LinkedIn"
    assert res.profile_candidate_url is None  # Full names containing spaces shouldn't match direct handle candidate URL
    assert "firstName=Jane" in res.search_url
    assert "lastName=Doe" in res.search_url

def test_api_platforms_endpoint():
    response = client.get("/api/v1/platforms")
    assert response.status_code == 200
    data = response.json()
    assert "platforms" in data
    platform_keys = [p["key"] for p in data["platforms"]]
    assert "linkedin" in platform_keys
    assert "github" in platform_keys
    assert "gitlab" in platform_keys
    assert "stackoverflow" in platform_keys
    assert "medium" in platform_keys

def test_api_search_endpoint():
    response = client.get("/api/v1/search?q=testuser")
    assert response.status_code == 200
    data = response.json()
    assert data["raw_query"] == "testuser"
    assert data["extracted_target"] == "testuser"
    assert len(data["results"]) == 5

def test_api_search_url_input():
    response = client.get("/api/v1/search?q=https://stackoverflow.com/users/12888115/kofi")
    assert response.status_code == 200
    data = response.json()
    assert data["extracted_target"] == "kofi"
    assert data["is_url"] is True
    # Ensure candidate URL is generated properly for extracted handle 'kofi'
    github_res = next(r for r in data["results"] if r["platform"] == "GitHub")
    assert github_res["profile_candidate_url"] == "https://github.com/kofi"

def test_api_search_with_platform_filter():
    response = client.get("/api/v1/search?q=testuser&platforms=github&platforms=medium")
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 2
    platforms = [r["platform"] for r in data["results"]]
    assert "GitHub" in platforms
    assert "Medium" in platforms

def test_api_search_invalid_platform():
    response = client.get("/api/v1/search?q=testuser&platforms=invalid_platform")
    assert response.status_code == 400
    assert "Invalid platform" in response.json()["detail"]

def test_web_home_route():
    response = client.get("/")
    assert response.status_code == 200
    assert "ProfScope" in response.text

def test_web_home_route_with_query():
    response = client.get("/?q=Jane+Doe")
    assert response.status_code == 200
    assert "Results for target: &quot;Jane Doe&quot;" in response.text or 'Results for target: "Jane Doe"' in response.text
    assert "LinkedIn" in response.text
