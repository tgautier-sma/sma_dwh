"""
Modèles pour les contrats clients d'assurance construction
Ces modèles permettent de créer des contrats personnalisés combinant les éléments du référentiel
"""
from sqlalchemy import Column, String, Text, Boolean, Integer, Float, DateTime, ForeignKey, JSON, Table, Date
from sqlalchemy.orm import relationship
from datetime import datetime, date
import enum

from app.database import Base


# =============================================================================
# ÉNUMÉRATIONS
# =============================================================================

class ContractStatusEnum(str, enum.Enum):
    """Statuts d'un contrat"""
    DRAFT = "brouillon"
    PENDING = "en_attente"
    ACTIVE = "actif"
    SUSPENDED = "suspendu"
    CANCELLED = "resilie"
    EXPIRED = "expire"


class ClientTypeEnum(str, enum.Enum):
    """Types de clients"""
    INDIVIDUAL = "particulier"
    COMPANY = "entreprise"
    PUBLIC_ENTITY = "entite_publique"
    PROFESSIONAL = "professionnel"
    PROMOTER = "promoteur"


class AddressTypeEnum(str, enum.Enum):
    """Types d'adresses"""
    HEADQUARTERS = "siege_social"  # Siège social / Entreprise (1 max)
    WAREHOUSE = "entrepot"  # Entrepôt (1 à 3 max)
    CONSTRUCTION_SITE = "chantier"  # Chantier (1 à 10 max)


# =============================================================================
# TABLES D'ASSOCIATION
# =============================================================================

# Association contrat <-> garanties sélectionnées
contract_guarantees = Table(
    'contract_guarantees',
    Base.metadata,
    Column('contract_id', String(36), ForeignKey('client_contracts.id'), primary_key=True),
    Column('guarantee_id', String(36), ForeignKey('ref_guarantees.id'), primary_key=True),
    Column('custom_ceiling', Float, nullable=True),
    Column('custom_franchise', Float, nullable=True),
    Column('is_included', Boolean, default=True)
)

# Association contrat <-> clauses applicables
contract_clauses = Table(
    'contract_clauses',
    Base.metadata,
    Column('contract_id', String(36), ForeignKey('client_contracts.id'), primary_key=True),
    Column('clause_id', String(36), ForeignKey('ref_contract_clauses.id'), primary_key=True),
    Column('variable_values', JSON, nullable=True),  # Valeurs des variables de la clause
    Column('is_modified', Boolean, default=False)
)


# =============================================================================
# MODÈLE ADRESSE CLIENT
# =============================================================================

class ClientAddressModel(Base):
    """Adresses des clients (siège, entrepôts, chantiers)"""
    __tablename__ = "client_addresses"
    
    id = Column(String(36), primary_key=True)
    client_id = Column(String(36), ForeignKey("clients.id"), nullable=False)
    
    # Type d'adresse
    address_type = Column(String(30), nullable=False)  # AddressTypeEnum
    
    # Identification
    name = Column(String(100), nullable=True)  # Nom de l'adresse (ex: "Entrepôt Nord", "Chantier Lyon")
    reference = Column(String(50), nullable=True)  # Référence interne
    
    # Adresse complète
    address_line1 = Column(String(255), nullable=False)
    address_line2 = Column(String(255), nullable=True)
    address_line3 = Column(String(255), nullable=True)
    postal_code = Column(String(10), nullable=False)
    city = Column(String(100), nullable=False)
    department = Column(String(3), nullable=True)
    region = Column(String(100), nullable=True)
    country = Column(String(50), default="France")
    
    # Coordonnées GPS (optionnel)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # Contact sur site
    contact_name = Column(String(100), nullable=True)
    contact_phone = Column(String(20), nullable=True)
    contact_email = Column(String(255), nullable=True)
    
    # Informations complémentaires pour les entrepôts
    warehouse_surface_m2 = Column(Float, nullable=True)  # Surface entrepôt
    warehouse_capacity = Column(String(100), nullable=True)  # Capacité
    stored_materials = Column(Text, nullable=True)  # Types de matériaux stockés
    
    # Informations complémentaires pour les chantiers
    site_start_date = Column(Date, nullable=True)  # Date début chantier
    site_end_date = Column(Date, nullable=True)  # Date fin prévue
    site_status = Column(String(30), nullable=True)  # en_cours, termine, suspendu
    
    # Ordre d'affichage (pour trier les adresses)
    display_order = Column(Integer, default=0)
    
    # Métadonnées
    is_active = Column(Boolean, default=True)
    is_primary = Column(Boolean, default=False)  # Adresse principale pour ce type
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relation
    client = relationship("ClientModel", back_populates="addresses")
    
    @property
    def full_address(self):
        """Retourne l'adresse complète formatée"""
        parts = [self.address_line1]
        if self.address_line2:
            parts.append(self.address_line2)
        if self.address_line3:
            parts.append(self.address_line3)
        parts.append(f"{self.postal_code} {self.city}")
        if self.country and self.country != "France":
            parts.append(self.country)
        return ", ".join(parts)
    
    def __repr__(self):
        return f"<ClientAddress(type={self.address_type}, city={self.city})>"


