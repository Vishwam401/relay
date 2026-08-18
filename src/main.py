from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.middleware import limit_payload_size
from src.models import Job
from src.schemas import JobCreate, JobResponse

app = FastAPI(title="Relay API")


app.middleware("http")(limit_payload_size)


@app.get("/health")
async def health_check():
    return {"ok": True}


@app.get("/db-ping")
async def db_ping(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT 1"))
    return {"db": result.scalar()}


@app.post(
    "/jobs",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=JobResponse,
)
async def create_job(
    job_in: JobCreate,
    db: AsyncSession = Depends(get_db),
):
    job = Job(type=job_in.type, payload=job_in.payload)
    db.add(job)
    await db.commit()
    return JobResponse(job_id=job.id, status=job.status)


@app.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: int, db: AsyncSession = Depends(get_db)):
    query = select(Job.id, Job.status).where(Job.id == job_id)
    result = await db.execute(query)
    row = result.first()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    return JobResponse(job_id=row.id, status=row.status)
