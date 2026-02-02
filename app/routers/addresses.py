"""Routes API pour la gestion des adresses"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import ClientAddressModel

router = APIRouter(prefix="/addresses", tags=["Addresses"])


@router.get("/", response_model=List[dict])
@router.get("", response_model=List[dict])
def get_all_addresses(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Récupérer toutes les adresses"""
    addresses = db.query(ClientAddressModel).offset(skip).limit(limit).all()
    
    return [
        {
            "id": addr.id,
            "client_id": addr.client_id,
            "address_type": addr.address_type,
            "name": addr.name,
            "reference": addr.reference,
            "address_line1": addr.address_line1,
            "address_line2": addr.address_line2,
            "address_line3": addr.address_line3,
            "postal_code": addr.postal_code,
            "city": addr.city,
            "department": addr.department,
            "region": addr.region,
            "country": addr.country,
            "latitude": addr.latitude,
            "longitude": addr.longitude,
            "contact_name": addr.contact_name,
            "contact_phone": addr.contact_phone,
            "contact_email": addr.contact_email,
            "warehouse_surface_m2": addr.warehouse_surface_m2,
            "warehouse_capacity": addr.warehouse_capacity,
            "stored_materials": addr.stored_materials,
            "site_start_date": addr.site_start_date,
            "site_end_date": addr.site_end_date,
            "site_status": addr.site_status,
            "display_order": addr.display_order,
            "is_active": addr.is_active,
            "is_primary": addr.is_primary,
            "notes": addr.notes,
            "created_at": addr.created_at,
            "updated_at": addr.updated_at
        }
        for addr in addresses
    ]


@router.get("/{address_id}", response_model=dict)
def get_address(address_id: int, db: Session = Depends(get_db)):
    """Récupérer une adresse par son ID"""
    address = db.query(ClientAddressModel).filter(ClientAddressModel.id == address_id).first()
    
    if not address:
        raise HTTPException(status_code=404, detail="Adresse non trouvée")
    
    return {
        "id": address.id,
        "client_id": address.client_id,
        "address_type": address.address_type,
        "name": address.name,
        "reference": address.reference,
        "address_line1": address.address_line1,
        "address_line2": address.address_line2,
        "address_line3": address.address_line3,
        "postal_code": address.postal_code,
        "city": address.city,
        "department": address.department,
        "region": address.region,
        "country": address.country,
        "latitude": address.latitude,
        "longitude": address.longitude,
        "contact_name": address.contact_name,
        "contact_phone": address.contact_phone,
        "contact_email": address.contact_email,
        "warehouse_surface_m2": address.warehouse_surface_m2,
        "warehouse_capacity": address.warehouse_capacity,
        "stored_materials": address.stored_materials,
        "site_start_date": address.site_start_date,
        "site_end_date": address.site_end_date,
        "site_status": address.site_status,
        "display_order": address.display_order,
        "is_active": address.is_active,
        "is_primary": address.is_primary,
        "notes": address.notes,
        "created_at": address.created_at,
        "updated_at": address.updated_at
    }


@router.delete("/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_address(address_id: int, db: Session = Depends(get_db)):
    """Supprimer une adresse"""
    db_address = db.query(ClientAddressModel).filter(ClientAddressModel.id == address_id).first()
    if not db_address:
        raise HTTPException(status_code=404, detail="Adresse non trouvée")
    
    db.delete(db_address)
    db.commit()
    return None
