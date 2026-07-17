"""Application principale FastAPI"""
from fastapi import FastAPI, BackgroundTasks, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session
from fastapi import Depends
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import Optional
import subprocess
import os

from app.config import settings
from app.database import init_db, get_db
from app.routers import clients, contracts, sites, referentials, addresses, history, claims, diagrams, sales_reps, visits, proposals, analytics


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie de l'application"""
    # Démarrage : initialisation de la base de données
    print("🚀 Initialisation de la base de données...")
    try:
        init_db()
        print("✅ Base de données initialisée avec succès")
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation de la base de données: {e}")
    
    yield
    
    # Arrêt : nettoyage si nécessaire
    print("👋 Arrêt de l'application")


# Création de l'application FastAPI
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=settings.API_DESCRIPTION,
    lifespan=lifespan,
    redirect_slashes=False  # Désactiver la redirection automatique des slashes
)

# Middleware pour gérer les headers de proxy (HTTPS)
@app.middleware("http")
async def proxy_headers_middleware(request: Request, call_next):
    """Middleware pour gérer les headers X-Forwarded-* du proxy"""
    # Si on est derrière un proxy HTTPS, on doit récupérer le bon schéma
    forwarded_proto = request.headers.get("X-Forwarded-Proto")
    if forwarded_proto:
        request.scope["scheme"] = forwarded_proto
    
    response = await call_next(request)
    return response

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion des routers
app.include_router(clients.router)
app.include_router(addresses.router)
app.include_router(contracts.router)
app.include_router(sites.router)
app.include_router(referentials.router)
app.include_router(history.router)
app.include_router(claims.router)
app.include_router(diagrams.router)
app.include_router(sales_reps.router)
app.include_router(visits.router)
app.include_router(proposals.router)
app.include_router(analytics.router)

# Montage des fichiers statiques pour le front-end
frontend_path = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")


@app.get("/", tags=["Root"])
def root():
    """Serve the frontend application"""
    frontend_index = os.path.join(frontend_path, "index.html")
    if os.path.exists(frontend_index):
        return FileResponse(frontend_index)
    return {
        "message": "API Gestion Assurance Construction",
        "version": settings.API_VERSION,
        "documentation": "/docs",
        "frontend": "Frontend files not found. Access API docs at /docs",
        "status": "operational"
    }


@app.get("/diagram-editor", tags=["Root"])
@app.get("/diagram-editor/", tags=["Root"])
def diagram_editor():
    """Serve the Mermaid diagram editor"""
    editor_path = os.path.join(frontend_path, "diagram_editor.html")
    if os.path.exists(editor_path):
        return FileResponse(editor_path)
    raise HTTPException(status_code=404, detail="Diagram editor not found")


@app.get("/health", tags=["Health"])
def health_check():
    """Vérification de la santé de l'API"""
    return {
        "status": "healthy",
        "database": "connected"
    }


@app.get("/stats/", tags=["Statistics"])
@app.get("/stats", tags=["Statistics"])
def get_statistics(db: Session = Depends(get_db)):
    """Obtenir les statistiques globales de la base de données"""
    from app.models import (
        ClientModel, ClientAddressModel, ConstructionSiteModel, ClientContractModel,
        SalesRepModel, ClientVisitModel, InsuranceProposalModel
    )

    total_clients = db.query(ClientModel).count()
    total_addresses = db.query(ClientAddressModel).count()
    total_construction_sites = db.query(ConstructionSiteModel).count()
    total_contracts = db.query(ClientContractModel).count()
    total_sales_reps = db.query(SalesRepModel).count()
    total_visits = db.query(ClientVisitModel).count()
    total_proposals = db.query(InsuranceProposalModel).count()
    
    # Statistiques par type de client
    clients_particulier = db.query(ClientModel).filter(ClientModel.client_type == 'particulier').count()
    clients_professionnel = db.query(ClientModel).filter(ClientModel.client_type == 'professionnel').count()
    
    # Statistiques par statut de contrat
    from sqlalchemy import func
    contracts_by_status = db.query(
        ClientContractModel.status,
        func.count(ClientContractModel.id)
    ).group_by(ClientContractModel.status).all()
    
    return {
        "total_clients": total_clients,
        "total_addresses": total_addresses,
        "total_construction_sites": total_construction_sites,
        "total_contracts": total_contracts,
        "total_sales_reps": total_sales_reps,
        "total_visits": total_visits,
        "total_proposals": total_proposals,
        "clients_by_type": {
            "particulier": clients_particulier,
            "professionnel": clients_professionnel
        },
        "contracts_by_status": {status: count for status, count in contracts_by_status}
    }


