from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.config import settings
from app.routes import auth, chat, confluence, admin
from app.dependencies.redis import close_redis
from app.services.cleanup_service import cleanup_service
from pathlib import Path

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    scheduler.add_job(cleanup_service.cleanup_old_files, 'interval', hours=1)
    scheduler.start()
    yield
    # Shutdown
    scheduler.shutdown()
    await close_redis()


app = FastAPI(
    title="Confluence Chatbot API",
    description="AI-powered chatbot with Confluence integration",
    version="2.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount uploads directory for static file serving
uploads_dir = Path("/app/uploads")
uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

# Include routers
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(confluence.router)
app.include_router(admin.router)


@app.get("/")
async def root():
    return {"message": "Confluence Chatbot API", "version": "2.1.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
