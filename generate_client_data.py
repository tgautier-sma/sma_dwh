"""
Script de génération de données clients avec toutes leurs relations
Usage:
    python generate_client_data.py --clean  # Supprimer tous les clients
    python generate_client_data.py --create # Créer un client avec relations
    python generate_client_data.py --create --count 5  # Créer 5 clients (mixte)
    python generate_client_data.py --create --count 3 --type particulier  # 3 particuliers
    python generate_client_data.py --create --count 2 --type entreprise  # 2 entreprises
"""
import argparse
import random
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from faker import Faker

from app.database import SessionLocal, engine
from app.models import (
    Base, ClientModel, ClientAddressModel, ConstructionSiteModel,
    ClientContractModel, ContractHistoryModel, ClaimModel, contract_guarantees,
    GuaranteeModel
)

# Initialiser Faker en français
fake = Faker('fr_FR')

# Données de référence françaises
CIVILITES = ["M.", "Mme", "Mlle"]
CLIENT_TYPES = ["particulier", "professionnel"]
LEGAL_FORMS = [
    "SARL", "SAS", "SASU", "EURL", "SA", "SNC", "SCI", 
    "Auto-entrepreneur", "Association"
]
ADDRESS_TYPES = ["siege_social", "entrepot", "chantier"]
CONTRACT_TYPES = ["RCD", "DO", "TRC", "CNR", "RCMO", "PUC"]
CONTRACT_STATUS = ["brouillon", "en_attente", "actif", "suspendu", "resilie", "expire"]
BUILDING_CATEGORIES = [
    "maison_individuelle", "immeuble_collectif", "local_commercial",
    "batiment_industriel", "renovation", "extension"
]
WORK_CATEGORIES = [
    "gros_oeuvre", "second_oeuvre", "finitions", "amenagement_exterieur",
    "renovation_complete", "extension_surelevation"
]
FOUNDATION_TYPES = ["semelles", "radier", "pieux", "micropieux", "sur_vide"]
STRUCTURE_TYPES = ["beton_arme", "ossature_bois", "mixte", "metallique", "maconnerie"]
SEISMIC_ZONES = ["1", "2", "3", "4", "5"]
ACTION_TYPES = ["creation", "modification", "changement_statut", "renouvellement", "resiliation"]