def format_size(size_bytes: int) -> str:
    """Formate une taille en octets en unité lisible (Ko, Mo, Go...)"""
    size = float(size_bytes or 0)
    for unit in ["o", "Ko", "Mo", "Go", "To"]:
        if size < 1024 or unit == "To":
            return f"{size:.0f} {unit}" if unit == "o" else f"{size:.1f} {unit}"
        size /= 1024


# Tables dont on veut mesurer la place disque utilisée, une par entité du tableau de bord
STORAGE_ENTITIES = [
    ("clients", "Clients"),
    ("addresses", "Adresses"),
    ("sites", "Chantiers"),
    ("contracts", "Contrats"),
    ("claims", "Sinistres"),
    ("sales_reps", "Commerciaux"),
    ("visits", "Visites clients"),
    ("proposals", "Propositions"),
]


@app.get("/stats/storage/", tags=["Statistics"])
@app.get("/stats/storage", tags=["Statistics"])
def get_storage_statistics(db: Session = Depends(get_db)):
    """Obtenir la place disque utilisée par chaque entité en base"""
    from sqlalchemy import text
    from app.models import (
        ClientModel, ClientAddressModel, ConstructionSiteModel, ClientContractModel,
        ClaimModel, SalesRepModel, ClientVisitModel, InsuranceProposalModel
    )

    table_by_key = {
        "clients": ClientModel.__tablename__,
        "addresses": ClientAddressModel.__tablename__,
        "sites": ConstructionSiteModel.__tablename__,
        "contracts": ClientContractModel.__tablename__,
        "claims": ClaimModel.__tablename__,
        "sales_reps": SalesRepModel.__tablename__,
        "visits": ClientVisitModel.__tablename__,
        "proposals": InsuranceProposalModel.__tablename__,
    }
    table_names = list(table_by_key.values())

    rows = db.execute(
        text(
            "SELECT t.table_name, pg_total_relation_size(t.table_name::regclass) AS size_bytes "
            "FROM unnest(:table_names) AS t(table_name)"
        ),
        {"table_names": table_names}
    ).all()
    size_by_table = {row.table_name: row.size_bytes or 0 for row in rows}

    entities = []
    total_bytes = 0
    for key, label in STORAGE_ENTITIES:
        size_bytes = size_by_table.get(table_by_key[key], 0)
        total_bytes += size_bytes
        entities.append({
            "key": key,
            "label": label,
            "size_bytes": size_bytes,
            "size_pretty": format_size(size_bytes),
        })

    entities.sort(key=lambda e: e["size_bytes"], reverse=True)

    return {
        "entities": entities,
        "total_bytes": total_bytes,
        "total_pretty": format_size(total_bytes),
    }


# Modèles pour la génération de données
class DataGenerationRequest(BaseModel):
    count: int = 5
    client_type: str = "mixte"
    clean: bool = False


class ClaimsGenerationRequest(BaseModel):
    count: int = 15
    clean: bool = False


@app.post("/generate-data/", tags=["Data Generation"])
@app.post("/generate-data", tags=["Data Generation"])
async def generate_data(request: DataGenerationRequest, background_tasks: BackgroundTasks):
    """
    Générer des données de test en lançant le script generate_client_data.py
    """
    script_path = os.path.join(os.path.dirname(__file__), "generate_client_data.py")
    
    if not os.path.exists(script_path):
        raise HTTPException(status_code=500, detail="Script de génération introuvable")
    
    # Construction de la commande
    cmd = ["python3", script_path, "--create", "--count", str(request.count), "--type", request.client_type]
    
    if request.clean:
        cmd.insert(2, "--clean")
    
    try:
        # Exécution du script dans un thread pour ne pas bloquer la boucle asyncio
        result = await run_in_threadpool(
            subprocess.run,
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes max
        )
        
        if result.returncode == 0:
            return {
                "status": "success",
                "message": f"Génération terminée : {request.count} clients créés",
                "output": result.stdout,
                "clean": request.clean
            }
        else:
            raise HTTPException(
                status_code=500,
                detail={
                    "message": "Erreur lors de la génération",
                    "error": result.stderr,
                    "output": result.stdout
                }
            )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="La génération a pris trop de temps (timeout)")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


@app.post("/clean-data/", tags=["Data Generation"])
@app.post("/clean-data", tags=["Data Generation"])
async def clean_data():
    """
    Supprimer toutes les données en lançant le script avec --clean
    """
    script_path = os.path.join(os.path.dirname(__file__), "generate_client_data.py")
    
    if not os.path.exists(script_path):
        raise HTTPException(status_code=500, detail="Script de génération introuvable")
    
    try:
        # Exécution du script dans un thread pool pour ne pas bloquer la boucle asyncio
        result = await run_in_threadpool(
            subprocess.run,
            ["python3", script_path, "--clean"],
            capture_output=True,
            text=True,
            timeout=60  # 1 minute max
        )
        
        if result.returncode == 0:
            return {
                "status": "success",
                "message": "Toutes les données ont été supprimées",
                "output": result.stdout
            }
        else:
            raise HTTPException(
                status_code=500,
                detail={
                    "message": "Erreur lors de la suppression",
                    "error": result.stderr,
                    "output": result.stdout
                }
            )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="La suppression a pris trop de temps (timeout)")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


