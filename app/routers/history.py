"""Routes API pour l'historique des contrats"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models import ContractHistoryModel

router = APIRouter(prefix="/contract-history", tags=["Contract History"])


@router.get("/", response_model=List[dict])
def get_contract_history(
    contract_id: Optional[int] = None,
    action: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Récupérer l'historique des contrats"""
    query = db.query(ContractHistoryModel)
    
    if contract_id:
        query = query.filter(ContractHistoryModel.contract_id == contract_id)
    
    if action:
        query = query.filter(ContractHistoryModel.action == action)
    
    if date_from:
        query = query.filter(ContractHistoryModel.changed_at >= datetime.fromisoformat(date_from))
    
    if date_to:
        query = query.filter(ContractHistoryModel.changed_at <= datetime.fromisoformat(date_to))
    
    # Trier par date décroissante
    query = query.order_by(ContractHistoryModel.changed_at.desc())
    
    history = query.offset(skip).limit(limit).all()
    
    return [
        {
            "id": h.id,
            "contract_id": h.contract_id,
            "action": h.action,
            "field_changed": h.field_changed,
            "old_value": h.old_value,
            "new_value": h.new_value,
            "changed_by": h.changed_by,
            "changed_at": h.changed_at,
            "comment": h.comment
        }
        for h in history
    ]
