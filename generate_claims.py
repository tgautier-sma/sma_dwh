"""
Script de génération de sinistres construction
Usage:
    python generate_claims.py --create --count 10  # Créer 10 sinistres
    python generate_claims.py --clean  # Supprimer tous les sinistres
"""
import argparse
import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from faker import Faker

from app.database import SessionLocal
from app.models import ClaimModel, ClientContractModel, ConstructionSiteModel

# Initialiser Faker en français
fake = Faker('fr_FR')

# Données de référence
CLAIM_TYPES = [
    "structurel", "degats_des_eaux", "incendie", "intemperies",
    "vol", "vandalisme", "malfacons", "rc", "autre"
]

CLAIM_STATUS = [
    "declare", "pris_en_compte", "en_cours_expertise", "attente_pieces",
    "accepte", "refuse", "regle", "cloture"
]

SEVERITIES = ["mineur", "moyen", "grave", "tres_grave"]

# Templates de sinistres par type
CLAIM_TEMPLATES = {
    "structurel": {
        "titles": [
            "Fissures structurelles sur mur porteur",
            "Affaissement de la dalle du RDC",
            "Désordres sur fondations",
            "Déformation de la charpente",
            "Lézardes importantes sur façade"
        ],
        "areas": ["Façade principale", "Mur porteur Est", "Fondations", "Dalle RDC", "Charpente"],
        "guarantees": ["GAR_DEC_01", "GAR_STRUCT_01"]
    },
    "degats_des_eaux": {
        "titles": [
            "Infiltration d'eau par la toiture",
            "Fuite de canalisation",
            "Dégâts des eaux suite à rupture de conduite",
            "Infiltration par façade",
            "Débordement de gouttière"
        ],
        "areas": ["Toiture", "Salle de bains", "Cuisine", "Cave", "Façade Nord"],
        "guarantees": ["GAR_BIEN_01", "GAR_INST_01"]
    },
    "incendie": {
        "titles": [
            "Incendie dans le local technique",
            "Début d'incendie électrique",
            "Incendie de l'atelier",
            "Feu de chantier",
            "Court-circuit ayant provoqué un incendie"
        ],
        "areas": ["Local technique", "Atelier", "Bureau", "Chantier", "Salle électrique"],
        "guarantees": ["GAR_INC_01", "GAR_BIEN_02"]
    },
    "intemperies": {
        "titles": [
            "Dégâts suite à tempête",
            "Inondation du sous-sol",
            "Dommages causés par la grêle",
            "Arrachement de toiture par vent violent",
            "Infiltrations suite à fortes pluies"
        ],
        "areas": ["Toiture", "Sous-sol", "Façade", "Bardage", "Menuiseries extérieures"],
        "guarantees": ["GAR_TEMP_01", "GAR_BIEN_01"]
    },
    "vol": {
        "titles": [
            "Vol de matériaux sur chantier",
            "Vol d'équipements",
            "Cambriolage du local de stockage",
            "Disparition d'outillage",
            "Vol de métaux (cuivre, zinc)"
        ],
        "areas": ["Chantier", "Local de stockage", "Container", "Zone de stockage", "Atelier"],
        "guarantees": ["GAR_VOL_01"]
    },
    "vandalisme": {
        "titles": [
            "Dégradations volontaires sur chantier",
            "Tags sur façade",
            "Bris de vitrages",
            "Destruction d'équipements",
            "Sabotage du chantier"
        ],
        "areas": ["Façade", "Vitrines", "Chantier", "Local technique", "Zone d'accès"],
        "guarantees": ["GAR_VAN_01"]
    },
    "malfacons": {
        "titles": [
            "Malfaçons dans l'isolation",
            "Défaut d'étanchéité",
            "Non-conformité des travaux d'électricité",
            "Mauvaise pose de la toiture",
            "Défaut dans les travaux de plomberie"
        ],
        "areas": ["Isolation", "Toiture", "Installation électrique", "Plomberie", "Façade"],
        "guarantees": ["GAR_DEC_01", "GAR_PF_01"]
    },
    "rc": {
        "titles": [
            "Dommages causés à un tiers",
            "Blessure d'un passant sur chantier",
            "Dégâts matériels chez le voisin",
            "Chute d'échafaudage sur véhicule",
            "Projection de gravats"
        ],
        "areas": ["Chantier", "Voie publique", "Propriété voisine", "Zone d'échafaudage", "Accès chantier"],
        "guarantees": ["GAR_RC_01", "GAR_RCMO_01"]
    },
    "autre": {
        "titles": [
            "Dommage non classé",
            "Sinistre multiple",
            "Incident technique",
            "Dégradation diverse",
            "Problème spécifique"
        ],
        "areas": ["Divers", "Multiple", "À déterminer"],
        "guarantees": ["GAR_BIEN_01"]
    }
}


