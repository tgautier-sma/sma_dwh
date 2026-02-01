"""Application principale FastAPI"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import init_db
from app.routers import clients, contracts, sites, referentials


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
app.include_router(contracts.router)
app.include_router(sites.router)
app.include_router(referentials.router)


@app.get("/", tags=["Root"])
def root():
    """Point d'entrée de l'API"""
    return {
        "message": "API Gestion Assurance Construction",
        "version": settings.API_VERSION,
        "documentation": "/docs",
        "status": "operational"
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Vérification de la santé de l'API"""
    return {
        "status": "healthy",
        "database": "connected"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
