"""Routes API pour la gestion des visites clients et de leurs comptes rendus"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.database import get_db
from app import schemas
from app.models import ClientVisitModel, ClientModel, SalesRepModel

router = APIRouter(prefix="/visits", tags=["Visites clients"])


@router.post("/", response_model=schemas.ClientVisit, status_code=status.HTTP_201_CREATED)
@router.post("", response_model=schemas.ClientVisit, status_code=status.HTTP_201_CREATED)
def create_visit(visit: schemas.ClientVisitCreate, db: Session = Depends(get_db)):
    """Créer une nouvelle visite client"""
    client = db.query(ClientModel).filter(ClientModel.id == visit.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client non trouvé")

    sales_rep = db.query(SalesRepModel).filter(SalesRepModel.id == visit.sales_rep_id).first()
    if not sales_rep:
        raise HTTPException(status_code=404, detail="Commercial non trouvé")

    existing = db.query(ClientVisitModel).filter(ClientVisitModel.visit_number == visit.visit_number).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ce numéro de visite existe déjà")

    db_visit = ClientVisitModel(**visit.model_dump())
    db.add(db_visit)
    db.commit()
    db.refresh(db_visit)
    return db_visit


@router.get("/")
@router.get("")
def list_visits(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=500),
    client_id: Optional[int] = None,
    sales_rep_id: Optional[int] = None,
    visit_type: Optional[str] = None,
    visit_status: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """Liste des visites avec filtres et pagination"""
    query = db.query(ClientVisitModel)

    if client_id:
        query = query.filter(ClientVisitModel.client_id == client_id)

    if sales_rep_id:
        query = query.filter(ClientVisitModel.sales_rep_id == sales_rep_id)

    if visit_type:
        query = query.filter(ClientVisitModel.visit_type == visit_type)

    if visit_status:
        query = query.filter(ClientVisitModel.visit_status == visit_status)

    if date_from:
        query = query.filter(ClientVisitModel.visit_date >= date_from)

    if date_to:
        query = query.filter(ClientVisitModel.visit_date <= date_to)

    total = query.count()
    visits = query.order_by(ClientVisitModel.visit_date.desc()).offset(skip).limit(limit).all()

    return JSONResponse(content={
        "items": [schemas.ClientVisit.model_validate(v).model_dump(mode="json") for v in visits],
        "total": total,
        "skip": skip,
        "limit": limit,
        "page": (skip // limit) + 1 if limit > 0 else 1,
        "pages": (total + limit - 1) // limit if limit > 0 else 1
    })


@router.get("/{visit_id}", response_model=schemas.ClientVisit)
def get_visit(visit_id: int, db: Session = Depends(get_db)):
    """Récupérer une visite par son ID (avec compte rendu complet)"""
    visit = db.query(ClientVisitModel).filter(ClientVisitModel.id == visit_id).first()
    if not visit:
        raise HTTPException(status_code=404, detail="Visite non trouvée")
    return visit


@router.put("/{visit_id}", response_model=schemas.ClientVisit)
def update_visit(visit_id: int, update: schemas.ClientVisitUpdate, db: Session = Depends(get_db)):
    """Mettre à jour une visite (ex: compléter le compte rendu)"""
    db_visit = db.query(ClientVisitModel).filter(ClientVisitModel.id == visit_id).first()
    if not db_visit:
        raise HTTPException(status_code=404, detail="Visite non trouvée")

    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(db_visit, field, value)

    db.commit()
    db.refresh(db_visit)
    return db_visit


@router.delete("/{visit_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_visit(visit_id: int, db: Session = Depends(get_db)):
    """Supprimer une visite"""
    db_visit = db.query(ClientVisitModel).filter(ClientVisitModel.id == visit_id).first()
    if not db_visit:
        raise HTTPException(status_code=404, detail="Visite non trouvée")

    db.delete(db_visit)
    db.commit()
    return None
