import os
from typing import Optional
from fastapi import FastAPI, Request, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from app.api.routes import router as api_router
from app.services.search_service import perform_search

app = FastAPI(
    title="ProfScope",
    description="Professional OSINT Profile Discovery Tool",
    version="1.0.0"
)

# Setup Jinja2 Templates
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_dir)

app.include_router(api_router)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, q: Optional[str] = Query(None)):
    results = None
    if q:
        search_res = await perform_search(query=q)
        results = search_res.results
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"query": q, "results": results}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
