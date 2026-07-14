"""Routes API pour la gestion des commerciaux (réseau de vente terrain)"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app import schemas
from app.models import SalesRepModel

router = APIRouter(prefix="/sales-reps", tags=["Commerciaux"])


@router.post("/", response_model=schemas.SalesRep, status_code=status.HTTP_201_CREATED)
@router.post("", response_model=schemas.SalesRep, status_code=status.HTTP_201_CREATED)
def create_sales_rep(sales_rep: schemas.SalesRepCreate, db: Session = Depends(get_db)):
    """Créer un nouveau commercial"""
    existing = db.query(SalesRepModel).filter(SalesRepModel.employee_number == sales_rep.employee_number).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ce matricule commercial existe déjà")

    db_sales_rep = SalesRepModel(**sales_rep.model_dump())
    db.add(db_sales_rep)
    db.commit()
    db.refresh(db_sales_rep)
    return db_sales_rep


@router.get("/")
@router.get("")
def list_sales_reps(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=500),
    region: Optional[str] = None,
    agency: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Liste des commerciaux avec filtres et pagination"""
    query = db.query(SalesRepModel)

    if region:
        query = query.filter(SalesRepModel.region == region)

    if agency:
        query = query.filter(SalesRepModel.agency == agency)

    if is_active is not None:
        query = query.filter(SalesRepModel.is_active == is_active)

    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (SalesRepModel.first_name.ilike(search_filter)) |
            (SalesRepModel.last_name.ilike(search_filter)) |
            (SalesRepModel.employee_number.ilike(search_filter))
        )

    total = query.count()
    sales_reps = query.offset(skip).limit(limit).all()

    return JSONResponse(content={
        "items": [schemas.SalesRep.model_validate(sr).model_dump(mode="json") for sr in sales_reps],
        "total": total,
        "skip": skip,
        "limit": limit,
        "page": (skip // limit) + 1 if limit > 0 else 1,
        "pages": (total + limit - 1) // limit if limit > 0 else 1
    })


@router.get("/{sales_rep_id}", response_model=schemas.SalesRep)
def get_sales_rep(sales_rep_id: int, db: Session = Depends(get_db)):
    """Récupérer un commercial par son ID"""
    sales_rep = db.query(SalesRepModel).filter(SalesRepModel.id == sales_rep_id).first()
    if not sales_rep:
        raise HTTPException(status_code=404, detail="Commercial non trouvé")
    return sales_rep


@router.put("/{sales_rep_id}", response_model=schemas.SalesRep)
def update_sales_rep(sales_rep_id: int, update: schemas.SalesRepUpdate, db: Session = Depends(get_db)):
    """Mettre à jour un commercial"""
    db_sales_rep = db.query(SalesRepModel).filter(SalesRepModel.id == sales_rep_id).first()
    if not db_sales_rep:
        raise HTTPException(status_code=404, detail="Commercial non trouvé")

    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(db_sales_rep, field, value)

    db.commit()
    db.refresh(db_sales_rep)
    return db_sales_rep


@router.get("/statistics/summary")
def get_sales_reps_statistics(db: Session = Depends(get_db)):
    """Statistiques globales sur le réseau commercial"""
    from sqlalchemy import func
    from app.models import ClientVisitModel, InsuranceProposalModel

    total = db.query(func.count(SalesRepModel.id)).scalar() or 0
    active = db.query(func.count(SalesRepModel.id)).filter(SalesRepModel.is_active == True).scalar() or 0  # noqa: E712
    total_visits = db.query(func.count(ClientVisitModel.id)).scalar() or 0
    total_proposals = db.query(func.count(InsuranceProposalModel.id)).scalar() or 0
    converted_proposals = db.query(func.count(InsuranceProposalModel.id)).filter(
        InsuranceProposalModel.converted_contract_id.isnot(None)
    ).scalar() or 0

    return {
        "total_sales_reps": total,
        "active_sales_reps": active,
        "total_visits": total_visits,
        "total_proposals": total_proposals,
        "converted_proposals": converted_proposals,
        "conversion_rate": round(converted_proposals / total_proposals * 100, 2) if total_proposals else 0.0
    }
