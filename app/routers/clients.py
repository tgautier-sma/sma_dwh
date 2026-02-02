"""Routes API pour la gestion des clients"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import unicodedata
import re

from app.database import get_db
from app import schemas
from app.models import ClientModel, ClientAddressModel

router = APIRouter(prefix="/clients", tags=["Clients"])


# =============================================================================
# FONCTIONS UTILITAIRES POUR RECHERCHE PHONÉTIQUE
# =============================================================================

def normalize_text(text: str) -> str:
    """Normalise le texte pour la recherche phonétique"""
    if not text:
        return ""
    # Supprime les accents
    text = unicodedata.normalize('NFD', text)
    text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')
    # Convertit en majuscules et supprime les caractères non-alphabétiques
    text = re.sub(r'[^A-Z]', '', text.upper())
    return text


def soundex_fr(text: str) -> str:
    """
    Implémentation simplifiée de Soundex pour le français.
    Retourne un code phonétique de 4 caractères.
    """
    if not text:
        return "0000"
    
    text = normalize_text(text)
    if not text:
        return "0000"
    
    # Première lettre conservée
    soundex = text[0]
    
    # Table de conversion phonétique adaptée au français
    conversions = {
        'B': '1', 'P': '1',
        'C': '2', 'K': '2', 'Q': '2',
        'D': '3', 'T': '3',
        'L': '4',
        'M': '5', 'N': '5',
        'R': '6',
        'G': '7', 'J': '7',
        'X': '8', 'Z': '8', 'S': '8',
        'F': '9', 'V': '9'
    }
    
    previous_code = conversions.get(text[0], '0')
    
    for char in text[1:]:
        code = conversions.get(char, '0')
        
        # Ignore les voyelles et les caractères identiques consécutifs
        if code != '0' and code != previous_code:
            soundex += code
            previous_code = code
        
        # Limite à 4 caractères
        if len(soundex) >= 4:
            break
    
    # Complète avec des zéros si nécessaire
    soundex = soundex.ljust(4, '0')
    
    return soundex[:4]


# =============================================================================
# CLIENTS
# =============================================================================

@router.post("/", response_model=schemas.Client, status_code=status.HTTP_201_CREATED)
@router.post("", response_model=schemas.Client, status_code=status.HTTP_201_CREATED)
def create_client(client: schemas.ClientCreate, db: Session = Depends(get_db)):
    """Créer un nouveau client"""
    # Vérifier si le numéro client existe déjà
    existing = db.query(ClientModel).filter(ClientModel.client_number == client.client_number).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ce numéro de client existe déjà")
    
    db_client = ClientModel(**client.model_dump())
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client


@router.get("/", response_model=List[schemas.Client])
@router.get("", response_model=List[schemas.Client])
def list_clients(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    client_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Liste des clients avec filtres"""
    query = db.query(ClientModel)
    
    if client_type:
        query = query.filter(ClientModel.client_type == client_type)
    
    if is_active is not None:
        query = query.filter(ClientModel.is_active == is_active)
    
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (ClientModel.client_number.ilike(search_filter)) |
            (ClientModel.company_name.ilike(search_filter)) |
            (ClientModel.first_name.ilike(search_filter)) |
            (ClientModel.last_name.ilike(search_filter))
        )
    
    return query.offset(skip).limit(limit).all()


