"""Routes API pour la gestion des contrats"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.database import get_db
from app import schemas
from app.models import ClientContractModel, ClientModel, ConstructionSiteModel

router = APIRouter(prefix="/contracts", tags=["Contrats"])


@router.post("/", response_model=schemas.ClientContract, status_code=status.HTTP_201_CREATED)
def create_contract(contract: schemas.ClientContractCreate, db: Session = Depends(get_db)):
    """Créer un nouveau contrat"""
    # Vérifier que le client existe
    client = db.query(ClientModel).filter(ClientModel.id == contract.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    
    # Vérifier que le numéro de contrat n'existe pas
    existing = db.query(ClientContractModel).filter(ClientContractModel.contract_number == contract.contract_number).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ce numéro de contrat existe déjà")
    
    # Vérifier le chantier si fourni
    if contract.construction_site_id:
        site = db.query(ConstructionSiteModel).filter(ConstructionSiteModel.id == contract.construction_site_id).first()
        if not site:
            raise HTTPException(status_code=404, detail="Chantier non trouvé")
    
    db_contract = ClientContractModel(
        id=str(uuid.uuid4()),
        **contract.model_dump()
    )
    db.add(db_contract)
    db.commit()
    db.refresh(db_contract)
    return db_contract


@router.get("/", response_model=List[schemas.ClientContract])
def list_contracts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    client_id: Optional[str] = None,
    status: Optional[str] = None,
    contract_type_code: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Liste des contrats avec filtres"""
    query = db.query(ClientContractModel)
    
    if client_id:
        query = query.filter(ClientContractModel.client_id == client_id)
    
    if status:
        query = query.filter(ClientContractModel.status == status)
    
    if contract_type_code:
        query = query.filter(ClientContractModel.contract_type_code == contract_type_code)
    
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (ClientContractModel.contract_number.ilike(search_filter)) |
            (ClientContractModel.external_reference.ilike(search_filter))
        )
    
    return query.offset(skip).limit(limit).all()


@router.get("/{contract_id}", response_model=schemas.ClientContract)
def get_contract(contract_id: str, db: Session = Depends(get_db)):
    """Récupérer un contrat par son ID"""
    contract = db.query(ClientContractModel).filter(ClientContractModel.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contrat non trouvé")
    return contract


@router.get("/number/{contract_number}", response_model=schemas.ClientContract)
def get_contract_by_number(contract_number: str, db: Session = Depends(get_db)):
    """Récupérer un contrat par son numéro"""
    contract = db.query(ClientContractModel).filter(ClientContractModel.contract_number == contract_number).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contrat non trouvé")
    return contract


@router.put("/{contract_id}", response_model=schemas.ClientContract)
def update_contract(contract_id: str, contract_update: schemas.ClientContractUpdate, db: Session = Depends(get_db)):
    """Mettre à jour un contrat"""
    db_contract = db.query(ClientContractModel).filter(ClientContractModel.id == contract_id).first()
    if not db_contract:
        raise HTTPException(status_code=404, detail="Contrat non trouvé")
    
    update_data = contract_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_contract, field, value)
    
    db.commit()
    db.refresh(db_contract)
    return db_contract


@router.delete("/{contract_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contract(contract_id: str, db: Session = Depends(get_db)):
    """Supprimer un contrat"""
    db_contract = db.query(ClientContractModel).filter(ClientContractModel.id == contract_id).first()
    if not db_contract:
        raise HTTPException(status_code=404, detail="Contrat non trouvé")
    
    db.delete(db_contract)
    db.commit()
    return None


@router.get("/statistics/summary", response_model=schemas.ContractStatistics)
def get_contract_statistics(db: Session = Depends(get_db)):
    """Obtenir les statistiques des contrats"""
    from sqlalchemy import func
    
    total = db.query(func.count(ClientContractModel.id)).scalar()
    active = db.query(func.count(ClientContractModel.id)).filter(ClientContractModel.status == "actif").scalar()
    draft = db.query(func.count(ClientContractModel.id)).filter(ClientContractModel.status == "brouillon").scalar()
    cancelled = db.query(func.count(ClientContractModel.id)).filter(ClientContractModel.status == "resilie").scalar()
    
    total_premium = db.query(func.sum(ClientContractModel.annual_premium)).scalar() or 0
    avg_premium = db.query(func.avg(ClientContractModel.annual_premium)).scalar() or 0
    
    return {
        "total_contracts": total or 0,
        "active_contracts": active or 0,
        "draft_contracts": draft or 0,
        "cancelled_contracts": cancelled or 0,
        "total_premium_volume": float(total_premium),
        "average_premium": float(avg_premium)
    }
