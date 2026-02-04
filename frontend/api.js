// API Configuration
// Utiliser une URL relative pour que ça fonctionne avec n'importe quel domaine
const API_BASE_URL = '';

// API Client avec support du mode hors ligne
class API {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
        this.isOnline = navigator.onLine;
        this.dbReady = false;
        console.log('API initialized with baseUrl:', this.baseUrl);
        
        // Écouter les changements de connexion
        window.addEventListener('online', () => {
            console.log('Connexion réseau restaurée');
            this.isOnline = true;
            this.syncPendingChanges();
        });
        
        window.addEventListener('offline', () => {
            console.log('Connexion réseau perdue - Mode hors ligne activé');
            this.isOnline = false;
        });
        
        // Initialiser IndexedDB
        this.initDB();
    }

    async initDB() {
        try {
            if (typeof dbManager !== 'undefined') {
                await dbManager.init();
                this.dbReady = true;
                console.log('IndexedDB initialisé et prêt');
                
                // Vérifier si des données existent déjà
                const stats = await dbManager.getStats();
                const hasData = stats.claims > 0 || stats.clients > 0 || stats.contracts > 0;
                
                // Si pas de données et en ligne, proposer le téléchargement
                if (!hasData && this.isOnline) {
                    this.showDownloadPrompt();
                }
            }
        } catch (error) {
            console.error('Erreur d\'initialisation IndexedDB:', error);
        }
    }

    showDownloadPrompt() {
        if (typeof window.showOfflineDownloadModal === 'function') {
            window.showOfflineDownloadModal();
        }
    }

    async downloadAllData(progressCallback) {
        try {
            console.log('🔄 Téléchargement de toutes les données pour le mode hors ligne...');
            const steps = 8;
            let currentStep = 0;
            
            // Étape 1: Charger les sinistres
            currentStep++;
            if (progressCallback) progressCallback(currentStep, steps, 'Téléchargement des sinistres...');
            console.log('Chargement des sinistres...');
            const claimsResponse = await this.getClaims({ limit: 100 });
            if (claimsResponse.items && claimsResponse.items.length > 0) {
                await dbManager.saveClaims(claimsResponse.items);
                console.log(`✅ ${claimsResponse.items.length} sinistres sauvegardés`);
            }
            
            // Étape 2: Charger les clients
            currentStep++;
            if (progressCallback) progressCallback(currentStep, steps, 'Téléchargement des clients...');
            console.log('Chargement des clients...');
            const clients = await this.getClients({ limit: 100 });
            if (Array.isArray(clients) && clients.length > 0) {
                await dbManager.saveClients(clients);
                console.log(`✅ ${clients.length} clients sauvegardés`);
            }
            
            // Étape 3: Charger les contrats
            currentStep++;
            if (progressCallback) progressCallback(currentStep, steps, 'Téléchargement des contrats...');
            console.log('Chargement des contrats...');
            const contractsResponse = await this.getContracts(null, { limit: 100 });
            if (contractsResponse.items && contractsResponse.items.length > 0) {
                await dbManager.saveContracts(contractsResponse.items);
                console.log(`✅ ${contractsResponse.items.length} contrats sauvegardés`);
            }
            
            // Étape 4: Charger les adresses
            currentStep++;
            if (progressCallback) progressCallback(currentStep, steps, 'Téléchargement des adresses...');
            console.log('Chargement des adresses...');
            const addresses = await this.getAddresses();
            if (Array.isArray(addresses) && addresses.length > 0) {
                await dbManager.saveAddresses(addresses);
                console.log(`✅ ${addresses.length} adresses sauvegardées`);
            }
            
            // Étape 5: Charger les chantiers
            currentStep++;
            if (progressCallback) progressCallback(currentStep, steps, 'Téléchargement des chantiers...');
            console.log('Chargement des chantiers...');
            const sites = await this.getSites();
            if (Array.isArray(sites) && sites.length > 0) {
                await dbManager.saveSites(sites);
                console.log(`✅ ${sites.length} chantiers sauvegardés`);
            }
            
            // Étape 6: Charger l'historique
            currentStep++;
            if (progressCallback) progressCallback(currentStep, steps, 'Téléchargement de l\'historique...');
            console.log('Chargement de l\'historique...');
            const history = await this.getContractHistory();
            if (Array.isArray(history) && history.length > 0) {
                await dbManager.saveHistory(history);
                console.log(`✅ ${history.length} entrées d'historique sauvegardées`);
            }
            
            // Étape 7: Charger les référentiels
            currentStep++;
            if (progressCallback) progressCallback(currentStep, steps, 'Téléchargement des référentiels...');
            console.log('Chargement des référentiels...');
            const [guarantees, contractTypes, clauses, buildingCategories, workCategories, professions] = await Promise.all([
                this.getGuaranteeTypes(),
                this.getContractTypes(),
                this.getClauses(),
                this.getBuildingCategories(),
                this.getWorkCategories(),
                this.getProfessions()
            ]);
            await dbManager.saveReferential('guarantees', guarantees);
            await dbManager.saveReferential('contract_types', contractTypes);
            await dbManager.saveReferential('clauses', clauses);
            await dbManager.saveReferential('building_categories', buildingCategories);
            await dbManager.saveReferential('work_categories', workCategories);
            await dbManager.saveReferential('professions', professions);
            console.log('✅ Référentiels sauvegardés');
            
            // Étape 8: Finalisation
            currentStep++;
            if (progressCallback) progressCallback(currentStep, steps, 'Finalisation...');
            
            // Mettre à jour la date de dernière synchronisation
            await dbManager.setMetadata('last_sync', new Date().toISOString());
            await dbManager.setMetadata('full_download_completed', 'true');
            
            // Afficher un résumé
            const stats = await dbManager.getStats();
            console.log('📊 Résumé du cache:', stats);
            console.log('✅ Téléchargement complet terminé');
            
            if (progressCallback) progressCallback(steps, steps, 'Téléchargement terminé !', true);
            
            return stats;
        } catch (error) {
            console.error('❌ Erreur lors du téléchargement:', error);
            if (progressCallback) progressCallback(0, 0, 'Erreur: ' + error.message, false, true);
            throw error;
        }
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        console.log('API request to:', url, 'Full URL:', new URL(url, window.location.origin).href);
        
        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers,
                },
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || `HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            // Si la requête est réussie et que c'est un GET, mettre en cache
            if (!options.method || options.method === 'GET') {
                this.cacheResponse(endpoint, data);
            }
            
            return data;
        } catch (error) {
            console.error('API Error:', error);
            console.error('Failed URL:', url);
            
            // En cas d'erreur de fetch (hors ligne ou erreur réseau), essayer le cache pour les GET
            // Ne pas se fier uniquement à navigator.onLine qui peut être inexact
            if (!options.method || options.method === 'GET') {
                console.log('📦 Tentative de récupération depuis le cache local pour:', endpoint);
                const cachedData = await this.getCachedResponse(endpoint);
                if (cachedData) {
                    console.log('✅ Données récupérées depuis le cache local:', Array.isArray(cachedData) ? `${cachedData.length} éléments` : typeof cachedData);
                    return cachedData;
                } else {
                    console.warn('❌ Aucune donnée en cache pour:', endpoint);
                    // Afficher le contenu du cache pour déboguer
                    const stats = await dbManager.getStats();
                    console.log('📊 État actuel du cache:', stats);
                }
            }
            
            throw error;
        }
    }

    async cacheResponse(endpoint, data) {
        if (!this.dbReady) return;
        
        try {
            // Déterminer le type de données et les sauvegarder appropriément
            if (endpoint.includes('/claims')) {
                if (Array.isArray(data)) {
                    await dbManager.saveClaims(data);
                } else if (data.items) {
                    await dbManager.saveClaims(data.items);
                }
            } else if (endpoint.includes('/clients')) {
                // Les clients peuvent être un array direct ou un objet avec items
                const clientsArray = Array.isArray(data) ? data : (data.items || []);
                if (clientsArray.length > 0) {
                    await dbManager.saveClients(clientsArray);
                }
            } else if (endpoint.includes('/contracts')) {
                // Les contrats peuvent être un array direct ou un objet avec items
                const contractsArray = Array.isArray(data) ? data : (data.items || []);
                if (contractsArray.length > 0) {
                    await dbManager.saveContracts(contractsArray);
                }
            }
        } catch (error) {
            console.error('Erreur de mise en cache:', error);
        }
    }

    async getCachedResponse(endpoint) {
        if (!this.dbReady) return null;
        
        try {
            // Nettoyer l'endpoint pour enlever les paramètres de query
            const cleanEndpoint = endpoint.split('?')[0];
            
            // Récupérer depuis IndexedDB selon le type d'endpoint
            if (cleanEndpoint.match(/\/claims\/\d+$/)) {
                // Endpoint spécifique: /claims/12345
                const claimNumber = cleanEndpoint.split('/').pop();
                return await dbManager.getClaim(claimNumber);
            } else if (cleanEndpoint.includes('/claims/search')) {
                // Recherche de sinistres - retourner tous les sinistres
                const claims = await dbManager.getAllClaims();
                return { items: claims, total: claims.length };
            } else if (cleanEndpoint.includes('/claims/stats')) {
                // Stats des sinistres - calculer depuis le cache
                const claims = await dbManager.getAllClaims();
                return {
                    total_claims: claims.length,
                    open_claims: claims.filter(c => c.status === 'open').length,
                    closed_claims: claims.filter(c => c.status === 'closed').length
                };
            } else if (cleanEndpoint.includes('/claims')) {
                // Liste de tous les sinistres
                const claims = await dbManager.getAllClaims();
                return { items: claims, total: claims.length, skip: 0, limit: claims.length, page: 1, pages: 1 };
            } else if (cleanEndpoint.match(/\/clients\/\d+$/)) {
                // Endpoint spécifique: /clients/123
                const clientId = cleanEndpoint.split('/').pop();
                return await dbManager.getClient(clientId);
            } else if (cleanEndpoint.includes('/clients/search')) {
                // Recherche de clients - retourner tous les clients
                const clients = await dbManager.getAllClients();
                return { items: clients, total: clients.length };
            } else if (cleanEndpoint.includes('/clients')) {
                // Liste de tous les clients - retourne un array simple
                const clients = await dbManager.getAllClients();
                return clients;
            } else if (cleanEndpoint.match(/\/contracts\/\d+$/)) {
                // Endpoint spécifique: /contracts/456
                const contractId = cleanEndpoint.split('/').pop();
                return await dbManager.getContract(contractId);
            } else if (cleanEndpoint.includes('/contracts/number/')) {
                // Recherche par numéro de contrat
                const contractNumber = cleanEndpoint.split('/number/')[1];
                return await dbManager.getContractByNumber(contractNumber);
            } else if (cleanEndpoint.includes('/contracts')) {
                // Liste de tous les contrats
                const contracts = await dbManager.getAllContracts();
                return { items: contracts, total: contracts.length, skip: 0, limit: contracts.length, page: 1, pages: 1 };
            } else if (cleanEndpoint.includes('/addresses')) {
                // Adresses
                const addresses = await dbManager.getAllAddresses();
                return addresses;
            } else if (cleanEndpoint.includes('/construction-sites') || cleanEndpoint.includes('/sites')) {
                // Chantiers
                const sites = await dbManager.getAllSites();
                return sites;
            } else if (cleanEndpoint.includes('/contract-history') || cleanEndpoint.includes('/history')) {
                // Historique
                const history = await dbManager.getAllHistory();
                return history;
            } else if (cleanEndpoint.includes('/stats')) {
                // Stats générales - calculer depuis le cache
                const stats = await dbManager.getStats();
                const addresses = await dbManager.getAllAddresses();
                return {
                    total_clients: stats.clients || 0,
                    total_contracts: stats.contracts || 0,
                    total_claims: stats.claims || 0,
                    total_addresses: addresses.length || 0,
                    total_construction_sites: stats.sites || 0
                };
            } else if (cleanEndpoint.includes('/referentials/guarantees') || cleanEndpoint.includes('/referentials/guarantee-types')) {
                return await dbManager.getReferential('guarantees');
            } else if (cleanEndpoint.includes('/referentials/contract-types')) {
                return await dbManager.getReferential('contract_types');
            } else if (cleanEndpoint.includes('/referentials/clauses')) {
                return await dbManager.getReferential('clauses');
            } else if (cleanEndpoint.includes('/referentials/building-categories')) {
                return await dbManager.getReferential('building_categories');
            } else if (cleanEndpoint.includes('/referentials/work-categories')) {
                return await dbManager.getReferential('work_categories');
            } else if (cleanEndpoint.includes('/referentials/professions')) {
                return await dbManager.getReferential('professions');
            } else if (cleanEndpoint.includes('/referentials')) {
                // Référentiel générique non géré
                return [];
            }
        } catch (error) {
            console.error('Erreur de récupération du cache:', error);
        }
        
        return null;
    }

    async syncPendingChanges() {
        if (!this.dbReady || !this.isOnline) return;
        
        try {
            const pendingChanges = await dbManager.getPendingChanges();
            console.log(`Synchronisation de ${pendingChanges.length} modifications en attente`);
            
            for (const change of pendingChanges) {
                try {
                    // Envoyer la modification au serveur
                    await this.syncChange(change);
                    
                    // Supprimer la modification de la file d'attente
                    await dbManager.deletePendingChange(change.id);
                    console.log(`Modification ${change.id} synchronisée`);
                } catch (error) {
                    console.error(`Erreur de synchronisation de la modification ${change.id}:`, error);
                }
            }
        } catch (error) {
            console.error('Erreur de synchronisation:', error);
        }
    }

    async syncChange(change) {
        switch (change.entity_type) {
            case 'claim':
                return await this.updateClaim(change.entity_id, change.data);
            case 'contract':
                return await this.updateContract(change.entity_id, change.data);
            case 'client':
                return await this.updateClient(change.entity_id, change.data);
            default:
                throw new Error(`Type d'entité non géré: ${change.entity_type}`);
        }
    }

    // Health check
    async checkHealth() {
        try {
            await this.request('/health');
            return true;
        } catch {
            return false;
        }
    }

    // Clients
    async getClients(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return this.request(`/clients/?${queryString}`);
    }

    async getClient(clientNumber) {
        return this.request(`/clients/${clientNumber}`);
    }

    async searchClients(query, phonetic = false) {
        return this.request(`/clients/search?query=${encodeURIComponent(query)}&phonetic=${phonetic}`);
    }

    async createClient(clientData) {
        return this.request('/clients', {
            method: 'POST',
            body: JSON.stringify(clientData),
        });
    }

    async updateClient(clientNumber, clientData) {
        return this.request(`/clients/${clientNumber}`, {
            method: 'PUT',
            body: JSON.stringify(clientData),
        });
    }

    async deleteClient(clientId) {
        return this.request(`/clients/${clientId}`, {
            method: 'DELETE',
        });
    }

    // Addresses
    async getAddresses(clientId = null) {
        const endpoint = clientId ? `/clients/${clientId}/addresses` : '/addresses';
        return this.request(endpoint);
    }

    async getAddress(addressId) {
        return this.request(`/addresses/${addressId}`);
    }

    async createAddress(addressData) {
        return this.request('/addresses', {
            method: 'POST',
            body: JSON.stringify(addressData),
        });
    }

    async updateAddress(addressId, addressData) {
        return this.request(`/addresses/${addressId}`, {
            method: 'PUT',
            body: JSON.stringify(addressData),
        });
    }

    async deleteAddress(addressId) {
        return this.request(`/addresses/${addressId}`, {
            method: 'DELETE',
        });
    }

    // Construction Sites
    async getSites(clientId = null) {
        const endpoint = clientId ? `/clients/${clientId}/construction-sites` : '/construction-sites';
        return this.request(endpoint);
    }

    async getSite(siteId) {
        return this.request(`/construction-sites/${siteId}`);
    }

    async createSite(siteData) {
        return this.request('/construction-sites', {
            method: 'POST',
            body: JSON.stringify(siteData),
        });
    }

    async updateSite(siteId, siteData) {
        return this.request(`/construction-sites/${siteId}`, {
            method: 'PUT',
            body: JSON.stringify(siteData),
        });
    }

    async deleteSite(siteId) {
        return this.request(`/construction-sites/${siteId}`, {
            method: 'DELETE',
        });
    }

    // Contracts
    async getContracts(clientId = null, params = {}) {
        const endpoint = clientId ? `/clients/${clientId}/contracts` : '/contracts';
        const queryString = new URLSearchParams(params).toString();
        return this.request(`${endpoint}?${queryString}`);
    }

    async getContract(contractNumber) {
        return this.request(`/contracts/number/${contractNumber}`);
    }

    async getContractById(contractId) {
        return this.request(`/contracts/${contractId}`);
    }

    async createContract(contractData) {
        return this.request('/contracts', {
            method: 'POST',
            body: JSON.stringify(contractData),
        });
    }

    async updateContract(contractNumber, contractData) {
        return this.request(`/contracts/${contractNumber}`, {
            method: 'PUT',
            body: JSON.stringify(contractData),
        });
    }

    async deleteContract(contractId) {
        return this.request(`/contracts/${contractId}`, {
            method: 'DELETE',
        });
    }

    // Contract History
    async getContractHistory(contractId = null) {
        const endpoint = contractId ? `/contracts/${contractId}/history` : '/contract-history';
        return this.request(endpoint);
    }

    // Statistics
    async getStats() {
        return this.request('/stats');
    }

    // Referentials
    async getContractTypes() {
        return this.request('/referentials/contract-types');
    }

    async getContractType(code) {
        return this.request(`/referentials/contract-types/${code}`);
    }

    async createContractType(data) {
        return this.request('/referentials/contract-types', 'POST', data);
    }

    async getGuaranteeTypes(contractTypeCode = null) {
        const endpoint = contractTypeCode 
            ? `/referentials/contract-types/${contractTypeCode}/guarantees`
            : '/referentials/guarantees';
        return this.request(endpoint);
    }

    async getGuarantee(code) {
        return this.request(`/referentials/guarantees/${code}`);
    }

    async createGuarantee(data) {
        return this.request('/referentials/guarantees', 'POST', data);
    }

    async getClauses() {
        return this.request('/referentials/clauses');
    }

    async getClause(code) {
        return this.request(`/referentials/clauses/${code}`);
    }

    async createClause(data) {
        return this.request('/referentials/clauses', 'POST', data);
    }

    async getBuildingCategories() {
        return this.request('/referentials/building-categories');
    }

    async getBuildingCategory(code) {
        return this.request(`/referentials/building-categories/${code}`);
    }

    async createBuildingCategory(data) {
        return this.request('/referentials/building-categories', 'POST', data);
    }

    async getWorkCategories() {
        return this.request('/referentials/work-categories');
    }

    async getWorkCategory(code) {
        return this.request(`/referentials/work-categories/${code}`);
    }

    async createWorkCategory(data) {
        return this.request('/referentials/work-categories', 'POST', data);
    }

    async getProfessions() {
        return this.request('/referentials/professions');
    }

    async getProfession(code) {
        return this.request(`/referentials/professions/${code}`);
    }

    async createProfession(data) {
        return this.request('/referentials/professions', 'POST', data);
    }

    // Claims
    async getClaims(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return this.request(`/claims/?${queryString}`);
    }

    async getClaim(claimNumber) {
        return this.request(`/claims/${claimNumber}`);
    }

    async searchClaims(query) {
        // En mode hors ligne, rechercher dans IndexedDB
        if (!this.isOnline && this.dbReady) {
            console.log('Recherche hors ligne dans IndexedDB');
            return await dbManager.searchClaims(query);
        }
        
        return this.request(`/claims/search?query=${encodeURIComponent(query)}`);
    }

    async getClaimsByContract(contractId) {
        return this.request(`/claims/contract/${contractId}`);
    }

    async getClaimsStats() {
        return this.request('/claims/stats');
    }

    async createClaim(claimData) {
        return this.request('/claims/', {
            method: 'POST',
            body: JSON.stringify(claimData),
        });
    }

    async updateClaim(claimNumber, claimData) {
        // Si hors ligne, sauvegarder la modification localement
        if (!this.isOnline && this.dbReady) {
            console.log('Mode hors ligne: sauvegarde locale de la modification');
            await dbManager.updateClaim(claimNumber, claimData);
            return { ...claimData, claim_number: claimNumber, offline: true };
        }
        
        return this.request(`/claims/${claimNumber}`, {
            method: 'PUT',
            body: JSON.stringify(claimData),
        });
    }

    async deleteClaim(claimNumber) {
        return this.request(`/claims/${claimNumber}`, {
            method: 'DELETE',
        });
    }

    // Data Generation (via Python script - simulate with API calls)
    async generateData(count, type, clean) {
        return this.request('/generate-data', {
            method: 'POST',
            body: JSON.stringify({
                count: count,
                client_type: type,
                clean: clean
            })
        });
    }

    async generateClaims(count, clean) {
        return this.request('/generate-claims', {
            method: 'POST',
            body: JSON.stringify({
                count: count,
                clean: clean
            })
        });
    }

    async deleteAllData() {
        return this.request('/clean-data', {
            method: 'POST'
        });
    }
}

// Create global API instance
const api = new API(API_BASE_URL);
