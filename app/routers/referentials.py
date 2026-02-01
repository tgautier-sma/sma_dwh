"""Routes API pour la gestion des référentiels"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.database import get_db
from app import schemas
from app.models import (
    InsuranceContractTypeModel, GuaranteeModel, ContractClauseModel,
    BuildingCategoryModel, WorkCategoryModel, ProfessionModel
)

router = APIRouter(prefix="/referentials", tags=["Référentiels"])


# =============================================================================
# TYPES DE CONTRATS
# =============================================================================

@router.post("/contract-types", response_model=schemas.InsuranceContractType, status_code=status.HTTP_201_CREATED)
def create_contract_type(contract_type: schemas.InsuranceContractTypeCreate, db: Session = Depends(get_db)):
    """Créer un nouveau type de contrat"""
    existing = db.query(InsuranceContractTypeModel).filter(InsuranceContractTypeModel.code == contract_type.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ce code de type de contrat existe déjà")
    
    db_type = InsuranceContractTypeModel(
        id=str(uuid.uuid4()),
        **contract_type.model_dump()
    )
    db.add(db_type)
    db.commit()
    db.refresh(db_type)
    return db_type


@router.get("/contract-types", response_model=List[schemas.InsuranceContractType])
def list_contract_types(
    is_active: Optional[bool] = None,
    is_mandatory: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Liste des types de contrats"""
    query = db.query(InsuranceContractTypeModel)
    
    if is_active is not None:
        query = query.filter(InsuranceContractTypeModel.is_active == is_active)
    
    if is_mandatory is not None:
        query = query.filter(InsuranceContractTypeModel.is_mandatory == is_mandatory)
    
    return query.all()


@router.get("/contract-types/{code}", response_model=schemas.InsuranceContractType)
def get_contract_type(code: str, db: Session = Depends(get_db)):
    """Récupérer un type de contrat par son code"""
    contract_type = db.query(InsuranceContractTypeModel).filter(InsuranceContractTypeModel.code == code).first()
    if not contract_type:
        raise HTTPException(status_code=404, detail="Type de contrat non trouvé")
    return contract_type


# =============================================================================
# GARANTIES
# =============================================================================

