from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import get_settings
from src.db.session import Base, engine
from src.modules.assessment.router import router as assessment_router
from src.modules.auth.router import router as auth_router
from src.modules.project.intervention_router import router as intervention_router
from src.modules.project.router import router as project_router
from src.modules.report.router import router as report_router
from src.modules.generator.router import router as generator_router

settings = get_settings()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    # For local bootstrap. Production should rely on Alembic migrations.
    Base.metadata.create_all(bind=engine)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": settings.app_name, "env": settings.app_env}


app.include_router(auth_router)
app.include_router(project_router)
app.include_router(intervention_router)
app.include_router(assessment_router)
app.include_router(report_router)
app.include_router(generator_router)
