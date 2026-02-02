# Interface Web - Gestion Assurance Construction

Interface web moderne pour gérer l'ensemble des données de la base de données d'assurance construction.

## 🎯 Fonctionnalités

### 📊 Tableau de bord
- Vue d'ensemble des statistiques (clients, adresses, chantiers, contrats)
- Activité récente
- Alertes sur les contrats arrivant à expiration

### 👥 Gestion des clients
- Liste complète des clients (particuliers et professionnels)
- Recherche par numéro, nom, email
- **Recherche phonétique** pour trouver des clients même avec des fautes d'orthographe
- Filtrage par type de client
- Visualisation, modification et suppression

### 📍 Gestion des adresses
- Liste de toutes les adresses avec coordonnées GPS
- Visualisation des coordonnées GPS (latitude/longitude)
- CRUD complet sur les adresses

### 🏗️ Gestion des chantiers
- Liste des chantiers de construction
- Informations détaillées (coût, catégorie, dates)
- CRUD complet

### 📄 Gestion des contrats
- Liste des contrats d'assurance
- Filtrage par statut (brouillon, actif, expiré, résilié)
- Visualisation des montants assurés et primes
- CRUD complet

### 📜 Historique
- Historique complet des modifications de contrats
- Filtrage par action et par date
- Traçabilité complète

### 🎲 Génération de données
- Interface pour générer des données de test
- Choix du nombre de clients
- Choix du type (particuliers, entreprises, mixte)
- Option de nettoyage avant génération

### 🗂️ Référentiels
- Accès aux données de référence :
  - Types de contrats
  - Types de garanties
  - Catégories de bâtiments
  - Catégories de travaux

## 🔍 Recherche avancée

### Recherche textuelle standard
Recherchez des clients par :
- Numéro de client
- Nom (prénom, nom de famille, raison sociale)
- Email
- Téléphone

### Recherche phonétique 🎤
Active la recherche phonétique pour trouver des clients même avec :
- Fautes d'orthographe
- Variations orthographiques
- Homophones

**Exemples de recherches phonétiques :**
- "Martin" trouvera "Marten"
- "Dupont" trouvera "Dupond"
- "François" trouvera "Francois"
- "Lefèvre" trouvera "Lefevre"

Pour activer la recherche phonétique, cliquez sur l'icône microphone 🎤 dans la barre de recherche.

## 🚀 Démarrage

### Prérequis
- Serveur FastAPI en cours d'exécution sur `http://localhost:8000`
- Base de données PostgreSQL configurée

### Lancement

1. **Démarrer le serveur API** (si ce n'est pas déjà fait) :
   ```bash
   python3 main.py
   ```

2. **Accéder à l'interface web** :
   Ouvrez votre navigateur et allez à :
   ```
   http://localhost:8000
   ```

L'interface web sera automatiquement servie à la racine du serveur FastAPI.

## 🎨 Interface utilisateur

### Thème
- Design moderne et épuré
- Palette de couleurs professionnelle
- Animations fluides
- Responsive design (adapté aux mobiles et tablettes)

### Navigation
- Barre latérale fixe avec menu de navigation
- Indicateur de connexion API en temps réel
- Recherche globale toujours accessible
- Breadcrumb pour la navigation

### Notifications
- Toast notifications pour les actions
- Badges de statut colorés
- Indicateurs de chargement

## 📋 Structure des fichiers

```
frontend/
├── index.html      # Page principale
├── styles.css      # Styles CSS
├── app.js          # Logique principale de l'application
├── api.js          # Client API pour communiquer avec FastAPI
└── phonetic.js     # Algorithme de recherche phonétique
```

## 🔧 Configuration

### URL de l'API
Par défaut, l'interface se connecte à `http://localhost:8000`.

Pour modifier l'URL de l'API, éditez le fichier `api.js` :
```javascript
const API_BASE_URL = 'http://localhost:8000';
```

## 🌐 Endpoints API utilisés

L'interface utilise les endpoints suivants :

- `GET /health` - Vérification de l'état de l'API
- `GET /stats/` - Statistiques globales
- `GET /clients/` - Liste des clients
- `GET /clients/search` - Recherche de clients
- `GET /clients/{id}` - Détails d'un client
- `POST /clients/` - Création d'un client
- `PUT /clients/{id}` - Modification d'un client
- `DELETE /clients/{id}` - Suppression d'un client
- `GET /addresses/` - Liste des adresses
- `GET /construction-sites/` - Liste des chantiers
- `GET /contracts/` - Liste des contrats
- `GET /contract-history/` - Historique des contrats
- `GET /referentials/*` - Données de référence

## 💡 Astuces d'utilisation

### Recherche rapide
- Utilisez la barre de recherche globale en haut pour chercher un client
- Activez la recherche phonétique pour une recherche plus tolérante

### Génération de données
Pour générer des données de test :
1. Allez dans "Génération de données"
2. Choisissez le nombre de clients
3. Sélectionnez le type (particuliers, entreprises, mixte)
4. Cochez "Nettoyer" si vous voulez supprimer les données existantes
5. Suivez les instructions pour exécuter le script Python

### Filtres
- Utilisez les filtres en haut de chaque vue pour affiner les résultats
- Les filtres sont combinables

### Alertes
Le tableau de bord affiche automatiquement :
- Les contrats expirant dans les 30 prochains jours
- Les dernières activités

## 🔒 Sécurité

⚠️ **Important** : Cette interface est destinée à un usage en développement local.

Pour un usage en production :
- Ajoutez une authentification
- Configurez HTTPS
- Limitez les CORS
- Validez toutes les entrées côté serveur
- Ajoutez des confirmations pour les actions critiques

## 📱 Compatibilité

### Navigateurs supportés
- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

### Responsive
- ✅ Desktop (1920x1080 et +)
- ✅ Laptop (1366x768)
- ✅ Tablet (768x1024)
- ✅ Mobile (360x640 et +)

## 🐛 Problèmes connus

### API déconnectée
Si l'indicateur d'API affiche "API déconnectée" :
1. Vérifiez que le serveur FastAPI est bien démarré
2. Vérifiez l'URL dans `api.js`
3. Vérifiez les CORS dans la configuration FastAPI

### Données GPS non affichées
Les coordonnées GPS ne s'affichent que si :
- Les champs `latitude` et `longitude` sont renseignés dans la base de données
- Le script de génération a été exécuté avec la dernière version

## 🚀 Évolutions futures

- [ ] Création/édition de clients via l'interface
- [ ] Création/édition d'adresses via l'interface
- [ ] Création/édition de chantiers via l'interface
- [ ] Création/édition de contrats via l'interface
- [ ] Carte interactive pour visualiser les adresses GPS
- [ ] Export des données (CSV, Excel, PDF)
- [ ] Graphiques et statistiques avancées
- [ ] Authentification utilisateur
- [ ] Gestion des droits d'accès
- [ ] Mode sombre

## 📞 Support

Pour toute question ou problème :
1. Consultez la documentation de l'API : `http://localhost:8000/docs`
2. Vérifiez les logs du serveur FastAPI
3. Consultez la console du navigateur (F12) pour les erreurs JavaScript
