# Serveur FastAPI - Gestion d'assurances

API RESTful pour la gestion de données d'assurance sur PostgreSQL.

## 🚀 Démarrage

### Installation des dépendances

```bash
pip install fastapi==0.115.0 uvicorn sqlalchemy psycopg2-binary faker
```

### Configuration de la base de données

La connexion PostgreSQL est configurée dans `app/database.py` :
- Serveur : gautiersa.fr:5432
- Base de données : dwh
- Utilisateur : autogere

### Démarrage du serveur

```bash
python3 main.py
```

Le serveur démarre sur http://127.0.0.1:8000

Documentation interactive : http://127.0.0.1:8000/docs

## 📊 Structure des données

### Tables principales

Toutes les tables sont préfixées par `fake_` :

- **fake_clients** : Clients (particuliers et entreprises)
- **fake_client_addresses** : Adresses des clients (siège social, entrepôts, chantiers)
- **fake_construction_sites** : Chantiers/ouvrages assurés
- **fake_client_contracts** : Contrats d'assurance
- **fake_contract_history** : Historique des modifications de contrats

### Tables référentielles

- **fake_ref_insurance_contract_types** : Types de contrats d'assurance
- **fake_ref_guarantees** : Garanties disponibles
- **fake_ref_contract_clauses** : Clauses contractuelles
- **fake_ref_building_categories** : Catégories de bâtiments
- **fake_ref_work_categories** : Catégories de travaux
- **fake_ref_professions** : Professions
- **fake_ref_franchise_grids** : Grilles de franchises
- **fake_ref_exclusions** : Exclusions

## 🔧 API Endpoints

### Clients

#### Liste des clients
```bash
GET /clients/
```

#### Détails d'un client
```bash
GET /clients/{client_id}
```

#### Informations complètes d'un client
```bash
GET /clients/{client_id}/full
```

Retourne toutes les informations du client, incluant :
- Informations client
- Toutes les adresses (siège social, entrepôts, chantiers)
- Tous les contrats avec leurs détails :
  - Garanties sélectionnées
  - Clauses spécifiques
  - Chantier associé (si applicable)
  - Historique des modifications
- Statistiques globales :
  - Nombre total d'adresses
  - Nombre total de contrats
  - Montant total assuré
  - Prime annuelle totale

#### Recherche de clients (phonétique)
```bash
GET /clients/search?query=<terme>
```

Recherche par :
- Numéro de client (exact)
- Nom de famille (phonétique avec algorithme Soundex adapté au français)

Exemples :
```bash
# Par numéro de client
curl "http://127.0.0.1:8000/clients/search?query=CLI1751"

# Par nom (recherche phonétique)
curl "http://127.0.0.1:8000/clients/search?query=pottier"
```

### Contrats

```bash
GET /contracts/                    # Liste
GET /contracts/{contract_id}       # Détails
POST /contracts/                   # Créer
PUT /contracts/{contract_id}       # Modifier
DELETE /contracts/{contract_id}    # Supprimer
```

### Chantiers

```bash
GET /construction-sites/                         # Liste
GET /construction-sites/{site_id}                # Détails
GET /construction-sites/reference/{reference}    # Par référence
POST /construction-sites/                        # Créer
PUT /construction-sites/{site_id}                # Modifier
DELETE /construction-sites/{site_id}             # Supprimer
```

### Référentiels

Chaque table référentielle dispose des endpoints :
```bash
GET /<resource>/           # Liste
GET /<resource>/{id}       # Détails
POST /<resource>/          # Créer
PUT /<resource>/{id}       # Modifier
DELETE /<resource>/{id}    # Supprimer
```

Ressources disponibles :
- `/contract-types/` : Types de contrats
- `/guarantees/` : Garanties
- `/clauses/` : Clauses
- `/building-categories/` : Catégories de bâtiments
- `/work-categories/` : Catégories de travaux
- `/professions/` : Professions
- `/franchise-grids/` : Grilles de franchises
- `/exclusions/` : Exclusions

## 🎲 Génération de données de test

