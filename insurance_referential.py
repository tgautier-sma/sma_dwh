"""
Référentiel de codification des contrats d'assurance construction
Ce module définit les garanties, clauses et structures pour les contrats RC/DO
"""
from sqlalchemy import Column, String, Text, Boolean, Integer, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


# =============================================================================
# ÉNUMÉRATIONS
# =============================================================================

class InsuranceTypeEnum(str, enum.Enum):
    """Types de contrats d'assurance construction"""
    DO = "dommages_ouvrage"  # Dommage-Ouvrage
    RCD = "rc_decennale"  # Responsabilité Civile Décennale
    TRC = "tous_risques_chantier"  # Tous Risques Chantier
    CNR = "constructeur_non_realisateur"  # Constructeur Non Réalisateur
    RCMO = "rc_maitre_ouvrage"  # RC Maître d'Ouvrage
    PUC = "police_unique_chantier"  # Police Unique Chantier


class GuaranteeTypeEnum(str, enum.Enum):
    """Types de garanties"""
    MANDATORY = "obligatoire"
    OPTIONAL = "optionnelle"
    COMPLEMENTARY = "complementaire"


class GuaranteeCategoryEnum(str, enum.Enum):
    """Catégories de garanties"""
    DECENNIAL = "decennale"  # Garantie décennale
    BIENNALE = "biennale"  # Garantie biennale (bon fonctionnement)
    PARFAIT_ACHEVEMENT = "parfait_achevement"  # Garantie de parfait achèvement
    DOMMAGES = "dommages"  # Dommages matériels
    RC_PRO = "rc_professionnelle"  # Responsabilité civile professionnelle
    EFFONDREMENT = "effondrement"  # Risque effondrement
    EXISTING = "existants"  # Dommages aux existants
    IMMATERIELS = "immateriels"  # Dommages immatériels


class ClauseCategoryEnum(str, enum.Enum):
    """Catégories de clauses contractuelles"""
    EXCLUSION = "exclusion"
    LIMITATION = "limitation"
    FRANCHISE = "franchise"
    CONDITION = "condition"
    DECLARATION = "declaration"
    RESILIATION = "resiliation"
    SINISTRE = "sinistre"
    PRIME = "prime"
    SUBROGATION = "subrogation"


class BuildingCategoryEnum(str, enum.Enum):
    """Catégories de bâtiments"""
    RESIDENTIAL_INDIVIDUAL = "habitation_individuelle"
    RESIDENTIAL_COLLECTIVE = "habitation_collective"
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industriel"
    AGRICULTURAL = "agricole"
    PUBLIC = "erp"  # Établissement Recevant du Public
    OFFICE = "bureaux"
    MIXED = "mixte"


class WorkCategoryEnum(str, enum.Enum):
    """Catégories de travaux"""
    CONSTRUCTION_NEW = "construction_neuve"
    EXTENSION = "extension"
    RENOVATION_HEAVY = "renovation_lourde"
    RENOVATION_LIGHT = "renovation_legere"
    REHABILITATION = "rehabilitation"
    TRANSFORMATION = "transformation"


class ProfessionCodeEnum(str, enum.Enum):
    """Codes des professions du bâtiment"""
    ARCHITECT = "architecte"
    ENGINEER = "ingenieur"
    ECONOMIST = "economiste"
    CONTROL_BUREAU = "bureau_controle"
    GENERAL_CONTRACTOR = "entreprise_generale"
    MASON = "macon"
    CARPENTER = "charpentier"
    ROOFER = "couvreur"
    PLUMBER = "plombier"
    ELECTRICIAN = "electricien"
    PAINTER = "peintre"
    TILER = "carreleur"
    PLASTERER = "platrier"
    HVAC = "chauffagiste"
    LANDSCAPER = "paysagiste"
    PROMOTER = "promoteur"
    DEVELOPER = "lotisseur"


# =============================================================================
# MODÈLES DE BASE DE DONNÉES
# =============================================================================

