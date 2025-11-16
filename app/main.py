from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import subprocess
import sys
from app.config import settings
from app.database import init_db_pool, close_db_pool
from app.middleware.error_handler import setup_error_handlers
from app.middleware.security import setup_security_middleware
from app.api.routes import auth, notes, dashboard

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting application...")
    
    # Run database migrations automatically
    try:
        logger.info("Running database migrations...")
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            logger.info("Database migrations completed successfully")
        else:
            logger.warning(f"Migration output: {result.stdout}")
            if result.stderr:
                logger.warning(f"Migration errors: {result.stderr}")
    except Exception as e:
        logger.error(f"Error running migrations: {e}")
        # Don't fail startup if migrations fail - let it be handled by Procfile
    
    init_db_pool()
    yield
    # Shutdown
    logger.info("Shutting down application...")
    close_db_pool()


app = FastAPI(
    title="Vamo Junto API",
    description="Backend API for Vamo Junto - NFC-e price monitoring platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup error handlers
setup_error_handlers(app)

# Setup security middleware
setup_security_middleware(app)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(notes.router, prefix="/api/notes", tags=["notes"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])


@app.get("/")
async def root():
    return {"message": "Vamo Junto API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}