@app.post("/generate-claims/", tags=["Data Generation"])
@app.post("/generate-claims", tags=["Data Generation"])
async def generate_claims(request: ClaimsGenerationRequest):
    """
    Générer des sinistres de test en lançant le script generate_claims.py
    """
    script_path = os.path.join(os.path.dirname(__file__), "generate_claims.py")
    
    if not os.path.exists(script_path):
        raise HTTPException(status_code=500, detail="Script de génération de sinistres introuvable")
    
    # Construction de la commande
    cmd = ["python3", script_path, "--create", "--count", str(request.count)]
    
    if request.clean:
        cmd.insert(2, "--clean")
    
    try:
        # Exécution du script dans un thread pool pour ne pas bloquer la boucle asyncio
        result = await run_in_threadpool(
            subprocess.run,
            cmd,
            capture_output=True,
            text=True,
            timeout=120  # 2 minutes max
        )
        
        if result.returncode == 0:
            return {
                "status": "success",
                "message": f"Génération terminée : {request.count} sinistres créés",
                "output": result.stdout,
                "clean": request.clean
            }
        else:
            raise HTTPException(
                status_code=500,
                detail={
                    "message": "Erreur lors de la génération des sinistres",
                    "error": result.stderr,
                    "output": result.stdout
                }
            )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="La génération des sinistres a pris trop de temps (timeout)")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


@app.post("/init-referential-data/", tags=["Data Generation"])
@app.post("/init-referential-data", tags=["Data Generation"])
async def init_referential_data_endpoint():
    """
    Initialiser les données de référence (types de contrats, garanties, clauses,
    catégories de bâtiments/travaux, professions, exclusions) en lançant init_data.py.
    Idempotent : peut être relancé sans dupliquer les données existantes.
    """
    script_path = os.path.join(os.path.dirname(__file__), "init_data.py")

    if not os.path.exists(script_path):
        raise HTTPException(status_code=500, detail="Script d'initialisation introuvable")

    try:
        result = await run_in_threadpool(
            subprocess.run,
            ["python3", script_path],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            return {
                "status": "success",
                "message": "Données de référence initialisées",
                "output": result.stdout
            }
        else:
            raise HTTPException(
                status_code=500,
                detail={
                    "message": "Erreur lors de l'initialisation des données de référence",
                    "error": result.stderr,
                    "output": result.stdout
                }
            )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="L'initialisation a pris trop de temps (timeout)")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


class VisitsGenerationRequest(BaseModel):
    clean: bool = False
    create_reps: bool = True
    reps_count: int = 20
    create_visits: bool = True
    max_days: Optional[int] = 30


@app.post("/generate-visits/", tags=["Data Generation"])
@app.post("/generate-visits", tags=["Data Generation"])
async def generate_visits(request: VisitsGenerationRequest):
    """
    Générer le réseau commercial (commerciaux, visites, propositions, souscriptions)
    en lançant generate_visits_data.py
    """
    script_path = os.path.join(os.path.dirname(__file__), "generate_visits_data.py")

    if not os.path.exists(script_path):
        raise HTTPException(status_code=500, detail="Script de génération du réseau commercial introuvable")

    if not any([request.clean, request.create_reps, request.create_visits]):
        raise HTTPException(status_code=400, detail="Sélectionnez au moins une action à effectuer")

    cmd = ["python3", script_path]
    if request.clean:
        cmd.append("--clean")
    if request.create_reps:
        cmd += ["--create-reps", "--count", str(request.reps_count)]
    if request.create_visits:
        cmd.append("--create-visits")
        if request.max_days:
            cmd += ["--max-days", str(request.max_days)]

    try:
        result = await run_in_threadpool(
            subprocess.run,
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes max : génération de visites sur une période, peut être long
        )

        if result.returncode == 0:
            return {
                "status": "success",
                "message": "Génération du réseau commercial terminée",
                "output": result.stdout
            }
        else:
            raise HTTPException(
                status_code=500,
                detail={
                    "message": "Erreur lors de la génération du réseau commercial",
                    "error": result.stderr,
                    "output": result.stdout
                }
            )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="La génération a pris trop de temps (timeout) : réduisez le nombre de jours ou de commerciaux")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
