# 🏗️ Architecture du Serveur FastAPI

## Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────────┐
│                      CLIENT (Browser/App)                        │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP/REST
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                         FastAPI Server                           │
│                       (main.py - Port 8000)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐ │
│  │   Router Layer   │  │  Schema Layer    │  │  Config Layer │ │
│  │  (app/routers/)  │  │ (app/schemas.py) │  │(app/config.py)│ │
│  │                  │  │                  │  │               │ │
│  │ • clients.py     │  │ • Validation     │  │ • DATABASE_   │ │
│  │ • contracts.py   │  │ • Serialization  │  │   settings    │ │
│  │ • sites.py       │  │ • Request/       │  │ • API config  │ │
│  │ • referentials.py│  │   Response       │  │ • CORS        │ │
│  └──────┬───────────┘  └──────────────────┘  └───────────────┘ │
│         │                                                         │
│         ▼                                                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │             Database Layer (app/database.py)             │   │
│  │  • SessionLocal (SQLAlchemy session factory)            │   │
│  │  • get_db() dependency injection                         │   │
│  └───────────────────────────┬─────────────────────────────┘   │
│                               │                                   │
│                               ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Models Layer (app/models.py)                │   │
│  │  • ORM Models (SQLAlchemy)                              │   │
│  │  • Table definitions                                     │   │
│  │  • Relationships                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
└───────────────────────────────┬───────────────────────────────────┘
                                │ SQL Queries
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   PostgreSQL Database                             │
│                      (gautiersa.fr:5432)                         │
│                       Database: dwh                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌────────────────────┐  ┌────────────────────┐                │
│  │  Business Tables   │  │  Referential Tables│                │
│  │                    │  │                    │                │
│  │ • clients          │  │ • ref_insurance_   │                │
│  │ • client_addresses │  │   contract_types   │                │
│  │ • client_contracts │  │ • ref_guarantees   │                │
│  │ • construction_    │  │ • ref_contract_    │                │
│  │   sites            │  │   clauses          │                │
│  │ • contract_history │  │ • ref_building_    │                │
│  │                    │  │   categories       │                │
│  │                    │  │ • ref_work_        │                │
│  │                    │  │   categories       │                │
│  │                    │  │ • ref_professions  │                │
│  │                    │  │ • ref_franchise_   │                │
│  │                    │  │   grids            │                │
│  │                    │  │ • ref_exclusions   │                │
│  └────────────────────┘  └────────────────────┘                │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Flux de requête typique

### Exemple : Créer un client

```
1. CLIENT
   │
   │ POST /clients/
   │ {
   │   "client_number": "CLI-2024-001",
   │   "client_type": "entreprise",
   │   "company_name": "Test SA",
   │   ...
   │ }
   ▼
2. FASTAPI (main.py)
   │
   │ Route matching
   ▼
3. ROUTER (app/routers/clients.py)
   │
   │ @router.post("/")
   │ def create_client(client: schemas.ClientCreate, db: Session)
   ▼
4. SCHEMA VALIDATION (app/schemas.py)
   │
   │ ClientCreate validates:
   │  - client_number (required, string)
   │  - client_type (required, enum)
   │  - email (optional, format check)
   │  - etc.
   ▼
5. DATABASE SESSION (app/database.py)
   │
   │ get_db() provides SQLAlchemy session
   ▼
6. MODEL CREATION (app/models.py)
   │
   │ db_client = ClientModel(
   │   id=str(uuid.uuid4()),
   │   **client.model_dump()
   │ )
   │ db.add(db_client)
   │ db.commit()
   ▼
7. POSTGRESQL
   │
   │ INSERT INTO clients (id, client_number, ...)
   │ VALUES (...)
   ▼
8. RESPONSE
   │
   │ return db_client
   │ → Pydantic serialization
   │ → JSON response with HTTP 201
   ▼
9. CLIENT
   │
   │ Receives JSON:
   │ {
   │   "id": "uuid...",
   │   "client_number": "CLI-2024-001",
   │   "created_at": "2024-02-02T...",
   │   ...
   │ }
```