# =============================================================================
# MODÈLE CLIENT
# =============================================================================

class ClientModel(Base):
    """Modèle pour les clients (assurés)"""
    __tablename__ = "clients"
    
    id = Column(String(36), primary_key=True)
    
    # Identité
    client_number = Column(String(20), unique=True, nullable=False, index=True)
    client_type = Column(String(30), nullable=False)  # ClientTypeEnum
    
    # Personne physique
    civility = Column(String(10), nullable=True)  # M., Mme, etc.
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    birth_date = Column(Date, nullable=True)
    
    # Personne morale
    company_name = Column(String(200), nullable=True)
    legal_form = Column(String(50), nullable=True)  # SARL, SAS, SA, etc.
    siret = Column(String(14), nullable=True)
    siren = Column(String(9), nullable=True)
    
    # Contact principal
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    mobile = Column(String(20), nullable=True)
    website = Column(String(255), nullable=True)
    
    # Adresse principale (conservée pour compatibilité, mais utiliser addresses pour la gestion complète)
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    postal_code = Column(String(10), nullable=True)
    city = Column(String(100), nullable=True)
    country = Column(String(50), default="France")
    
    # Profession (pour professionnels du bâtiment)
    profession_code = Column(String(30), nullable=True)  # Lien avec ref_professions
    
    # Métadonnées
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    contracts = relationship("ClientContractModel", back_populates="client")
    addresses = relationship("ClientAddressModel", back_populates="client", cascade="all, delete-orphan")
    
    @property
    def display_name(self):
        if self.company_name:
            return self.company_name
        return f"{self.civility or ''} {self.first_name or ''} {self.last_name or ''}".strip()
    
    @property
    def headquarters_address(self):
        """Retourne l'adresse du siège social"""
        for addr in self.addresses:
            if addr.address_type == AddressTypeEnum.HEADQUARTERS.value and addr.is_active:
                return addr
        return None
    
    @property
    def warehouse_addresses(self):
        """Retourne la liste des adresses d'entrepôts (max 3)"""
        return [addr for addr in self.addresses 
                if addr.address_type == AddressTypeEnum.WAREHOUSE.value and addr.is_active]
    
    @property
    def site_addresses(self):
        """Retourne la liste des adresses de chantiers (max 10)"""
        return [addr for addr in self.addresses 
                if addr.address_type == AddressTypeEnum.CONSTRUCTION_SITE.value and addr.is_active]
    
    def __repr__(self):
        return f"<Client(number={self.client_number}, name={self.display_name})>"


# =============================================================================
# MODÈLE CHANTIER / OUVRAGE
# =============================================================================

class ConstructionSiteModel(Base):
    """Modèle pour les chantiers / ouvrages assurés"""
    __tablename__ = "construction_sites"
    
    id = Column(String(36), primary_key=True)
    
    # Identification
    site_reference = Column(String(30), unique=True, nullable=False, index=True)
    site_name = Column(String(200), nullable=False)
    
    # Localisation
    address_line1 = Column(String(255), nullable=False)
    address_line2 = Column(String(255), nullable=True)
    postal_code = Column(String(10), nullable=False)
    city = Column(String(100), nullable=False)
    department = Column(String(3), nullable=True)
    region = Column(String(100), nullable=True)
    
    # Caractéristiques de l'ouvrage
    building_category_code = Column(String(20), nullable=True)  # Lien ref_building_categories
    work_category_code = Column(String(30), nullable=True)  # Lien ref_work_categories
    
    # Surface et dimensions
    total_surface_m2 = Column(Float, nullable=True)
    habitable_surface_m2 = Column(Float, nullable=True)
    num_floors = Column(Integer, nullable=True)
    num_units = Column(Integer, nullable=True)  # Nombre de logements/lots
    
    # Montants
    construction_cost = Column(Float, nullable=True)  # Coût de construction HT
    land_value = Column(Float, nullable=True)  # Valeur du terrain
    total_project_value = Column(Float, nullable=True)
    
    # Dates
    permit_date = Column(Date, nullable=True)  # Date permis de construire
    opening_date = Column(Date, nullable=True)  # Date ouverture de chantier
    planned_completion_date = Column(Date, nullable=True)
    actual_completion_date = Column(Date, nullable=True)
    reception_date = Column(Date, nullable=True)  # Date de réception des travaux
    
    # Caractéristiques techniques
    foundation_type = Column(String(50), nullable=True)  # Type de fondations
    structure_type = Column(String(50), nullable=True)  # Type de structure
    has_basement = Column(Boolean, default=False)
    has_swimming_pool = Column(Boolean, default=False)
    has_elevator = Column(Boolean, default=False)
    
    # Zone géographique / risques
    seismic_zone = Column(Integer, nullable=True)  # Zone sismique 1-5
    flood_zone = Column(Boolean, default=False)
    soil_study_done = Column(Boolean, default=False)
    
    # Métadonnées
    description = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    contracts = relationship("ClientContractModel", back_populates="construction_site")
    
    def __repr__(self):
        return f"<ConstructionSite(ref={self.site_reference}, name={self.site_name})>"