Le script `generate_client_data.py` permet de créer des données de test cohérentes en français.

### Options

```bash
# Supprimer tous les clients et leurs relations
python3 generate_client_data.py --clean

# Créer des clients avec toutes leurs relations
python3 generate_client_data.py --create --count <nombre>

# Créer uniquement des particuliers
python3 generate_client_data.py --create --count 5 --type particulier

# Créer uniquement des entreprises
python3 generate_client_data.py --create --count 3 --type entreprise

# Créer un mélange (par défaut)
python3 generate_client_data.py --create --count 10 --type mixte

# Nettoyer et créer en une seule commande
python3 generate_client_data.py --clean --create --count 5
```

**Option `--type`** :
- `particulier` : Génère uniquement des clients particuliers (personnes physiques)
- `entreprise` : Génère uniquement des clients professionnels (entreprises)
- `mixte` : Génère un mélange aléatoire de particuliers et d'entreprises (défaut)

### Données générées par client

Pour chaque client créé, le script génère automatiquement :

1. **Client** (particulier ou entreprise)
   - Informations personnelles (nom, prénom, civilité, date de naissance)
   - OU informations entreprise (raison sociale, forme juridique, SIRET/SIREN)
   - Contact (email, téléphone, mobile)
   - Profession aléatoire

2. **Adresses** (1 à 3 par client)
   - Siège social (obligatoire)
   - 0-1 entrepôt
   - 0-1 chantier
   - Données françaises cohérentes (codes postaux, départements)

