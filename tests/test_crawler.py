import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.crawler_service import crawl_profile_info, fetch_github_profile, fetch_gitlab_profile
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.mark.asyncio
async def test_fetch_github_profile_mocked():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "name": "Octocat",
        "bio": "GitHub mascot",
        "location": "San Francisco",
        "avatar_url": "https://github.com/images/error/octocat_happy.gif",
        "html_url": "https://github.com/octocat",
        "public_repos": 8,
        "followers": 9000,
        "following": 0
    }

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        data = await fetch_github_profile("octocat")
        assert data["platform"] == "GitHub"
        assert data["name"] == "Octocat"
        assert data["metrics"]["Public Repos"] == 8

@pytest.mark.asyncio
async def test_fetch_gitlab_profile_mocked():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{
        "name": "GitLab User",
        "bio": "Developer",
        "location": "Remote",
        "avatar_url": "https://gitlab.com/avatar.png",
        "web_url": "https://gitlab.com/testuser",
        "state": "active"
    }]

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        data = await fetch_gitlab_profile("testuser")
        assert data["platform"] == "GitLab"
        assert data["name"] == "GitLab User"

@pytest.mark.asyncio
async def test_crawl_profile_info_social_platforms():
    with patch("app.services.crawler_service.fetch_opengraph_profile", new_callable=AsyncMock) as mock_og:
        mock_og.return_value = {
            "platform": "X (Twitter)",
            "username": "kofi",
            "name": "Kofi",
            "bio": "Developer",
            "location": "Public Profile",
            "avatar_url": None,
            "profile_url": "https://x.com/kofi",
            "metrics": {"Status": "Publicly Accessible"}
        }
        res = await crawl_profile_info("x", "kofi")
        assert res["platform"] == "X (Twitter)"
        assert res["profile_url"] == "https://x.com/kofi"

def test_api_profile_info_endpoint():
    mock_data = {
        "platform": "GitHub",
        "username": "octocat",
        "name": "Octocat",
        "bio": "GitHub mascot",
        "location": "San Francisco",
        "avatar_url": "https://github.com/images/error/octocat_happy.gif",
        "profile_url": "https://github.com/octocat",
        "metrics": {"Public Repos": 8}
    }
    with patch("app.api.routes.crawl_profile_info", new_callable=AsyncMock) as mock_crawl:
        mock_crawl.return_value = mock_data
        response = client.get("/api/v1/profile-info?platform=github&username=octocat")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Octocat"
