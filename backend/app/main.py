from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.routes import config, dashboard, health
from app.core.config import get_settings
from app.core.rate_limit import limiter

settings = get_settings()

app = FastAPI(title="Dashboard de Projetos Web API")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def no_store_cache(request, call_next):
    """Os dados vem de uma planilha externa que pode mudar a qualquer
    momento -- nunca deixar o navegador (ou qualquer proxy no meio)
    reaproveitar uma resposta antiga de GET /dashboard."""
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    return response


app.include_router(health.router)
app.include_router(config.router)
app.include_router(dashboard.router)
