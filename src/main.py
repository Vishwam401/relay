from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.middleware import limit_payload_size
from src.models import Job
from src.schemas import JobCreate, JobResponse, request_fingerprint

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
    if job_in.idempotency_key is None:
        job = Job(type=job_in.type, payload=job_in.payload)
        db.add(job)
        await db.commit()
        return JobResponse(job_id=job.id, status=job.status)

    current_fp = request_fingerprint(job_in.type, job_in.payload)

    stmt = (
        pg_insert(Job)
        .values(
            type=job_in.type,
            payload=job_in.payload,
            idempotency_key=job_in.idempotency_key,
            request_fingerprint=current_fp,
        )
        .on_conflict_do_nothing(constraint="uq_jobs_idempotency_key")
        .returning(Job.id, Job.status)
    )
    result = await db.execute(stmt)
    row = result.first()
    if row is not None:
        await db.commit()
        return JobResponse(job_id=row.id, status=row.status)

    # Conflict on uq_jobs_idempotency_key: read existing job
    query = select(Job.id, Job.status, Job.request_fingerprint).where(
        Job.idempotency_key == job_in.idempotency_key
    )
    existing = (await db.execute(query)).first()
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Conflict occurred but existing job not found",
        )

    if existing.request_fingerprint != current_fp:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "idempotency_key_mismatch",
                "job_id": existing.id,
            },
        )

    return JobResponse(job_id=existing.id, status=existing.status)



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