# Coordonnées GPS approximatives par département français (centre du département)
DEPARTEMENT_GPS = {
    "01": {"lat": 46.0667, "lon": 5.3333},  # Ain
    "02": {"lat": 49.5667, "lon": 3.6167},  # Aisne
    "03": {"lat": 46.5667, "lon": 3.3333},  # Allier
    "04": {"lat": 44.1000, "lon": 6.2333},  # Alpes-de-Haute-Provence
    "05": {"lat": 44.6667, "lon": 6.0833},  # Hautes-Alpes
    "06": {"lat": 43.9333, "lon": 7.2167},  # Alpes-Maritimes
    "07": {"lat": 44.7333, "lon": 4.6000},  # Ardèche
    "08": {"lat": 49.7667, "lon": 4.7167},  # Ardennes
    "09": {"lat": 42.9667, "lon": 1.6000},  # Ariège
    "10": {"lat": 48.3000, "lon": 4.0833},  # Aube
    "11": {"lat": 43.2167, "lon": 2.3500},  # Aude
    "12": {"lat": 44.3500, "lon": 2.5833},  # Aveyron
    "13": {"lat": 43.5333, "lon": 5.4500},  # Bouches-du-Rhône
    "14": {"lat": 49.1833, "lon": -0.3667},  # Calvados
    "15": {"lat": 45.0333, "lon": 2.4333},  # Cantal
    "16": {"lat": 45.6500, "lon": 0.1500},  # Charente
    "17": {"lat": 45.7500, "lon": -0.6333},  # Charente-Maritime
    "18": {"lat": 47.0833, "lon": 2.4000},  # Cher
    "19": {"lat": 45.2667, "lon": 1.7667},  # Corrèze
    "21": {"lat": 47.3167, "lon": 5.0167},  # Côte-d'Or
    "22": {"lat": 48.5167, "lon": -2.7667},  # Côtes-d'Armor
    "23": {"lat": 46.1667, "lon": 1.8667},  # Creuse
    "24": {"lat": 45.1833, "lon": 0.7167},  # Dordogne
    "25": {"lat": 47.2333, "lon": 6.0333},  # Doubs
    "26": {"lat": 44.7333, "lon": 5.0500},  # Drôme
    "27": {"lat": 49.0250, "lon": 0.9500},  # Eure
    "28": {"lat": 48.4472, "lon": 1.4889},  # Eure-et-Loir
    "29": {"lat": 48.2667, "lon": -4.0833},  # Finistère
    "30": {"lat": 43.8333, "lon": 4.3667},  # Gard
    "31": {"lat": 43.6047, "lon": 1.4442},  # Haute-Garonne
    "32": {"lat": 43.6500, "lon": 0.5833},  # Gers
    "33": {"lat": 44.8378, "lon": -0.5792},  # Gironde
    "34": {"lat": 43.6108, "lon": 3.8767},  # Hérault
    "35": {"lat": 48.1173, "lon": -1.6778},  # Ille-et-Vilaine
    "36": {"lat": 46.8108, "lon": 1.6900},  # Indre
    "37": {"lat": 47.3936, "lon": 0.6889},  # Indre-et-Loire
    "38": {"lat": 45.1885, "lon": 5.7245},  # Isère
    "39": {"lat": 46.6689, "lon": 5.5550},  # Jura
    "40": {"lat": 43.8958, "lon": -0.5000},  # Landes
    "41": {"lat": 47.5889, "lon": 1.3358},  # Loir-et-Cher
    "42": {"lat": 45.4397, "lon": 4.3872},  # Loire
    "43": {"lat": 45.0439, "lon": 3.8850},  # Haute-Loire
    "44": {"lat": 47.2184, "lon": -1.5536},  # Loire-Atlantique
    "45": {"lat": 47.9028, "lon": 1.9086},  # Loiret
    "46": {"lat": 44.4472, "lon": 1.4414},  # Lot
    "47": {"lat": 44.2028, "lon": 0.6197},  # Lot-et-Garonne
    "48": {"lat": 44.5186, "lon": 3.5008},  # Lozère
    "49": {"lat": 47.4739, "lon": -0.5542},  # Maine-et-Loire
    "50": {"lat": 49.1167, "lon": -1.0833},  # Manche
    "51": {"lat": 48.9569, "lon": 4.3658},  # Marne
    "52": {"lat": 48.1128, "lon": 5.1397},  # Haute-Marne
    "53": {"lat": 48.0706, "lon": -0.7703},  # Mayenne
    "54": {"lat": 48.6844, "lon": 6.1844},  # Meurthe-et-Moselle
    "55": {"lat": 49.1611, "lon": 5.3847},  # Meuse
    "56": {"lat": 47.7467, "lon": -2.7597},  # Morbihan
    "57": {"lat": 49.1197, "lon": 6.1769},  # Moselle
    "58": {"lat": 47.0000, "lon": 3.5333},  # Nièvre
    "59": {"lat": 50.6292, "lon": 3.0573},  # Nord
    "60": {"lat": 49.4167, "lon": 2.0833},  # Oise
    "61": {"lat": 48.4333, "lon": 0.0833},  # Orne
    "62": {"lat": 50.5167, "lon": 2.6333},  # Pas-de-Calais
    "63": {"lat": 45.7667, "lon": 3.0833},  # Puy-de-Dôme
    "64": {"lat": 43.3000, "lon": -0.3667},  # Pyrénées-Atlantiques
    "65": {"lat": 43.2333, "lon": 0.0833},  # Hautes-Pyrénées
    "66": {"lat": 42.5000, "lon": 2.7500},  # Pyrénées-Orientales
    "67": {"lat": 48.5833, "lon": 7.7500},  # Bas-Rhin
    "68": {"lat": 47.7500, "lon": 7.3333},  # Haut-Rhin
    "69": {"lat": 45.7640, "lon": 4.8357},  # Rhône
    "70": {"lat": 47.6167, "lon": 6.1500},  # Haute-Saône
    "71": {"lat": 46.6500, "lon": 4.7667},  # Saône-et-Loire
    "72": {"lat": 48.0061, "lon": 0.1996},  # Sarthe
    "73": {"lat": 45.5647, "lon": 6.3767},  # Savoie
    "74": {"lat": 46.0672, "lon": 6.3769},  # Haute-Savoie
    "75": {"lat": 48.8566, "lon": 2.3522},  # Paris
    "76": {"lat": 49.4433, "lon": 1.0993},  # Seine-Maritime
    "77": {"lat": 48.8424, "lon": 2.9978},  # Seine-et-Marne
    "78": {"lat": 48.8033, "lon": 2.1333},  # Yvelines
    "79": {"lat": 46.3239, "lon": -0.4642},  # Deux-Sèvres
    "80": {"lat": 49.8944, "lon": 2.2958},  # Somme
    "81": {"lat": 43.9286, "lon": 2.1478},  # Tarn
    "82": {"lat": 44.0167, "lon": 1.3500},  # Tarn-et-Garonne
    "83": {"lat": 43.4667, "lon": 6.2333},  # Var
    "84": {"lat": 44.0000, "lon": 5.1333},  # Vaucluse
    "85": {"lat": 46.6708, "lon": -1.4264},  # Vendée
    "86": {"lat": 46.5819, "lon": 0.3339},  # Vienne
    "87": {"lat": 45.8333, "lon": 1.2667},  # Haute-Vienne
    "88": {"lat": 48.1706, "lon": 6.4514},  # Vosges
    "89": {"lat": 47.7986, "lon": 3.5672},  # Yonne
    "90": {"lat": 47.6406, "lon": 6.8631},  # Territoire de Belfort
    "91": {"lat": 48.6308, "lon": 2.4286},  # Essonne
    "92": {"lat": 48.8922, "lon": 2.2392},  # Hauts-de-Seine
    "93": {"lat": 48.9103, "lon": 2.4839},  # Seine-Saint-Denis
    "94": {"lat": 48.7917, "lon": 2.4856},  # Val-de-Marne
    "95": {"lat": 49.0400, "lon": 2.1003},  # Val-d'Oise
}