## Structure des fichiers détaillée

```
sma_dwh/
│
├── main.py                         # Application FastAPI principale
│   ├── FastAPI app creation
│   ├── CORS middleware
│   ├── Lifespan events (startup/shutdown)
│   ├── Router inclusion
│   └── Root endpoints (/, /health)
│
├── app/
│   ├── __init__.py
│   │
│   ├── config.py                   # Configuration
│   │   ├── Settings class (Pydantic)
│   │   ├── DATABASE_* variables
│   │   ├── API_* variables
│   │   └── settings instance
│   │
│   ├── database.py                 # Database setup
│   │   ├── SQLAlchemy engine
│   │   ├── SessionLocal factory
│   │   ├── Base (declarative_base)
│   │   ├── get_db() dependency
│   │   └── init_db() function
│   │
│   ├── models.py                   # ORM Models
│   │   ├── Enums (Status, Types, Categories)
│   │   ├── Association tables
│   │   ├── ClientModel
│   │   ├── ClientAddressModel
│   │   ├── ConstructionSiteModel
│   │   ├── ClientContractModel
│   │   ├── ContractHistoryModel
│   │   ├── InsuranceContractTypeModel
│   │   ├── GuaranteeModel
│   │   ├── ContractClauseModel
│   │   ├── BuildingCategoryModel
│   │   ├── WorkCategoryModel
│   │   ├── ProfessionModel
│   │   ├── FranchiseGridModel
│   │   ├── ExclusionModel
│   │   └── DEFAULT_* data
│   │
│   ├── schemas.py                  # Pydantic Schemas
│   │   ├── Enums (mirror models)
│   │   ├── Base schemas (Base, Create, Update, Response)
│   │   │   ├── ClientBase/Create/Update/Client
│   │   │   ├── ClientAddressBase/Create/Update/ClientAddress
│   │   │   ├── ConstructionSiteBase/Create/Update/ConstructionSite
│   │   │   ├── ClientContractBase/Create/Update/ClientContract
│   │   │   ├── InsuranceContractTypeBase/Create/InsuranceContractType
│   │   │   ├── GuaranteeBase/Create/Guarantee
│   │   │   ├── ContractClauseBase/Create/ContractClause
│   │   │   ├── BuildingCategoryBase/Create/BuildingCategory
│   │   │   ├── WorkCategoryBase/Create/WorkCategory
│   │   │   └── ProfessionBase/Create/Profession
│   │   ├── PaginatedResponse
│   │   └── ContractStatistics
│   │
│   └── routers/
│       ├── __init__.py
│       │
│       ├── clients.py              # Client routes
│       │   ├── POST   /clients/
│       │   ├── GET    /clients/
│       │   ├── GET    /clients/{id}
│       │   ├── GET    /clients/number/{number}
│       │   ├── PUT    /clients/{id}
│       │   ├── DELETE /clients/{id}
│       │   ├── POST   /clients/{id}/addresses
│       │   ├── GET    /clients/{id}/addresses
│       │   ├── GET    /clients/addresses/{id}
│       │   ├── PUT    /clients/addresses/{id}
│       │   └── DELETE /clients/addresses/{id}
│       │
│       ├── contracts.py            # Contract routes
│       │   ├── POST   /contracts/
│       │   ├── GET    /contracts/
│       │   ├── GET    /contracts/{id}
│       │   ├── GET    /contracts/number/{number}
│       │   ├── PUT    /contracts/{id}
│       │   ├── DELETE /contracts/{id}
│       │   └── GET    /contracts/statistics/summary
│       │
│       ├── sites.py                # Construction site routes
│       │   ├── POST   /sites/
│       │   ├── GET    /sites/
│       │   ├── GET    /sites/{id}
│       │   ├── GET    /sites/reference/{ref}
│       │   ├── PUT    /sites/{id}
│       │   └── DELETE /sites/{id}
│       │
│       └── referentials.py         # Referential routes
│           ├── Contract Types
│           │   ├── POST /referentials/contract-types
│           │   ├── GET  /referentials/contract-types
│           │   └── GET  /referentials/contract-types/{code}
│           ├── Guarantees
│           │   ├── POST /referentials/guarantees
│           │   ├── GET  /referentials/guarantees
│           │   └── GET  /referentials/guarantees/{code}
│           ├── Clauses
│           │   ├── POST /referentials/clauses
│           │   ├── GET  /referentials/clauses
│           │   └── GET  /referentials/clauses/{code}
│           ├── Building Categories
│           │   ├── POST /referentials/building-categories
│           │   ├── GET  /referentials/building-categories
│           │   └── GET  /referentials/building-categories/{code}
│           ├── Work Categories
│           │   ├── POST /referentials/work-categories
│           │   ├── GET  /referentials/work-categories
│           │   └── GET  /referentials/work-categories/{code}
│           └── Professions
│               ├── POST /referentials/professions
│               ├── GET  /referentials/professions
│               └── GET  /referentials/professions/{code}
│
├── init_data.py                    # Database initialization script
│   ├── init_db() - Create tables
│   ├── init_referential_data() - Populate referentials
│   └── main() - Entry point
│
├── test_api.py                     # API testing script
│   └── test_api() - Test all endpoints
│
├── requirements.txt                # Python dependencies
│   ├── fastapi
│   ├── uvicorn
│   ├── sqlalchemy
│   ├── psycopg2-binary
│   ├── pydantic
│   └── ...
│
├── .env                            # Environment variables (local)
├── .env.example                    # Environment template
├── .gitignore                      # Git ignore rules
│
├── README.md                       # Complete documentation
├── QUICKSTART.md                   # Quick start guide
├── PROJECT_SUMMARY.md              # Project summary
├── DATA_MODELS.md                  # Data models documentation
├── ARCHITECTURE.md                 # This file
└── api_examples.http               # HTTP request examples
```

