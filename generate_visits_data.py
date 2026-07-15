"""
Script de génération de données du réseau commercial : commerciaux, visites clients
(avec compte rendu), propositions d'assurance sur les produits du référentiel
(DO, RCD, TRC, CNR, RCMO, PUC) et souscriptions de contrat consécutives.

Usage:
    # Nettoyage (ne supprime pas les clients/contrats, seulement le réseau commercial)
    python generate_visits_data.py --clean

    # Créer 300 commerciaux
    python generate_visits_data.py --create-reps --count 300

    # Générer les visites depuis le 01/01/2025 jusqu'à aujourd'hui, en moyenne 2/jour/commercial,
    # jours ouvrés uniquement, en limitant à 20 commerciaux et aux 60 derniers jours ouvrés
    # (échantillon rapide à valider avant un run complet)
    python generate_visits_data.py --create-visits --start 2025-01-01 --max-reps 20 --max-days 60

    # Run complet (300 commerciaux, tout l'historique depuis 2025) - volumineux, prévoir plusieurs minutes
    python generate_visits_data.py --create-visits --start 2025-01-01
"""
import argparse
import random
import types
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import OperationalError, DBAPIError
from faker import Faker

from app.database import engine

# Le moteur applicatif logue chaque requête SQL (utile pour l'API, inutile et très
# coûteux ici vu le volume de requêtes générées par ce script en masse).
engine.echo = False

# expire_on_commit=False : les objets chargés (commerciaux, clients) doivent rester
# utilisables en mémoire après un commit ou une reconnexion, sans requête de rafraîchissement
# (indispensable pour survivre à une coupure de connexion en cours de génération).
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)
from app.models import (
    SalesRepModel, ClientVisitModel, InsuranceProposalModel,
    ClientModel, ConstructionSiteModel,
    ClientContractModel, GuaranteeModel, InsuranceContractTypeModel, contract_guarantees
)

fake = Faker('fr_FR')

# =============================================================================
# DONNÉES DE RÉFÉRENCE
# =============================================================================

CIVILITES = ["M.", "Mme"]

REGIONS = [
    "Île-de-France", "Auvergne-Rhône-Alpes", "Nouvelle-Aquitaine", "Occitanie",
    "Hauts-de-France", "Grand Est", "Provence-Alpes-Côte d'Azur", "Pays de la Loire",
    "Bretagne", "Normandie", "Bourgogne-Franche-Comté", "Centre-Val de Loire"
]

AGENCY_CITIES = [
    "Paris", "Lyon", "Bordeaux", "Toulouse", "Lille", "Strasbourg", "Marseille",
    "Nantes", "Rennes", "Rouen", "Dijon", "Orléans", "Nice", "Nancy", "Reims"
]

CONTRACT_TYPES = ["DO", "RCD", "TRC", "CNR", "RCMO", "PUC"]
CONTRACT_TYPE_WEIGHTS = [30, 30, 15, 10, 10, 5]

VISIT_TYPES = [
    "prospection", "decouverte_besoins", "suivi_contrat",
    "renouvellement", "gestion_sinistre", "fidelisation", "souscription"
]
VISIT_TYPE_WEIGHTS = [12, 13, 30, 15, 8, 17, 5]

VISIT_STATUS_WEIGHTS = {
    "realisee": 82,
    "annulee": 6,
    "reportee": 7,
    "absence_client": 5,
}

PROPOSAL_STATUS_WEIGHTS = {
    "envoyee": 25,
    "en_reflexion": 25,
    "acceptee": 22,
    "refusee": 15,
    "expiree": 7,
    "sans_suite": 6,
}

TOPICS_POOL = [
    "Point sur le contrat en cours", "Renouvellement annuel", "Nouvelle garantie décennale",
    "Suivi d'un sinistre", "Nouveau chantier à assurer", "Tarification et franchises",
    "Garanties complémentaires", "Évolution du besoin d'assurance", "Bilan annuel des sinistres",
    "Présentation offre TRC", "Présentation offre DO", "Mise à jour des coordonnées",
    "Attestations d'assurance des sous-traitants", "Extension de garantie chantier"
]