@router.get("/search", response_model=List[schemas.Client])
def search_clients(
    query: Optional[str] = Query(None, description="Numéro de client ou nom à rechercher"),
    phonetic: bool = Query(False, description="Activer la recherche phonétique sur les noms"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Recherche avancée de clients par numéro ou nom.
    
    - **query**: Texte de recherche (numéro client, nom d'entreprise, nom/prénom)
    - **phonetic**: Si True, utilise la recherche phonétique pour trouver des noms similaires
    - **skip**: Nombre de résultats à ignorer (pagination)
    - **limit**: Nombre maximum de résultats à retourner
    
    Exemples:
    - `/clients/search?query=CLI-2024-001` : Recherche par numéro exact
    - `/clients/search?query=Dupont&phonetic=true` : Recherche phonétique (trouve Dupond, Dupon, etc.)
    - `/clients/search?query=Construction` : Recherche dans les noms d'entreprise
    """
    if not query:
        raise HTTPException(status_code=400, detail="Le paramètre 'query' est requis")
    
    db_query = db.query(ClientModel)
    
    # Recherche exacte par numéro de client
    exact_number = db_query.filter(ClientModel.client_number == query).first()
    if exact_number:
        return [exact_number]
    
    # Recherche standard (LIKE)
    search_filter = f"%{query}%"
    standard_results = db_query.filter(
        (ClientModel.client_number.ilike(search_filter)) |
        (ClientModel.company_name.ilike(search_filter)) |
        (ClientModel.first_name.ilike(search_filter)) |
        (ClientModel.last_name.ilike(search_filter))
    ).offset(skip).limit(limit).all()
    
    # Si recherche phonétique activée et pas de résultats standards
    if phonetic and not standard_results:
        query_soundex = soundex_fr(query)
        
        # Récupère tous les clients actifs pour comparaison phonétique
        all_clients = db.query(ClientModel).filter(ClientModel.is_active == True).all()
        
        phonetic_matches = []
        for client in all_clients:
            # Compare avec le nom d'entreprise
            if client.company_name:
                if soundex_fr(client.company_name) == query_soundex:
                    phonetic_matches.append(client)
                    continue
            
            # Compare avec nom/prénom pour les particuliers
            if client.last_name:
                if soundex_fr(client.last_name) == query_soundex:
                    phonetic_matches.append(client)
                    continue
            
            if client.first_name:
                if soundex_fr(client.first_name) == query_soundex:
                    phonetic_matches.append(client)
                    continue
        
        return phonetic_matches[skip:skip+limit] if phonetic_matches else []
    
    return standard_results


@router.get("/{client_id}/full", response_model=dict)
def get_client_full(client_id: int, db: Session = Depends(get_db)):
    """Récupérer un client avec toutes ses relations (adresses, contrats, etc.)"""
    from sqlalchemy.orm import joinedload
    from app.models import ClientContractModel, ClientAddressModel, ContractHistoryModel
    
    # Récupérer le client avec toutes ses relations
    client = db.query(ClientModel).options(
        joinedload(ClientModel.addresses),
        joinedload(ClientModel.contracts).joinedload(ClientContractModel.construction_site),
        joinedload(ClientModel.contracts).joinedload(ClientContractModel.history)
    ).filter(ClientModel.id == client_id).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    
    # Construire la réponse avec toutes les informations
    return {
        "client": {
            "id": client.id,
            "client_number": client.client_number,
            "client_type": client.client_type,
            "civility": client.civility,
            "first_name": client.first_name,
            "last_name": client.last_name,
            "birth_date": client.birth_date,
            "company_name": client.company_name,
            "legal_form": client.legal_form,
            "siret": client.siret,
            "siren": client.siren,
            "email": client.email,
            "phone": client.phone,
            "mobile": client.mobile,
            "website": client.website,
            "address_line1": client.address_line1,
            "address_line2": client.address_line2,
            "postal_code": client.postal_code,
            "city": client.city,
            "country": client.country,
            "profession_code": client.profession_code,
            "is_active": client.is_active,
            "notes": client.notes,
            "created_at": client.created_at,
            "updated_at": client.updated_at
        },
        "addresses": [
            {
                "id": addr.id,
                "address_type": addr.address_type,
                "address_line1": addr.address_line1,
                "address_line2": addr.address_line2,
                "postal_code": addr.postal_code,
                "city": addr.city,
                "country": addr.country,
                "is_primary": addr.is_primary,
                "created_at": addr.created_at,
                "updated_at": addr.updated_at
            }
            for addr in client.addresses
        ],
        "contracts": [
            {
                "id": contract.id,
                "contract_number": contract.contract_number,
                "contract_type_code": contract.contract_type_code,
                "status": contract.status,
                "issue_date": contract.issue_date,
                "effective_date": contract.effective_date,
                "expiry_date": contract.expiry_date,
                "cancellation_date": contract.cancellation_date,
                "insured_amount": float(contract.insured_amount) if contract.insured_amount else None,
                "annual_premium": float(contract.annual_premium) if contract.annual_premium else None,
                "total_premium": float(contract.total_premium) if contract.total_premium else None,
                "franchise_amount": float(contract.franchise_amount) if contract.franchise_amount else None,
                "duration_years": contract.duration_years,
                "is_renewable": contract.is_renewable,
                "construction_site": {
                    "id": contract.construction_site.id,
                    "site_name": contract.construction_site.site_name,
                    "address_line1": contract.construction_site.address_line1,
                    "address_line2": contract.construction_site.address_line2,
                    "postal_code": contract.construction_site.postal_code,
                    "city": contract.construction_site.city,
                    "total_project_value": float(contract.construction_site.total_project_value) if contract.construction_site.total_project_value else None,
                    "construction_cost": float(contract.construction_site.construction_cost) if contract.construction_site.construction_cost else None,
                    "opening_date": contract.construction_site.opening_date,
                    "planned_completion_date": contract.construction_site.planned_completion_date
                } if contract.construction_site else None,
                "selected_guarantees": contract.selected_guarantees or [],
                "selected_clauses": contract.selected_clauses or [],
                "specific_exclusions": contract.specific_exclusions or [],
                "special_conditions": contract.special_conditions,
                "broker_name": contract.broker_name,
                "broker_code": contract.broker_code,
                "underwriter": contract.underwriter,
                "history": [
                    {
                        "id": hist.id,
                        "action": hist.action,
                        "field_changed": hist.field_changed,
                        "old_value": hist.old_value,
                        "new_value": hist.new_value,
                        "changed_by": hist.changed_by,
                        "changed_at": hist.changed_at,
                        "comment": hist.comment
                    }
                    for hist in contract.history
                ]
            }
            for contract in client.contracts
        ],
        "stats": {
            "total_addresses": len(client.addresses),
            "total_contracts": len(client.contracts),
            "active_contracts": len([c for c in client.contracts if c.status == "active"]),
            "total_insured_amount": sum(float(c.insured_amount) for c in client.contracts if c.insured_amount),
            "total_annual_premium": sum(float(c.annual_premium) for c in client.contracts if c.annual_premium)
        }
    }


@router.get("/{client_id}", response_model=schemas.Client)
def get_client(client_id: int, db: Session = Depends(get_db)):
    """Récupérer un client par son ID (informations de base uniquement)"""
    client = db.query(ClientModel).filter(ClientModel.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    return client


@router.get("/number/{client_number}", response_model=schemas.Client)
def get_client_by_number(client_number: str, db: Session = Depends(get_db)):
    """Récupérer un client par son numéro"""
    client = db.query(ClientModel).filter(ClientModel.client_number == client_number).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    return client


@router.put("/{client_id}", response_model=schemas.Client)
def update_client(client_id: int, client_update: schemas.ClientUpdate, db: Session = Depends(get_db)):
    """Mettre à jour un client"""
    db_client = db.query(ClientModel).filter(ClientModel.id == client_id).first()
    if not db_client:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    
    update_data = client_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_client, field, value)
    
    db.commit()
    db.refresh(db_client)
    return db_client


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(client_id: int, db: Session = Depends(get_db)):
    """Supprimer un client (soft delete)"""
    db_client = db.query(ClientModel).filter(ClientModel.id == client_id).first()
    if not db_client:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    
    db_client.is_active = False
    db.commit()
    return None


# =============================================================================
# ADRESSES CLIENTS
# =============================================================================

@router.post("/{client_id}/addresses", response_model=schemas.ClientAddress, status_code=status.HTTP_201_CREATED)
def create_client_address(client_id: int, address: schemas.ClientAddressCreate, db: Session = Depends(get_db)):
    """Ajouter une adresse à un client"""
    # Vérifier que le client existe
    client = db.query(ClientModel).filter(ClientModel.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    
    db_address = ClientAddressModel(
        client_id=client_id,
        **address.model_dump(exclude={'client_id'})
    )
    db.add(db_address)
    db.commit()
    db.refresh(db_address)
    return db_address


@router.get("/{client_id}/addresses", response_model=List[schemas.ClientAddress])
def list_client_addresses(
    client_id: int,
    address_type: Optional[str] = None,
    is_active: Optional[bool] = True,
    db: Session = Depends(get_db)
):
    """Liste des adresses d'un client"""
    query = db.query(ClientAddressModel).filter(ClientAddressModel.client_id == client_id)
    
    if address_type:
        query = query.filter(ClientAddressModel.address_type == address_type)
    
    if is_active is not None:
        query = query.filter(ClientAddressModel.is_active == is_active)
    
    return query.order_by(ClientAddressModel.display_order).all()


@router.get("/addresses/{address_id}", response_model=schemas.ClientAddress)
def get_client_address(address_id: int, db: Session = Depends(get_db)):
    """Récupérer une adresse par son ID"""
    address = db.query(ClientAddressModel).filter(ClientAddressModel.id == address_id).first()
    if not address:
        raise HTTPException(status_code=404, detail="Adresse non trouvée")
    return address


@router.put("/addresses/{address_id}", response_model=schemas.ClientAddress)
def update_client_address(address_id: int, address_update: schemas.ClientAddressUpdate, db: Session = Depends(get_db)):
    """Mettre à jour une adresse"""
    db_address = db.query(ClientAddressModel).filter(ClientAddressModel.id == address_id).first()
    if not db_address:
        raise HTTPException(status_code=404, detail="Adresse non trouvée")
    
    update_data = address_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_address, field, value)
    
    db.commit()
    db.refresh(db_address)
    return db_address


@router.delete("/addresses/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client_address(address_id: int, db: Session = Depends(get_db)):
    """Supprimer une adresse"""
    db_address = db.query(ClientAddressModel).filter(ClientAddressModel.id == address_id).first()
    if not db_address:
        raise HTTPException(status_code=404, detail="Adresse non trouvée")
    
    db.delete(db_address)
    db.commit()
    return None
