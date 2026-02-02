"""Routes API pour la gestion des chantiers"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.database import get_db
from app import schemas
from app.models import ConstructionSiteModel

router = APIRouter(prefix="/construction-sites", tags=["Chantiers"])


@router.post("/", response_model=schemas.ConstructionSite, status_code=status.HTTP_201_CREATED)
def create_site(site: schemas.ConstructionSiteCreate, db: Session = Depends(get_db)):
    """Créer un nouveau chantier"""
    # Vérifier que la référence n'existe pas
    existing = db.query(ConstructionSiteModel).filter(ConstructionSiteModel.site_reference == site.site_reference).first()
    if existing:
        raise HTTPException(status_code=400, detail="Cette référence de chantier existe déjà")
    
    db_site = ConstructionSiteModel(
        id=str(uuid.uuid4()),
        **site.model_dump()
    )
    db.add(db_site)
    db.commit()
    db.refresh(db_site)
    return db_site


@router.get("/", response_model=List[schemas.ConstructionSite])
def list_sites(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    building_category: Optional[str] = None,
    work_category: Optional[str] = None,
    city: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Liste des chantiers avec filtres"""
    query = db.query(ConstructionSiteModel)
    
    if building_category:
        query = query.filter(ConstructionSiteModel.building_category_code == building_category)
    
    if work_category:
        query = query.filter(ConstructionSiteModel.work_category_code == work_category)
    
    if city:
        query = query.filter(ConstructionSiteModel.city.ilike(f"%{city}%"))
    
    if is_active is not None:
        query = query.filter(ConstructionSiteModel.is_active == is_active)
    
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (ConstructionSiteModel.site_reference.ilike(search_filter)) |
            (ConstructionSiteModel.site_name.ilike(search_filter)) |
            (ConstructionSiteModel.city.ilike(search_filter))
        )
    
    return query.offset(skip).limit(limit).all()


@router.get("/{site_id}", response_model=schemas.ConstructionSite)
def get_site(site_id: str, db: Session = Depends(get_db)):
    """Récupérer un chantier par son ID"""
    site = db.query(ConstructionSiteModel).filter(ConstructionSiteModel.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Chantier non trouvé")
    return site


@router.get("/reference/{site_reference}", response_model=schemas.ConstructionSite)
def get_site_by_reference(site_reference: str, db: Session = Depends(get_db)):
    """Récupérer un chantier par sa référence"""
    site = db.query(ConstructionSiteModel).filter(ConstructionSiteModel.site_reference == site_reference).first()
    if not site:
        raise HTTPException(status_code=404, detail="Chantier non trouvé")
    return site


@router.put("/{site_id}", response_model=schemas.ConstructionSite)
def update_site(site_id: str, site_update: schemas.ConstructionSiteUpdate, db: Session = Depends(get_db)):
    """Mettre à jour un chantier"""
    db_site = db.query(ConstructionSiteModel).filter(ConstructionSiteModel.id == site_id).first()
    if not db_site:
        raise HTTPException(status_code=404, detail="Chantier non trouvé")
    
    update_data = site_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_site, field, value)
    
    db.commit()
    db.refresh(db_site)
    return db_site


@router.delete("/{site_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_site(site_id: str, db: Session = Depends(get_db)):
    """Supprimer un chantier (soft delete)"""
    db_site = db.query(ConstructionSiteModel).filter(ConstructionSiteModel.id == site_id).first()
    if not db_site:
        raise HTTPException(status_code=404, detail="Chantier non trouvé")
    
    db_site.is_active = False
    db.commit()
    return None
