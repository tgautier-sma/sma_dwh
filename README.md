# API FastAPI Gestion Assurance Construction

API REST pour gérer les données d'assurance construction stockées sur PostgreSQL.

## 🚀 Fonctionnalités

- **Gestion des clients** : CRUD complet pour les clients (particuliers, entreprises, professionnels)
- **Gestion des adresses** : Sièges sociaux, entrepôts, chantiers
- **Gestion des contrats** : Contrats d'assurance DO, RCD, TRC, etc.
- **Gestion des chantiers** : Ouvrages et sites de construction
- **Référentiels** : Types de contrats, garanties, clauses, catégories, professions

## 📋 Prérequis

- Python 3.8+
- PostgreSQL 12+
- pip

## 🔧 Installation

1. **Cloner le projet** (si applicable)

2. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

3. **Configurer la base de données**

Créer un fichier `.env` à la racine du projet :
```bash
cp .env.example .env
```

Modifier le fichier `.env` avec vos paramètres :
```env
DATABASE_HOST=gautiersa.fr
DATABASE_PORT=5432
DATABASE_NAME=insurance_db
DATABASE_USER=postgres
DATABASE_PASSWORD=votre_mot_de_passe
```

4. **Initialiser la base de données**

La base de données sera automatiquement initialisée au premier démarrage du serveur.

## 🏃 Lancer le serveur

### Mode développement (avec rechargement automatique)
```bash
python main.py
```

ou

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Mode production
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

Le serveur sera accessible sur : **http://localhost:8000**

## 📚 Documentation

Une fois le serveur lancé, la documentation interactive est disponible :

- **Swagger UI** : http://localhost:8000/docs
- **ReDoc** : http://localhost:8000/redoc

## 🔌 Endpoints principaux

### Clients
- `POST /clients/` - Créer un client
- `GET /clients/` - Liste des clients (avec filtres)
- `GET /clients/{client_id}` - Détails d'un client
- `PUT /clients/{client_id}` - Mettre à jour un client
- `DELETE /clients/{client_id}` - Supprimer un client

### Adresses clients
- `POST /clients/{client_id}/addresses` - Ajouter une adresse
- `GET /clients/{client_id}/addresses` - Liste des adresses d'un client
- `PUT /clients/addresses/{address_id}` - Mettre à jour une adresse
- `DELETE /clients/addresses/{address_id}` - Supprimer une adresse

### Contrats
- `POST /contracts/` - Créer un contrat
- `GET /contracts/` - Liste des contrats (avec filtres)
- `GET /contracts/{contract_id}` - Détails d'un contrat
- `PUT /contracts/{contract_id}` - Mettre à jour un contrat
- `GET /contracts/statistics/summary` - Statistiques des contrats

### Chantiers
- `POST /sites/` - Créer un chantier
- `GET /sites/` - Liste des chantiers (avec filtres)
- `GET /sites/{site_id}` - Détails d'un chantier
- `PUT /sites/{site_id}` - Mettre à jour un chantier

### Référentiels
- `GET /referentials/contract-types` - Types de contrats
- `GET /referentials/guarantees` - Garanties
- `GET /referentials/clauses` - Clauses contractuelles
- `GET /referentials/building-categories` - Catégories de bâtiments
- `GET /referentials/work-categories` - Catégories de travaux
- `GET /referentials/professions` - Professions du bâtiment

## 📦 Structure du projet

```
sma_dwh/
├── app/
│   ├── __init__.py
│   ├── config.py           # Configuration de l'application
│   ├── database.py         # Configuration de la base de données
│   ├── models.py           # Modèles SQLAlchemy
│   ├── schemas.py          # Schémas Pydantic
│   └── routers/
│       ├── __init__.py
│       ├── clients.py      # Routes clients et adresses
│       ├── contracts.py    # Routes contrats
│       ├── sites.py        # Routes chantiers
│       └── referentials.py # Routes référentiels
├── main.py                 # Point d'entrée de l'application
├── requirements.txt        # Dépendances Python
├── .env.example            # Exemple de configuration
└── README.md               # Ce fichier
```

## 🗃️ Modèle de données

### Tables principales
- **clients** : Informations sur les clients assurés
- **client_addresses** : Adresses multiples des clients (sièges, entrepôts, chantiers)
- **client_contracts** : Contrats d'assurance
- **construction_sites** : Chantiers et ouvrages
- **contract_history** : Historique des modifications de contrats

### Tables de référentiel
- **ref_insurance_contract_types** : Types de contrats (DO, RCD, TRC, etc.)
- **ref_guarantees** : Garanties d'assurance
- **ref_contract_clauses** : Clauses contractuelles
- **ref_building_categories** : Catégories de bâtiments
- **ref_work_categories** : Catégories de travaux
- **ref_professions** : Professions du bâtiment
- **ref_exclusions** : Exclusions types

## 🔐 Sécurité

Pour la production, pensez à :
- Utiliser des variables d'environnement sécurisées
- Activer HTTPS
- Ajouter une authentification (JWT, OAuth2)
- Limiter les CORS aux domaines autorisés
- Mettre en place des rate limits

## 📝 Exemple d'utilisation

### Créer un client
```bash
curl -X POST "http://localhost:8000/clients/" \
  -H "Content-Type: application/json" \
  -d '{
    "client_number": "CLI-2024-001",
    "client_type": "entreprise",
    "company_name": "Entreprise Construction SA",
    "siret": "12345678901234",
    "email": "contact@entreprise.fr",
    "phone": "0123456789",
    "address_line1": "10 rue de la Construction",
    "postal_code": "75001",
    "city": "Paris"
  }'
```

### Récupérer la liste des contrats actifs
```bash
curl "http://localhost:8000/contracts/?status=actif"
```

## 🛠️ Migrations de base de données

Pour gérer les évolutions de schéma, vous pouvez utiliser Alembic :

```bash
# Initialiser Alembic (première fois)
alembic init alembic

# Créer une migration
alembic revision --autogenerate -m "Description de la migration"

# Appliquer les migrations
alembic upgrade head
```

## 📞 Support

Pour toute question ou problème, contactez l'équipe de développement.

## 📄 Licence

Tous droits réservés - 2024
