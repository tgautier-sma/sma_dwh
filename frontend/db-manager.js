/**
 * Gestionnaire IndexedDB pour le stockage local des données
 * Permet la consultation et la mise à jour des données en mode hors ligne
 */

class DBManager {
    constructor() {
        this.dbName = 'SMA_DWH_DB';
        this.version = 1;
        this.db = null;
    }

    /**
     * Initialise la base de données IndexedDB
     */
    async init() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbName, this.version);

            request.onerror = () => {
                console.error('Erreur d\'ouverture de la base de données:', request.error);
                reject(request.error);
            };

            request.onsuccess = () => {
                this.db = request.result;
                console.log('Base de données ouverte avec succès');
                resolve(this.db);
            };

            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                console.log('Mise à jour de la structure de la base de données...');

                // Store pour les sinistres
                if (!db.objectStoreNames.contains('claims')) {
                    const claimsStore = db.createObjectStore('claims', { keyPath: 'claim_number' });
                    claimsStore.createIndex('contract_id', 'contract_id', { unique: false });
                    claimsStore.createIndex('status', 'status', { unique: false });
                    claimsStore.createIndex('declaration_date', 'declaration_date', { unique: false });
                    claimsStore.createIndex('modified', 'modified', { unique: false });
                }

                // Store pour les contrats
                if (!db.objectStoreNames.contains('contracts')) {
                    const contractsStore = db.createObjectStore('contracts', { keyPath: 'id' });
                    contractsStore.createIndex('contract_number', 'contract_number', { unique: true });
                    contractsStore.createIndex('client_id', 'client_id', { unique: false });
                    contractsStore.createIndex('modified', 'modified', { unique: false });
                }

                // Store pour les clients
                if (!db.objectStoreNames.contains('clients')) {
                    const clientsStore = db.createObjectStore('clients', { keyPath: 'id' });
                    clientsStore.createIndex('client_number', 'client_number', { unique: true });
                    clientsStore.createIndex('modified', 'modified', { unique: false });
                }

                // Store pour les chantiers
                if (!db.objectStoreNames.contains('sites')) {
                    const sitesStore = db.createObjectStore('sites', { keyPath: 'id' });
                    sitesStore.createIndex('site_reference', 'site_reference', { unique: false });
                    sitesStore.createIndex('modified', 'modified', { unique: false });
                }

                // Store pour les référentiels
                if (!db.objectStoreNames.contains('referentials')) {
                    db.createObjectStore('referentials', { keyPath: 'type' });
                }

                // Store pour les modifications en attente de synchronisation
                if (!db.objectStoreNames.contains('pending_changes')) {
                    const pendingStore = db.createObjectStore('pending_changes', { keyPath: 'id', autoIncrement: true });
                    pendingStore.createIndex('timestamp', 'timestamp', { unique: false });
                    pendingStore.createIndex('entity_type', 'entity_type', { unique: false });
                    pendingStore.createIndex('operation', 'operation', { unique: false });
                }

                // Store pour les métadonnées
                if (!db.objectStoreNames.contains('metadata')) {
                    db.createObjectStore('metadata', { keyPath: 'key' });
                }
            };
        });
    }

    /**
     * Sauvegarde des sinistres
     */
    async saveClaims(claims) {
        const transaction = this.db.transaction(['claims'], 'readwrite');
        const store = transaction.objectStore('claims');
        
        for (const claim of claims) {
            await store.put(claim);
        }
        
        return transaction.complete;
    }

    /**
     * Récupère tous les sinistres
     */
    async getAllClaims() {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['claims'], 'readonly');
            const store = transaction.objectStore('claims');
            const request = store.getAll();
            
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Récupère un sinistre par son numéro
     */
    async getClaim(claimNumber) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['claims'], 'readonly');
            const store = transaction.objectStore('claims');
            const request = store.get(claimNumber);
            
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Recherche de sinistres
     */
    async searchClaims(query) {
        const allClaims = await this.getAllClaims();
        const lowerQuery = query.toLowerCase();
        
        return allClaims.filter(claim => 
            claim.claim_number?.toLowerCase().includes(lowerQuery) ||
            claim.title?.toLowerCase().includes(lowerQuery) ||
            claim.description?.toLowerCase().includes(lowerQuery) ||
            claim.client_name?.toLowerCase().includes(lowerQuery)
        );
    }

    /**
     * Met à jour un sinistre (avec tracking des modifications)
     */
    async updateClaim(claimNumber, updates) {
        const claim = await this.getClaim(claimNumber);
        
        if (!claim) {
            throw new Error('Sinistre non trouvé');
        }
        
        const updatedClaim = { ...claim, ...updates, modified: new Date().toISOString() };
        
        // Sauvegarder le sinistre mis à jour
        const transaction = this.db.transaction(['claims', 'pending_changes'], 'readwrite');
        const claimsStore = transaction.objectStore('claims');
        const pendingStore = transaction.objectStore('pending_changes');
        
        await claimsStore.put(updatedClaim);
        
        // Enregistrer la modification pour synchronisation ultérieure
        await pendingStore.add({
            entity_type: 'claim',
            entity_id: claimNumber,
            operation: 'update',
            data: updates,
            timestamp: new Date().toISOString()
        });
        
        return updatedClaim;
    }

    /**
     * Sauvegarde des contrats
     */
    async saveContracts(contracts) {
        const transaction = this.db.transaction(['contracts'], 'readwrite');
        const store = transaction.objectStore('contracts');
        
        for (const contract of contracts) {
            await store.put(contract);
        }
        
        return transaction.complete;
    }

    /**
     * Récupère un contrat par son ID
     */
    async getContract(contractId) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['contracts'], 'readonly');
            const store = transaction.objectStore('contracts');
            const request = store.get(contractId);
            
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Récupère un contrat par son numéro
     */
    async getContractByNumber(contractNumber) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['contracts'], 'readonly');
            const store = transaction.objectStore('contracts');
            const index = store.index('contract_number');
            const request = index.get(contractNumber);
            
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Récupère tous les contrats
     */
    async getAllContracts() {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['contracts'], 'readonly');
            const store = transaction.objectStore('contracts');
            const request = store.getAll();
            
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Sauvegarde des clients
     */
    async saveClients(clients) {
        const transaction = this.db.transaction(['clients'], 'readwrite');
        const store = transaction.objectStore('clients');
        
        for (const client of clients) {
            await store.put(client);
        }
        
        return transaction.complete;
    }

    /**
     * Récupère un client par son ID
     */
    async getClient(clientId) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['clients'], 'readonly');
            const store = transaction.objectStore('clients');
            const request = store.get(clientId);
            
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Récupère tous les clients
     */
    async getAllClients() {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['clients'], 'readonly');
            const store = transaction.objectStore('clients');
            const request = store.getAll();
            
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Sauvegarde des référentiels
     */
    async saveReferential(type, data) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['referentials'], 'readwrite');
            const store = transaction.objectStore('referentials');
            const request = store.put({ type, data, updated: new Date().toISOString() });
            
            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Récupère un référentiel
     */
    async getReferential(type) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['referentials'], 'readonly');
            const store = transaction.objectStore('referentials');
            const request = store.get(type);
            
            request.onsuccess = () => resolve(request.result?.data || null);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Récupère toutes les modifications en attente
     */
    async getPendingChanges() {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['pending_changes'], 'readonly');
            const store = transaction.objectStore('pending_changes');
            const request = store.getAll();
            
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Supprime une modification en attente
     */
    async deletePendingChange(id) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['pending_changes'], 'readwrite');
            const store = transaction.objectStore('pending_changes');
            const request = store.delete(id);
            
            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Sauvegarde des métadonnées
     */
    async setMetadata(key, value) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['metadata'], 'readwrite');
            const store = transaction.objectStore('metadata');
            const request = store.put({ key, value, updated: new Date().toISOString() });
            
            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Récupère des métadonnées
     */
    async getMetadata(key) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['metadata'], 'readonly');
            const store = transaction.objectStore('metadata');
            const request = store.get(key);
            
            request.onsuccess = () => resolve(request.result?.value || null);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Vide toutes les données (utile pour le développement)
     */
    async clearAll() {
        const stores = ['claims', 'contracts', 'clients', 'sites', 'referentials', 'pending_changes', 'metadata'];
        const transaction = this.db.transaction(stores, 'readwrite');
        
        for (const storeName of stores) {
            const store = transaction.objectStore(storeName);
            await store.clear();
        }
        
        console.log('Toutes les données ont été supprimées');
    }

    /**
     * Obtient des statistiques sur la base de données
     */
    async getStats() {
        const stats = {};
        const stores = ['claims', 'contracts', 'clients', 'sites', 'pending_changes'];
        
        for (const storeName of stores) {
            const count = await new Promise((resolve, reject) => {
                const transaction = this.db.transaction([storeName], 'readonly');
                const store = transaction.objectStore(storeName);
                const request = store.count();
                
                request.onsuccess = () => resolve(request.result);
                request.onerror = () => reject(request.error);
            });
            
            stats[storeName] = count;
        }
        
        return stats;
    }

    /**
     * Sauvegarde des chantiers
     */
    async saveSites(sites) {
        const transaction = this.db.transaction(['sites'], 'readwrite');
        const store = transaction.objectStore('sites');
        
        for (const site of sites) {
            await store.put(site);
        }
    }

    /**
     * Récupération de tous les chantiers
     */
    async getAllSites() {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['sites'], 'readonly');
            const store = transaction.objectStore('sites');
            const request = store.getAll();
            
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Sauvegarde des adresses
     */
    async saveAddresses(addresses) {
        // Les adresses n'ont pas de store dédié, on les sauvegarde dans les métadonnées
        await this.setMetadata('addresses', addresses);
    }

    /**
     * Récupération de toutes les adresses
     */
    async getAllAddresses() {
        const addresses = await this.getMetadata('addresses');
        return addresses || [];
    }

    /**
     * Sauvegarde de l'historique
     */
    async saveHistory(history) {
        // L'historique n'a pas de store dédié, on le sauvegarde dans les métadonnées
        await this.setMetadata('history', history);
    }

    /**
     * Récupération de l'historique
     */
    async getAllHistory() {
        const history = await this.getMetadata('history');
        return history || [];
    }
}

// Instance globale
const dbManager = new DBManager();

// Export pour utilisation dans d'autres modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DBManager;
}