OBJECTIVES_BY_TYPE = {
    "prospection": "Prospection commerciale et présentation de l'offre assurance construction",
    "decouverte_besoins": "Découverte des besoins d'assurance du client sur ses opérations en cours",
    "suivi_contrat": "Point de suivi sur les contrats en portefeuille",
    "renouvellement": "Préparation du renouvellement du contrat arrivant à échéance",
    "gestion_sinistre": "Accompagnement du client dans la gestion d'un sinistre en cours",
    "fidelisation": "Visite de fidélisation et bilan de la relation commerciale",
    "souscription": "Finalisation de la souscription d'un nouveau contrat",
}

REPORT_TEMPLATES = {
    "prospection": "Premier contact avec {client}. Présentation de l'offre {gamme}. "
                   "Le client {reaction}.",
    "decouverte_besoins": "Entretien de découverte avec {client} sur ses besoins de couverture. "
                          "Chantiers/activités évoqués : {sujet}. Le client {reaction}.",
    "suivi_contrat": "Point périodique avec {client} sur les contrats en cours. "
                     "Aucune anomalie majeure signalée. {sujet} abordé(e).",
    "renouvellement": "Revue du contrat de {client} avant échéance. "
                      "Discussion sur {sujet}. Le client {reaction}.",
    "gestion_sinistre": "Rencontre avec {client} suite à la déclaration d'un sinistre. "
                        "Point sur l'avancement du dossier et les prochaines étapes.",
    "fidelisation": "Visite de courtoisie chez {client}. Bilan de la relation commerciale "
                    "et recueil de son niveau de satisfaction.",
    "souscription": "Signature des documents de souscription avec {client} pour {gamme}. "
                    "Dossier transmis au service souscription.",
}

REACTIONS = [
    "s'est montré intéressé", "souhaite réfléchir", "a demandé un devis complémentaire",
    "a validé les grandes lignes de l'offre", "reste prudent sur le tarif proposé",
    "est très satisfait de l'échange"
]

REJECTION_REASONS = [
    "Tarif jugé trop élevé par rapport à la concurrence",
    "Client a finalement conservé son assureur actuel",
    "Projet de construction reporté par le client",
    "Garanties proposées jugées insuffisantes",
    "Absence de retour du client après plusieurs relances",
]

CONTRACT_TYPE_NAMES = {
    "DO": "l'offre Dommage-Ouvrage",
    "RCD": "l'offre RC Décennale",
    "TRC": "l'offre Tous Risques Chantier",
    "CNR": "l'offre Constructeur Non Réalisateur",
    "RCMO": "l'offre RC Maître d'Ouvrage",
    "PUC": "la Police Unique de Chantier",
}


def weighted_choice(weights_dict):
    keys = list(weights_dict.keys())
    weights = list(weights_dict.values())
    return random.choices(keys, weights=weights)[0]


def business_days(start: date, end: date):
    """Génère les jours ouvrés (lundi-vendredi) entre start et end inclus"""
    current = start
    while current <= end:
        if current.weekday() < 5:  # 0=lundi ... 4=vendredi
            yield current
        current += timedelta(days=1)


def visits_per_day():
    """Nombre de visites d'un commercial sur une journée donnée (2 à 5, moyenne ~3.2)"""
    return random.choices([2, 3, 4, 5], weights=[30, 35, 20, 15])[0]


# =============================================================================
# COMMERCIAUX
# =============================================================================

