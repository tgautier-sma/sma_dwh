# SMA DWH - Docker Deployment Guide

## 🐳 Déploiement avec Docker

### Prérequis

- Docker Desktop installé et démarré
- Docker Compose (inclus avec Docker Desktop)

### Configuration rapide

1. **Copier le fichier de configuration**
   ```bash
   cp .env.docker .env
   ```

2. **Modifier les variables dans `.env`** (obligatoire)
   - Changez `POSTGRES_PASSWORD` avec un mot de passe sécurisé
   - Mettez à jour `DATABASE_URL` avec le même mot de passe

### Commandes de déploiement

#### Déploiement complet (build + start)
```bash
./deploy.sh
# ou
./deploy.sh deploy
```

#### Build de l'image seulement
```bash
./deploy.sh build
```

#### Démarrer les services
```bash
./deploy.sh start
```

#### Arrêter les services
```bash
./deploy.sh stop
```

#### Redémarrer les services
```bash
./deploy.sh restart
```

#### Voir les logs en temps réel
```bash
./deploy.sh logs
```

#### Vérifier le statut des services
```bash
./deploy.sh status
```

#### Nettoyer complètement
```bash
./deploy.sh clean
```

### URLs d'accès

Une fois déployé, l'application est accessible sur :

- **Application web** : http://localhost:8000
- **Documentation API** : http://localhost:8000/docs
- **API Redoc** : http://localhost:8000/redoc
- **Health check** : http://localhost:8000/health

### Architecture Docker

Le déploiement Docker Compose inclut :

1. **Service `app`** : Application FastAPI
   - Port : 8000
   - Health check automatique
   - Redémarrage automatique

2. **Service `db`** : Base de données PostgreSQL 15
   - Port : 5432
   - Volume persistant pour les données
   - Health check automatique

### Configuration avancée

#### Utiliser une base de données externe

1. Commentez le service `db` dans `docker-compose.yml`
2. Modifiez `DATABASE_URL` dans `.env` pour pointer vers votre base externe
3. Supprimez la dépendance `depends_on: db` du service `app`

#### Mode développement

Les volumes sont montés pour permettre le hot-reload :
```yaml
volumes:
  - ./app:/app/app
  - ./frontend:/app/frontend
  - ./main.py:/app/main.py
```

En production, vous pouvez les commenter pour de meilleures performances.

#### Variables d'environnement personnalisées

Éditez `.env` pour ajuster :
- `APP_PORT` : Port de l'application (défaut: 8000)
- `POSTGRES_PORT` : Port PostgreSQL (défaut: 5432)
- `DEBUG` : Mode debug (défaut: false)
- `CORS_ORIGINS` : Origines CORS autorisées (défaut: *)

### Commandes Docker manuelles

Si vous préférez utiliser Docker Compose directement :

```bash
# Build
docker compose build

# Démarrer
docker compose up -d

# Arrêter
docker compose down

# Logs
docker compose logs -f app

# Status
docker compose ps

# Shell dans le container
docker compose exec app bash
```

### Initialisation des données

Pour générer des données de test après le déploiement :

```bash
# Via l'interface web
# Accédez à http://localhost:8000 → Génération de données

# Ou via le container
docker compose exec app python generate_client_data.py --create --count 10 --type mixte
```

### Troubleshooting

#### L'application ne démarre pas
```bash
# Vérifier les logs
./deploy.sh logs

# Vérifier le statut
./deploy.sh status

# Vérifier que Docker tourne
docker info
```

#### Problème de connexion à la base de données
```bash
# Vérifier que la DB est accessible
docker compose exec db psql -U postgres -c "SELECT version();"

# Vérifier les variables d'environnement
docker compose exec app env | grep DATABASE
```

#### Reconstruire complètement
```bash
./deploy.sh clean
./deploy.sh deploy
```

### Backup de la base de données

```bash
# Dump
docker compose exec db pg_dump -U postgres sma_dwh > backup.sql

# Restore
docker compose exec -T db psql -U postgres sma_dwh < backup.sql
```

### Production

Pour un déploiement en production :

1. Utilisez des secrets pour les mots de passe (Docker Secrets ou variables d'environnement sécurisées)
2. Commentez les volumes de code montés dans `docker-compose.yml`
3. Configurez un reverse proxy (nginx, Traefik) devant l'application
4. Activez HTTPS avec des certificats SSL
5. Limitez `CORS_ORIGINS` aux domaines autorisés
6. Configurez des sauvegardes automatiques de la base de données
7. Mettez en place une supervision (logs, métriques, alertes)

### Exemple de déploiement complet

```bash
# 1. Configuration
cp .env.docker .env
nano .env  # Éditer les valeurs

# 2. Build et déploiement
./deploy.sh deploy

# 3. Vérification
curl http://localhost:8000/health

# 4. Génération de données de test
curl -X POST http://localhost:8000/generate-data/ \
  -H "Content-Type: application/json" \
  -d '{"count": 5, "client_type": "mixte", "clean": false}'

# 5. Accès à l'interface
open http://localhost:8000
```
