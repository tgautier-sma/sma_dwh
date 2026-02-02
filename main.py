"""Application principale FastAPI"""
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from fastapi import Depends
from contextlib import asynccontextmanager
from pydantic import BaseModel
import subprocess
import os

from app.config import settings
from app.database import init_db, get_db
from app.routers import clients, contracts, sites, referentials, addresses, history


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
    lifespan=lifespan
)

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


@app.get("/health", tags=["Health"])
def health_check():
    """Vérification de la santé de l'API"""
    return {
        "status": "healthy",
        "database": "connected"
    }


@app.get("/stats/", tags=["Statistics"])
def get_statistics(db: Session = Depends(get_db)):
    """Obtenir les statistiques globales de la base de données"""
    from app.models import ClientModel, ClientAddressModel, ConstructionSiteModel, ClientContractModel
    
    total_clients = db.query(ClientModel).count()
    total_addresses = db.query(ClientAddressModel).count()
    total_construction_sites = db.query(ConstructionSiteModel).count()
    total_contracts = db.query(ClientContractModel).count()
    
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
        "clients_by_type": {
            "particulier": clients_particulier,
            "professionnel": clients_professionnel
        },
        "contracts_by_status": {status: count for status, count in contracts_by_status}
    }


# Modèles pour la génération de données
class DataGenerationRequest(BaseModel):
    count: int = 5
    client_type: str = "mixte"
    clean: bool = False


@app.post("/generate-data/", tags=["Data Generation"])
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
        # Exécution du script
        result = subprocess.run(
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
async def clean_data():
    """
    Supprimer toutes les données en lançant le script avec --clean
    """
    script_path = os.path.join(os.path.dirname(__file__), "generate_client_data.py")
    
    if not os.path.exists(script_path):
        raise HTTPException(status_code=500, detail="Script de génération introuvable")
    
    try:
        # Exécution du script avec --clean uniquement
        result = subprocess.run(
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