# =============================================================================
# MODÈLE CONTRAT CLIENT
# =============================================================================

class ClientContractModel(Base):
    """Contrat d'assurance construction client"""
    __tablename__ = "client_contracts"
    
    id = Column(String(36), primary_key=True)
    
    # Identification
    contract_number = Column(String(30), unique=True, nullable=False, index=True)
    external_reference = Column(String(50), nullable=True)  # Référence externe (assureur)
    
    # Type de contrat (référentiel)
    contract_type_code = Column(String(20), nullable=False)  # Lien avec ref_insurance_contract_types
    
    # Relations client et chantier
    client_id = Column(String(36), ForeignKey("clients.id"), nullable=False)
    client = relationship("ClientModel", back_populates="contracts")
    
    construction_site_id = Column(String(36), ForeignKey("construction_sites.id"), nullable=True)
    construction_site = relationship("ConstructionSiteModel", back_populates="contracts")
    
    # Statut
    status = Column(String(30), default="brouillon")  # ContractStatusEnum
    
    # Dates du contrat
    issue_date = Column(Date, nullable=True)  # Date d'émission
    effective_date = Column(Date, nullable=True)  # Date d'effet
    expiry_date = Column(Date, nullable=True)  # Date d'expiration
    cancellation_date = Column(Date, nullable=True)  # Date de résiliation
    
    # Montants
    insured_amount = Column(Float, nullable=True)  # Montant assuré
    annual_premium = Column(Float, nullable=True)  # Prime annuelle
    total_premium = Column(Float, nullable=True)  # Prime totale (pour contrats pluriannuels)
    franchise_amount = Column(Float, nullable=True)  # Franchise globale
    
    # Durée
    duration_years = Column(Integer, default=10)  # Durée en années
    is_renewable = Column(Boolean, default=False)  # Tacite reconduction
    
    # Garanties sélectionnées (JSON simplifié pour faciliter la consultation)
    selected_guarantees = Column(JSON, nullable=True)  # Liste des codes de garanties avec paramètres
    """
    Format: [
        {"code": "GAR_DEC_01", "ceiling": 1000000, "franchise": 5000, "included": true},
        {"code": "GAR_BIEN_01", "ceiling": 500000, "franchise": 2500, "included": true}
    ]
    """
    
    # Clauses applicables
    selected_clauses = Column(JSON, nullable=True)  # Liste des codes de clauses avec variables
    """
    Format: [
        {"code": "CL_FRAN_01", "variables": {"montant_franchise": 5000}},
        {"code": "CL_EXCL_01", "variables": {}}
    ]
    """
    
    # Exclusions spécifiques
    specific_exclusions = Column(JSON, nullable=True)  # Exclusions ajoutées manuellement
    
    # Conditions particulières
    special_conditions = Column(Text, nullable=True)
    
    # Intervenants
    broker_name = Column(String(200), nullable=True)  # Courtier
    broker_code = Column(String(30), nullable=True)
    underwriter = Column(String(200), nullable=True)  # Souscripteur
    
    # Pièces jointes (références)
    attached_documents = Column(JSON, nullable=True)  # IDs des documents attachés
    
    # Notes et commentaires
    internal_notes = Column(Text, nullable=True)
    client_notes = Column(Text, nullable=True)
    
    # Métadonnées
    created_by = Column(String(36), nullable=True)  # ID utilisateur
    updated_by = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<ClientContract(number={self.contract_number}, type={self.contract_type_code})>"
    
    @property
    def is_active(self):
        """Vérifie si le contrat est actif"""
        return self.status == ContractStatusEnum.ACTIVE.value
    
    @property
    def days_until_expiry(self):
        """Calcule le nombre de jours avant expiration"""
        if self.expiry_date:
            return (self.expiry_date - date.today()).days
        return None


# =============================================================================
# HISTORIQUE DES MODIFICATIONS
# =============================================================================

class ContractHistoryModel(Base):
    """Historique des modifications de contrat"""
    __tablename__ = "contract_history"
    
    id = Column(String(36), primary_key=True)
    contract_id = Column(String(36), ForeignKey("client_contracts.id"), nullable=False)
    
    # Type de modification
    action = Column(String(50), nullable=False)  # create, update, status_change, etc.
    field_changed = Column(String(100), nullable=True)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    
    # Utilisateur et date
    changed_by = Column(String(36), nullable=True)
    changed_at = Column(DateTime, default=datetime.utcnow)
    
    # Notes
    comment = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<ContractHistory(contract_id={self.contract_id}, action={self.action})>"
