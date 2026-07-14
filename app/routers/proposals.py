"""Routes API pour la gestion des propositions d'assurance et de leur transformation en souscription"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app import schemas
from app.models import InsuranceProposalModel, ClientModel, SalesRepModel, ClientContractModel

router = APIRouter(prefix="/proposals", tags=["Propositions d'assurance"])


@router.post("/", response_model=schemas.InsuranceProposal, status_code=status.HTTP_201_CREATED)
@router.post("", response_model=schemas.InsuranceProposal, status_code=status.HTTP_201_CREATED)
def create_proposal(proposal: schemas.InsuranceProposalCreate, db: Session = Depends(get_db)):
    """Créer une nouvelle proposition d'assurance"""
    client = db.query(ClientModel).filter(ClientModel.id == proposal.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client non trouvé")

    sales_rep = db.query(SalesRepModel).filter(SalesRepModel.id == proposal.sales_rep_id).first()
    if not sales_rep:
        raise HTTPException(status_code=404, detail="Commercial non trouvé")

    existing = db.query(InsuranceProposalModel).filter(
        InsuranceProposalModel.proposal_number == proposal.proposal_number
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ce numéro de proposition existe déjà")

    db_proposal = InsuranceProposalModel(**proposal.model_dump())
    db.add(db_proposal)
    db.commit()
    db.refresh(db_proposal)
    return db_proposal


@router.get("/")
@router.get("")
def list_proposals(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=500),
    client_id: Optional[int] = None,
    sales_rep_id: Optional[int] = None,
    contract_type_code: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db)
):
    """Liste des propositions d'assurance avec filtres et pagination"""
    query = db.query(InsuranceProposalModel)

    if client_id:
        query = query.filter(InsuranceProposalModel.client_id == client_id)

    if sales_rep_id:
        query = query.filter(InsuranceProposalModel.sales_rep_id == sales_rep_id)

    if contract_type_code:
        query = query.filter(InsuranceProposalModel.contract_type_code == contract_type_code)

    if status_filter:
        query = query.filter(InsuranceProposalModel.status == status_filter)

    total = query.count()
    proposals = query.order_by(InsuranceProposalModel.proposal_date.desc()).offset(skip).limit(limit).all()

    return JSONResponse(content={
        "items": [schemas.InsuranceProposal.model_validate(p).model_dump(mode="json") for p in proposals],
        "total": total,
        "skip": skip,
        "limit": limit,
        "page": (skip // limit) + 1 if limit > 0 else 1,
        "pages": (total + limit - 1) // limit if limit > 0 else 1
    })


@router.get("/{proposal_id}", response_model=schemas.InsuranceProposal)
def get_proposal(proposal_id: int, db: Session = Depends(get_db)):
    """Récupérer une proposition par son ID"""
    proposal = db.query(InsuranceProposalModel).filter(InsuranceProposalModel.id == proposal_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposition non trouvée")
    return proposal


@router.put("/{proposal_id}", response_model=schemas.InsuranceProposal)
def update_proposal(proposal_id: int, update: schemas.InsuranceProposalUpdate, db: Session = Depends(get_db)):
    """Mettre à jour une proposition (statut, montants négociés, etc.)"""
    db_proposal = db.query(InsuranceProposalModel).filter(InsuranceProposalModel.id == proposal_id).first()
    if not db_proposal:
        raise HTTPException(status_code=404, detail="Proposition non trouvée")

    update_data = update.model_dump(exclude_unset=True)
    if "converted_contract_id" in update_data and update_data["converted_contract_id"] is not None:
        contract = db.query(ClientContractModel).filter(
            ClientContractModel.id == update_data["converted_contract_id"]
        ).first()
        if not contract:
            raise HTTPException(status_code=404, detail="Contrat non trouvé")

    for field, value in update_data.items():
        setattr(db_proposal, field, value)

    db.commit()
    db.refresh(db_proposal)
    return db_proposal


@router.delete("/{proposal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_proposal(proposal_id: int, db: Session = Depends(get_db)):
    """Supprimer une proposition"""
    db_proposal = db.query(InsuranceProposalModel).filter(InsuranceProposalModel.id == proposal_id).first()
    if not db_proposal:
        raise HTTPException(status_code=404, detail="Proposition non trouvée")

    db.delete(db_proposal)
    db.commit()
    return None