def generate_sales_rep(db: Session, employee_number: str, start_date: date) -> SalesRepModel:
    """Génère un commercial actif depuis avant le début de la période d'étude"""
    civility = random.choice(CIVILITES)
    first_name = fake.first_name_male() if civility == "M." else fake.first_name_female()
    last_name = fake.last_name()
    region = random.choice(REGIONS)
    city = random.choice(AGENCY_CITIES)

    hire_date = fake.date_between(start_date=date(2010, 1, 1), end_date=start_date - timedelta(days=30))
    is_active = random.random() > 0.08  # ~8% ont quitté depuis

    sales_rep = SalesRepModel(
        employee_number=employee_number,
        civility=civility,
        first_name=first_name,
        last_name=last_name,
        email=f"{first_name.lower()}.{last_name.lower()}@sma-assurances.fr".replace(" ", "-").replace("'", ""),
        phone=fake.phone_number().replace(' ', '')[:14],
        mobile=fake.phone_number().replace(' ', '')[:14],
        region=region,
        agency=f"Agence {city}",
        manager_name=fake.name(),
        hire_date=hire_date,
        is_active=is_active,
        notes=None,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(sales_rep)
    return sales_rep


def create_sales_reps(db: Session, count: int, start_date: date) -> list:
    """Crée `count` commerciaux, avec des matricules uniques"""
    existing_numbers = {n[0] for n in db.query(SalesRepModel.employee_number).all()}
    existing_count = len(existing_numbers)

    sales_reps = []
    seq = existing_count + 1
    for _ in range(count):
        employee_number = f"COM-{seq:04d}"
        while employee_number in existing_numbers:
            seq += 1
            employee_number = f"COM-{seq:04d}"
        sales_reps.append(generate_sales_rep(db, employee_number, start_date))
        existing_numbers.add(employee_number)
        seq += 1

    db.commit()
    for sr in sales_reps:
        db.refresh(sr)
    return sales_reps


# =============================================================================
# PORTEFEUILLE CLIENTS / OUTILS
# =============================================================================

def to_plain_rep(rep: SalesRepModel):
    """Copie les seuls attributs utilisés dans une structure indépendante de toute Session,
    pour survivre à une reconnexion en cours de génération (cf. reconnect())."""
    return types.SimpleNamespace(id=rep.id, hire_date=rep.hire_date, full_name=rep.full_name)


def to_plain_client(client: ClientModel):
    """Idem pour les clients (avec leurs adresses), utilisés massivement dans la boucle principale."""
    return types.SimpleNamespace(
        id=client.id,
        company_name=client.company_name,
        first_name=client.first_name,
        last_name=client.last_name,
        addresses=[
            types.SimpleNamespace(id=a.id, latitude=a.latitude, longitude=a.longitude)
            for a in client.addresses
        ],
    )


def build_rep_portfolios(db: Session, sales_reps: list) -> dict:
    """Attribue à chaque commercial un portefeuille de quelques clients existants"""
    from sqlalchemy.orm import selectinload
    all_clients = db.query(ClientModel).options(selectinload(ClientModel.addresses)).filter(
        ClientModel.is_active == True  # noqa: E712
    ).all()
    if not all_clients:
        raise Exception("Aucun client actif trouvé. Générez d'abord des clients (generate_client_data.py).")

    plain_clients = [to_plain_client(c) for c in all_clients]

    portfolios = {}
    for rep in sales_reps:
        size = min(len(plain_clients), random.randint(3, 8))
        portfolios[rep.id] = random.sample(plain_clients, size)
    return portfolios


def get_contract_type_id_map(db: Session) -> dict:
    """Correspondance code produit (DO, RCD, ...) -> id en base du référentiel ref_insurance_contract_types"""
    return {ct.code: ct.id for ct in db.query(InsuranceContractTypeModel).all()}


def next_sequence_from_db(db: Session, model, column_name: str, prefix: str) -> int:
    """Trouve le prochain numéro séquentiel disponible (unique tous préfixes/années confondus)"""
    like_pattern = f"{prefix}-%"
    column = getattr(model, column_name)
    existing = db.query(column).filter(column.like(like_pattern)).all()
    max_seq = 0
    for (value,) in existing:
        try:
            seq = int(value.split("-")[-1])
            max_seq = max(max_seq, seq)
        except (ValueError, IndexError):
            continue
    return max_seq + 1


# =============================================================================
# SOUSCRIPTION (contrat généré à partir d'une proposition acceptée)
# =============================================================================

def create_contract_from_proposal(db: Session, proposal: InsuranceProposalModel,
                                   client: ClientModel, sales_rep: SalesRepModel,
                                   visit: ClientVisitModel, contract_seq: list,
                                   contract_type_ids: dict) -> ClientContractModel:
    """Crée un contrat client suite à l'acceptation d'une proposition (souscription)"""
    sites = db.query(ConstructionSiteModel).all()
    site = random.choice(sites) if sites and random.random() > 0.2 else None

    contract_seq[0] += 1
    contract_number = f"CNT{contract_seq[0]:06d}"
    while db.query(ClientContractModel).filter(ClientContractModel.contract_number == contract_number).first():
        contract_seq[0] += 1
        contract_number = f"CNT{contract_seq[0]:06d}"

    issue_date = proposal.proposal_date + timedelta(days=random.randint(2, 20))
    effective_date = issue_date + timedelta(days=random.randint(0, 15))
    duration_years = random.choice([1, 2, 3, 5, 10])
    expiry_date = effective_date + timedelta(days=365 * duration_years)

    insured_amount = proposal.proposed_insured_amount or random.randint(100000, 5000000)
    annual_premium = proposal.proposed_annual_premium or insured_amount * random.uniform(0.001, 0.005)

    contract = ClientContractModel(
        contract_number=contract_number,
        external_reference=f"EXT{random.randint(10000, 99999)}",
        contract_type_code=proposal.contract_type_code,
        client_id=client.id,
        construction_site_id=site.id if site else None,
        sales_rep_id=sales_rep.id,
        originating_visit_id=visit.id if visit else None,
        status=random.choice(["actif", "actif", "actif", "en_attente"]),
        issue_date=issue_date,
        effective_date=effective_date,
        expiry_date=expiry_date,
        insured_amount=insured_amount,
        annual_premium=annual_premium,
        total_premium=annual_premium * duration_years,
        franchise_amount=proposal.proposed_franchise or random.randint(500, 10000),
        duration_years=duration_years,
        is_renewable=random.choice([True, False]),
        selected_guarantees=None,
        broker_name=None,
        underwriter=sales_rep.full_name,
        internal_notes=f"Souscription issue de la visite {visit.visit_number}" if visit else None,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(contract)
    db.flush()

    contract_type_id = contract_type_ids.get(proposal.contract_type_code)
    available_guarantees = db.query(GuaranteeModel).filter(
        GuaranteeModel.contract_type_id == contract_type_id
    ).all() if contract_type_id else []
    if available_guarantees:
        num_guarantees = min(random.randint(1, 4), len(available_guarantees))
        selected = random.sample(available_guarantees, num_guarantees)
        db.execute(contract_guarantees.insert(), [
            {
                'contract_id': contract.id,
                'guarantee_code': g.code,
                'custom_ceiling': g.default_ceiling or random.randint(50000, 1000000),
                'custom_franchise': g.default_franchise or random.randint(500, 5000),
                'is_included': True,
                'annual_premium': random.uniform(500, 5000),
            }
            for g in selected
        ])

    return contract


# =============================================================================
# PROPOSITION D'ASSURANCE
# =============================================================================

def create_proposal(db: Session, visit: ClientVisitModel, client: ClientModel,
                     sales_rep: SalesRepModel, proposal_seq: list, contract_seq: list,
                     conversion_rate: float, contract_type_ids: dict) -> InsuranceProposalModel:
    contract_type_code = random.choices(CONTRACT_TYPES, weights=CONTRACT_TYPE_WEIGHTS)[0]

    proposal_seq[0] += 1
    proposal_number = f"PROP-{visit.visit_date.year}-{proposal_seq[0]:06d}"

    insured_amount = random.randint(100000, 8000000)
    annual_premium = insured_amount * random.uniform(0.001, 0.005)
    status = weighted_choice(PROPOSAL_STATUS_WEIGHTS)

    contract_type_id = contract_type_ids.get(contract_type_code)
    guarantees_ref = db.query(GuaranteeModel).filter(
        GuaranteeModel.contract_type_id == contract_type_id
    ).all() if contract_type_id else []
    selected_guarantees = [
        {"code": g.code, "ceiling": g.default_ceiling, "franchise": g.default_franchise, "included": True}
        for g in random.sample(guarantees_ref, min(len(guarantees_ref), random.randint(1, 3)))
    ] if guarantees_ref else None

    proposal = InsuranceProposalModel(
        proposal_number=proposal_number,
        visit_id=visit.id,
        client_id=client.id,
        sales_rep_id=sales_rep.id,
        contract_type_code=contract_type_code,
        proposal_date=visit.visit_date.date(),
        validity_date=visit.visit_date.date() + timedelta(days=random.randint(30, 60)),
        status=status,
        proposed_insured_amount=insured_amount,
        proposed_annual_premium=round(annual_premium, 2),
        proposed_franchise=random.choice([500, 1000, 1500, 2500, 5000]),
        selected_guarantees=selected_guarantees,
        rejection_reason=random.choice(REJECTION_REASONS) if status in ("refusee", "sans_suite") else None,
        notes=f"Proposition {CONTRACT_TYPE_NAMES.get(contract_type_code, contract_type_code)} suite à la visite {visit.visit_number}",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(proposal)
    db.flush()

    if status == "acceptee" and random.random() < conversion_rate:
        contract = create_contract_from_proposal(db, proposal, client, sales_rep, visit, contract_seq, contract_type_ids)
        proposal.converted_contract_id = contract.id

    return proposal


# =============================================================================
# VISITE CLIENT (avec compte rendu)
# =============================================================================

def create_visit(db: Session, sales_rep: SalesRepModel, client: ClientModel,
                  visit_datetime: datetime, visit_seq: list) -> ClientVisitModel:
    visit_type = random.choices(VISIT_TYPES, weights=VISIT_TYPE_WEIGHTS)[0]
    visit_status = weighted_choice(VISIT_STATUS_WEIGHTS)

    client_display = client.company_name or f"{client.first_name} {client.last_name}"

    address = None
    if client.addresses:
        address = random.choice(client.addresses)

    visit_seq[0] += 1
    visit_number = f"VIS-{visit_datetime.year}-{visit_seq[0]:06d}"

    report_summary = None
    topics_discussed = None
    client_satisfaction = None
    next_action = None
    next_visit_date = None

    if visit_status == "realisee":
        template = REPORT_TEMPLATES[visit_type]
        report_summary = template.format(
            client=client_display,
            gamme=random.choice(list(CONTRACT_TYPE_NAMES.values())),
            reaction=random.choice(REACTIONS),
            sujet=random.choice(TOPICS_POOL).lower(),
        )
        topics_discussed = random.sample(TOPICS_POOL, random.randint(1, 3))
        client_satisfaction = random.choices([2, 3, 4, 5], weights=[5, 20, 45, 30])[0]
        if random.random() > 0.4:
            next_action = random.choice([
                "Envoyer un devis complémentaire", "Relancer sous 15 jours",
                "Planifier une visite de renouvellement", "Transmettre le dossier à la souscription",
                "Adresser les attestations d'assurance",
            ])
            next_visit_date = visit_datetime.date() + timedelta(days=random.randint(15, 90))
    elif visit_status == "reportee":
        next_visit_date = visit_datetime.date() + timedelta(days=random.randint(3, 14))

    visit = ClientVisitModel(
        visit_number=visit_number,
        sales_rep_id=sales_rep.id,
        client_id=client.id,
        address_id=address.id if address else None,
        visit_date=visit_datetime,
        duration_minutes=random.randint(20, 90) if visit_status == "realisee" else None,
        visit_type=visit_type,
        visit_status=visit_status,
        objective=OBJECTIVES_BY_TYPE[visit_type],
        report_summary=report_summary,
        topics_discussed=topics_discussed,
        client_satisfaction=client_satisfaction,
        next_action=next_action,
        next_visit_date=next_visit_date,
        latitude=address.latitude if address else None,
        longitude=address.longitude if address else None,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(visit)
    db.flush()
    return visit


# =============================================================================
# ORCHESTRATION
# =============================================================================

def reconnect(db: Session) -> Session:
    """Abandonne la session courante (potentiellement morte) et en ouvre une nouvelle.
    Le pool_pre_ping du moteur revalide la nouvelle connexion à la première requête."""
    try:
        db.rollback()
    except Exception:
        pass
    try:
        db.close()
    except Exception:
        pass
    return SessionLocal()


def generate_visits_campaign(db: Session, start_date: date, end_date: date,
                              max_reps: int, max_days: int, proposal_rate: float,
                              conversion_rate: float, commit_every: int = 200):
    all_reps = db.query(SalesRepModel).filter(SalesRepModel.is_active == True).all()  # noqa: E712
    if not all_reps:
        raise Exception("Aucun commercial trouvé. Créez d'abord des commerciaux avec --create-reps.")

    if max_reps:
        all_reps = random.sample(all_reps, min(max_reps, len(all_reps)))

    all_reps = [to_plain_rep(r) for r in all_reps]
    portfolios = build_rep_portfolios(db, all_reps)
    contract_type_ids = get_contract_type_id_map(db)

    days = list(business_days(start_date, end_date))
    if max_days:
        days = days[-max_days:]

    visit_seq = [next_sequence_from_db(db, ClientVisitModel, "visit_number", "VIS") - 1]
    proposal_seq = [next_sequence_from_db(db, InsuranceProposalModel, "proposal_number", "PROP") - 1]
    contract_seq = [0]  # Le contrôle d'unicité de contract_number gère les collisions avec l'existant

    total_visits = 0
    total_proposals = 0
    total_contracts = 0

    print(f"\n📅 Génération des visites du {start_date} au {end_date} "
          f"({len(days)} jours ouvrés, {len(all_reps)} commercial(aux))\n")

    for day_index, day in enumerate(days, start=1):
        for rep in all_reps:
            if rep.hire_date and rep.hire_date > day:
                continue  # pas encore embauché à cette date

            num_visits = visits_per_day()
            rep_clients = portfolios.get(rep.id) or []
            if not rep_clients or num_visits == 0:
                continue

            try:
                for _ in range(num_visits):
                    client = random.choice(rep_clients)
                    visit_time = datetime.combine(day, datetime.min.time()) + timedelta(
                        hours=random.randint(8, 17), minutes=random.choice([0, 15, 30, 45])
                    )
                    visit = create_visit(db, rep, client, visit_time, visit_seq)
                    total_visits += 1

                    if (visit.visit_status == "realisee"
                            and visit.visit_type in ("prospection", "decouverte_besoins", "renouvellement", "souscription")
                            and random.random() < proposal_rate):
                        proposal = create_proposal(db, visit, client, rep, proposal_seq, contract_seq, conversion_rate, contract_type_ids)
                        total_proposals += 1
                        if proposal.converted_contract_id:
                            total_contracts += 1

                if total_visits % commit_every == 0:
                    db.commit()
            except (OperationalError, DBAPIError) as e:
                print(f"  ⚠️  Connexion perdue ({e.__class__.__name__}), reconnexion et poursuite...")
                db = reconnect(db)
                continue

        if day_index % 20 == 0 or day_index == len(days):
            try:
                db.commit()
            except (OperationalError, DBAPIError):
                db = reconnect(db)
            print(f"  ... {day_index}/{len(days)} jours traités "
                  f"({total_visits} visites, {total_proposals} propositions, {total_contracts} souscriptions)")

    try:
        db.commit()
    except (OperationalError, DBAPIError):
        db = reconnect(db)
    return total_visits, total_proposals, total_contracts


def clean_commercial_network(db: Session):
    """Supprime commerciaux / visites / propositions, et délie les contrats (sans les supprimer)"""
    print("\n🗑️  Nettoyage du réseau commercial (commerciaux, visites, propositions)...")

    updated = db.query(ClientContractModel).filter(
        ClientContractModel.sales_rep_id.isnot(None)
    ).update({"sales_rep_id": None, "originating_visit_id": None}, synchronize_session=False)
    print(f"  ✓ {updated} contrat(s) délié(s) du réseau commercial")

    deleted_proposals = db.query(InsuranceProposalModel).delete()
    print(f"  ✓ {deleted_proposals} proposition(s) supprimée(s)")

    deleted_visits = db.query(ClientVisitModel).delete()
    print(f"  ✓ {deleted_visits} visite(s) supprimée(s)")

    deleted_reps = db.query(SalesRepModel).delete()
    print(f"  ✓ {deleted_reps} commercial(aux) supprimé(s)")

    db.commit()
    print("✅ Nettoyage terminé\n")


def main():
    parser = argparse.ArgumentParser(
        description="Générer les données du réseau commercial : commerciaux, visites, propositions, souscriptions"
    )
    parser.add_argument("--clean", action="store_true", help="Supprimer le réseau commercial existant")
    parser.add_argument("--create-reps", action="store_true", help="Créer des commerciaux")
    parser.add_argument("--count", type=int, default=300, help="Nombre de commerciaux à créer (défaut: 300)")
    parser.add_argument("--create-visits", action="store_true", help="Générer les visites/propositions/souscriptions")
    parser.add_argument("--start", type=str, default="2025-01-01", help="Date de début (YYYY-MM-DD, défaut: 2025-01-01)")
    parser.add_argument("--end", type=str, default=None, help="Date de fin (YYYY-MM-DD, défaut: aujourd'hui)")
    parser.add_argument("--max-reps", type=int, default=None, help="Limiter le nombre de commerciaux utilisés (échantillonnage)")
    parser.add_argument("--max-days", type=int, default=None, help="Limiter aux N derniers jours ouvrés de la période (échantillonnage)")
    parser.add_argument("--proposal-rate", type=float, default=0.35, help="Probabilité qu'une visite génère une proposition (défaut: 0.35)")
    parser.add_argument("--conversion-rate", type=float, default=0.85, help="Probabilité qu'une proposition acceptée soit transformée en contrat (défaut: 0.85)")

    args = parser.parse_args()
    db = SessionLocal()

    try:
        if args.clean:
            clean_commercial_network(db)

        start_date = datetime.strptime(args.start, "%Y-%m-%d").date()
        end_date = datetime.strptime(args.end, "%Y-%m-%d").date() if args.end else date.today()

        if args.create_reps:
            print(f"\n👥 Création de {args.count} commercial(aux)...\n")
            reps = create_sales_reps(db, args.count, start_date)
            print(f"✅ {len(reps)} commercial(aux) créé(s)\n")

        if args.create_visits:
            total_visits, total_proposals, total_contracts = generate_visits_campaign(
                db, start_date, end_date,
                max_reps=args.max_reps, max_days=args.max_days,
                proposal_rate=args.proposal_rate, conversion_rate=args.conversion_rate,
            )
            print("\n" + "=" * 60)
            print("📊 RÉSUMÉ DE LA GÉNÉRATION")
            print("=" * 60)
            print(f"  Visites créées:        {total_visits}")
            print(f"  Propositions créées:   {total_proposals}")
            print(f"  Souscriptions créées:  {total_contracts}")
            print("=" * 60)
            print("✅ Génération terminée avec succès\n")

        if not any([args.clean, args.create_reps, args.create_visits]):
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