def generate_claim_number(db: Session) -> str:
    """Génère un numéro de sinistre unique"""
    year = datetime.now().year
    count = db.query(ClaimModel).count() + 1
    return f"SIN-{year}-{count:05d}"


def generate_claim_description(claim_type: str) -> tuple:
    """Génère une description détaillée du sinistre"""
    template = CLAIM_TEMPLATES.get(claim_type, CLAIM_TEMPLATES["autre"])
    
    title = random.choice(template["titles"])
    area = random.choice(template["areas"])
    guarantees = template["guarantees"]
    
    descriptions = {
        "structurel": f"Apparition de {random.choice(['fissures', 'lézardes', 'déformations', 'affaissements'])} "
                     f"d'une {random.choice(['largeur', 'profondeur'])} de {random.randint(5, 50)}mm. "
                     f"Les désordres sont visibles {random.choice(['en façade', 'en intérieur', 'sur plusieurs niveaux'])}. "
                     f"Expertise technique nécessaire pour déterminer l'origine et l'ampleur des dommages.",
        
        "degats_des_eaux": f"Constatation d'une {random.choice(['infiltration', 'fuite', 'inondation'])} "
                          f"ayant causé des dégâts sur environ {random.randint(5, 50)}m². "
                          f"Présence de {random.choice(['traces d\'humidité', 'moisissures', 'détérioration des revêtements'])}. "
                          f"Origine : {random.choice(['toiture', 'canalisation', 'façade', 'installation sanitaire'])}.",
        
        "incendie": f"Incendie survenu le {fake.date_between(start_date='-30d', end_date='today').strftime('%d/%m/%Y')}. "
                   f"Surface touchée : environ {random.randint(10, 100)}m². "
                   f"Dégâts constatés : {random.choice(['fumée', 'flammes', 'court-circuit'])}. "
                   f"Intervention des pompiers effectuée. Dépôt de plainte le cas échéant.",
        
        "intemperies": f"Suite à {random.choice(['tempête', 'fortes pluies', 'grêle', 'vent violent'])} "
                      f"du {fake.date_between(start_date='-60d', end_date='today').strftime('%d/%m/%Y')}, "
                      f"constatation de dommages importants. "
                      f"Éléments endommagés : {random.choice(['toiture', 'bardage', 'menuiseries', 'installations extérieures'])}.",
        
        "vol": f"Constatation d'un vol de {random.choice(['matériaux', 'équipements', 'outillage', 'métaux'])} "
              f"sur le site. Valeur estimée : {random.randint(500, 20000)}€. "
              f"Dépôt de plainte effectué. Mesures de sécurité à renforcer.",
        
        "vandalisme": f"Actes de vandalisme constatés le {fake.date_between(start_date='-30d', end_date='today').strftime('%d/%m/%Y')}. "
                     f"Nature des dégradations : {random.choice(['tags', 'bris', 'destruction', 'détérioration'])}. "
                     f"Dépôt de plainte en cours.",
        
        "malfacons": f"Constatation de malfaçons concernant {random.choice(['l\'isolation', 'l\'étanchéité', 'les finitions', 'les installations'])}. "
                    f"Non-conformité avec les normes {random.choice(['DTU', 'NF', 'RT2012', 'RE2020'])}. "
                    f"Expertise technique requise pour évaluation des travaux de reprise.",
        
        "rc": f"Incident survenu le {fake.date_between(start_date='-90d', end_date='today').strftime('%d/%m/%Y')} "
             f"ayant causé des dommages à {random.choice(['un tiers', 'un voisin', 'un passant', 'un véhicule'])}. "
             f"Dommages : {random.choice(['matériels', 'corporels', 'mixtes'])}. "
             f"Constat établi. Déclaration à l'assurance responsabilité civile.",
        
        "autre": f"Sinistre particulier nécessitant une analyse approfondie. "
                f"Circonstances spécifiques à documenter. "
                f"Évaluation en cours."
    }
    
    description = descriptions.get(claim_type, "Description du sinistre à compléter.")
    
    circumstances = f"Le sinistre est survenu dans le contexte de {random.choice(['travaux en cours', 'phase de réception', 'exploitation du bâtiment', 'période de garantie'])}. " \
                   f"Conditions météo au moment des faits : {random.choice(['normales', 'pluvieuses', 'venteuses', 'orageuses'])}. " \
                   f"Aucun antécédent similaire constaté sur ce chantier."
    
    return title, description, circumstances, area, guarantees


