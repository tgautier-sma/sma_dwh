"""Routes API pour la gestion des diagrammes Mermaid"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from datetime import datetime

from app.database import get_db
from app import schemas
from app.models import MermaidDiagram

router = APIRouter(prefix="/diagrams", tags=["Diagrammes Mermaid"])


# =============================================================================
# CRUD DIAGRAMMES
# =============================================================================

@router.post("/", response_model=schemas.MermaidDiagram, status_code=status.HTTP_201_CREATED)
@router.post("", response_model=schemas.MermaidDiagram, status_code=status.HTTP_201_CREATED)
def create_diagram(diagram: schemas.MermaidDiagramCreate, db: Session = Depends(get_db)):
    """Créer un nouveau diagramme Mermaid"""
    # Générer un ID unique
    diagram_id = str(uuid.uuid4())
    
    db_diagram = MermaidDiagram(
        id=diagram_id,
        **diagram.model_dump()
    )
    db.add(db_diagram)
    db.commit()
    db.refresh(db_diagram)
    return db_diagram


@router.get("/", response_model=List[schemas.MermaidDiagram])
@router.get("", response_model=List[schemas.MermaidDiagram])
def list_diagrams(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    diagram_type: Optional[str] = Query(None, description="Filtrer par type de diagramme"),
    tag: Optional[str] = Query(None, description="Filtrer par tag"),
    search: Optional[str] = Query(None, description="Rechercher dans le titre et la description"),
    public_only: bool = Query(False, description="Afficher uniquement les diagrammes publics"),
    db: Session = Depends(get_db)
):
    """Lister tous les diagrammes avec filtres optionnels"""
    query = db.query(MermaidDiagram)
    
    # Filtre par type
    if diagram_type:
        query = query.filter(MermaidDiagram.diagram_type == diagram_type)
    
    # Filtre par visibilité
    if public_only:
        query = query.filter(MermaidDiagram.is_public == True)
    
    # Filtre par tag
    if tag:
        query = query.filter(MermaidDiagram.tags.contains([tag]))
    
    # Recherche texte
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (MermaidDiagram.title.ilike(search_pattern)) |
            (MermaidDiagram.description.ilike(search_pattern))
        )
    
    # Tri par date de mise à jour (plus récent en premier)
    query = query.order_by(MermaidDiagram.updated_at.desc())
    
    diagrams = query.offset(skip).limit(limit).all()
    return diagrams


@router.get("/{diagram_id}", response_model=schemas.MermaidDiagram)
def get_diagram(diagram_id: str, db: Session = Depends(get_db)):
    """Récupérer un diagramme par son ID"""
    diagram = db.query(MermaidDiagram).filter(MermaidDiagram.id == diagram_id).first()
    if not diagram:
        raise HTTPException(status_code=404, detail="Diagramme non trouvé")
    return diagram


@router.put("/{diagram_id}", response_model=schemas.MermaidDiagram)
def update_diagram(
    diagram_id: str,
    diagram_update: schemas.MermaidDiagramUpdate,
    db: Session = Depends(get_db)
):
    """Mettre à jour un diagramme"""
    db_diagram = db.query(MermaidDiagram).filter(MermaidDiagram.id == diagram_id).first()
    if not db_diagram:
        raise HTTPException(status_code=404, detail="Diagramme non trouvé")
    
    # Mettre à jour les champs fournis
    update_data = diagram_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_diagram, field, value)
    
    db_diagram.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_diagram)
    return db_diagram


@router.delete("/{diagram_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_diagram(diagram_id: str, db: Session = Depends(get_db)):
    """Supprimer un diagramme"""
    db_diagram = db.query(MermaidDiagram).filter(MermaidDiagram.id == diagram_id).first()
    if not db_diagram:
        raise HTTPException(status_code=404, detail="Diagramme non trouvé")
    
    db.delete(db_diagram)
    db.commit()
    return None


@router.get("/types/available", response_model=List[dict])
@router.get("/types/available/", response_model=List[dict])
def get_available_diagram_types():
    """Retourner la liste des types de diagrammes disponibles"""
    return [
        {"value": "flowchart", "label": "Diagramme de flux", "icon": "fa-project-diagram"},
        {"value": "sequence", "label": "Diagramme de séquence", "icon": "fa-exchange-alt"},
        {"value": "class", "label": "Diagramme de classes", "icon": "fa-sitemap"},
        {"value": "state", "label": "Diagramme d'états", "icon": "fa-circle-notch"},
        {"value": "er", "label": "Diagramme Entité-Relation", "icon": "fa-database"},
        {"value": "gantt", "label": "Diagramme de Gantt", "icon": "fa-chart-bar"},
        {"value": "pie", "label": "Diagramme circulaire", "icon": "fa-chart-pie"},
        {"value": "journey", "label": "Diagramme de parcours", "icon": "fa-route"},
        {"value": "git", "label": "Diagramme Git", "icon": "fa-code-branch"},
        {"value": "mindmap", "label": "Carte mentale", "icon": "fa-brain"}
    ]
