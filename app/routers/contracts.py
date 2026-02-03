"""Routes API pour la gestion des contrats"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
import uuid
from datetime import date

from app.database import get_db
from app import schemas
from app.models import ClientContractModel, ClientModel, ConstructionSiteModel, contract_guarantees

router = APIRouter(prefix="/contracts", tags=["Contrats"])


@router.post("/", response_model=schemas.ClientContract, status_code=status.HTTP_201_CREATED)
@router.post("", response_model=schemas.ClientContract, status_code=status.HTTP_201_CREATED)
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


@router.get("/")
@router.get("")
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
    
    # Compter le total avant la pagination
    total = query.count()
    
    contracts = query.offset(skip).limit(limit).all()
    
    # Enrichir avec les données des chantiers et garanties
    result = []
    for contract in contracts:
        contract_dict = {
            "id": contract.id,
            "client_id": contract.client_id,
            "contract_number": contract.contract_number,
            "contract_type_code": contract.contract_type_code,
            "status": contract.status,
            "issue_date": contract.issue_date.isoformat() if contract.issue_date else None,
            "effective_date": contract.effective_date.isoformat() if contract.effective_date else None,
            "expiry_date": contract.expiry_date.isoformat() if contract.expiry_date else None,
            "cancellation_date": contract.cancellation_date.isoformat() if contract.cancellation_date else None,
            "insured_amount": float(contract.insured_amount) if contract.insured_amount else None,
            "annual_premium": float(contract.annual_premium) if contract.annual_premium else None,
            "total_premium": float(contract.total_premium) if contract.total_premium else None,
            "franchise_amount": float(contract.franchise_amount) if contract.franchise_amount else None,
            "duration_years": contract.duration_years,
            "is_renewable": contract.is_renewable,
            "external_reference": contract.external_reference,
            "special_conditions": contract.special_conditions,
            "construction_site_id": contract.construction_site_id,
            "created_at": contract.created_at.isoformat() if contract.created_at else None,
            "updated_at": contract.updated_at.isoformat() if contract.updated_at else None,
            "construction_site": None,
            "guarantees": []
        }
        
        # Ajouter les infos du chantier si présent
        if contract.construction_site_id:
            site = db.query(ConstructionSiteModel).filter(
                ConstructionSiteModel.id == contract.construction_site_id
            ).first()
            if site:
                contract_dict["construction_site"] = {
                    "id": site.id,
                    "site_reference": site.site_reference,
                    "site_name": site.site_name
                }
        
        # Compter les garanties
        guarantees = db.execute(
            text("SELECT guarantee_code FROM fake_contract_guarantees WHERE contract_id = :contract_id"),
            {"contract_id": contract.id}
        ).fetchall()
        
        contract_dict["guarantees"] = [{"code": g[0]} for g in guarantees]
        
        result.append(contract_dict)
    
    # Retourner avec métadonnées de pagination
    response = {
        "items": result,
        "total": total,
        "skip": skip,
        "limit": limit,
        "page": (skip // limit) + 1 if limit > 0 else 1,
        "pages": (total + limit - 1) // limit if limit > 0 else 1
    }
    
    return JSONResponse(content=response)


@router.get("/{contract_id}", response_model=schemas.ClientContract)
def get_contract(contract_id: str, db: Session = Depends(get_db)):
    """Récupérer un contrat par son ID"""
    contract = db.query(ClientContractModel).filter(ClientContractModel.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contrat non trouvé")
    return contract


@router.get("/number/{contract_number}")
def get_contract_by_number(contract_number: str, db: Session = Depends(get_db)):
    """Récupérer un contrat par son numéro avec les informations du chantier"""
    
    # Fonction helper pour générer un nom de garantie basé sur le code
    def get_guarantee_display_name(code, db_name):
        if db_name:
            return db_name
        # Génération du nom basé sur le préfixe du code
        prefixes = {
            'GAR_DO': 'Dommages Ouvrage',
            'GAR_RCD': 'Responsabilité Civile Décennale',
            'GAR_CNR': 'Construction Non Réalisée',
            'GAR_PUC': 'Perte d\'Usage et Charge',
            'GAR_RC': 'Responsabilité Civile',
            'GAR_TRC': 'Tous Risques Chantier',
            'GAR_DEC': 'Garantie Décennale',
            'GAR_BIEN': 'Biens et Équipements',
            'DO-': 'Dommages',
            'RCD-': 'RC Décennale'
        }
        for prefix, name in prefixes.items():
            if code.startswith(prefix):
                return name
        return code
    
    contract = db.query(ClientContractModel).filter(ClientContractModel.contract_number == contract_number).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contrat non trouvé")
    
    # Convertir en dict et ajouter les infos du chantier
    contract_dict = {
        "id": contract.id,
        "contract_number": contract.contract_number,
        "external_reference": contract.external_reference,
        "contract_type_code": contract.contract_type_code,
        "client_id": contract.client_id,
        "construction_site_id": contract.construction_site_id,
        "status": contract.status,
        "issue_date": contract.issue_date.isoformat() if contract.issue_date else None,
        "effective_date": contract.effective_date.isoformat() if contract.effective_date else None,
        "expiry_date": contract.expiry_date.isoformat() if contract.expiry_date else None,
        "cancellation_date": contract.cancellation_date.isoformat() if contract.cancellation_date else None,
        "insured_amount": float(contract.insured_amount) if contract.insured_amount else None,
        "annual_premium": float(contract.annual_premium) if contract.annual_premium else None,
        "total_premium": float(contract.total_premium) if contract.total_premium else None,
        "franchise_amount": float(contract.franchise_amount) if contract.franchise_amount else None,
        "duration_years": contract.duration_years,
        "is_renewable": contract.is_renewable,
        "selected_guarantees": contract.selected_guarantees,
        "selected_clauses": contract.selected_clauses,
        "special_conditions": contract.special_conditions,
        "broker_name": contract.broker_name,
        "broker_code": contract.broker_code,
        "underwriter": contract.underwriter,
        "internal_notes": contract.internal_notes,
        "created_at": contract.created_at.isoformat() if contract.created_at else None,
        "updated_at": contract.updated_at.isoformat() if contract.updated_at else None,
        "construction_site": None,
        "guarantees": []
    }
    
    # Charger les informations du chantier si existant
    if contract.construction_site_id:
        site = db.query(ConstructionSiteModel).filter(ConstructionSiteModel.id == contract.construction_site_id).first()
        if site:
            contract_dict["construction_site"] = {
                "id": site.id,
                "site_code": site.site_reference,
                "site_name": site.site_name,
                "description": site.description,
                "address": site.address_line1,
                "postal_code": site.postal_code,
                "city": site.city,
                "latitude": None,  # Pas de latitude dans le modèle
                "longitude": None,  # Pas de longitude dans le modèle
                "building_category": site.building_category_code,
                "work_category": site.work_category_code,
                "estimated_budget": float(site.construction_cost) if site.construction_cost else None,
                "actual_cost": float(site.construction_cost) if site.construction_cost else None,
                "start_date": site.opening_date.isoformat() if site.opening_date else None,
                "planned_end_date": site.planned_completion_date.isoformat() if site.planned_completion_date else None,
                "actual_end_date": site.actual_completion_date.isoformat() if site.actual_completion_date else None
            }
    
    # Charger les garanties du contrat
    guarantees_query = text("""
        SELECT cg.guarantee_code, cg.custom_ceiling, cg.custom_franchise, 
               cg.is_included, cg.annual_premium, g.name as guarantee_name
        FROM fake_contract_guarantees cg
        LEFT JOIN fake_ref_guarantees g ON g.code = cg.guarantee_code
        WHERE cg.contract_id = :contract_id
        ORDER BY cg.guarantee_code
    """)
    guarantees_result = db.execute(guarantees_query, {"contract_id": contract.id})
    contract_dict["guarantees"] = [
        {
            "code": row.guarantee_code,
            "name": get_guarantee_display_name(row.guarantee_code, row.guarantee_name),
            "ceiling": float(row.custom_ceiling) if row.custom_ceiling else None,
            "franchise": float(row.custom_franchise) if row.custom_franchise else None,
            "included": bool(row.is_included),
            "annual_premium": float(row.annual_premium) if row.annual_premium else None
        }
        for row in guarantees_result
    ]
    
    return JSONResponse(content=contract_dict)


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
