"""Routes de suivi des générations de données exécutées en arrière-plan"""
from fastapi import APIRouter, HTTPException

from app import jobs

router = APIRouter(prefix="/jobs", tags=["Data Generation"])


@router.get("/current")
def get_current_job():
    """Tâche de génération en cours, sinon la plus récente (null si aucune)"""
    job = jobs.current_job()
    return job.to_dict() if job else None


@router.get("/{job_id}")
def get_job(job_id: str):
    job = jobs.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Tâche introuvable")
    return job.to_dict()