class InsuranceContractTypeModel(Base):
    """Types de contrats d'assurance construction"""
    __tablename__ = "ref_insurance_contract_types"
    
    id = Column(String(36), primary_key=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    legal_reference = Column(String(255), nullable=True)  # Référence légale (ex: L241-1 Code des assurances)
    is_mandatory = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    guarantees = relationship("GuaranteeModel", back_populates="contract_type")
    
    def __repr__(self):
        return f"<InsuranceContractType(code={self.code}, name={self.name})>"


class GuaranteeModel(Base):
    """Garanties d'assurance construction"""
    __tablename__ = "ref_guarantees"
    
    id = Column(String(36), primary_key=True)
    code = Column(String(30), unique=True, nullable=False, index=True)
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    
    # Classification
    category = Column(String(50), nullable=False)  # GuaranteeCategoryEnum
    guarantee_type = Column(String(30), nullable=False)  # GuaranteeTypeEnum
    
    # Lien avec le type de contrat
    contract_type_id = Column(String(36), ForeignKey("ref_insurance_contract_types.id"), nullable=True)
    contract_type = relationship("InsuranceContractTypeModel", back_populates="guarantees")
    
    # Durée de la garantie
    duration_years = Column(Integer, nullable=True)  # 1, 2, 10 ans...
    duration_description = Column(String(255), nullable=True)
    
    # Références légales
    legal_reference = Column(String(255), nullable=True)
    legal_articles = Column(JSON, nullable=True)  # Liste des articles de loi
    
    # Paramètres par défaut
    default_ceiling = Column(Float, nullable=True)  # Plafond par défaut
    default_franchise = Column(Float, nullable=True)  # Franchise par défaut
    franchise_type = Column(String(30), nullable=True)  # fixe, proportionnelle, indexée
    
    # Conditions d'application
    conditions = Column(JSON, nullable=True)  # Conditions d'application
    exclusions_default = Column(JSON, nullable=True)  # Exclusions par défaut
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Guarantee(code={self.code}, name={self.name})>"


class ContractClauseModel(Base):
    """Clauses contractuelles d'assurance construction"""
    __tablename__ = "ref_contract_clauses"
    
    id = Column(String(36), primary_key=True)
    code = Column(String(30), unique=True, nullable=False, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)  # Texte complet de la clause
    
    # Classification
    category = Column(String(50), nullable=False)  # ClauseCategoryEnum
    subcategory = Column(String(50), nullable=True)
    
    # Applicabilité
    applies_to_contract_types = Column(JSON, nullable=True)  # Liste des codes de types de contrats
    applies_to_guarantees = Column(JSON, nullable=True)  # Liste des codes de garanties
    
    # Caractéristiques
    is_mandatory = Column(Boolean, default=False)  # Clause obligatoire ou non
    is_negotiable = Column(Boolean, default=True)  # Clause négociable
    priority_order = Column(Integer, default=0)  # Ordre de priorité dans le contrat
    
    # Références
    legal_reference = Column(String(255), nullable=True)
    version = Column(Integer, default=1)
    
    # Variables de la clause (pour personnalisation)
    variables = Column(JSON, nullable=True)  # Ex: {montant_franchise: {type: "float", label: "Montant"}}
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<ContractClause(code={self.code}, title={self.title})>"


class BuildingCategoryModel(Base):
    """Catégories de bâtiments pour la tarification"""
    __tablename__ = "ref_building_categories"
    
    id = Column(String(36), primary_key=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Coefficients de risque
    risk_coefficient = Column(Float, default=1.0)
    technical_complexity = Column(Integer, default=1)  # 1 à 5
    
    # Applicabilité des garanties
    applicable_guarantees = Column(JSON, nullable=True)  # Codes des garanties applicables
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<BuildingCategory(code={self.code}, name={self.name})>"


class WorkCategoryModel(Base):
    """Catégories de travaux"""
    __tablename__ = "ref_work_categories"
    
    id = Column(String(36), primary_key=True)
    code = Column(String(30), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Classification
    parent_code = Column(String(30), nullable=True)  # Pour hiérarchie
    
    # Paramètres de risque
    risk_level = Column(Integer, default=1)  # 1 à 5
    requires_control = Column(Boolean, default=False)  # Contrôle technique obligatoire
    
    # Garanties applicables
    mandatory_guarantees = Column(JSON, nullable=True)
    recommended_guarantees = Column(JSON, nullable=True)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<WorkCategory(code={self.code}, name={self.name})>"


class ProfessionModel(Base):
    """Professions du bâtiment"""
    __tablename__ = "ref_professions"
    
    id = Column(String(36), primary_key=True)
    code = Column(String(30), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Classification
    category = Column(String(50), nullable=True)  # concepteur, réalisateur, contrôleur
    subcategory = Column(String(50), nullable=True)
    
    # Obligations d'assurance
    rc_decennale_required = Column(Boolean, default=True)
    rc_pro_required = Column(Boolean, default=False)
    
    # Activités couvertes
    covered_activities = Column(JSON, nullable=True)  # Liste des activités
    
    # Coefficients
    base_rate_coefficient = Column(Float, default=1.0)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Profession(code={self.code}, name={self.name})>"


class FranchiseGridModel(Base):
    """Grille de franchises par type de garantie"""
    __tablename__ = "ref_franchise_grids"
    
    id = Column(String(36), primary_key=True)
    code = Column(String(30), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    
    # Applicabilité
    guarantee_code = Column(String(30), nullable=False, index=True)
    contract_type_code = Column(String(20), nullable=True)
    
    # Montants
    min_amount = Column(Float, nullable=True)
    max_amount = Column(Float, nullable=True)
    default_amount = Column(Float, nullable=True)
    
    # Type de franchise
    franchise_type = Column(String(30), nullable=False)  # fixe, proportionnelle, indexée
    percentage = Column(Float, nullable=True)  # Si proportionnelle
    index_reference = Column(String(50), nullable=True)  # Si indexée (ex: FFB, BT01)
    
    # Conditions
    conditions = Column(JSON, nullable=True)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<FranchiseGrid(code={self.code}, guarantee={self.guarantee_code})>"


class ExclusionModel(Base):
    """Exclusions types pour les contrats"""
    __tablename__ = "ref_exclusions"
    
    id = Column(String(36), primary_key=True)
    code = Column(String(30), unique=True, nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    
    # Classification
    category = Column(String(50), nullable=False)  # légale, contractuelle, technique
    
    # Applicabilité
    applies_to_guarantees = Column(JSON, nullable=True)  # Codes des garanties
    applies_to_contract_types = Column(JSON, nullable=True)  # Codes des contrats
    
    # Caractéristiques
    is_legal = Column(Boolean, default=False)  # Exclusion légale non négociable
    legal_reference = Column(String(255), nullable=True)
    can_be_racheted = Column(Boolean, default=False)  # Peut être rachetée
    rachat_conditions = Column(Text, nullable=True)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Exclusion(code={self.code}, title={self.title})>"


# =============================================================================
# DONNÉES DE RÉFÉRENTIEL PAR DÉFAUT
# =============================================================================

DEFAULT_CONTRACT_TYPES = [
    {
        "code": "DO",
        "name": "Dommage-Ouvrage",
        "description": "Assurance obligatoire permettant le préfinancement des travaux de réparation des désordres de nature décennale sans attendre la recherche des responsabilités",
        "legal_reference": "L242-1 Code des assurances",
        "is_mandatory": True
    },
    {
        "code": "RCD",
        "name": "Responsabilité Civile Décennale",
        "description": "Assurance obligatoire couvrant la responsabilité décennale des constructeurs pour les dommages compromettant la solidité de l'ouvrage ou le rendant impropre à sa destination",
        "legal_reference": "L241-1 Code des assurances",
        "is_mandatory": True
    },
    {
        "code": "TRC",
        "name": "Tous Risques Chantier",
        "description": "Assurance couvrant les dommages matériels survenant pendant la période de construction",
        "legal_reference": None,
        "is_mandatory": False
    },
    {
        "code": "CNR",
        "name": "Constructeur Non Réalisateur",
        "description": "Assurance pour les personnes faisant construire sans réaliser eux-mêmes les travaux (vendeur d'immeuble à construire)",
        "legal_reference": "L241-2 Code des assurances",
        "is_mandatory": True
    },
    {
        "code": "RCMO",
        "name": "RC Maître d'Ouvrage",
        "description": "Assurance couvrant la responsabilité civile du maître d'ouvrage pendant les travaux",
        "legal_reference": None,
        "is_mandatory": False
    },
    {
        "code": "PUC",
        "name": "Police Unique de Chantier",
        "description": "Police regroupant plusieurs garanties pour l'ensemble des intervenants d'un chantier",
        "legal_reference": None,
        "is_mandatory": False
    }
]


DEFAULT_GUARANTEES = [
    # Garanties DO
    {
        "code": "DO-DEC",
        "name": "Garantie Dommages Décennaux DO",
        "description": "Préfinancement des dommages de nature décennale (solidité et impropriété à destination)",
        "category": "decennale",
        "guarantee_type": "obligatoire",
        "contract_type_code": "DO",
        "duration_years": 10,
        "legal_reference": "Art. 1792 et 1792-2 Code civil",
        "default_franchise": 1500
    },
    {
        "code": "DO-EFF",
        "name": "Garantie Effondrement avant réception",
        "description": "Couverture des effondrements survenant avant la réception des travaux",
        "category": "effondrement",
        "guarantee_type": "optionnelle",
        "contract_type_code": "DO",
        "duration_years": None,
        "default_franchise": 2500
    },
    {
        "code": "DO-EXIST",
        "name": "Dommages aux existants",
        "description": "Couverture des dommages causés aux parties existantes du bâtiment lors des travaux",
        "category": "existants",
        "guarantee_type": "optionnelle",
        "contract_type_code": "DO",
        "duration_years": 10,
        "default_franchise": 3000
    },
    {
        "code": "DO-IMMAT",
        "name": "Dommages immatériels consécutifs",
        "description": "Couverture des préjudices immatériels résultant des dommages matériels garantis",
        "category": "immateriels",
        "guarantee_type": "optionnelle",
        "contract_type_code": "DO",
        "duration_years": 10,
        "default_franchise": 5000
    },
    
    # Garanties RCD
    {
        "code": "RCD-DEC",
        "name": "Responsabilité Décennale",
        "description": "Couverture de la responsabilité décennale du constructeur pour les dommages compromettant la solidité ou l'impropriété à destination",
        "category": "decennale",
        "guarantee_type": "obligatoire",
        "contract_type_code": "RCD",
        "duration_years": 10,
        "legal_reference": "Art. 1792 Code civil",
        "default_franchise": 1500
    },
    {
        "code": "RCD-BIEN",
        "name": "Garantie Biennale de bon fonctionnement",
        "description": "Couverture des désordres affectant les éléments d'équipement dissociables pendant 2 ans",
        "category": "biennale",
        "guarantee_type": "obligatoire",
        "contract_type_code": "RCD",
        "duration_years": 2,
        "legal_reference": "Art. 1792-3 Code civil",
        "default_franchise": 500
    },
    {
        "code": "RCD-PA",
        "name": "Garantie de Parfait Achèvement",
        "description": "Couverture des défauts de conformité et malfaçons pendant 1 an après réception",
        "category": "parfait_achevement",
        "guarantee_type": "complementaire",
        "contract_type_code": "RCD",
        "duration_years": 1,
        "legal_reference": "Art. 1792-6 Code civil",
        "default_franchise": 300
    },
    {
        "code": "RCD-EXIST",
        "name": "Dommages aux existants RCD",
        "description": "Dommages causés aux parties existantes non incluses dans les travaux",
        "category": "existants",
        "guarantee_type": "optionnelle",
        "contract_type_code": "RCD",
        "duration_years": 10,
        "default_franchise": 2000
    },
    {
        "code": "RCD-IMMAT",
        "name": "Dommages immatériels RCD",
        "description": "Préjudices immatériels consécutifs à un dommage matériel garanti",
        "category": "immateriels",
        "guarantee_type": "optionnelle",
        "contract_type_code": "RCD",
        "duration_years": 10,
        "default_franchise": 3000
    },
    {
        "code": "RCD-RCPRO",
        "name": "RC Professionnelle exploitation",
        "description": "Responsabilité civile professionnelle pendant l'exécution des travaux",
        "category": "rc_professionnelle",
        "guarantee_type": "complementaire",
        "contract_type_code": "RCD",
        "duration_years": None,
        "default_franchise": 1000
    },
    
    # Garanties TRC
    {
        "code": "TRC-DOM",
        "name": "Dommages à l'ouvrage en construction",
        "description": "Couverture des dommages matériels à l'ouvrage pendant la construction",
        "category": "dommages",
        "guarantee_type": "obligatoire",
        "contract_type_code": "TRC",
        "duration_years": None,
        "default_franchise": 5000
    },
    {
        "code": "TRC-MAT",
        "name": "Dommages aux matériaux et équipements",
        "description": "Couverture des dommages aux matériaux stockés sur le chantier",
        "category": "dommages",
        "guarantee_type": "optionnelle",
        "contract_type_code": "TRC",
        "duration_years": None,
        "default_franchise": 2500
    },
    {
        "code": "TRC-MAINT",
        "name": "Période de maintenance",
        "description": "Extension de garantie pendant la période de maintenance post-réception",
        "category": "dommages",
        "guarantee_type": "optionnelle",
        "contract_type_code": "TRC",
        "duration_years": 1,
        "default_franchise": 5000
    }
]


DEFAULT_CLAUSES = [
    # Clauses d'exclusion
    {
        "code": "EXCL-001",
        "title": "Exclusion des dommages résultant de l'usure normale",
        "content": "Sont exclus de la garantie les dommages résultant de l'usure normale des ouvrages, du défaut d'entretien ou de l'usage anormal de l'ouvrage par l'assuré ou les occupants.",
        "category": "exclusion",
        "is_mandatory": True,
        "is_negotiable": False,
        "legal_reference": "Art. L113-1 Code des assurances"
    },
    {
        "code": "EXCL-002",
        "title": "Exclusion des dommages intentionnels",
        "content": "Sont exclus de la garantie les dommages causés intentionnellement par l'assuré, le bénéficiaire, ou avec leur complicité.",
        "category": "exclusion",
        "is_mandatory": True,
        "is_negotiable": False,
        "legal_reference": "Art. L113-1 Code des assurances"
    },
    {
        "code": "EXCL-003",
        "title": "Exclusion des dommages nucléaires",
        "content": "Sont exclus les dommages ou l'aggravation des dommages causés par des armes ou engins destinés à exploser par modification de structure du noyau de l'atome, ou par tout combustible nucléaire.",
        "category": "exclusion",
        "is_mandatory": True,
        "is_negotiable": False
    },
    {
        "code": "EXCL-004",
        "title": "Exclusion des dommages de guerre",
        "content": "Sont exclus les dommages résultant de faits de guerre étrangère, de guerre civile, d'émeutes ou de mouvements populaires.",
        "category": "exclusion",
        "is_mandatory": True,
        "is_negotiable": False
    },
    {
        "code": "EXCL-005",
        "title": "Exclusion défaut de conformité",
        "content": "Sont exclus les défauts de conformité qui n'entraînent pas de désordre de nature décennale, sauf option contraire souscrite.",
        "category": "exclusion",
        "is_mandatory": False,
        "is_negotiable": True
    },
    {
        "code": "EXCL-006",
        "title": "Exclusion travaux sans assurance",
        "content": "Sont exclus les dommages dont l'origine provient de travaux réalisés par des entreprises ne justifiant pas d'une assurance de responsabilité décennale valide.",
        "category": "exclusion",
        "is_mandatory": False,
        "is_negotiable": True
    },
    
    # Clauses de franchise
    {
        "code": "FRAN-001",
        "title": "Franchise absolue",
        "content": "Une franchise absolue de {montant_franchise} euros reste à la charge de l'assuré pour tout sinistre. Cette franchise n'est pas récupérable auprès des responsables.",
        "category": "franchise",
        "is_mandatory": False,
        "is_negotiable": True,
        "variables": {"montant_franchise": {"type": "float", "label": "Montant de la franchise", "default": 1500}}
    },
    {
        "code": "FRAN-002",
        "title": "Franchise proportionnelle",
        "content": "Une franchise égale à {pourcentage}% du montant du sinistre avec un minimum de {min_franchise} euros et un maximum de {max_franchise} euros reste à la charge de l'assuré.",
        "category": "franchise",
        "is_mandatory": False,
        "is_negotiable": True,
        "variables": {
            "pourcentage": {"type": "float", "label": "Pourcentage", "default": 10},
            "min_franchise": {"type": "float", "label": "Minimum", "default": 1500},
            "max_franchise": {"type": "float", "label": "Maximum", "default": 15000}
        }
    },
    {
        "code": "FRAN-003",
        "title": "Franchise indexée",
        "content": "La franchise est indexée sur l'indice {indice_reference} publié par la Fédération Française du Bâtiment. Le montant de base est de {montant_base} euros à la date de référence du {date_reference}.",
        "category": "franchise",
        "is_mandatory": False,
        "is_negotiable": True,
        "variables": {
            "indice_reference": {"type": "string", "label": "Indice de référence", "default": "BT01"},
            "montant_base": {"type": "float", "label": "Montant de base", "default": 1500},
            "date_reference": {"type": "date", "label": "Date de référence", "default": "01/01/2024"}
        }
    },
    
    # Clauses de déclaration
    {
        "code": "DECL-001",
        "title": "Déclaration du risque",
        "content": "L'assuré s'engage à déclarer exactement les circonstances connues de lui permettant d'apprécier les risques. Toute réticence ou fausse déclaration intentionnelle entraîne la nullité du contrat conformément à l'article L113-8 du Code des assurances.",
        "category": "declaration",
        "is_mandatory": True,
        "is_negotiable": False,
        "legal_reference": "Art. L113-8 Code des assurances"
    },
    {
        "code": "DECL-002",
        "title": "Déclaration d'aggravation du risque",
        "content": "L'assuré s'engage à déclarer toute circonstance nouvelle de nature à aggraver le risque dans un délai de 15 jours, notamment tout changement dans la nature des travaux, les conditions d'exécution ou les intervenants.",
        "category": "declaration",
        "is_mandatory": True,
        "is_negotiable": False,
        "legal_reference": "Art. L113-2 Code des assurances"
    },
    
    # Clauses de sinistre
    {
        "code": "SINI-001",
        "title": "Déclaration de sinistre",
        "content": "L'assuré doit déclarer tout sinistre dans un délai de {delai_declaration} jours à compter de sa connaissance, par lettre recommandée avec accusé de réception ou par déclaration électronique sur l'espace client.",
        "category": "sinistre",
        "is_mandatory": True,
        "is_negotiable": True,
        "legal_reference": "Art. L113-2 Code des assurances",
        "variables": {"delai_declaration": {"type": "integer", "label": "Délai en jours", "default": 5}}
    },
    {
        "code": "SINI-002",
        "title": "Conservation des éléments de preuve",
        "content": "L'assuré s'engage à conserver les éléments de preuve du sinistre et à faciliter les constatations de l'expert désigné par l'assureur. Il ne doit procéder à aucune modification, réparation ou remplacement avant accord de l'assureur, sauf mesures conservatoires urgentes.",
        "category": "sinistre",
        "is_mandatory": True,
        "is_negotiable": False
    },
    {
        "code": "SINI-003",
        "title": "Expertise amiable contradictoire",
        "content": "En cas de désaccord sur l'évaluation des dommages, il sera procédé à une expertise amiable contradictoire. Chaque partie désigne son expert. En cas de désaccord entre les experts, un tiers expert est désigné d'un commun accord ou par le président du tribunal judiciaire.",
        "category": "sinistre",
        "is_mandatory": False,
        "is_negotiable": True
    },
    
    # Clauses de résiliation
    {
        "code": "RESI-001",
        "title": "Résiliation pour non-paiement de prime",
        "content": "À défaut de paiement de la prime dans les {delai_paiement} jours de son échéance, l'assureur peut suspendre la garantie après mise en demeure restée infructueuse pendant {delai_suspension} jours, puis résilier le contrat {delai_resiliation} jours après la suspension.",
        "category": "resiliation",
        "is_mandatory": True,
        "is_negotiable": False,
        "legal_reference": "Art. L113-3 Code des assurances",
        "variables": {
            "delai_paiement": {"type": "integer", "label": "Délai paiement", "default": 10},
            "delai_suspension": {"type": "integer", "label": "Délai suspension", "default": 30},
            "delai_resiliation": {"type": "integer", "label": "Délai résiliation", "default": 10}
        }
    },
    {
        "code": "RESI-002",
        "title": "Résiliation après sinistre",
        "content": "L'assureur peut résilier le contrat après sinistre, par lettre recommandée avec préavis d'un mois. Cette faculté ne peut être exercée qu'à la notification de l'indemnité ou du refus de prise en charge.",
        "category": "resiliation",
        "is_mandatory": False,
        "is_negotiable": True,
        "legal_reference": "Art. L113-4 Code des assurances"
    },
    
    # Clauses de limitation
    {
        "code": "LIMIT-001",
        "title": "Plafond de garantie par sinistre",
        "content": "Le montant maximum de l'indemnité est limité à {plafond_sinistre} euros par sinistre, tous préjudices confondus.",
        "category": "limitation",
        "is_mandatory": False,
        "is_negotiable": True,
        "variables": {"plafond_sinistre": {"type": "float", "label": "Plafond par sinistre", "default": 5000000}}
    },
    {
        "code": "LIMIT-002",
        "title": "Plafond de garantie annuel",
        "content": "Le montant maximum des indemnités est limité à {plafond_annuel} euros par année d'assurance, tous sinistres confondus.",
        "category": "limitation",
        "is_mandatory": False,
        "is_negotiable": True,
        "variables": {"plafond_annuel": {"type": "float", "label": "Plafond annuel", "default": 10000000}}
    },
    {
        "code": "LIMIT-003",
        "title": "Limitation dommages immatériels",
        "content": "Les dommages immatériels consécutifs sont garantis dans la limite de {plafond_immat} euros par sinistre et {plafond_immat_annuel} euros par année d'assurance.",
        "category": "limitation",
        "is_mandatory": False,
        "is_negotiable": True,
        "variables": {
            "plafond_immat": {"type": "float", "label": "Plafond immatériels/sinistre", "default": 500000},
            "plafond_immat_annuel": {"type": "float", "label": "Plafond immatériels/an", "default": 1000000}
        }
    },
    
    # Clauses de subrogation
    {
        "code": "SUBR-001",
        "title": "Subrogation légale",
        "content": "Conformément à l'article L121-12 du Code des assurances, l'assureur qui a payé l'indemnité est subrogé dans les droits et actions de l'assuré contre les tiers responsables.",
        "category": "subrogation",
        "is_mandatory": True,
        "is_negotiable": False,
        "legal_reference": "Art. L121-12 Code des assurances"
    },
    {
        "code": "SUBR-002",
        "title": "Renonciation à recours",
        "content": "L'assureur renonce à exercer tout recours contre {liste_personnes}. Cette renonciation ne s'applique pas en cas de malveillance.",
        "category": "subrogation",
        "is_mandatory": False,
        "is_negotiable": True,
        "variables": {"liste_personnes": {"type": "string", "label": "Personnes bénéficiaires", "default": "les locataires et occupants des lieux"}}
    },
    
    # Clauses de prime
    {
        "code": "PRIM-001",
        "title": "Révision de prime",
        "content": "La prime est révisable annuellement en fonction de l'évolution de l'indice {indice_prime}. La révision s'applique à chaque échéance anniversaire du contrat.",
        "category": "prime",
        "is_mandatory": False,
        "is_negotiable": True,
        "variables": {"indice_prime": {"type": "string", "label": "Indice de révision", "default": "FFB"}}
    },
    {
        "code": "PRIM-002",
        "title": "Prime provisionnelle et régularisation",
        "content": "La prime est calculée provisionnellement sur le coût prévisionnel des travaux déclaré de {cout_previsionnel} euros. Une régularisation sera effectuée sur la base du coût définitif dans les {delai_regul} mois suivant la réception.",
        "category": "prime",
        "is_mandatory": False,
        "is_negotiable": True,
        "variables": {
            "cout_previsionnel": {"type": "float", "label": "Coût prévisionnel", "default": 0},
            "delai_regul": {"type": "integer", "label": "Délai régularisation (mois)", "default": 6}
        }
    },
    
    # Clauses de condition
    {
        "code": "COND-001",
        "title": "Attestation d'assurance des intervenants",
        "content": "La garantie est subordonnée à l'obtention, avant le début des travaux, des attestations d'assurance de responsabilité décennale de tous les intervenants à l'acte de construire.",
        "category": "condition",
        "is_mandatory": False,
        "is_negotiable": True
    },
    {
        "code": "COND-002",
        "title": "Contrôle technique obligatoire",
        "content": "Pour les ouvrages soumis à contrôle technique obligatoire (art. L111-23 CCH), la garantie est subordonnée à la mission d'un contrôleur technique agréé portant au minimum sur la solidité des ouvrages et la sécurité des personnes.",
        "category": "condition",
        "is_mandatory": True,
        "is_negotiable": False,
        "legal_reference": "Art. L111-23 CCH"
    },
    {
        "code": "COND-003",
        "title": "Respect des règles de l'art",
        "content": "La garantie est subordonnée au respect des règles de l'art, des normes en vigueur (DTU, Eurocodes, etc.) et des avis techniques pour les procédés non traditionnels.",
        "category": "condition",
        "is_mandatory": True,
        "is_negotiable": False
    }
]


DEFAULT_BUILDING_CATEGORIES = [
    {"code": "HAB-IND", "name": "Habitation individuelle", "description": "Maison individuelle isolée ou jumelée", "risk_coefficient": 1.0, "technical_complexity": 1},
    {"code": "HAB-COL", "name": "Habitation collective", "description": "Immeuble d'habitation collectif", "risk_coefficient": 1.2, "technical_complexity": 2},
    {"code": "COM", "name": "Commercial", "description": "Local commercial, centre commercial", "risk_coefficient": 1.3, "technical_complexity": 2},
    {"code": "IND", "name": "Industriel", "description": "Bâtiment industriel, usine, entrepôt", "risk_coefficient": 1.5, "technical_complexity": 3},
    {"code": "AGR", "name": "Agricole", "description": "Bâtiment agricole, hangar, stabulation", "risk_coefficient": 1.1, "technical_complexity": 2},
    {"code": "ERP", "name": "ERP", "description": "Établissement recevant du public", "risk_coefficient": 1.4, "technical_complexity": 3},
    {"code": "BUR", "name": "Bureaux", "description": "Immeuble de bureaux", "risk_coefficient": 1.2, "technical_complexity": 2},
    {"code": "MIX", "name": "Mixte", "description": "Bâtiment à usage mixte", "risk_coefficient": 1.3, "technical_complexity": 3},
    {"code": "IGH", "name": "IGH", "description": "Immeuble de grande hauteur (>28m hab, >50m autres)", "risk_coefficient": 2.0, "technical_complexity": 5},
    {"code": "OAR", "name": "Ouvrage d'art", "description": "Pont, tunnel, barrage", "risk_coefficient": 2.5, "technical_complexity": 5}
]


DEFAULT_WORK_CATEGORIES = [
    {"code": "CONST-NEUF", "name": "Construction neuve", "description": "Construction d'un bâtiment neuf", "risk_level": 2, "requires_control": False},
    {"code": "EXT", "name": "Extension", "description": "Agrandissement d'un bâtiment existant", "risk_level": 3, "requires_control": False},
    {"code": "RENOV-L", "name": "Rénovation légère", "description": "Travaux de rénovation sans toucher à la structure", "risk_level": 1, "requires_control": False},
    {"code": "RENOV-H", "name": "Rénovation lourde", "description": "Travaux de rénovation touchant la structure", "risk_level": 4, "requires_control": True},
    {"code": "REHAB", "name": "Réhabilitation", "description": "Remise en état complète avec changement d'usage possible", "risk_level": 4, "requires_control": True},
    {"code": "TRANSF", "name": "Transformation", "description": "Changement de destination du bâtiment", "risk_level": 3, "requires_control": False},
    {"code": "SURES", "name": "Surélévation", "description": "Ajout d'étages sur un bâtiment existant", "risk_level": 5, "requires_control": True},
    {"code": "SOUS-SOL", "name": "Travaux en sous-sol", "description": "Excavation, sous-œuvre, parking souterrain", "risk_level": 5, "requires_control": True}
]


DEFAULT_PROFESSIONS = [
    {"code": "ARCHI", "name": "Architecte", "category": "concepteur", "rc_decennale_required": True, "rc_pro_required": True},
    {"code": "ING-STRUCT", "name": "Ingénieur structure", "category": "concepteur", "rc_decennale_required": True, "rc_pro_required": True},
    {"code": "ING-FLUID", "name": "Ingénieur fluides", "category": "concepteur", "rc_decennale_required": True, "rc_pro_required": True},
    {"code": "ECO", "name": "Économiste de la construction", "category": "concepteur", "rc_decennale_required": True, "rc_pro_required": True},
    {"code": "BC", "name": "Bureau de contrôle", "category": "controleur", "rc_decennale_required": True, "rc_pro_required": True},
    {"code": "CSPS", "name": "Coordonnateur SPS", "category": "controleur", "rc_decennale_required": False, "rc_pro_required": True},
    {"code": "ENT-GEN", "name": "Entreprise générale", "category": "realisateur", "rc_decennale_required": True, "rc_pro_required": False},
    {"code": "MAC", "name": "Maçon", "category": "realisateur", "rc_decennale_required": True, "rc_pro_required": False},
    {"code": "CHARP", "name": "Charpentier", "category": "realisateur", "rc_decennale_required": True, "rc_pro_required": False},
    {"code": "COUV", "name": "Couvreur", "category": "realisateur", "rc_decennale_required": True, "rc_pro_required": False},
    {"code": "PLOMB", "name": "Plombier", "category": "realisateur", "rc_decennale_required": True, "rc_pro_required": False},
    {"code": "ELEC", "name": "Électricien", "category": "realisateur", "rc_decennale_required": True, "rc_pro_required": False},
    {"code": "CHAUF", "name": "Chauffagiste/Climaticien", "category": "realisateur", "rc_decennale_required": True, "rc_pro_required": False},
    {"code": "MENU", "name": "Menuisier", "category": "realisateur", "rc_decennale_required": True, "rc_pro_required": False},
    {"code": "CARR", "name": "Carreleur", "category": "realisateur", "rc_decennale_required": True, "rc_pro_required": False},
    {"code": "PEINT", "name": "Peintre", "category": "realisateur", "rc_decennale_required": True, "rc_pro_required": False},
    {"code": "PLAT", "name": "Plâtrier/Plaquiste", "category": "realisateur", "rc_decennale_required": True, "rc_pro_required": False},
    {"code": "ETANCH", "name": "Étancheur", "category": "realisateur", "rc_decennale_required": True, "rc_pro_required": False},
    {"code": "PROM", "name": "Promoteur immobilier", "category": "maitre_ouvrage", "rc_decennale_required": True, "rc_pro_required": True},
    {"code": "CMI", "name": "Constructeur de maisons individuelles", "category": "realisateur", "rc_decennale_required": True, "rc_pro_required": False}
]


DEFAULT_EXCLUSIONS = [
    {
        "code": "EXC-USURE",
        "title": "Usure normale et vétusté",
        "description": "Dommages résultant de l'usure normale, de la vétusté ou du défaut d'entretien de l'ouvrage",
        "category": "légale",
        "is_legal": True,
        "can_be_racheted": False
    },
    {
        "code": "EXC-INTENT",
        "title": "Dommages intentionnels",
        "description": "Dommages causés intentionnellement par l'assuré ou avec sa complicité",
        "category": "légale",
        "is_legal": True,
        "can_be_racheted": False
    },
    {
        "code": "EXC-GUERRE",
        "title": "Faits de guerre",
        "description": "Dommages résultant de faits de guerre, guerre civile, insurrection",
        "category": "légale",
        "is_legal": True,
        "can_be_racheted": False
    },
    {
        "code": "EXC-NUCLEAIRE",
        "title": "Risques nucléaires",
        "description": "Dommages d'origine nucléaire ou liés à la radioactivité",
        "category": "légale",
        "is_legal": True,
        "can_be_racheted": False
    },
    {
        "code": "EXC-ESTH",
        "title": "Dommages purement esthétiques",
        "description": "Dommages de nature purement esthétique n'affectant pas la solidité ou la destination",
        "category": "contractuelle",
        "is_legal": False,
        "can_be_racheted": True,
        "rachat_conditions": "Souscription d'une garantie complémentaire avec surprime"
    },
    {
        "code": "EXC-EQUIP-MOB",
        "title": "Équipements mobiliers",
        "description": "Dommages aux équipements professionnels ou mobiliers non incorporés à l'ouvrage",
        "category": "contractuelle",
        "is_legal": False,
        "can_be_racheted": True,
        "rachat_conditions": "Extension de garantie spécifique"
    },
    {
        "code": "EXC-POLLU",
        "title": "Pollution et contamination",
        "description": "Dommages de pollution, contamination ou atteinte à l'environnement",
        "category": "contractuelle",
        "is_legal": False,
        "can_be_racheted": True,
        "rachat_conditions": "Souscription d'une garantie pollution spécifique"
    },
    {
        "code": "EXC-AMIANTE",
        "title": "Amiante préexistant",
        "description": "Dommages liés à la présence d'amiante préexistante aux travaux",
        "category": "technique",
        "is_legal": False,
        "can_be_racheted": True,
        "rachat_conditions": "Diagnostic amiante préalable et mesures de traitement"
    },
    {
        "code": "EXC-TERR",
        "title": "Vice du sol",
        "description": "Dommages dus à un vice du sol non décelable par une étude géotechnique normalement diligente",
        "category": "technique",
        "is_legal": False,
        "can_be_racheted": True,
        "rachat_conditions": "Réalisation d'une étude géotechnique G2 minimum"
    },
    {
        "code": "EXC-RETRAIT",
        "title": "Retrait-gonflement des argiles",
        "description": "Dommages causés par le phénomène de retrait-gonflement des argiles",
        "category": "technique",
        "is_legal": False,
        "can_be_racheted": True,
        "rachat_conditions": "Respect des préconisations de l'étude de sol et des règles de construction adaptées"
    }
]
