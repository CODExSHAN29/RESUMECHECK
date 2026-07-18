from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_check import router as check_router
from app.api.routes_report import router as report_router
from app.config import settings

app = FastAPI(title="ResumeCheck API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(check_router, prefix="/api")
app.include_router(report_router, prefix="/api")


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok", "db_configured": settings.db_configured, "email_configured": settings.email_configured}
