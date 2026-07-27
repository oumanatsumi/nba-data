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


@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    print("Shutting down application")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to NBA Data API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


# Import and include routers
from app.api.v1 import players, teams, games, playoffs

api_prefix = settings.API_V1_PREFIX  # "/api/v1"
app.include_router(players.router, prefix=api_prefix, tags=["Players"])
app.include_router(teams.router, prefix=api_prefix, tags=["Teams"])
app.include_router(games.router, prefix=api_prefix, tags=["Games & Stats"])
app.include_router(playoffs.router, prefix=api_prefix, tags=["Playoffs"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
