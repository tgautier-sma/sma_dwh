# Mode Hors Ligne - Guide d'Utilisation

## 📱 Fonctionnalités Hors Ligne

L'application SMA DWH supporte maintenant le **mode hors ligne complet** grâce aux technologies PWA (Progressive Web App).

## 🚀 Fonctionnalités Disponibles

### ✅ En Mode Hors Ligne

- **Consultation** de tous les sinistres préchargés
- **Recherche** dans les données locales
- **Consultation** des détails des sinistres, contrats et clients
- **Modification** des sinistres (synchronisées automatiquement lors du retour en ligne)
- **Affichage** des cartes (tuiles mises en cache)
- **Navigation** complète dans l'application

### 🔄 Synchronisation Automatique

- Les données sont **préchargées** au premier accès
- Les modifications hors ligne sont **trackées** localement
- **Synchronisation automatique** lors du retour en ligne
- Synchronisation périodique toutes les **5 minutes**

## 📦 Fichiers Créés

### 1. `manifest.json`

Configuration PWA pour rendre l'application installable :

- Nom de l'application
- Icônes
- Thème couleur
- Mode d'affichage standalone

### 2. `service-worker.js`

Service Worker pour la gestion du cache :

- **Cache statique** : ressources HTML, CSS, JS
- **Cache API** : données des sinistres, contrats, clients
- **Cache images** : tuiles de cartes OpenStreetMap
- Stratégies de cache : Network First pour API, Cache First pour ressources statiques

### 3. `db-manager.js`

Gestionnaire IndexedDB pour le stockage local :

- **Claims** : stockage des sinistres
- **Contracts** : stockage des contrats
- **Clients** : stockage des clients
- **Referentials** : référentiels (garanties, etc.)
- **Pending Changes** : modifications en attente de synchronisation
- **Metadata** : métadonnées (dernière synchro, etc.)

### 4. `sync-manager.js`

Gestionnaire de synchronisation :

- Synchronisation automatique au retour en ligne
- Synchronisation périodique (toutes les 5 minutes)
- Gestion des conflits
- Notifications de synchronisation

### 5. Modifications `api.js`

API enrichie avec support hors ligne :

- Détection automatique du mode en ligne/hors ligne
- Utilisation d'IndexedDB quand hors ligne
- Préchargement automatique des données
- Tracking des modifications pour synchronisation

## 🔧 Utilisation

### Installation de l'Application

1. **Sur Desktop** (Chrome, Edge, Opera) :
   - Icône "Installer l'application" dans la barre d'adresse
   - Menu → "Installer SMA DWH"

2. **Sur Mobile** (iOS, Android) :
   - Safari iOS : Partager → "Sur l'écran d'accueil"
   - Chrome Android : Menu → "Installer l'application"

### Fonctions de Console Disponibles

```javascript
// Forcer une synchronisation immédiate
forceSync()

// Obtenir l'état de la synchronisation
getSyncStatus()

// Réinitialiser toutes les données et re-synchroniser
resetData()

// Obtenir les statistiques de la base locale
dbManager.getStats()

// Vider toutes les données locales
dbManager.clearAll()
```

### Vérification de l'État

Ouvrez la console développeur et utilisez :

```javascript
// Voir l'état de la synchronisation
getSyncStatus().then(status => console.log(status))

// Affiche :
// {
//   isOnline: true,
//   syncInProgress: false,
//   lastSyncTime: "2026-02-04T10:30:00.000Z",
//   pendingChangesCount: 0,
//   localDataStats: { claims: 17, contracts: 34, ... }
// }
```

## 🎯 Scénarios d'Utilisation

### Scenario 1 : Consultation Hors Ligne

1. Chargez l'application avec connexion internet
2. Les données sont automatiquement préchargées
3. Coupez la connexion internet
4. Continuez à consulter les sinistres normalement
5. La recherche fonctionne sur les données locales

### Scenario 2 : Modification Hors Ligne

1. Ouvrez un sinistre en mode hors ligne
2. Modifiez les informations
3. Les modifications sont sauvegardées localement
4. Au retour de la connexion, synchronisation automatique
5. Les modifications sont envoyées au serveur

### Scenario 3 : Installation comme Application

1. Installez l'application sur votre appareil
2. Lancez-la depuis l'icône
3. Fonctionne comme une application native
4. Pas besoin d'ouvrir le navigateur

## 📊 Stockage Local

### Limites de Stockage

- **IndexedDB** : ~50 MB minimum, souvent plusieurs GB selon le navigateur
- **Service Worker Cache** : 50 MB recommandé

### Données Stockées Localement

- Jusqu'à 100 sinistres récents
- Contrats associés
- Clients
- Référentiels (garanties, types de contrats, etc.)
- Tuiles de cartes visitées

## 🔒 Sécurité

- Les données sont stockées **localement** dans le navigateur
- Suppression automatique en effaçant les données du site
- Pas de transmission de données sensibles en cache
- Synchronisation sécurisée via HTTPS

## 🐛 Dépannage

### L'application ne fonctionne pas hors ligne

1. Vérifier que le Service Worker est enregistré :

   ```javascript
   navigator.serviceWorker.getRegistrations().then(r => console.log(r))
   ```

2. Vérifier IndexedDB :

   ```javascript
   dbManager.getStats().then(stats => console.log(stats))
   ```

3. Réinitialiser les données :

   ```javascript
   resetData()
   ```

### Les modifications ne se synchronisent pas

1. Vérifier la connexion internet
2. Forcer la synchronisation :

   ```javascript
   forceSync()
   ```

3. Vérifier les modifications en attente :

   ```javascript
   dbManager.getPendingChanges().then(c => console.log(c))
   ```

### Réinitialisation Complète

```javascript
// Désinscrire le Service Worker
navigator.serviceWorker.getRegistrations().then(registrations => {
    registrations.forEach(r => r.unregister())
})

// Vider IndexedDB
dbManager.clearAll()

// Vider le cache
caches.keys().then(names => {
    names.forEach(name => caches.delete(name))
})

// Recharger la page
location.reload()
```

## 📝 Notes de Développement

### Pour Ajouter une Nouvelle Fonctionnalité Hors Ligne

1. **Ajouter le stockage dans `db-manager.js`** :

   ```javascript
   async saveNewEntity(entities) {
       const transaction = this.db.transaction(['new_entity'], 'readwrite');
       const store = transaction.objectStore('new_entity');
       for (const entity of entities) {
           await store.put(entity);
       }
   }
   ```

2. **Modifier `api.js`** pour supporter le mode hors ligne :

   ```javascript
   async getNewEntity(id) {
       if (!this.isOnline && this.dbReady) {
           return await dbManager.getNewEntity(id);
       }
       return this.request(`/new-entity/${id}`);
   }
   ```

3. **Ajouter à `sync-manager.js`** pour la synchronisation :

   ```javascript
   async syncNewEntity() {
       const entities = await this.api.getNewEntities();
       await this.dbManager.saveNewEntities(entities);
   }
   ```

## 🎉 Avantages

- ✅ **Disponibilité 24/7** même sans connexion
- ✅ **Performance améliorée** (données en cache)
- ✅ **Expérience mobile** optimale
- ✅ **Installation sur appareil** comme une app native
- ✅ **Synchronisation automatique** transparente
- ✅ **Réduction de la charge serveur**

## 📱 Compatibilité

- ✅ Chrome/Edge 90+
- ✅ Firefox 88+
- ✅ Safari 15+
- ✅ Chrome Android
- ✅ Safari iOS 15+

---

**Dernière mise à jour** : 4 février 2026
