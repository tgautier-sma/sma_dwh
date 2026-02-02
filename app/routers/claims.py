"""Routes API pour la gestion des sinistres construction"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app import schemas
from app.models import ClaimModel, ClientContractModel

router = APIRouter(prefix="/claims", tags=["Sinistres"])


@router.post("/", response_model=schemas.Claim, status_code=status.HTTP_201_CREATED)
@router.post("", response_model=schemas.Claim, status_code=status.HTTP_201_CREATED)
def create_claim(claim: schemas.ClaimCreate, db: Session = Depends(get_db)):
    """Créer un nouveau sinistre"""
    # Vérifier que le contrat existe
    contract = db.query(ClientContractModel).filter(ClientContractModel.id == claim.contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contrat non trouvé")
    
    # Vérifier que le numéro de sinistre n'existe pas déjà
    existing = db.query(ClaimModel).filter(ClaimModel.claim_number == claim.claim_number).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ce numéro de sinistre existe déjà")
    
    db_claim = ClaimModel(**claim.model_dump())
    db.add(db_claim)
    db.commit()
    db.refresh(db_claim)
    return db_claim


@router.get("/", response_model=List[schemas.Claim])
@router.get("", response_model=List[schemas.Claim])
def list_claims(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    contract_id: Optional[int] = None,
    status: Optional[str] = None,
    claim_type: Optional[str] = None,
    severity: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Liste des sinistres avec filtres"""
    query = db.query(ClaimModel)
    
    if contract_id:
        query = query.filter(ClaimModel.contract_id == contract_id)
    
    if status:
        query = query.filter(ClaimModel.status == status)
    
    if claim_type:
        query = query.filter(ClaimModel.claim_type == claim_type)
    
    if severity:
        query = query.filter(ClaimModel.severity == severity)
    
    return query.order_by(ClaimModel.declaration_date.desc()).offset(skip).limit(limit).all()


@router.get("/search", response_model=List[schemas.Claim])
def search_claims(
    query: Optional[str] = Query(None, description="Numéro de sinistre, titre ou description"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Recherche de sinistres"""
    if not query:
        raise HTTPException(status_code=400, detail="Le paramètre 'query' est requis")
    
    search_filter = f"%{query}%"
    claims = db.query(ClaimModel).filter(
        (ClaimModel.claim_number.ilike(search_filter)) |
        (ClaimModel.title.ilike(search_filter)) |
        (ClaimModel.description.ilike(search_filter))
    ).offset(skip).limit(limit).all()
    
    return claims


@router.get("/contract/{contract_id}", response_model=List[schemas.Claim])
def get_claims_by_contract(
    contract_id: int,
    db: Session = Depends(get_db)
):
    """Récupère tous les sinistres d'un contrat"""
    contract = db.query(ClientContractModel).filter(ClientContractModel.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contrat non trouvé")
    
    claims = db.query(ClaimModel).filter(ClaimModel.contract_id == contract_id).order_by(
        ClaimModel.declaration_date.desc()
    ).all()
    
    return claims


@router.get("/stats", response_model=dict)
def get_claims_statistics(db: Session = Depends(get_db)):
    """Statistiques sur les sinistres"""
    total = db.query(ClaimModel).count()
    open_claims = db.query(ClaimModel).filter(
        ClaimModel.status.in_(["declare", "pris_en_compte", "en_cours_expertise", "attente_pieces", "accepte"])
    ).count()
    settled = db.query(ClaimModel).filter(ClaimModel.status == "regle").count()
    rejected = db.query(ClaimModel).filter(ClaimModel.status == "refuse").count()
    
    # Montants
    total_estimated = db.query(ClaimModel).with_entities(
        func.sum(ClaimModel.estimated_amount)
    ).scalar() or 0
    
    total_indemnity = db.query(ClaimModel).with_entities(
        func.sum(ClaimModel.indemnity_amount)
    ).scalar() or 0
    
    # Par type
    by_type = {}
    for claim_type in ["structurel", "degats_des_eaux", "incendie", "intemperies", "vol", "vandalisme", "malfacons", "rc", "autre"]:
        count = db.query(ClaimModel).filter(ClaimModel.claim_type == claim_type).count()
        by_type[claim_type] = count
    
    return {
        "total_claims": total,
        "open_claims": open_claims,
        "settled_claims": settled,
        "rejected_claims": rejected,
        "total_estimated_amount": total_estimated,
        "total_indemnity_amount": total_indemnity,
        "claims_by_type": by_type
    }


@router.get("/{claim_number}", response_model=schemas.Claim)
def get_claim(claim_number: str, db: Session = Depends(get_db)):
    """Récupérer un sinistre par son numéro"""
    claim = db.query(ClaimModel).filter(ClaimModel.claim_number == claim_number).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Sinistre non trouvé")
    return claim


@router.put("/{claim_number}", response_model=schemas.Claim)
def update_claim(
    claim_number: str,
    claim_update: schemas.ClaimUpdate,
    db: Session = Depends(get_db)
):
    """Mettre à jour un sinistre"""
    db_claim = db.query(ClaimModel).filter(ClaimModel.claim_number == claim_number).first()
    if not db_claim:
        raise HTTPException(status_code=404, detail="Sinistre non trouvé")
    
    update_data = claim_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_claim, field, value)
    
    db_claim.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_claim)
    return db_claim


@router.delete("/{claim_number}", status_code=status.HTTP_204_NO_CONTENT)
def delete_claim(claim_number: str, db: Session = Depends(get_db)):
    """Supprimer un sinistre"""
    db_claim = db.query(ClaimModel).filter(ClaimModel.claim_number == claim_number).first()
    if not db_claim:
        raise HTTPException(status_code=404, detail="Sinistre non trouvé")
    
    db.delete(db_claim)
    db.commit()
    return None
