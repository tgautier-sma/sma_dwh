"""Schémas Pydantic pour la validation et sérialisation des données"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, date
from enum import Enum


# =============================================================================
# ÉNUMÉRATIONS
# =============================================================================

class ContractStatusEnum(str, Enum):
    DRAFT = "brouillon"
    PENDING = "en_attente"
    ACTIVE = "actif"
    SUSPENDED = "suspendu"
    CANCELLED = "resilie"
    EXPIRED = "expire"


class ClientTypeEnum(str, Enum):
    INDIVIDUAL = "particulier"
    COMPANY = "entreprise"
    PUBLIC_ENTITY = "entite_publique"
    PROFESSIONAL = "professionnel"
    PROMOTER = "promoteur"


class AddressTypeEnum(str, Enum):
    HEADQUARTERS = "siege_social"
    WAREHOUSE = "entrepot"
    CONSTRUCTION_SITE = "chantier"


class InsuranceTypeEnum(str, Enum):
    DO = "dommages_ouvrage"
    RCD = "rc_decennale"
    TRC = "tous_risques_chantier"
    CNR = "constructeur_non_realisateur"
    RCMO = "rc_maitre_ouvrage"
    PUC = "police_unique_chantier"


class GuaranteeTypeEnum(str, Enum):
    MANDATORY = "obligatoire"
    OPTIONAL = "optionnelle"
    COMPLEMENTARY = "complementaire"


# =============================================================================
# SCHÉMAS CLIENT
# =============================================================================

class ClientBase(BaseModel):
    """Schéma de base pour un client"""
    client_number: str = Field(..., description="Numéro unique du client")
    client_type: ClientTypeEnum = Field(..., description="Type de client")
    civility: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    birth_date: Optional[date] = None
    company_name: Optional[str] = None
    legal_form: Optional[str] = None
    siret: Optional[str] = None
    siren: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    website: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    country: str = "France"
    profession_code: Optional[str] = None
    is_active: bool = True
    notes: Optional[str] = None


class ClientCreate(ClientBase):
    """Schéma pour créer un client"""
    pass


class ClientUpdate(BaseModel):
    """Schéma pour mettre à jour un client"""
    client_type: Optional[ClientTypeEnum] = None
    civility: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    birth_date: Optional[date] = None
    company_name: Optional[str] = None
    legal_form: Optional[str] = None
    siret: Optional[str] = None
    siren: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    website: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    profession_code: Optional[str] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class Client(ClientBase):
    """Schéma de réponse pour un client"""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SCHÉMAS ADRESSE CLIENT
# =============================================================================

class ClientAddressBase(BaseModel):
    """Schéma de base pour une adresse client"""
    address_type: AddressTypeEnum
    name: Optional[str] = None
    reference: Optional[str] = None
    address_line1: str
    address_line2: Optional[str] = None
    address_line3: Optional[str] = None
    postal_code: str
    city: str
    department: Optional[str] = None
    region: Optional[str] = None
    country: str = "France"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    warehouse_surface_m2: Optional[float] = None
    warehouse_capacity: Optional[str] = None
    stored_materials: Optional[str] = None
    site_start_date: Optional[date] = None
    site_end_date: Optional[date] = None
    site_status: Optional[str] = None
    display_order: int = 0
    is_active: bool = True
    is_primary: bool = False
    notes: Optional[str] = None


class ClientAddressCreate(ClientAddressBase):
    """Schéma pour créer une adresse client"""
    client_id: int


class ClientAddressUpdate(BaseModel):
    """Schéma pour mettre à jour une adresse client"""
    address_type: Optional[AddressTypeEnum] = None
    name: Optional[str] = None
    reference: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    address_line3: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    department: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class ClientAddress(ClientAddressBase):
    """Schéma de réponse pour une adresse client"""
    id: int
    client_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SCHÉMAS CHANTIER
# =============================================================================

class ConstructionSiteBase(BaseModel):
    """Schéma de base pour un chantier"""
    site_reference: str
    site_name: str
    address_line1: str
    address_line2: Optional[str] = None
    postal_code: str
    city: str
    department: Optional[str] = None
    region: Optional[str] = None
    building_category_code: Optional[str] = None
    work_category_code: Optional[str] = None
    total_surface_m2: Optional[float] = None
    habitable_surface_m2: Optional[float] = None
    num_floors: Optional[int] = None
    num_units: Optional[int] = None
    construction_cost: Optional[float] = None
    land_value: Optional[float] = None
    total_project_value: Optional[float] = None
    permit_date: Optional[date] = None
    opening_date: Optional[date] = None
    planned_completion_date: Optional[date] = None
    actual_completion_date: Optional[date] = None
    reception_date: Optional[date] = None
    foundation_type: Optional[str] = None
    structure_type: Optional[str] = None
    has_basement: bool = False
    has_swimming_pool: bool = False
    has_elevator: bool = False
    seismic_zone: Optional[int] = None
    flood_zone: bool = False
    soil_study_done: bool = False
    description: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool = True


class ConstructionSiteCreate(ConstructionSiteBase):
    """Schéma pour créer un chantier"""
    pass


class ConstructionSiteUpdate(BaseModel):
    """Schéma pour mettre à jour un chantier"""
    site_name: Optional[str] = None
    address_line1: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    total_surface_m2: Optional[float] = None
    construction_cost: Optional[float] = None
    is_active: Optional[bool] = None


class ConstructionSite(ConstructionSiteBase):
    """Schéma de réponse pour un chantier"""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SCHÉMAS CONTRAT CLIENT
# =============================================================================

class ClientContractBase(BaseModel):
    """Schéma de base pour un contrat client"""
    contract_number: str
    external_reference: Optional[str] = None
    contract_type_code: str
    client_id: int
    construction_site_id: Optional[int] = None
    status: ContractStatusEnum = ContractStatusEnum.DRAFT
    issue_date: Optional[date] = None
    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None
    cancellation_date: Optional[date] = None
    insured_amount: Optional[float] = None
    annual_premium: Optional[float] = None
    total_premium: Optional[float] = None
    franchise_amount: Optional[float] = None
    duration_years: int = 10
    is_renewable: bool = False
    selected_guarantees: Optional[List[dict]] = None
    selected_clauses: Optional[List[dict]] = None
    specific_exclusions: Optional[dict] = None
    special_conditions: Optional[str] = None
    broker_name: Optional[str] = None
    broker_code: Optional[str] = None
    underwriter: Optional[str] = None
    attached_documents: Optional[dict] = None
    internal_notes: Optional[str] = None
    client_notes: Optional[str] = None


class ClientContractCreate(ClientContractBase):
    """Schéma pour créer un contrat client"""
    pass


class ClientContractUpdate(BaseModel):
    """Schéma pour mettre à jour un contrat client"""
    status: Optional[ContractStatusEnum] = None
    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None
    insured_amount: Optional[float] = None
    annual_premium: Optional[float] = None
    selected_guarantees: Optional[List[dict]] = None
    selected_clauses: Optional[List[dict]] = None
    internal_notes: Optional[str] = None


class ClientContract(ClientContractBase):
    """Schéma de réponse pour un contrat client"""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SCHÉMAS RÉFÉRENTIEL - Type de contrat
# =============================================================================

class InsuranceContractTypeBase(BaseModel):
    """Schéma de base pour un type de contrat"""
    code: str
    name: str
    description: Optional[str] = None
    legal_reference: Optional[str] = None
    is_mandatory: bool = False
    is_active: bool = True


class InsuranceContractTypeCreate(InsuranceContractTypeBase):
    """Schéma pour créer un type de contrat"""
    pass


class InsuranceContractType(InsuranceContractTypeBase):
    """Schéma de réponse pour un type de contrat"""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SCHÉMAS RÉFÉRENTIEL - Garanties
# =============================================================================

class GuaranteeBase(BaseModel):
    """Schéma de base pour une garantie"""
    code: str
    name: str
    description: Optional[str] = None
    category: str
    guarantee_type: GuaranteeTypeEnum
    contract_type_id: Optional[int] = None
    duration_years: Optional[int] = None
    duration_description: Optional[str] = None
    legal_reference: Optional[str] = None
    legal_articles: Optional[dict] = None
    default_ceiling: Optional[float] = None
    default_franchise: Optional[float] = None
    franchise_type: Optional[str] = None
    conditions: Optional[dict] = None
    exclusions_default: Optional[dict] = None
    is_active: bool = True


class GuaranteeCreate(GuaranteeBase):
    """Schéma pour créer une garantie"""
    pass


class Guarantee(GuaranteeBase):
    """Schéma de réponse pour une garantie"""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SCHÉMAS RÉFÉRENTIEL - Clauses
# =============================================================================

class ContractClauseBase(BaseModel):
    """Schéma de base pour une clause"""
    code: str
    title: str
    content: str
    category: str
    subcategory: Optional[str] = None
    applies_to_contract_types: Optional[dict] = None
    applies_to_guarantees: Optional[dict] = None
    is_mandatory: bool = False
    is_negotiable: bool = True
    priority_order: int = 0
    legal_reference: Optional[str] = None
    version: int = 1
    variables: Optional[dict] = None
    is_active: bool = True


class ContractClauseCreate(ContractClauseBase):
    """Schéma pour créer une clause"""
    pass


class ContractClause(ContractClauseBase):
    """Schéma de réponse pour une clause"""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SCHÉMAS RÉFÉRENTIEL - Catégories de bâtiments
# =============================================================================

class BuildingCategoryBase(BaseModel):
    """Schéma de base pour une catégorie de bâtiment"""
    code: str
    name: str
    description: Optional[str] = None
    risk_coefficient: float = 1.0
    technical_complexity: int = 1
    applicable_guarantees: Optional[dict] = None
    is_active: bool = True


class BuildingCategoryCreate(BuildingCategoryBase):
    """Schéma pour créer une catégorie de bâtiment"""
    pass


class BuildingCategory(BuildingCategoryBase):
    """Schéma de réponse pour une catégorie de bâtiment"""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SCHÉMAS RÉFÉRENTIEL - Catégories de travaux
# =============================================================================

class WorkCategoryBase(BaseModel):
    """Schéma de base pour une catégorie de travaux"""
    code: str
    name: str
    description: Optional[str] = None
    parent_code: Optional[str] = None
    risk_level: int = 1
    requires_control: bool = False
    mandatory_guarantees: Optional[dict] = None
    recommended_guarantees: Optional[dict] = None
    is_active: bool = True


class WorkCategoryCreate(WorkCategoryBase):
    """Schéma pour créer une catégorie de travaux"""
    pass


class WorkCategory(WorkCategoryBase):
    """Schéma de réponse pour une catégorie de travaux"""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SCHÉMAS RÉFÉRENTIEL - Professions
# =============================================================================

class ProfessionBase(BaseModel):
    """Schéma de base pour une profession"""
    code: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    rc_decennale_required: bool = True
    rc_pro_required: bool = False
    covered_activities: Optional[dict] = None
    base_rate_coefficient: float = 1.0
    is_active: bool = True


class ProfessionCreate(ProfessionBase):
    """Schéma pour créer une profession"""
    pass


class Profession(ProfessionBase):
    """Schéma de réponse pour une profession"""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SCHÉMAS DE RÉPONSE PAGINÉS
# =============================================================================

class PaginatedResponse(BaseModel):
    """Schéma de réponse paginée"""
    total: int
    page: int
    page_size: int
    items: List[dict]


# =============================================================================
# SCHÉMAS POUR LES STATISTIQUES
# =============================================================================

class ContractStatistics(BaseModel):
    """Statistiques sur les contrats"""
    total_contracts: int
    active_contracts: int
    draft_contracts: int
    cancelled_contracts: int
    total_premium_volume: float
    average_premium: float


# =============================================================================
# SCHÉMAS SINISTRE
# =============================================================================

class ClaimStatusEnum(str, Enum):
    DECLARED = "declare"
    ACKNOWLEDGED = "pris_en_compte"
    INVESTIGATING = "en_cours_expertise"
    PENDING_DOCS = "attente_pieces"
    ACCEPTED = "accepte"
    REJECTED = "refuse"
    SETTLED = "regle"
    CLOSED = "cloture"


class ClaimTypeEnum(str, Enum):
    STRUCTURAL = "structurel"
    WATER_DAMAGE = "degats_des_eaux"
    FIRE = "incendie"
    WEATHER = "intemperies"
    THEFT = "vol"
    VANDALISM = "vandalisme"
    DEFECT = "malfacons"
    CIVIL_LIABILITY = "rc"
    OTHER = "autre"


class ClaimSeverityEnum(str, Enum):
    MINOR = "mineur"
    MODERATE = "moyen"
    MAJOR = "grave"
    CRITICAL = "tres_grave"


class ClaimBase(BaseModel):
    """Schéma de base pour un sinistre"""
    claim_number: str = Field(..., description="Numéro unique du sinistre")
    external_reference: Optional[str] = None
    contract_id: int = Field(..., description="ID du contrat associé")
    construction_site_id: Optional[int] = None
    claim_type: ClaimTypeEnum
    severity: Optional[ClaimSeverityEnum] = None
    status: ClaimStatusEnum = ClaimStatusEnum.DECLARED
    incident_date: datetime = Field(..., description="Date du sinistre")
    declaration_date: datetime = Field(..., description="Date de déclaration")
    title: str = Field(..., max_length=200, description="Titre du sinistre")
    description: str = Field(..., description="Description détaillée")
    circumstances: Optional[str] = None
    affected_area: Optional[str] = None
    floor: Optional[str] = None
    estimated_amount: Optional[float] = None
    declared_by: Optional[str] = None


class ClaimCreate(ClaimBase):
    """Schéma pour créer un sinistre"""
    pass


class ClaimUpdate(BaseModel):
    """Schéma pour mettre à jour un sinistre"""
    external_reference: Optional[str] = None
    claim_type: Optional[ClaimTypeEnum] = None
    severity: Optional[ClaimSeverityEnum] = None
    status: Optional[ClaimStatusEnum] = None
    acknowledgment_date: Optional[datetime] = None
    settlement_date: Optional[datetime] = None
    closure_date: Optional[datetime] = None
    title: Optional[str] = None
    description: Optional[str] = None
    circumstances: Optional[str] = None
    affected_area: Optional[str] = None
    floor: Optional[str] = None
    estimated_amount: Optional[float] = None
    expert_amount: Optional[float] = None
    franchise_applied: Optional[float] = None
    indemnity_amount: Optional[float] = None
    reserve_amount: Optional[float] = None
    expert_name: Optional[str] = None
    expert_company: Optional[str] = None
    activated_guarantees: Optional[List[str]] = None
    attached_documents: Optional[List[dict]] = None
    has_photos: Optional[bool] = None
    has_expert_report: Optional[bool] = None
    has_repair_quote: Optional[bool] = None
    third_party_involved: Optional[bool] = None
    third_party_info: Optional[dict] = None
    police_report_number: Optional[str] = None
    repair_status: Optional[str] = None
    repair_company: Optional[str] = None
    repair_start_date: Optional[date] = None
    repair_end_date: Optional[date] = None
    internal_notes: Optional[str] = None
    expert_conclusions: Optional[str] = None
    rejection_reason: Optional[str] = None


class Claim(ClaimBase):
    """Schéma complet d'un sinistre"""
    id: int
    acknowledgment_date: Optional[datetime] = None
    settlement_date: Optional[datetime] = None
    closure_date: Optional[datetime] = None
    expert_amount: Optional[float] = None
    franchise_applied: Optional[float] = None
    indemnity_amount: Optional[float] = None
    reserve_amount: Optional[float] = None
    expert_name: Optional[str] = None
    expert_company: Optional[str] = None
    activated_guarantees: Optional[List[str]] = None
    attached_documents: Optional[List[dict]] = None
    has_photos: bool = False
    has_expert_report: bool = False
    has_repair_quote: bool = False
    third_party_involved: bool = False
    third_party_info: Optional[dict] = None
    police_report_number: Optional[str] = None
    repair_status: Optional[str] = None
    repair_company: Optional[str] = None
    repair_start_date: Optional[date] = None
    repair_end_date: Optional[date] = None
    internal_notes: Optional[str] = None
    expert_conclusions: Optional[str] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