3. **Chantier** (optionnel, 50% des clients)
   - Référence unique
   - Localisation complète
   - Montants (coût construction, valeur projet)
   - Dates (ouverture, fin prévue)
   - Caractéristiques (surface, nombre d'étages, etc.)

4. **Contrats** (1 à 4 par client)
   - Type de contrat aléatoire
   - Montants (assuré, prime annuelle, franchise)
   - Dates (émission, effet, expiration)
   - Statut (brouillon, actif, etc.)
   - 2-5 garanties sélectionnées
   - 1-3 clauses spécifiques
   - Lié au chantier si disponible

5. **Historique** (1 à 5 entrées par contrat)
   - Actions (création, modification, renouvellement, etc.)
   - Horodatage
   - Utilisateur
   - Commentaires

### Exemples d'utilisation

```bash
# Créer 10 clients de test
python3 generate_client_data.py --clean --create --count 10

# Ajouter 5 clients supplémentaires
python3 generate_client_data.py --create --count 5
```

### Sortie du script

Le script affiche un résumé détaillé :

```
✅ Tous les clients et données associées ont été supprimés

Création de 2 clients avec toutes leurs relations...

✅ Client créé : CLI1751 - Françoise Pottier
   📍 Adresses créées : 2
   🏗️ Chantier créé : Projet boulevard Roland Costa
   📄 Contrats créés : 2

✅ Client créé : CLI3357 - Susan Fontaine
   📍 Adresses créées : 2
   🏗️ Chantier créé : Projet chemin de Dubois
   📄 Contrats créés : 4

📊 Résumé de la génération :
   Clients créés      : 2
   Adresses créées    : 4
   Chantiers créés    : 2
   Contrats créés     : 6
   Historiques créés  : 15
```

### Données françaises cohérentes

Le script utilise la librairie `Faker` avec la locale française (`fr_FR`) :
- Noms et prénoms français
- Adresses françaises réelles
- Codes postaux valides (5 chiffres)
- Départements calculés à partir du code postal
- Numéros de téléphone au format français
- SIRET/SIREN pour les entreprises
- Professions françaises

## 🔍 Exemples d'utilisation

### Récupérer toutes les informations d'un client

```bash
curl http://127.0.0.1:8000/clients/11/full | python3 -m json.tool
```

Exemple de réponse :
```json
{
    "client": {
        "id": 11,
        "client_number": "CLI1751",
        "first_name": "Françoise",
        "last_name": "Pottier",
        "email": "epinto@example.net",
        ...
    },
    "addresses": [
        {
            "address_type": "siege_social",
            "address_line1": "62, rue de Denis",
            "postal_code": "23468",
            "city": "Dupréboeuf",
            ...
        }
    ],
    "contracts": [
        {
            "contract_number": "CNT573827",
            "status": "brouillon",
            "insured_amount": 5295845.0,
            "construction_site": {...},
            "selected_guarantees": [...],
            "history": [...]
        }
    ],
    "stats": {
        "total_addresses": 2,
        "total_contracts": 2,
        "total_insured_amount": 11537011.0,
        "total_annual_premium": 38298.56
    }
}
```

### Rechercher un client

```bash
# Par numéro
curl "http://127.0.0.1:8000/clients/search?query=CLI3357" | python3 -m json.tool

# Par nom (recherche phonétique)
curl "http://127.0.0.1:8000/clients/search?query=fontaine" | python3 -m json.tool
```

## 📁 Structure du projet

```
sma_dwh/
├── app/
│   ├── __init__.py
│   ├── database.py          # Configuration DB
│   ├── models.py            # Modèles SQLAlchemy (15 tables)
│   ├── schemas.py           # Schémas Pydantic
│   ├── enums.py             # Énumérations
│   └── routers/
│       ├── clients.py       # Endpoints clients
│       ├── contracts.py     # Endpoints contrats
│       ├── sites.py         # Endpoints chantiers
│       └── referentials.py  # Endpoints référentiels
├── main.py                  # Point d'entrée
├── generate_client_data.py  # Script de génération de données
└── README.md               # Cette documentation
```

## 🔐 Caractéristiques techniques

### Authentification et sécurité
- Base de données PostgreSQL avec authentification
- Validation des données avec Pydantic
- Gestion des erreurs HTTP appropriée

### Performance
- ORM SQLAlchemy avec support des relations complexes
- Chargement optimisé avec `joinedload` pour les relations
- Index sur les champs de recherche fréquents

### Qualité du code
- Séparation des responsabilités (models, schemas, routers)
- Documentation automatique OpenAPI/Swagger
- Schémas de validation pour toutes les entrées/sorties
- Gestion cohérente des types (Integer pour les IDs)

## 🌐 Documentation API interactive

Une fois le serveur démarré, accédez à :
- **Swagger UI** : http://127.0.0.1:8000/docs
- **ReDoc** : http://127.0.0.1:8000/redoc

## ⚙️ Configuration

### Base de données

Modifier dans `app/database.py` :
```python
DATABASE_URL = "postgresql://user:password@host:port/database"
```

### Port du serveur

Modifier dans `main.py` :
```python
uvicorn.run(app, host="0.0.0.0", port=8000)
```

## 🧪 Tests

### Vérifier l'état du serveur

```bash
curl http://127.0.0.1:8000/
```

### Lister tous les clients

```bash
curl http://127.0.0.1:8000/clients/ | python3 -m json.tool
```

### Tester la recherche phonétique

```bash
curl "http://127.0.0.1:8000/clients/search?query=martin" | python3 -m json.tool
```

## 📝 Notes

- Tous les noms de tables sont préfixés par `fake_` pour identifier facilement les données de test
- Les IDs sont de type Integer avec auto-incrémentation
- La recherche phonétique utilise un algorithme Soundex adapté au français
- Le script de génération crée des données cohérentes et réalistes
- Les montants sont en euros (€)
- Les dates sont au format ISO 8601

## 🐛 Dépannage

### Le serveur ne démarre pas
Vérifier les dépendances :
```bash
pip install --upgrade fastapi uvicorn sqlalchemy psycopg2-binary
```

### Erreur de connexion à la base de données
- Vérifier que PostgreSQL est accessible
- Vérifier les credentials dans `app/database.py`
- Tester la connexion avec `psql`

### Erreurs lors de la génération de données
- Vérifier que la base de données est accessible
- S'assurer que les tables sont créées
- Utiliser `--clean` pour repartir à zéro

## 📚 Ressources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Faker Documentation](https://faker.readthedocs.io/)

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