def calculate_amounts(severity: str, claim_type: str) -> dict:
    """Calcule les montants selon la gravité"""
    base_amounts = {
        "mineur": (1000, 10000),
        "moyen": (10000, 50000),
        "grave": (50000, 200000),
        "tres_grave": (200000, 1000000)
    }
    
    min_amount, max_amount = base_amounts.get(severity, (5000, 50000))
    estimated = random.uniform(min_amount, max_amount)
    
    # L'expert peut estimer différemment
    expert_variation = random.uniform(0.8, 1.2)
    expert = estimated * expert_variation
    
    # Franchise selon gravité
    franchise_rates = {"mineur": 0.1, "moyen": 0.08, "grave": 0.05, "tres_grave": 0.03}
    franchise = estimated * franchise_rates.get(severity, 0.1)
    
    # Indemnité (si accepté/réglé)
    indemnity = expert - franchise
    
    # Réserve (provision)
    reserve = expert * 1.1  # +10% de marge
    
    return {
        "estimated_amount": round(estimated, 2),
        "expert_amount": round(expert, 2),
        "franchise_applied": round(franchise, 2),
        "indemnity_amount": round(indemnity, 2),
        "reserve_amount": round(reserve, 2)
    }


def create_claim(db: Session, contract_id: int = None, verbose: bool = True) -> ClaimModel:
    """Crée un sinistre complet"""
    
    # Récupérer un contrat aléatoire si non spécifié
    if contract_id is None:
        contracts = db.query(ClientContractModel).filter(
            ClientContractModel.status == "actif"
        ).all()
        
        if not contracts:
            raise Exception("Aucun contrat actif trouvé. Créez d'abord des contrats.")
        
        contract = random.choice(contracts)
        contract_id = contract.id
    else:
        contract = db.query(ClientContractModel).filter(
            ClientContractModel.id == contract_id
        ).first()
        if not contract:
            raise Exception(f"Contrat ID {contract_id} non trouvé")
    
    # Type de sinistre
    claim_type = random.choice(CLAIM_TYPES)
    
    # Gravité basée sur le type
    if claim_type in ["structurel", "incendie"]:
        severity = random.choice(["grave", "tres_grave", "moyen"])
    elif claim_type in ["degats_des_eaux", "intemperies", "malfacons"]:
        severity = random.choice(["moyen", "grave", "mineur"])
    else:
        severity = random.choice(["mineur", "moyen"])
    
    # Dates
    incident_date = fake.date_time_between(start_date='-180d', end_date='-1d')
    declaration_date = incident_date + timedelta(days=random.randint(1, 15))
    
    # Statut avec progression logique
    status_weights = {
        "declare": 0.2,
        "pris_en_compte": 0.3,
        "en_cours_expertise": 0.2,
        "attente_pieces": 0.05,
        "accepte": 0.1,
        "refuse": 0.05,
        "regle": 0.08,
        "cloture": 0.02
    }
    
    status = random.choices(
        list(status_weights.keys()),
        weights=list(status_weights.values())
    )[0]
    
    # Dates supplémentaires selon le statut
    acknowledgment_date = None
    settlement_date = None
    closure_date = None
    
    if status != "declare":
        acknowledgment_date = declaration_date + timedelta(days=random.randint(2, 10))
    
    if status in ["regle", "cloture"]:
        settlement_date = acknowledgment_date + timedelta(days=random.randint(30, 120))
        closure_date = settlement_date + timedelta(days=random.randint(5, 30))
    
    # Génération des informations
    title, description, circumstances, area, guarantees = generate_claim_description(claim_type)
    amounts = calculate_amounts(severity, claim_type)
    
    # Numéro unique
    claim_number = generate_claim_number(db)
    
    # Expert
    expert_companies = [
        "Cabinet Expertise Construction", "SOCOTEC", "DEKRA", "APAVE",
        "Bureau Veritas", "Expert BTP Conseil", "CEA Expertise"
    ]
    expert_name = fake.name() if random.random() > 0.3 else None
    expert_company = random.choice(expert_companies) if expert_name else None
    
    # Documents
    has_photos = random.random() > 0.2
    has_expert_report = status in ["accepte", "refuse", "regle", "cloture"]
    has_repair_quote = status in ["accepte", "regle", "cloture"]
    
    documents = []
    if has_photos:
        documents.append({"type": "photos", "name": "photos_sinistre.zip", "date": declaration_date.strftime("%Y-%m-%d")})
    if has_expert_report:
        documents.append({"type": "rapport_expertise", "name": "rapport_expert.pdf", "date": (acknowledgment_date or declaration_date).strftime("%Y-%m-%d")})
    if has_repair_quote:
        documents.append({"type": "devis_reparation", "name": "devis_reparation.pdf", "date": (settlement_date or declaration_date).strftime("%Y-%m-%d")})
    
    # Tiers impliqué
    third_party = random.random() > 0.7
    third_party_info = None
    police_report = None
    
    if third_party:
        third_party_info = {
            "name": fake.name(),
            "contact": fake.phone_number(),
            "insurance": random.choice(["AXA", "Allianz", "MAIF", "MAAF", "Generali"])
        }
        if claim_type in ["vol", "vandalisme", "rc"]:
            police_report = f"PV-{random.randint(10000, 99999)}"
    
    # Réparations
    repair_status = None
    repair_company = None
    repair_start = None
    repair_end = None
    
    if status in ["accepte", "regle"]:
        repair_status = random.choice(["planifiee", "en_cours", "terminee"])
        repair_company = fake.company()
        if repair_status != "planifiee":
            repair_start = (settlement_date or acknowledgment_date or declaration_date) + timedelta(days=random.randint(10, 30))
            if repair_status == "terminee":
                repair_end = repair_start + timedelta(days=random.randint(15, 90))
    
    # Notes
    internal_notes = f"Sinistre {severity} - Suivi {random.choice(['normal', 'prioritaire', 'urgent'])}"
    expert_conclusions = None
    rejection_reason = None
    
    if status in ["accepte", "regle", "cloture"]:
        expert_conclusions = f"Les dommages constatés relèvent bien de la garantie {random.choice(guarantees)}. Travaux de reprise estimés à {amounts['expert_amount']:.2f}€."
    
    if status == "refuse":
        rejection_reason = random.choice([
            "Dommages antérieurs à la prise d'effet du contrat",
            "Exclusion contractuelle applicable",
            "Défaut d'entretien caractérisé",
            "Non-respect des conditions de garantie",
            "Franchise supérieure au montant des dommages"
        ])
    
    # Créer le sinistre
    claim = ClaimModel(
        claim_number=claim_number,
        external_reference=f"REF-{random.randint(100000, 999999)}" if random.random() > 0.5 else None,
        contract_id=contract_id,
        construction_site_id=contract.construction_site_id,
        claim_type=claim_type,
        severity=severity,
        status=status,
        incident_date=incident_date,
        declaration_date=declaration_date,
        acknowledgment_date=acknowledgment_date,
        settlement_date=settlement_date,
        closure_date=closure_date,
        title=title,
        description=description,
        circumstances=circumstances,
        affected_area=area,
        floor=random.choice(["RDC", "R+1", "R+2", "Sous-sol", "Combles", None]),
        **amounts,
        declared_by=fake.name(),
        expert_name=expert_name,
        expert_company=expert_company,
        activated_guarantees=guarantees,
        attached_documents=documents if documents else None,
        has_photos=has_photos,
        has_expert_report=has_expert_report,
        has_repair_quote=has_repair_quote,
        third_party_involved=third_party,
        third_party_info=third_party_info,
        police_report_number=police_report,
        repair_status=repair_status,
        repair_company=repair_company,
        repair_start_date=repair_start.date() if repair_start else None,
        repair_end_date=repair_end.date() if repair_end else None,
        internal_notes=internal_notes,
        expert_conclusions=expert_conclusions,
        rejection_reason=rejection_reason
    )
    
    db.add(claim)
    db.commit()
    db.refresh(claim)
    
    if verbose:
        print(f"  ✅ Sinistre créé: {claim.claim_number}")
        print(f"     Type: {claim.claim_type} - Gravité: {claim.severity} - Statut: {claim.status}")
        print(f"     Contrat: {contract.contract_number}")
        print(f"     Montant estimé: {claim.estimated_amount:.2f}€")
    
    return claim