@router.post("/guarantees", response_model=schemas.Guarantee, status_code=status.HTTP_201_CREATED)
def create_guarantee(guarantee: schemas.GuaranteeCreate, db: Session = Depends(get_db)):
    """Créer une nouvelle garantie"""
    existing = db.query(GuaranteeModel).filter(GuaranteeModel.code == guarantee.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ce code de garantie existe déjà")
    
    db_guarantee = GuaranteeModel(
        id=str(uuid.uuid4()),
        **guarantee.model_dump()
    )
    db.add(db_guarantee)
    db.commit()
    db.refresh(db_guarantee)
    return db_guarantee


@router.get("/guarantees", response_model=List[schemas.Guarantee])
def list_guarantees(
    contract_type_id: Optional[str] = None,
    category: Optional[str] = None,
    guarantee_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Liste des garanties avec filtres"""
    query = db.query(GuaranteeModel)
    
    if contract_type_id:
        query = query.filter(GuaranteeModel.contract_type_id == contract_type_id)
    
    if category:
        query = query.filter(GuaranteeModel.category == category)
    
    if guarantee_type:
        query = query.filter(GuaranteeModel.guarantee_type == guarantee_type)
    
    if is_active is not None:
        query = query.filter(GuaranteeModel.is_active == is_active)
    
    return query.all()


@router.get("/guarantees/{code}", response_model=schemas.Guarantee)
def get_guarantee(code: str, db: Session = Depends(get_db)):
    """Récupérer une garantie par son code"""
    guarantee = db.query(GuaranteeModel).filter(GuaranteeModel.code == code).first()
    if not guarantee:
        raise HTTPException(status_code=404, detail="Garantie non trouvée")
    return guarantee


# =============================================================================
# CLAUSES CONTRACTUELLES
# =============================================================================

@router.post("/clauses", response_model=schemas.ContractClause, status_code=status.HTTP_201_CREATED)
def create_clause(clause: schemas.ContractClauseCreate, db: Session = Depends(get_db)):
    """Créer une nouvelle clause"""
    existing = db.query(ContractClauseModel).filter(ContractClauseModel.code == clause.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ce code de clause existe déjà")
    
    db_clause = ContractClauseModel(
        id=str(uuid.uuid4()),
        **clause.model_dump()
    )
    db.add(db_clause)
    db.commit()
    db.refresh(db_clause)
    return db_clause


@router.get("/clauses", response_model=List[schemas.ContractClause])
def list_clauses(
    category: Optional[str] = None,
    is_mandatory: Optional[bool] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Liste des clauses avec filtres"""
    query = db.query(ContractClauseModel)
    
    if category:
        query = query.filter(ContractClauseModel.category == category)
    
    if is_mandatory is not None:
        query = query.filter(ContractClauseModel.is_mandatory == is_mandatory)
    
    if is_active is not None:
        query = query.filter(ContractClauseModel.is_active == is_active)
    
    return query.order_by(ContractClauseModel.priority_order).all()


@router.get("/clauses/{code}", response_model=schemas.ContractClause)
def get_clause(code: str, db: Session = Depends(get_db)):
    """Récupérer une clause par son code"""
    clause = db.query(ContractClauseModel).filter(ContractClauseModel.code == code).first()
    if not clause:
        raise HTTPException(status_code=404, detail="Clause non trouvée")
    return clause


# =============================================================================
# CATÉGORIES DE BÂTIMENTS
# =============================================================================

@router.post("/building-categories", response_model=schemas.BuildingCategory, status_code=status.HTTP_201_CREATED)
def create_building_category(category: schemas.BuildingCategoryCreate, db: Session = Depends(get_db)):
    """Créer une nouvelle catégorie de bâtiment"""
    existing = db.query(BuildingCategoryModel).filter(BuildingCategoryModel.code == category.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ce code de catégorie existe déjà")
    
    db_category = BuildingCategoryModel(
        id=str(uuid.uuid4()),
        **category.model_dump()
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


@router.get("/building-categories", response_model=List[schemas.BuildingCategory])
def list_building_categories(is_active: Optional[bool] = None, db: Session = Depends(get_db)):
    """Liste des catégories de bâtiments"""
    query = db.query(BuildingCategoryModel)
    
    if is_active is not None:
        query = query.filter(BuildingCategoryModel.is_active == is_active)
    
    return query.all()


@router.get("/building-categories/{code}", response_model=schemas.BuildingCategory)
def get_building_category(code: str, db: Session = Depends(get_db)):
    """Récupérer une catégorie de bâtiment par son code"""
    category = db.query(BuildingCategoryModel).filter(BuildingCategoryModel.code == code).first()
    if not category:
        raise HTTPException(status_code=404, detail="Catégorie non trouvée")
    return category


# =============================================================================
# CATÉGORIES DE TRAVAUX
# =============================================================================

@router.post("/work-categories", response_model=schemas.WorkCategory, status_code=status.HTTP_201_CREATED)
def create_work_category(category: schemas.WorkCategoryCreate, db: Session = Depends(get_db)):
    """Créer une nouvelle catégorie de travaux"""
    existing = db.query(WorkCategoryModel).filter(WorkCategoryModel.code == category.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ce code de catégorie existe déjà")
    
    db_category = WorkCategoryModel(
        id=str(uuid.uuid4()),
        **category.model_dump()
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


@router.get("/work-categories", response_model=List[schemas.WorkCategory])
def list_work_categories(is_active: Optional[bool] = None, db: Session = Depends(get_db)):
    """Liste des catégories de travaux"""
    query = db.query(WorkCategoryModel)
    
    if is_active is not None:
        query = query.filter(WorkCategoryModel.is_active == is_active)
    
    return query.all()


@router.get("/work-categories/{code}", response_model=schemas.WorkCategory)
def get_work_category(code: str, db: Session = Depends(get_db)):
    """Récupérer une catégorie de travaux par son code"""
    category = db.query(WorkCategoryModel).filter(WorkCategoryModel.code == code).first()
    if not category:
        raise HTTPException(status_code=404, detail="Catégorie non trouvée")
    return category


# =============================================================================
# PROFESSIONS
# =============================================================================

@router.post("/professions", response_model=schemas.Profession, status_code=status.HTTP_201_CREATED)
def create_profession(profession: schemas.ProfessionCreate, db: Session = Depends(get_db)):
    """Créer une nouvelle profession"""
    existing = db.query(ProfessionModel).filter(ProfessionModel.code == profession.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ce code de profession existe déjà")
    
    db_profession = ProfessionModel(
        id=str(uuid.uuid4()),
        **profession.model_dump()
    )
    db.add(db_profession)
    db.commit()
    db.refresh(db_profession)
    return db_profession


@router.get("/professions", response_model=List[schemas.Profession])
def list_professions(
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Liste des professions"""
    query = db.query(ProfessionModel)
    
    if category:
        query = query.filter(ProfessionModel.category == category)
    
    if is_active is not None:
        query = query.filter(ProfessionModel.is_active == is_active)
    
    return query.all()


@router.get("/professions/{code}", response_model=schemas.Profession)
def get_profession(code: str, db: Session = Depends(get_db)):
    """Récupérer une profession par son code"""
    profession = db.query(ProfessionModel).filter(ProfessionModel.code == code).first()
    if not profession:
        raise HTTPException(status_code=404, detail="Profession non trouvée")
    return profession
