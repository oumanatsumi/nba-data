"""FastAPI application entry point"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="NBA Historical Data API",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== Import and include routers =====
from app.api.v1 import players, teams, games, playoffs

prefix = settings.API_V1_PREFIX
app.include_router(players.router, prefix=prefix, tags=["Players"])
app.include_router(teams.router, prefix=prefix, tags=["Teams"])
app.include_router(games.router, prefix=prefix, tags=["Games & Stats"])
app.include_router(playoffs.router, prefix=prefix, tags=["Playoffs"])


@app.on_event("startup")
async def startup():
    print(f"NBA Data API v{settings.APP_VERSION} started")
    print(f"  Docs: http://localhost:8000/docs")


@app.get("/")
async def root():
    return {
        "message": "NBA Data API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