def clean_all_claims(db: Session):
    """Supprime tous les sinistres"""
    count = db.query(ClaimModel).count()
    if count == 0:
        print("Aucun sinistre à supprimer.")
        return
    
    print(f"Suppression de {count} sinistre(s)...")
    db.query(ClaimModel).delete()
    db.commit()
    print(f"✅ {count} sinistre(s) supprimé(s)")


def main():
    parser = argparse.ArgumentParser(
        description="Générer des sinistres construction"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Supprimer tous les sinistres"
    )
    parser.add_argument(
        "--create",
        action="store_true",
        help="Créer des sinistres"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=10,
        help="Nombre de sinistres à créer (défaut: 10)"
    )
    parser.add_argument(
        "--contract-id",
        type=int,
        help="ID du contrat spécifique (optionnel)"
    )
    
    args = parser.parse_args()
    
    db = SessionLocal()
    
    try:
        if args.clean:
            clean_all_claims(db)
        
        if args.create:
            print(f"\n📋 Création de {args.count} sinistre(s)...\n")
            
            for i in range(args.count):
                print(f"Sinistre {i+1}/{args.count}:")
                create_claim(db, contract_id=args.contract_id, verbose=True)
                print()
            
            # Résumé
            total = db.query(ClaimModel).count()
            by_type = {}
            for ct in CLAIM_TYPES:
                count = db.query(ClaimModel).filter(ClaimModel.claim_type == ct).count()
                by_type[ct] = count
            
            print("=" * 60)
            print("📊 RÉSUMÉ DES SINISTRES")
            print("=" * 60)
            print(f"  Total sinistres:      {total}")
            print(f"\n  Par type:")
            for ct, count in by_type.items():
                if count > 0:
                    print(f"    - {ct:20s}: {count}")
            print("=" * 60)
            print("✅ Génération terminée avec succès\n")
        
        if not args.clean and not args.create:
            parser.print_help()
    
    except Exception as e:
        print(f"\n❌ Erreur: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
