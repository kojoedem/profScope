from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException
from app.core.config import SearchResponse, PLATFORMS
from app.services.search_service import perform_search
from app.services.crawler_service import crawl_profile_info

router = APIRouter(prefix="/api/v1", tags=["search"])

@router.get("/search", response_model=SearchResponse)
async def search_profiles(
    q: str = Query(..., min_length=1, description="Target name or handle to search"),
    platforms: Optional[List[str]] = Query(None, description="Filter specific platforms (e.g., github, linkedin)"),
    check_status: bool = Query(False, description="Whether to verify profile availability live")
):
    try:
        if platforms:
            invalid_platforms = [p for p in platforms if p.lower() not in PLATFORMS]
            if invalid_platforms:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid platform(s): {', '.join(invalid_platforms)}. Supported: {', '.join(PLATFORMS.keys())}"
                )
        results = await perform_search(query=q, platforms=platforms, check_status=check_status)
        return results
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/profile-info")
async def get_profile_info(
    platform: str = Query(..., description="Target platform (e.g. github, stackoverflow)"),
    username: str = Query(..., min_length=1, description="Target handle or username")
):
    try:
        data = await crawl_profile_info(platform=platform, username=username)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/platforms")
async def get_platforms():
    return {
        "platforms": [
            {"key": key, "name": config.name, "domain": config.domain}
            for key, config in PLATFORMS.items()
        ]
    }
