// API Configuration
// Utiliser une URL relative pour que ça fonctionne avec n'importe quel domaine
const API_BASE_URL = '';

// API Client
class API {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        
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

            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
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
        return this.request(`/clients/search?q=${encodeURIComponent(query)}&phonetic=${phonetic}`);
    }

    async createClient(clientData) {
        return this.request('/clients/', {
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
        const endpoint = clientId ? `/clients/${clientId}/addresses` : '/addresses/';
        return this.request(endpoint);
    }

    async getAddress(addressId) {
        return this.request(`/addresses/${addressId}`);
    }

    async createAddress(addressData) {
        return this.request('/addresses/', {
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
        const endpoint = clientId ? `/clients/${clientId}/construction-sites` : '/construction-sites/';
        return this.request(endpoint);
    }

    async getSite(siteId) {
        return this.request(`/construction-sites/${siteId}`);
    }

    async createSite(siteData) {
        return this.request('/construction-sites/', {
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
        const endpoint = clientId ? `/clients/${clientId}/contracts` : '/contracts/';
        const queryString = new URLSearchParams(params).toString();
        return this.request(`${endpoint}?${queryString}`);
    }

    async getContract(contractNumber) {
        return this.request(`/contracts/${contractNumber}`);
    }

    async createContract(contractData) {
        return this.request('/contracts/', {
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
        const endpoint = contractId ? `/contracts/${contractId}/history` : '/contract-history/';
        return this.request(endpoint);
    }

    // Statistics
    async getStats() {
        return this.request('/stats/');
    }

    // Referentials
    async getContractTypes() {
        return this.request('/referentials/contract-types/');
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
            : '/referentials/guarantees/';
        return this.request(endpoint);
    }

    async getGuarantee(code) {
        return this.request(`/referentials/guarantees/${code}`);
    }

    async createGuarantee(data) {
        return this.request('/referentials/guarantees', 'POST', data);
    }

    async getClauses() {
        return this.request('/referentials/clauses/');
    }

    async getClause(code) {
        return this.request(`/referentials/clauses/${code}`);
    }

    async createClause(data) {
        return this.request('/referentials/clauses', 'POST', data);
    }

    async getBuildingCategories() {
        return this.request('/referentials/building-categories/');
    }

    async getBuildingCategory(code) {
        return this.request(`/referentials/building-categories/${code}`);
    }

    async createBuildingCategory(data) {
        return this.request('/referentials/building-categories', 'POST', data);
    }

    async getWorkCategories() {
        return this.request('/referentials/work-categories/');
    }

    async getWorkCategory(code) {
        return this.request(`/referentials/work-categories/${code}`);
    }

    async createWorkCategory(data) {
        return this.request('/referentials/work-categories', 'POST', data);
    }

    async getProfessions() {
        return this.request('/referentials/professions/');
    }

    async getProfession(code) {
        return this.request(`/referentials/professions/${code}`);
    }

    async createProfession(data) {
        return this.request('/referentials/professions', 'POST', data);
    }

    // Data Generation (via Python script - simulate with API calls)
    async generateData(count, type, clean) {
        return this.request('/generate-data/', {
            method: 'POST',
            body: JSON.stringify({
                count: count,
                client_type: type,
                clean: clean
            })
        });
    }

    async deleteAllData() {
        return this.request('/clean-data/', {
            method: 'POST'
        });
    }
}

// Create global API instance
const api = new API(API_BASE_URL);