def get_gps_coordinates(postal_code: str) -> tuple:
    """
    Obtenir des coordonnées GPS réalistes basées sur le code postal.
    Ajoute une variation aléatoire pour simuler différentes adresses dans le département.
    
    Args:
        postal_code: Code postal français (5 chiffres)
    
    Returns:
        tuple: (latitude, longitude)
    """
    if not postal_code or len(postal_code) < 2:
        # Coordonnées par défaut (centre de la France)
        return (46.6034, 1.8883)
    
    # Extraire le code département (2 premiers chiffres)
    dept_code = postal_code[:2]
    
    # Obtenir les coordonnées du département
    dept_coords = DEPARTEMENT_GPS.get(dept_code)
    
    if dept_coords:
        # Ajouter une variation aléatoire de ±0.1 à ±0.5 degrés
        # pour simuler différentes adresses dans le département
        lat_variation = random.uniform(-0.5, 0.5)
        lon_variation = random.uniform(-0.5, 0.5)
        
        latitude = round(dept_coords["lat"] + lat_variation, 6)
        longitude = round(dept_coords["lon"] + lon_variation, 6)
        
        return (latitude, longitude)
    else:
        # Coordonnées par défaut si département non trouvé
        return (46.6034, 1.8883)

def clean_all_clients(db: Session):
    """Supprimer tous les clients et leurs relations"""
    print("\n🗑️  Suppression de tous les clients et leurs relations...")
    
    # Supprimer dans l'ordre inverse des dépendances
    # 1. Sinistres (référencent contrats et chantiers)
    deleted_claims = db.query(ClaimModel).delete()
    print(f"  ✓ {deleted_claims} sinistres supprimés")
    
    # 2. Garanties de contrats (table d'association)
    result = db.execute(contract_guarantees.delete())
    print(f"  ✓ {result.rowcount} garanties de contrats supprimées")
    
    # 3. Historique contrats
    deleted_history = db.query(ContractHistoryModel).delete()
    print(f"  ✓ {deleted_history} historiques de contrats supprimés")
    
    # 4. Contrats
    deleted_contracts = db.query(ClientContractModel).delete()
    print(f"  ✓ {deleted_contracts} contrats supprimés")
    
    # 5. Chantiers
    deleted_sites = db.query(ConstructionSiteModel).delete()
    print(f"  ✓ {deleted_sites} chantiers supprimés")
    
    # 6. Adresses
    deleted_addresses = db.query(ClientAddressModel).delete()
    print(f"  ✓ {deleted_addresses} adresses supprimées")
    
    # 7. Clients
    deleted_clients = db.query(ClientModel).delete()
    print(f"  ✓ {deleted_clients} clients supprimés")
    
    db.commit()
    print("✅ Nettoyage terminé\n")


