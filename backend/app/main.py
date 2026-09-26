import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

logging.basicConfig(level=logging.INFO)
from app.routers import (
    analysis,
    analytics,
    applications,
    assistant,
    auth,
    bias,
    cvs,
    feedback,
    health,
    job_specs,
    questions,
    preparation,
    ranking,
    recordings,
    reports,
    scheduling,
    sessions,
)

app = FastAPI(
    title=settings.app_name,
    description="AI-assisted interview platform for software engineering roles",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(cvs.router)
app.include_router(job_specs.router)
app.include_router(analysis.router)
app.include_router(questions.router)
app.include_router(sessions.router)
app.include_router(reports.router)
app.include_router(scheduling.router)
app.include_router(analytics.router)
app.include_router(feedback.router)
app.include_router(bias.router)
app.include_router(applications.router)
app.include_router(ranking.router)
app.include_router(preparation.router)
app.include_router(assistant.router)
app.include_router(recordings.router)