## Technologies utilisées

### Backend Framework
- **FastAPI** 0.115.0 - Modern web framework
- **Uvicorn** 0.32.0 - ASGI server

### Database
- **PostgreSQL** - Relational database
- **SQLAlchemy** 2.0.36 - ORM
- **psycopg2** 2.9.10 - PostgreSQL adapter

### Validation & Serialization
- **Pydantic** 2.9.2 - Data validation
- **pydantic-settings** 2.6.1 - Settings management

### Utilities
- **python-dotenv** - Environment variables
- **python-multipart** - Form data support

## Sécurité

### Actuellement implémenté
✅ CORS configuré
✅ Validation des données (Pydantic)
✅ Connexion sécurisée PostgreSQL
✅ Soft delete pour certaines entités
✅ Séparation configuration/code

### À ajouter pour la production
⚠️ Authentification (JWT, OAuth2)
⚠️ Rate limiting
⚠️ HTTPS/TLS
⚠️ Logs structurés
⚠️ Monitoring
⚠️ Backup automatique

## Performance

### Optimisations présentes
- Connection pooling (SQLAlchemy)
- Requêtes optimisées avec filtres
- Pagination sur les listes
- Index sur les clés uniques

### Possibles améliorations
- Cache Redis pour les référentiels
- Requêtes asynchrones (async/await)
- Compression des réponses
- CDN pour les assets statiques

## Déploiement

### Développement
```bash
python main.py
# ou
uvicorn main:app --reload
```

### Production
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker (optionnel)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Monitoring & Logs

### Health Check
```
GET /health
Response: {"status": "healthy", "database": "connected"}
```

### Logs
- SQLAlchemy logs activés en développement
- À enrichir avec logging structuré en production

## API Documentation

### Auto-générée par FastAPI
- **Swagger UI** : http://localhost:8000/docs
- **ReDoc** : http://localhost:8000/redoc
- **OpenAPI Schema** : http://localhost:8000/openapi.json

---

📚 Pour plus d'informations :
- [README.md](README.md) - Documentation complète
- [QUICKSTART.md](QUICKSTART.md) - Guide de démarrage
- [DATA_MODELS.md](DATA_MODELS.md) - Documentation des modèles