def generate_client(db: Session, client_number: str = None, client_type: str = None) -> ClientModel:
    """Générer un client avec des données cohérentes
    
    Args:
        db: Session de base de données
        client_number: Numéro de client spécifique (optionnel)
        client_type: Type de client ('particulier', 'entreprise', ou None pour aléatoire)
    """
    # Déterminer si c'est une entreprise selon le paramètre ou aléatoirement
    if client_type == 'entreprise':
        is_company = True
    elif client_type == 'particulier':
        is_company = False
    else:
        is_company = random.choice([True, False])
    
    if client_number is None:
        # Générer un numéro de client unique
        existing_numbers = db.query(ClientModel.client_number).all()
        existing_numbers = [n[0] for n in existing_numbers]
        while True:
            client_number = f"CLI{random.randint(1000, 9999)}"
            if client_number not in existing_numbers:
                break
    
    client = ClientModel(
        client_number=client_number,
        client_type="professionnel" if is_company else "particulier",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    if is_company:
        # Client professionnel
        client.company_name = fake.company()
        client.legal_form = random.choice(LEGAL_FORMS)
        # Générer SIREN et SIRET sans espaces
        siren = ''.join(filter(str.isdigit, fake.siren()))[:9]
        client.siren = siren
        client.siret = siren + str(random.randint(10000, 99999))[:5]  # SIRET = SIREN + 5 chiffres
        client.email = fake.company_email()
        client.phone = fake.phone_number().replace(' ', '')[:14]  # Max 14 caractères
        client.mobile = fake.phone_number().replace(' ', '')[:14] if random.random() > 0.5 else None
        client.website = f"https://www.{fake.domain_name()}"
    else:
        # Client particulier
        client.civility = random.choice(CIVILITES)
        client.first_name = fake.first_name()
        client.last_name = fake.last_name()
        client.birth_date = fake.date_of_birth(minimum_age=25, maximum_age=75)
        client.email = fake.email()
        client.phone = fake.phone_number().replace(' ', '')[:14]  # Max 14 caractères
        client.mobile = fake.phone_number().replace(' ', '')[:14] if random.random() > 0.3 else None
    
    # Adresse principale du client
    client.address_line1 = fake.street_address()
    client.postal_code = fake.postcode()
    client.city = fake.city()
    client.country = "France"
    client.is_active = True
    client.profession_code = f"PROF{random.randint(100, 999)}"
    client.notes = fake.text(max_nb_chars=200) if random.random() > 0.5 else None
    
    db.add(client)
    db.commit()
    db.refresh(client)
    
    return client


def generate_addresses(db: Session, client: ClientModel) -> list:
    """Générer des adresses pour un client"""
    addresses = []
    num_addresses = random.randint(1, 3)
    
    for i in range(num_addresses):
        address_type = random.choice(ADDRESS_TYPES)
        
        # Générer le code postal d'abord
        postal_code = fake.postcode()
        
        # Obtenir les coordonnées GPS correspondantes
        latitude, longitude = get_gps_coordinates(postal_code)
        
        address = ClientAddressModel(
            client_id=client.id,
            address_type=address_type,
            name=f"{address_type.replace('_', ' ').title()} {i+1}",
            reference=f"ADR{random.randint(1000, 9999)}",
            address_line1=fake.street_address(),
            address_line2=f"Appartement {random.randint(1, 100)}" if random.random() > 0.7 else None,
            postal_code=postal_code,
            city=fake.city(),
            department=postal_code[:2],  # Code département (2 chiffres)
            region=fake.region(),
            country="France",
            latitude=latitude,
            longitude=longitude,
            is_primary=(i == 0),
            is_active=True,
            contact_name=fake.name() if random.random() > 0.5 else None,
            contact_phone=fake.phone_number().replace(' ', '')[:14] if random.random() > 0.5 else None,
            contact_email=fake.email() if random.random() > 0.5 else None,
            notes=fake.text(max_nb_chars=100) if random.random() > 0.6 else None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Ajouter des informations spécifiques selon le type
        if address_type == "entrepot":
            address.warehouse_surface_m2 = random.randint(100, 5000)
            address.warehouse_capacity = f"{random.randint(50, 500)} palettes"
            address.stored_materials = "Matériaux de construction, Outillage"
        elif address_type == "chantier":
            address.site_start_date = date.today() - timedelta(days=random.randint(30, 365))
            address.site_end_date = date.today() + timedelta(days=random.randint(30, 730))
            address.site_status = random.choice(["en_preparation", "en_cours", "termine"])
        
        addresses.append(address)
        db.add(address)
    
    db.commit()
    return addresses


def generate_construction_site(db: Session, client: ClientModel) -> ConstructionSiteModel:
    """Générer un chantier de construction"""
    building_category = random.choice(BUILDING_CATEGORIES)
    work_category = random.choice(WORK_CATEGORIES)
    
    construction_cost = random.randint(100000, 5000000)
    land_value = random.randint(50000, 1000000) if random.random() > 0.3 else 0
    
    # Générer des coordonnées GPS cohérentes avec une vraie localisation en France
    # local_latlng retourne (latitude, longitude, place_name, country_code, timezone)
    location = fake.local_latlng(country_code='FR')
    latitude = float(location[0])
    longitude = float(location[1])
    city = location[2]  # Utiliser le vrai nom de ville
    
    # Générer le code postal français (5 chiffres)
    postal_code = f"{random.randint(1, 95):02d}{random.randint(0, 999):03d}"
    
    site = ConstructionSiteModel(
        site_reference=f"SITE{random.randint(10000, 99999)}",
        site_name=f"Projet {fake.street_name()}",
        address_line1=fake.street_address(),
        postal_code=postal_code,
        city=city,
        department=postal_code[:2],  # Code département (2 premiers chiffres)
        region=fake.region(),
        latitude=latitude,
        longitude=longitude,
        building_category_code=building_category,
        work_category_code=work_category,
        total_surface_m2=random.randint(50, 2000),
        habitable_surface_m2=random.randint(40, 1800),
        num_floors=random.randint(1, 5),
        num_units=random.randint(1, 50) if "collectif" in building_category else 1,
        construction_cost=construction_cost,
        land_value=land_value,
        total_project_value=construction_cost + land_value,
        permit_date=date.today() - timedelta(days=random.randint(180, 730)),
        opening_date=date.today() - timedelta(days=random.randint(30, 180)),
        planned_completion_date=date.today() + timedelta(days=random.randint(180, 1095)),
        foundation_type=random.choice(FOUNDATION_TYPES),
        structure_type=random.choice(STRUCTURE_TYPES),
        has_basement=random.choice([True, False]),
        has_swimming_pool=random.choice([True, False]),
        has_elevator=random.choice([True, False]) if "collectif" in building_category else False,
        seismic_zone=random.choice(SEISMIC_ZONES),
        flood_zone=random.choice([True, False]),
        soil_study_done=True,
        description=fake.text(max_nb_chars=300),
        notes=fake.text(max_nb_chars=150) if random.random() > 0.5 else None,
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    db.add(site)
    db.commit()
    db.refresh(site)
    
    return site


def generate_contract(db: Session, client: ClientModel, site: ConstructionSiteModel = None) -> ClientContractModel:
    """Générer un contrat d'assurance"""
    if site is None:
        raise ValueError("Un contrat doit obligatoirement être rattaché à un chantier")
    
    contract_type = random.choice(CONTRACT_TYPES)
    status = random.choice(["actif", "en_attente", "brouillon"])
    
    # Générer un numéro de contrat unique
    existing_numbers = db.query(ClientContractModel.contract_number).all()
    existing_numbers = [n[0] for n in existing_numbers]
    while True:
        contract_number = f"CNT{random.randint(100000, 999999)}"
        if contract_number not in existing_numbers:
            break
    
    issue_date = date.today() - timedelta(days=random.randint(1, 90))
    effective_date = issue_date + timedelta(days=random.randint(0, 30))
    duration_years = random.choice([1, 2, 3, 5, 10])
    expiry_date = effective_date + timedelta(days=365 * duration_years)
    
    insured_amount = random.randint(100000, 10000000)
    annual_premium = insured_amount * random.uniform(0.001, 0.005)
    
    contract = ClientContractModel(
        contract_number=contract_number,
        external_reference=f"EXT{random.randint(10000, 99999)}",
        contract_type_code=contract_type,
        client_id=client.id,
        construction_site_id=site.id,  # Obligatoire - chaque contrat doit avoir un chantier
        status=status,
        issue_date=issue_date,
        effective_date=effective_date,
        expiry_date=expiry_date,
        insured_amount=insured_amount,
        annual_premium=annual_premium,
        total_premium=annual_premium * duration_years,
        franchise_amount=random.randint(500, 10000),
        duration_years=duration_years,
        is_renewable=random.choice([True, False]),
        selected_guarantees=None,  # Désormais dans une table séparée
        selected_clauses=[
            {
                "code": f"CL_{i:03d}",
                "name": f"Clause {fake.word()}",
                "variables": {"montant": random.randint(1000, 50000)}
            }
            for i in range(random.randint(1, 3))
        ],
        special_conditions=fake.text(max_nb_chars=500) if random.random() > 0.5 else None,
        broker_name=fake.company() if random.random() > 0.3 else None,
        broker_code=f"BRK{random.randint(100, 999)}" if random.random() > 0.3 else None,
        underwriter=fake.name(),
        internal_notes=fake.text(max_nb_chars=200) if random.random() > 0.5 else None,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    db.add(contract)
    db.flush()  # Obtenir l'ID du contrat avant de créer les garanties
    
    # Récupérer les garanties disponibles dans le référentiel
    available_guarantees = db.query(GuaranteeModel).all()
    
    if not available_guarantees:
        print("⚠️  Aucune garantie trouvée dans le référentiel. Les garanties ne seront pas créées.")
    else:
        # Créer les garanties associées (minimum 1, jusqu'à 5 garanties par contrat)
        # IMPORTANT: Chaque contrat doit avoir au moins 1 garantie
        num_guarantees = min(random.randint(1, 5), len(available_guarantees))
        selected_guarantees = random.sample(available_guarantees, num_guarantees)
        
        guarantees_data = []
        for guarantee in selected_guarantees:
            guarantees_data.append({
                'contract_id': contract.id,
                'guarantee_code': guarantee.code,
                'custom_ceiling': guarantee.default_ceiling or random.randint(50000, 1000000),
                'custom_franchise': guarantee.default_franchise or random.randint(500, 5000),
                'is_included': True,
                'annual_premium': random.uniform(500, 5000)
            })
        
        if guarantees_data:
            db.execute(contract_guarantees.insert(), guarantees_data)
    
    db.commit()
    db.refresh(contract)
    
    return contract


def generate_contract_history(db: Session, contract: ClientContractModel) -> list:
    """Générer l'historique d'un contrat"""
    history_entries = []
    num_entries = random.randint(1, 5)
    
    for i in range(num_entries):
        action = random.choice(ACTION_TYPES)
        
        history = ContractHistoryModel(
            contract_id=contract.id,
            action=action,
            field_changed=random.choice(["status", "premium", "garanties", "conditions"]) if action == "modification" else None,
            old_value=f"{random.randint(1000, 5000)} EUR" if action == "modification" else None,
            new_value=f"{random.randint(1000, 5000)} EUR" if action == "modification" else None,
            changed_by=f"USER{random.randint(100, 999)}",
            changed_at=contract.created_at + timedelta(days=random.randint(1, 90)),
            comment=fake.text(max_nb_chars=150) if random.random() > 0.5 else None
        )
        
        history_entries.append(history)
        db.add(history)
    
    db.commit()
    return history_entries


def create_complete_client(db: Session, verbose: bool = False, client_type: str = None) -> ClientModel:
    """Créer un client complet avec toutes ses relations
    
    Args:
        db: Session de base de données
        verbose: Afficher les détails de création
        client_type: Type de client ('particulier', 'entreprise', ou None pour aléatoire)
    """
    # 1. Créer le client
    client = generate_client(db, client_type=client_type)
    if verbose:
        nom = client.company_name if client.client_type == "professionnel" else f"{client.first_name} {client.last_name}"
        print(f"  ✓ Client créé: {client.client_number} - {nom}")
    
    # 2. Créer les adresses
    addresses = generate_addresses(db, client)
    if verbose:
        print(f"  ✓ {len(addresses)} adresse(s) créée(s)")
    
    # 3. Créer des chantiers (1 à 3)
    num_sites = random.randint(1, 3)
    sites = []
    for _ in range(num_sites):
        site = generate_construction_site(db, client)
        sites.append(site)
    if verbose:
        print(f"  ✓ {len(sites)} chantier(s) créé(s)")
    
    # 4. Créer des contrats (1 à 4)
    # IMPORTANT: Chaque contrat doit avoir un chantier rattaché
    num_contracts = random.randint(1, 4)
    contracts = []
    
    # Créer tous les contrats en associant obligatoirement un chantier
    for i in range(num_contracts):
        # Associer obligatoirement un chantier au contrat (plusieurs contrats peuvent partager le même chantier)
        site = random.choice(sites)
        contract = generate_contract(db, client, site)
        contracts.append(contract)
        
        # 5. Créer l'historique du contrat
        history = generate_contract_history(db, contract)
    
    if verbose:
        print(f"  ✓ {len(contracts)} contrat(s) créé(s) avec historique")
    
    return client


def main():
    parser = argparse.ArgumentParser(
        description="Générer des données clients avec toutes leurs relations"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Supprimer tous les clients et leurs relations"
    )
    parser.add_argument(
        "--create",
        action="store_true",
        help="Créer un ou plusieurs clients avec toutes leurs relations"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=1,
        help="Nombre de clients à créer (défaut: 1)"
    )
    parser.add_argument(
        "--type",
        type=str,
        choices=["particulier", "entreprise", "mixte"],
        default="mixte",
        help="Type de clients à créer: 'particulier', 'entreprise', ou 'mixte' (défaut: mixte)"
    )
    
    args = parser.parse_args()
    
    # Créer une session de base de données
    db = SessionLocal()
    
    try:
        if args.clean:
            clean_all_clients(db)
        
        if args.create:
            # Afficher le type de clients à créer
            type_msg = {
                "particulier": "particuliers",
                "entreprise": "entreprises",
                "mixte": "(particuliers et entreprises)"
            }.get(args.type, "")
            print(f"\n📦 Création de {args.count} client(s) {type_msg} avec toutes leurs relations...\n")
            
            for i in range(args.count):
                print(f"Client {i+1}/{args.count}:")
                # Déterminer le type pour ce client
                if args.type == "mixte":
                    client_type = None  # Aléatoire
                else:
                    client_type = args.type
                
                client = create_complete_client(db, verbose=True, client_type=client_type)
                print()
            
            # Afficher un résumé
            total_clients = db.query(ClientModel).count()
            total_addresses = db.query(ClientAddressModel).count()
            total_sites = db.query(ConstructionSiteModel).count()
            total_contracts = db.query(ClientContractModel).count()
            total_history = db.query(ContractHistoryModel).count()
            
            print("=" * 60)
            print("📊 RÉSUMÉ DE LA BASE DE DONNÉES")
            print("=" * 60)
            print(f"  Clients:              {total_clients}")
            print(f"  Adresses:             {total_addresses}")
            print(f"  Chantiers:            {total_sites}")
            print(f"  Contrats:             {total_contracts}")
            print(f"  Historiques:          {total_history}")
            print("=" * 60)
            print("✅ Génération terminée avec succès\n")
        
        if not args.clean and not args.create:
            parser.print_help()
    
    except Exception as e:
        print(f"\n❌ Erreur: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
