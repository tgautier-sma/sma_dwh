# 🚀 Guide de démarrage rapide

## Étape 1 : Configuration de la base de données

1. **Assurez-vous que PostgreSQL est installé et accessible sur gautiersa.fr**

2. **Modifiez le fichier `.env`** avec vos informations de connexion :
```env
DATABASE_HOST=gautiersa.fr
DATABASE_PORT=5432
DATABASE_NAME=insurance_db
DATABASE_USER=postgres
DATABASE_PASSWORD=VOTRE_MOT_DE_PASSE_ICI
```

## Étape 2 : Installation des dépendances

```bash
# Installer les dépendances Python
pip install -r requirements.txt
```

## Étape 3 : Initialisation de la base de données

```bash
# Créer les tables et insérer les données de référence
python init_data.py
```

Cette commande va :
- ✅ Créer toutes les tables de la base de données
- ✅ Insérer les types de contrats (DO, RCD, TRC, etc.)
- ✅ Insérer les garanties par défaut
- ✅ Insérer les clauses contractuelles
- ✅ Insérer les catégories de bâtiments
- ✅ Insérer les catégories de travaux
- ✅ Insérer les professions du bâtiment

## Étape 4 : Lancer le serveur

```bash
# Mode développement (avec rechargement automatique)
python main.py
```

Le serveur sera accessible sur : **http://localhost:8000**

## Étape 5 : Tester l'API

### Option 1 : Documentation interactive (recommandé)
Ouvrez votre navigateur : **http://localhost:8000/docs**

### Option 2 : Script de test
```bash
python test_api.py
```

### Option 3 : cURL
```bash
# Test de base
curl http://localhost:8000/

# Liste des types de contrats
curl http://localhost:8000/referentials/contract-types

# Créer un client
curl -X POST "http://localhost:8000/clients/" \
  -H "Content-Type: application/json" \
  -d '{
    "client_number": "CLI-2024-001",
    "client_type": "entreprise",
    "company_name": "Entreprise Construction SA",
    "email": "contact@entreprise.fr",
    "phone": "0123456789",
    "address_line1": "10 rue de la Construction",
    "postal_code": "75001",
    "city": "Paris"
  }'
```

## 📚 Documentation complète

- **Swagger UI** : http://localhost:8000/docs
- **ReDoc** : http://localhost:8000/redoc
- **README complet** : [README.md](README.md)

## ⚠️ Dépannage

### Erreur de connexion à la base de données
- Vérifiez que PostgreSQL est bien démarré
- Vérifiez les informations de connexion dans `.env`
- Vérifiez que la base de données `insurance_db` existe
- Vérifiez les droits d'accès de l'utilisateur PostgreSQL

### Port 8000 déjà utilisé
Changez le port dans `main.py` :
```python
uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
```

### Problème d'import de modules
```bash
# Assurez-vous d'être dans le bon répertoire
cd /Users/tgautier/DEV/sma/sma_dwh

# Réinstallez les dépendances
pip install -r requirements.txt
```

## 🎯 Prochaines étapes

1. ✅ Serveur opérationnel
2. 📊 Testez les endpoints dans Swagger UI
3. 🔧 Personnalisez les données de référence selon vos besoins
4. 🚀 Intégrez l'API dans votre application frontend
5. 🔐 Ajoutez l'authentification pour la production

## 📞 Support

Pour toute question, consultez la documentation complète dans [README.md](README.md)
