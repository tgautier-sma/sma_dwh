"""Configuration de l'application"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Configuration de l'application"""
    
    # Base de données PostgreSQL
    DATABASE_HOST: str = "gautiersa.fr"
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str = "insurance_db"
    DATABASE_USER: str = "postgres"
    DATABASE_PASSWORD: str = ""
    
    # Construction de l'URL de connexion
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
    
    # API
    API_TITLE: str = "API Gestion Assurance Construction"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "API pour gérer les contrats d'assurance construction, clients et référentiels"
    
    # CORS
    CORS_ORIGINS: list = ["*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
