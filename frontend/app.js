// Application State
const app = {
    currentView: 'dashboard',
    phoneticMode: false,
    data: {
        clients: [],
        addresses: [],
        sites: [],
        contracts: [],
        history: [],
    },
};

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initGlobalSearch();
    checkAPIStatus();
    loadDashboard();
    
    // Check API status every 30 seconds
    setInterval(checkAPIStatus, 30000);
});

// Navigation
function initNavigation() {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            const view = item.dataset.view;
            if (!view) return; // Skip items without data-view (like external links)
            e.preventDefault();
            switchView(view);
        });
    });
}

function switchView(viewName) {
    // Update navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.toggle('active', item.dataset.view === viewName);
    });
    
    // Update views
    document.querySelectorAll('.view').forEach(view => {
        view.classList.remove('active');
    });
    document.getElementById(`${viewName}-view`).classList.add('active');
    
    // Update header
    const titles = {
        dashboard: { title: 'Tableau de bord', subtitle: 'Vue d\'ensemble de la base de données' },
        clients: { title: 'Clients', subtitle: 'Gestion des clients particuliers et professionnels' },
        addresses: { title: 'Adresses', subtitle: 'Gestion des adresses des clients' },
        sites: { title: 'Chantiers', subtitle: 'Gestion des chantiers de construction' },
        contracts: { title: 'Contrats', subtitle: 'Gestion des contrats d\'assurance' },
        history: { title: 'Historique', subtitle: 'Historique des modifications de contrats' },
        generate: { title: 'Génération de données', subtitle: 'Outils de génération et suppression de données' },
        referentials: { title: 'Référentiels', subtitle: 'Gestion des données de référence' },
    };
    
    document.getElementById('page-title').textContent = titles[viewName].title;
    document.getElementById('page-subtitle').textContent = titles[viewName].subtitle;
    
    app.currentView = viewName;
    
    // Load view data
    loadViewData(viewName);
}

// API Status Check
async function checkAPIStatus() {
    const isOnline = await api.checkHealth();
    const icon = document.getElementById('api-status-icon');
    const text = document.getElementById('api-status-text');
    
    if (isOnline) {
        icon.className = 'fas fa-circle online';
        text.textContent = 'API connectée';
    } else {
        icon.className = 'fas fa-circle offline';
        text.textContent = 'API déconnectée';
    }
}

// Global Search
function initGlobalSearch() {
    const searchInput = document.getElementById('global-search');
    const phoneticToggle = document.getElementById('phonetic-toggle');
    
    let searchTimeout;
    searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => performSearch(e.target.value), 300);
    });
    
    phoneticToggle.addEventListener('click', () => {
        app.phoneticMode = !app.phoneticMode;
        phoneticToggle.classList.toggle('active', app.phoneticMode);
        if (searchInput.value) {
            performSearch(searchInput.value);
        }
    });
}

async function performSearch(query) {
    if (!query.trim()) {
        loadViewData(app.currentView);
        return;
    }
    
    if (query.trim().length < 3) {
        return;
    }
    
    try {
        const results = await api.searchClients(query, app.phoneticMode);
        
        if (app.currentView !== 'clients') {
            switchView('clients');
        }
        
        displayClients(results);
        showToast('success', 'Recherche', `${results.length} résultat(s) trouvé(s)`);
    } catch (error) {
        showToast('error', 'Erreur', 'Erreur lors de la recherche');
        console.error(error);
    }
}

// Load View Data
async function loadViewData(viewName) {
    switch (viewName) {
        case 'dashboard':
            await loadDashboard();
            break;
        case 'clients':
            await loadClients();
            break;
        case 'addresses':
            await loadAddresses();
            break;
        case 'sites':
            await loadSites();
            break;
        case 'contracts':
            await loadContracts();
            break;
        case 'claims':
            await loadClaims();
            break;
        case 'history':
            await loadHistory();
            break;
        case 'referentials':
            await loadReferentials();
            break;
    }
}

// Dashboard
async function loadDashboard() {
    try {
        const stats = await api.getStats();
        const claimsStats = await api.getClaimsStats();
        
        document.getElementById('stat-clients').textContent = stats.total_clients || 0;
        document.getElementById('stat-addresses').textContent = stats.total_addresses || 0;
        document.getElementById('stat-sites').textContent = stats.total_construction_sites || 0;
        document.getElementById('stat-contracts').textContent = stats.total_contracts || 0;
        document.getElementById('stat-claims').textContent = claimsStats.total_claims || 0;
        
        // Recent activity - simplified without loading contracts
        displayRecentActivity([]);
        
        // Alerts - simplified
        displayAlerts([]);
    } catch (error) {
        console.error('Error loading dashboard:', error);
        showToast('error', 'Erreur', 'Impossible de charger le tableau de bord');
    }
}

function displayRecentActivity(contracts) {
    const container = document.getElementById('recent-activity');
    
    container.innerHTML = `
        <p class="help-text">Statistiques chargées avec succès</p>
        <div style="padding: 12px; border-left: 3px solid var(--success-color); background: rgba(16, 185, 129, 0.05);">
            <p style="font-size: 14px;">✅ Base de données opérationnelle</p>
        </div>
    `;
}

function displayAlerts(contracts) {
    const container = document.getElementById('alerts-list');
    
    container.innerHTML = '<p class="help-text">Aucune alerte</p>';
}

// Clients
async function loadClients() {
    try {
        const clients = await api.getClients();
        app.data.clients = clients;
        displayClients(clients);
    } catch (error) {
        console.error('Error loading clients:', error);
        showToast('error', 'Erreur', 'Impossible de charger les clients');
    }
}

function displayClients(clients) {
    const container = document.getElementById('clients-table-container');
    
    if (!clients || clients.length === 0) {
        container.innerHTML = '<p class="help-text">Aucun client trouvé</p>';
        return;
    }
    
    const html = `
        <div class="data-table">
            <table>
                <thead>
                    <tr>
                        <th>Numéro</th>
                        <th>Type</th>
                        <th>Nom</th>
                        <th>Email</th>
                        <th>Téléphone</th>
                        <th>Ville</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${clients.map(client => `
                        <tr>
                            <td><strong>${client.client_number}</strong></td>
                            <td><span class="badge badge-info">${client.client_type}</span></td>
                            <td>${getClientName(client)}</td>
                            <td>${client.email || '-'}</td>
                            <td>${client.phone || '-'}</td>
                            <td>${client.city || '-'}</td>
                            <td>
                                <div class="table-actions">
                                    <button class="btn-edit" onclick="viewClient(${client.id})" title="Voir">
                                        <i class="fas fa-eye"></i>
                                    </button>
                                    <button class="btn-edit" onclick="editClient(${client.id})" title="Modifier">
                                        <i class="fas fa-edit"></i>
                                    </button>
                                    <button class="btn-delete" onclick="deleteClient(${client.id})" title="Supprimer">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </div>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
    
    container.innerHTML = html;
}

function getClientName(client) {
    if (client.client_type === 'professionnel') {
        return client.company_name || '-';
    }
    return `${client.first_name || ''} ${client.last_name || ''}`.trim() || '-';
}

// Addresses
async function loadAddresses() {
    try {
        const addresses = await api.getAddresses();
        app.data.addresses = addresses;
        displayAddresses(addresses);
    } catch (error) {
        console.error('Error loading addresses:', error);
        showToast('error', 'Erreur', 'Impossible de charger les adresses');
    }
}

function displayAddresses(addresses) {
    const container = document.getElementById('addresses-table-container');
    
    if (!addresses || addresses.length === 0) {
        container.innerHTML = '<p class="help-text">Aucune adresse trouvée</p>';
        return;
    }
    
    const html = `
        <div class="data-table">
            <table>
                <thead>
                    <tr>
                        <th>Référence</th>
                        <th>Type</th>
                        <th>Adresse</th>
                        <th>Code Postal</th>
                        <th>Ville</th>
                        <th>GPS</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${addresses.map(addr => `
                        <tr>
                            <td><strong>${addr.reference}</strong></td>
                            <td><span class="badge badge-info">${addr.address_type}</span></td>
                            <td>${addr.address_line1}</td>
                            <td>${addr.postal_code}</td>
                            <td>${addr.city}</td>
                            <td>${addr.latitude && addr.longitude ? `📍 ${addr.latitude.toFixed(4)}, ${addr.longitude.toFixed(4)}` : '-'}</td>
                            <td>
                                <div class="table-actions">
                                    <button class="btn-edit" onclick="editAddress(${addr.id})" title="Modifier">
                                        <i class="fas fa-edit"></i>
                                    </button>
                                    <button class="btn-delete" onclick="deleteAddress(${addr.id})" title="Supprimer">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </div>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
    
    container.innerHTML = html;
}

// Sites
async function loadSites() {
    try {
        const sites = await api.getSites();
        app.data.sites = sites;
        displaySites(sites);
    } catch (error) {
        console.error('Error loading sites:', error);
        showToast('error', 'Erreur', 'Impossible de charger les chantiers');
    }
}

function displaySites(sites) {
    const container = document.getElementById('sites-table-container');
    
    if (!sites || sites.length === 0) {
        container.innerHTML = '<p class="help-text">Aucun chantier trouvé</p>';
        return;
    }
    
    const html = `
        <div class="data-table">
            <table>
                <thead>
                    <tr>
                        <th>Référence</th>
                        <th>Nom</th>
                        <th>Catégorie</th>
                        <th>Ville</th>
                        <th>Coût</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${sites.map(site => `
                        <tr>
                            <td><strong>${site.site_reference}</strong></td>
                            <td>${site.site_name}</td>
                            <td><span class="badge badge-info">${site.building_category_code}</span></td>
                            <td>${site.city}</td>
                            <td>${formatCurrency(site.construction_cost)}</td>
                            <td>
                                <div class="table-actions">
                                    <button class="btn-edit" onclick="editSite(${site.id})" title="Modifier">
                                        <i class="fas fa-edit"></i>
                                    </button>
                                    <button class="btn-delete" onclick="deleteSite(${site.id})" title="Supprimer">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </div>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
    
    container.innerHTML = html;
}

// Contracts
async function loadContracts() {
    try {
        const contracts = await api.getContracts();
        app.data.contracts = contracts;
        displayContracts(contracts);
    } catch (error) {
        console.error('Error loading contracts:', error);
        showToast('error', 'Erreur', 'Impossible de charger les contrats');
    }
}

// Claims
async function loadClaims() {
    try {
        const claims = await api.getClaims();
        app.data.claims = claims;
        displayClaims(claims);
    } catch (error) {
        console.error('Error loading claims:', error);
        showToast('error', 'Erreur', 'Impossible de charger les sinistres');
    }
}

function displayClaims(claims) {
    const container = document.getElementById('claims-table-container');
    
    if (!claims || claims.length === 0) {
        container.innerHTML = '<p class="help-text">Aucun sinistre trouvé</p>';
        return;
    }
    
    const html = `
        <div class="data-table">
            <table>
                <thead>
                    <tr>
                        <th>Numéro</th>
                        <th>Titre</th>
                        <th>Type</th>
                        <th>Statut</th>
                        <th>Gravité</th>
                        <th>Date déclaration</th>
                        <th>Montant réclamé</th>
                        <th>Montant réservé</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${claims.map(claim => `
                        <tr>
                            <td><strong>${claim.claim_number}</strong></td>
                            <td>${claim.title}</td>
                            <td><span class="badge badge-info">${claim.claim_type}</span></td>
                            <td><span class="badge badge-${getClaimStatusBadge(claim.status)}">${claim.status}</span></td>
                            <td><span class="badge badge-${getSeverityBadge(claim.severity)}">${claim.severity}</span></td>
                            <td>${formatDate(claim.declaration_date)}</td>
                            <td>${formatCurrency(claim.claimed_amount)}</td>
                            <td>${formatCurrency(claim.reserved_amount)}</td>
                            <td>
                                <div class="table-actions">
                                    <button class="btn-edit" onclick="showClaimModal('${claim.claim_number}')" title="Voir/Modifier">
                                        <i class="fas fa-eye"></i>
                                    </button>
                                    <button class="btn-delete" onclick="deleteClaim('${claim.claim_number}')" title="Supprimer">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </div>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
    
    container.innerHTML = html;
}

async function filterClaims() {
    const statusFilter = document.getElementById('claim-status-filter').value;
    const typeFilter = document.getElementById('claim-type-filter').value;
    
    let filtered = app.data.claims || [];
    
    if (statusFilter !== 'all') {
        filtered = filtered.filter(c => c.status === statusFilter);
    }
    
    if (typeFilter !== 'all') {
        filtered = filtered.filter(c => c.claim_type === typeFilter);
    }
    
    displayClaims(filtered);
}

async function showClaimModal(claimNumber = null) {
    // TODO: Implement modal for viewing/editing claim details
    if (claimNumber) {
        try {
            const claim = await api.getClaim(claimNumber);
            console.log('Claim details:', claim);
            showToast('info', 'Info', `Détails du sinistre ${claimNumber}`);
        } catch (error) {
            console.error('Error loading claim:', error);
            showToast('error', 'Erreur', 'Impossible de charger les détails du sinistre');
        }
    }
}

async function deleteClaim(claimNumber) {
    if (!confirm(`Êtes-vous sûr de vouloir supprimer le sinistre ${claimNumber} ?`)) return;
    
    try {
        await api.deleteClaim(claimNumber);
        showToast('success', 'Succès', 'Sinistre supprimé');
        await loadClaims();
    } catch (error) {
        console.error('Error deleting claim:', error);
        showToast('error', 'Erreur', 'Impossible de supprimer le sinistre');
    }
}

function getClaimStatusBadge(status) {
    const badges = {
        'declared': 'warning',
        'acknowledged': 'info',
        'investigating': 'info',
        'expertise_ongoing': 'info',
        'settlement_pending': 'warning',
        'settled': 'success',
        'rejected': 'danger',
        'closed': 'secondary'
    };
    return badges[status] || 'secondary';
}

function getSeverityBadge(severity) {
    const badges = {
        'minor': 'success',
        'moderate': 'warning',
        'major': 'danger',
        'critical': 'danger'
    };
    return badges[severity] || 'secondary';
}

function displayContracts(contracts) {
    const container = document.getElementById('contracts-table-container');
    
    if (!contracts || contracts.length === 0) {
        container.innerHTML = '<p class="help-text">Aucun contrat trouvé</p>';
        return;
    }
    
    const html = `
        <div class="data-table">
            <table>
                <thead>
                    <tr>
                        <th>Numéro</th>
                        <th>Type</th>
                        <th>Statut</th>
                        <th>Date effet</th>
                        <th>Date expiration</th>
                        <th>Montant assuré</th>
                        <th>Prime annuelle</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${contracts.map(contract => `
                        <tr>
                            <td><strong>${contract.contract_number}</strong></td>
                            <td><span class="badge badge-info">${contract.contract_type_code}</span></td>
                            <td><span class="badge badge-${getStatusBadge(contract.status)}">${contract.status}</span></td>
                            <td>${formatDate(contract.effective_date)}</td>
                            <td>${formatDate(contract.expiry_date)}</td>
                            <td>${formatCurrency(contract.insured_amount)}</td>
                            <td>${formatCurrency(contract.annual_premium)}</td>
                            <td>
                                <div class="table-actions">
                                    <button class="btn-edit" onclick="editContract('${contract.contract_number}')" title="Modifier">
                                        <i class="fas fa-edit"></i>
                                    </button>
                                    <button class="btn-delete" onclick="deleteContract(${contract.id})" title="Supprimer">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </div>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
    
    container.innerHTML = html;
}

// History
async function loadHistory() {
    try {
        const history = await api.getContractHistory();
        app.data.history = history;
        displayHistory(history);
    } catch (error) {
        console.error('Error loading history:', error);
        showToast('error', 'Erreur', 'Impossible de charger l\'historique');
    }
}

function displayHistory(history) {
    const container = document.getElementById('history-table-container');
    
    if (!history || history.length === 0) {
        container.innerHTML = '<p class="help-text">Aucun historique trouvé</p>';
        return;
    }
    
    const html = `
        <div class="data-table">
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Action</th>
                        <th>Champ modifié</th>
                        <th>Ancienne valeur</th>
                        <th>Nouvelle valeur</th>
                        <th>Modifié par</th>
                        <th>Commentaire</th>
                    </tr>
                </thead>
                <tbody>
                    ${history.slice(0, 100).map(entry => `
                        <tr>
                            <td>${formatDateTime(entry.changed_at)}</td>
                            <td><span class="badge badge-info">${entry.action}</span></td>
                            <td>${entry.field_changed || '-'}</td>
                            <td>${entry.old_value || '-'}</td>
                            <td>${entry.new_value || '-'}</td>
                            <td>${entry.changed_by || '-'}</td>
                            <td>${entry.comment || '-'}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
    
    container.innerHTML = html;
}

// Referentials
async function loadReferentials() {
    try {
        const [contractTypes, guaranteeTypes, clauses, buildingCategories, workCategories, professions] = await Promise.all([
            api.getContractTypes(),
            api.getGuaranteeTypes(),
            api.getClauses(),
            api.getBuildingCategories(),
            api.getWorkCategories(),
            api.getProfessions(),
        ]);
        
        document.querySelector('[data-ref="contract_types"] .ref-count').textContent = `${contractTypes.length} types`;
        document.querySelector('[data-ref="guarantee_types"] .ref-count').textContent = `${guaranteeTypes.length} garanties`;
        document.querySelector('[data-ref="clauses"] .ref-count').textContent = `${clauses.length} clauses`;
        document.querySelector('[data-ref="building_categories"] .ref-count').textContent = `${buildingCategories.length} catégories`;
        document.querySelector('[data-ref="work_categories"] .ref-count').textContent = `${workCategories.length} catégories`;
        document.querySelector('[data-ref="professions"] .ref-count').textContent = `${professions.length} professions`;
    } catch (error) {
        console.error('Error loading referentials:', error);
    }
}

// Data Generation
async function generateData() {
    const count = parseInt(document.getElementById('gen-count').value);
    const type = document.getElementById('gen-type').value;
    const clean = document.getElementById('gen-clean').checked;
    
    const confirmMsg = clean 
        ? `⚠️ ATTENTION : Êtes-vous sûr de vouloir SUPPRIMER toutes les données existantes et générer ${count} nouveaux clients ?`
        : `Êtes-vous sûr de vouloir générer ${count} nouveaux clients ?`;
    
    if (!confirm(confirmMsg)) return;
    
    showToast('info', 'Génération en cours', 'Le script est en cours d\'exécution...');
    
    try {
        const result = await api.generateData(count, type, clean);
        showToast('success', 'Succès', result.message);
        
        // Afficher les détails dans une modale
        showModal(
            'Génération terminée',
            `<div style="color: var(--success-color); font-weight: 600; margin-bottom: 16px;">
                ✅ ${result.message}
            </div>
            <details>
                <summary style="cursor: pointer; font-weight: 500; margin-bottom: 8px;">Voir les logs</summary>
                <pre style="background: var(--bg-tertiary); padding: 16px; border-radius: 8px; overflow-x: auto; margin-top: 8px; font-size: 12px; max-height: 400px; overflow-y: auto;">
${result.output || 'Aucun log disponible'}
                </pre>
            </details>
            <p style="margin-top: 16px; font-size: 13px; color: var(--text-secondary);">
                Rechargez la page pour voir les nouvelles données dans le tableau de bord.
            </p>`,
            null
        );
        
        // Recharger les statistiques
        setTimeout(() => {
            loadDashboard();
        }, 1000);
    } catch (error) {
        console.error('Erreur génération:', error);
        showToast('error', 'Erreur', error.message || 'Impossible de générer les données');
    }
}

async function deleteAllData() {
    const confirmation = prompt('⚠️ DANGER : Pour confirmer la suppression de TOUTES les données, tapez "SUPPRIMER" :');
    
    if (confirmation !== 'SUPPRIMER') {
        showToast('info', 'Annulé', 'Suppression annulée');
        return;
    }
    
    showToast('warning', 'Suppression en cours', 'Suppression de toutes les données...');
    
    try {
        const result = await api.deleteAllData();
        showToast('success', 'Succès', result.message);
        
        // Afficher les détails dans une modale
        showModal(
            'Suppression terminée',
            `<div style="color: var(--success-color); font-weight: 600; margin-bottom: 16px;">
                ✅ ${result.message}
            </div>
            <details>
                <summary style="cursor: pointer; font-weight: 500; margin-bottom: 8px;">Voir les logs</summary>
                <pre style="background: var(--bg-tertiary); padding: 16px; border-radius: 8px; overflow-x: auto; margin-top: 8px; font-size: 12px; max-height: 400px; overflow-y: auto;">
${result.output || 'Aucun log disponible'}
                </pre>
            </details>
            <p style="margin-top: 16px; font-size: 13px; color: var(--text-secondary);">
                Rechargez la page pour voir les statistiques mises à jour.
            </p>`,
            null
        );
        
        // Recharger les statistiques
        setTimeout(() => {
            loadDashboard();
        }, 1000);
    } catch (error) {
        console.error('Erreur suppression:', error);
        showToast('error', 'Erreur', error.message || 'Impossible de supprimer les données');
    }
}

async function generateClaims() {
    const count = parseInt(document.getElementById('gen-claims-count').value);
    const clean = document.getElementById('gen-claims-clean').checked;
    
    const confirmMsg = clean 
        ? `⚠️ ATTENTION : Êtes-vous sûr de vouloir SUPPRIMER tous les sinistres existants et générer ${count} nouveaux sinistres ?`
        : `Êtes-vous sûr de vouloir générer ${count} nouveaux sinistres ?`;
    
    if (!confirm(confirmMsg)) return;
    
    showToast('info', 'Génération en cours', 'Génération des sinistres...');
    
    try {
        const result = await api.generateClaims(count, clean);
        showToast('success', 'Succès', result.message);
        
        // Afficher les détails dans une modale
        showModal(
            'Génération de sinistres terminée',
            `<div style="color: var(--success-color); font-weight: 600; margin-bottom: 16px;">
                ✅ ${result.message}
            </div>
            <p style="margin-top: 16px; font-size: 13px; color: var(--text-secondary);">
                Rechargez la page pour voir les nouveaux sinistres dans le tableau de bord.
            </p>`,
            null
        );
        
        // Recharger les statistiques
        setTimeout(() => {
            loadDashboard();
        }, 1000);
    } catch (error) {
        console.error('Erreur génération sinistres:', error);
        showToast('error', 'Erreur', error.message || 'Impossible de générer les sinistres');
    }
}

// CRUD Operations
async function viewClient(clientId) {
    // TODO: Implement view client detail modal
    showToast('info', 'Info', 'Fonctionnalité en cours de développement');
}

async function editClient(clientId) {
    // TODO: Implement edit client modal
    showToast('info', 'Info', 'Fonctionnalité en cours de développement');
}

async function deleteClient(clientId) {
    if (!confirm('Êtes-vous sûr de vouloir supprimer ce client et toutes ses données associées ?')) {
        return;
    }
    
    try {
        await api.deleteClient(clientId);
        showToast('success', 'Succès', 'Client supprimé avec succès');
        loadClients();
    } catch (error) {
        showToast('error', 'Erreur', 'Impossible de supprimer le client');
        console.error(error);
    }
}

// Modal
function showModal(title, bodyContent, onSave) {
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-body').innerHTML = bodyContent;
    document.getElementById('modal-overlay').classList.add('active');
    
    const actionBtn = document.getElementById('modal-action');
    if (onSave) {
        actionBtn.style.display = 'block';
        actionBtn.onclick = onSave;
    } else {
        actionBtn.style.display = 'none';
    }
}

function closeModal() {
    document.getElementById('modal-overlay').classList.remove('active');
}

// Toast Notifications
function showToast(type, title, message) {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle',
    };
    
    toast.innerHTML = `
        <i class="fas ${icons[type]}"></i>
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            <div class="toast-message">${message}</div>
        </div>
    `;
    
    document.getElementById('toast-container').appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 5000);
}

// Utility Functions
function formatCurrency(amount) {
    if (!amount) return '-';
    return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(amount);
}

function formatDate(dateString) {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('fr-FR');
}

function formatDateTime(dateString) {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleString('fr-FR');
}

function getStatusBadge(status) {
    const badges = {
        'actif': 'success',
        'en_attente': 'warning',
        'brouillon': 'info',
        'expire': 'danger',
        'resilie': 'danger',
    };
    return badges[status] || 'info';
}

// Placeholder functions for modals (to be implemented)
function showClientModal() { showToast('info', 'Info', 'Fonctionnalité en cours de développement'); }
function showAddressModal() { showToast('info', 'Info', 'Fonctionnalité en cours de développement'); }
function showSiteModal() { showToast('info', 'Info', 'Fonctionnalité en cours de développement'); }
function showContractModal() { showToast('info', 'Info', 'Fonctionnalité en cours de développement'); }
function editAddress(id) { showToast('info', 'Info', 'Fonctionnalité en cours de développement'); }
function deleteAddress(id) { showToast('info', 'Info', 'Fonctionnalité en cours de développement'); }
function editSite(id) { showToast('info', 'Info', 'Fonctionnalité en cours de développement'); }
function deleteSite(id) { showToast('info', 'Info', 'Fonctionnalité en cours de développement'); }
function editContract(number) { showToast('info', 'Info', 'Fonctionnalité en cours de développement'); }
function deleteContract(id) { showToast('info', 'Info', 'Fonctionnalité en cours de développement'); }

// Referential Management
async function loadReferential(type) {
    const config = {
        contract_types: {
            title: 'Types de contrats',
            apiMethod: 'getContractTypes',
            fields: ['code', 'name', 'description', 'is_mandatory', 'is_active'],
            labels: { code: 'Code', name: 'Nom', description: 'Description', is_mandatory: 'Obligatoire', is_active: 'Actif' },
            createModal: showContractTypeModal
        },
        guarantee_types: {
            title: 'Types de garanties',
            apiMethod: 'getGuaranteeTypes',
            fields: ['code', 'name', 'category', 'guarantee_type', 'default_ceiling', 'default_franchise'],
            labels: { code: 'Code', name: 'Nom', category: 'Catégorie', guarantee_type: 'Type', default_ceiling: 'Plafond', default_franchise: 'Franchise' },
            createModal: showGuaranteeModal
        },
        building_categories: {
            title: 'Catégories de bâtiments',
            apiMethod: 'getBuildingCategories',
            fields: ['code', 'name', 'description', 'risk_coefficient', 'is_active'],
            labels: { code: 'Code', name: 'Nom', description: 'Description', risk_coefficient: 'Coefficient risque', is_active: 'Actif' },
            createModal: showBuildingCategoryModal
        },
        work_categories: {
            title: 'Catégories de travaux',
            apiMethod: 'getWorkCategories',
            fields: ['code', 'name', 'description', 'risk_level', 'is_active'],
            labels: { code: 'Code', name: 'Nom', description: 'Description', risk_level: 'Niveau risque', is_active: 'Actif' },
            createModal: showWorkCategoryModal
        },
        clauses: {
            title: 'Clauses contractuelles',
            apiMethod: 'getClauses',
            fields: ['code', 'title', 'category', 'is_mandatory', 'is_negotiable', 'is_active'],
            labels: { code: 'Code', title: 'Titre', category: 'Catégorie', is_mandatory: 'Obligatoire', is_negotiable: 'Négociable', is_active: 'Actif' },
            createModal: showClauseModal
        },
        professions: {
            title: 'Professions',
            apiMethod: 'getProfessions',
            fields: ['code', 'name', 'category', 'rc_decennale_required', 'rc_pro_required', 'is_active'],
            labels: { code: 'Code', name: 'Nom', category: 'Catégorie', rc_decennale_required: 'RC Décennale', rc_pro_required: 'RC Pro', is_active: 'Actif' },
            createModal: showProfessionModal
        }
    };

    const refConfig = config[type];
    if (!refConfig) return;

    try {
        const data = await api[refConfig.apiMethod]();
        
        let html = `
            <div class="view-header">
                <h2>${refConfig.title}</h2>
                <button class="btn btn-primary" onclick="${refConfig.createModal.name}()">
                    <i class="fas fa-plus"></i> Nouveau
                </button>
            </div>
            <div class="data-table-container">
                <table class="data-table">
                    <thead>
                        <tr>
                            ${refConfig.fields.map(f => `<th>${refConfig.labels[f]}</th>`).join('')}
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        data.forEach(item => {
            html += '<tr>';
            refConfig.fields.forEach(field => {
                let value = item[field];
                if (typeof value === 'boolean') {
                    value = value ? '<i class="fas fa-check" style="color: var(--success-color)"></i>' : '<i class="fas fa-times" style="color: var(--danger-color)"></i>';
                } else if (field.includes('ceiling') || field.includes('franchise')) {
                    value = formatCurrency(value);
                } else if (!value) {
                    value = '-';
                }
                html += `<td>${value}</td>`;
            });
            html += `
                <td>
                    <button class="btn-icon" onclick="viewReferential('${type}', '${item.code}')" title="Voir">
                        <i class="fas fa-eye"></i>
                    </button>
                </td>
            </tr>`;
        });

        html += `
                    </tbody>
                </table>
            </div>
        `;

        showModal(refConfig.title, html, null);
    } catch (error) {
        console.error('Error loading referential:', error);
        showToast('error', 'Erreur', 'Impossible de charger les données');
    }
}

async function viewReferential(type, code) {
    try {
        let data;
        switch(type) {
            case 'contract_types':
                data = await api.getContractType(code);
                break;
            case 'guarantee_types':
                data = await api.getGuarantee(code);
                break;
            case 'building_categories':
                data = await api.getBuildingCategory(code);
                break;
            case 'work_categories':
                data = await api.getWorkCategory(code);
                break;
            case 'clauses':
                data = await api.getClause(code);
                break;
            case 'professions':
                data = await api.getProfession(code);
                break;
        }

        let html = '<div class="detail-view">';
        for (const [key, value] of Object.entries(data)) {
            if (key === 'id') continue;
            let displayValue = value;
            if (typeof value === 'boolean') {
                displayValue = value ? 'Oui' : 'Non';
            } else if (typeof value === 'object' && value !== null) {
                displayValue = JSON.stringify(value, null, 2);
            } else if (!value) {
                displayValue = '-';
            }
            html += `
                <div class="detail-item">
                    <label>${key}:</label>
                    <span>${displayValue}</span>
                </div>
            `;
        }
        html += '</div>';

        showModal('Détails', html, null);
    } catch (error) {
        console.error('Error viewing referential:', error);
        showToast('error', 'Erreur', 'Impossible de charger les détails');
    }
}

// Referential CRUD Modals
function showContractTypeModal(data = null) {
    const title = data ? 'Modifier le type de contrat' : 'Nouveau type de contrat';
    const html = `
        <form id="contract-type-form">
            <div class="form-group">
                <label for="ct-code">Code *</label>
                <input type="text" id="ct-code" value="${data?.code || ''}" ${data ? 'readonly' : ''} required>
            </div>
            <div class="form-group">
                <label for="ct-name">Nom *</label>
                <input type="text" id="ct-name" value="${data?.name || ''}" required>
            </div>
            <div class="form-group">
                <label for="ct-description">Description</label>
                <textarea id="ct-description" rows="3">${data?.description || ''}</textarea>
            </div>
            <div class="form-group">
                <label for="ct-legal-ref">Référence légale</label>
                <input type="text" id="ct-legal-ref" value="${data?.legal_reference || ''}">
            </div>
            <div class="form-group">
                <label>
                    <input type="checkbox" id="ct-mandatory" ${data?.is_mandatory ? 'checked' : ''}>
                    Obligatoire
                </label>
            </div>
            <div class="form-group">
                <label>
                    <input type="checkbox" id="ct-active" ${data?.is_active !== false ? 'checked' : ''}>
                    Actif
                </label>
            </div>
        </form>
    `;

    showModal(title, html, async () => {
        const formData = {
            code: document.getElementById('ct-code').value,
            name: document.getElementById('ct-name').value,
            description: document.getElementById('ct-description').value || null,
            legal_reference: document.getElementById('ct-legal-ref').value || null,
            is_mandatory: document.getElementById('ct-mandatory').checked,
            is_active: document.getElementById('ct-active').checked
        };

        try {
            await api.createContractType(formData);
            showToast('success', 'Succès', 'Type de contrat créé');
            closeModal();
            loadReferentials();
        } catch (error) {
            showToast('error', 'Erreur', error.message || 'Impossible de créer le type de contrat');
        }
    });
}

function showGuaranteeModal(data = null) {
    const title = data ? 'Modifier la garantie' : 'Nouvelle garantie';
    const html = `
        <form id="guarantee-form">
            <div class="form-group">
                <label for="g-code">Code *</label>
                <input type="text" id="g-code" value="${data?.code || ''}" ${data ? 'readonly' : ''} required>
            </div>
            <div class="form-group">
                <label for="g-name">Nom *</label>
                <input type="text" id="g-name" value="${data?.name || ''}" required>
            </div>
            <div class="form-group">
                <label for="g-description">Description</label>
                <textarea id="g-description" rows="3">${data?.description || ''}</textarea>
            </div>
            <div class="form-group">
                <label for="g-category">Catégorie *</label>
                <input type="text" id="g-category" value="${data?.category || ''}" required>
            </div>
            <div class="form-group">
                <label for="g-type">Type de garantie *</label>
                <select id="g-type" required>
                    <option value="obligatoire" ${data?.guarantee_type === 'obligatoire' ? 'selected' : ''}>Obligatoire</option>
                    <option value="optionnelle" ${data?.guarantee_type === 'optionnelle' ? 'selected' : ''}>Optionnelle</option>
                    <option value="complementaire" ${data?.guarantee_type === 'complementaire' ? 'selected' : ''}>Complémentaire</option>
                </select>
            </div>
            <div class="form-group">
                <label for="g-ceiling">Plafond par défaut</label>
                <input type="number" id="g-ceiling" value="${data?.default_ceiling || ''}" step="0.01">
            </div>
            <div class="form-group">
                <label for="g-franchise">Franchise par défaut</label>
                <input type="number" id="g-franchise" value="${data?.default_franchise || ''}" step="0.01">
            </div>
            <div class="form-group">
                <label>
                    <input type="checkbox" id="g-active" ${data?.is_active !== false ? 'checked' : ''}>
                    Actif
                </label>
            </div>
        </form>
    `;

    showModal(title, html, async () => {
        const formData = {
            code: document.getElementById('g-code').value,
            name: document.getElementById('g-name').value,
            description: document.getElementById('g-description').value || null,
            category: document.getElementById('g-category').value,
            guarantee_type: document.getElementById('g-type').value,
            default_ceiling: parseFloat(document.getElementById('g-ceiling').value) || null,
            default_franchise: parseFloat(document.getElementById('g-franchise').value) || null,
            is_active: document.getElementById('g-active').checked
        };

        try {
            await api.createGuarantee(formData);
            showToast('success', 'Succès', 'Garantie créée');
            closeModal();
            loadReferentials();
        } catch (error) {
            showToast('error', 'Erreur', error.message || 'Impossible de créer la garantie');
        }
    });
}

function showBuildingCategoryModal(data = null) {
    const title = data ? 'Modifier la catégorie de bâtiment' : 'Nouvelle catégorie de bâtiment';
    const html = `
        <form id="building-category-form">
            <div class="form-group">
                <label for="bc-code">Code *</label>
                <input type="text" id="bc-code" value="${data?.code || ''}" ${data ? 'readonly' : ''} required>
            </div>
            <div class="form-group">
                <label for="bc-name">Nom *</label>
                <input type="text" id="bc-name" value="${data?.name || ''}" required>
            </div>
            <div class="form-group">
                <label for="bc-description">Description</label>
                <textarea id="bc-description" rows="3">${data?.description || ''}</textarea>
            </div>
            <div class="form-group">
                <label for="bc-risk">Coefficient de risque</label>
                <input type="number" id="bc-risk" value="${data?.risk_coefficient || ''}" step="0.01" min="0" max="5">
            </div>
            <div class="form-group">
                <label for="bc-complexity">Complexité technique</label>
                <select id="bc-complexity">
                    <option value="simple" ${data?.technical_complexity === 'simple' ? 'selected' : ''}>Simple</option>
                    <option value="moyenne" ${data?.technical_complexity === 'moyenne' ? 'selected' : ''}>Moyenne</option>
                    <option value="complexe" ${data?.technical_complexity === 'complexe' ? 'selected' : ''}>Complexe</option>
                </select>
            </div>
            <div class="form-group">
                <label>
                    <input type="checkbox" id="bc-active" ${data?.is_active !== false ? 'checked' : ''}>
                    Actif
                </label>
            </div>
        </form>
    `;

    showModal(title, html, async () => {
        const formData = {
            code: document.getElementById('bc-code').value,
            name: document.getElementById('bc-name').value,
            description: document.getElementById('bc-description').value || null,
            risk_coefficient: parseFloat(document.getElementById('bc-risk').value) || null,
            technical_complexity: document.getElementById('bc-complexity').value || null,
            is_active: document.getElementById('bc-active').checked
        };

        try {
            await api.createBuildingCategory(formData);
            showToast('success', 'Succès', 'Catégorie de bâtiment créée');
            closeModal();
            loadReferentials();
        } catch (error) {
            showToast('error', 'Erreur', error.message || 'Impossible de créer la catégorie');
        }
    });
}

function showWorkCategoryModal(data = null) {
    const title = data ? 'Modifier la catégorie de travaux' : 'Nouvelle catégorie de travaux';
    const html = `
        <form id="work-category-form">
            <div class="form-group">
                <label for="wc-code">Code *</label>
                <input type="text" id="wc-code" value="${data?.code || ''}" ${data ? 'readonly' : ''} required>
            </div>
            <div class="form-group">
                <label for="wc-name">Nom *</label>
                <input type="text" id="wc-name" value="${data?.name || ''}" required>
            </div>
            <div class="form-group">
                <label for="wc-description">Description</label>
                <textarea id="wc-description" rows="3">${data?.description || ''}</textarea>
            </div>
            <div class="form-group">
                <label for="wc-risk">Niveau de risque</label>
                <select id="wc-risk">
                    <option value="faible" ${data?.risk_level === 'faible' ? 'selected' : ''}>Faible</option>
                    <option value="moyen" ${data?.risk_level === 'moyen' ? 'selected' : ''}>Moyen</option>
                    <option value="eleve" ${data?.risk_level === 'eleve' ? 'selected' : ''}>Élevé</option>
                </select>
            </div>
            <div class="form-group">
                <label>
                    <input type="checkbox" id="wc-control" ${data?.requires_control ? 'checked' : ''}>
                    Requiert un contrôle
                </label>
            </div>
            <div class="form-group">
                <label>
                    <input type="checkbox" id="wc-active" ${data?.is_active !== false ? 'checked' : ''}>
                    Actif
                </label>
            </div>
        </form>
    `;

    showModal(title, html, async () => {
        const formData = {
            code: document.getElementById('wc-code').value,
            name: document.getElementById('wc-name').value,
            description: document.getElementById('wc-description').value || null,
            risk_level: document.getElementById('wc-risk').value || null,
            requires_control: document.getElementById('wc-control').checked,
            is_active: document.getElementById('wc-active').checked
        };

        try {
            await api.createWorkCategory(formData);
            showToast('success', 'Succès', 'Catégorie de travaux créée');
            closeModal();
            loadReferentials();
        } catch (error) {
            showToast('error', 'Erreur', error.message || 'Impossible de créer la catégorie');
        }
    });
}

function showClauseModal(data = null) {
    const title = data ? 'Modifier la clause' : 'Nouvelle clause';
    const html = `
        <form id="clause-form">
            <div class="form-group">
                <label for="cl-code">Code *</label>
                <input type="text" id="cl-code" value="${data?.code || ''}" ${data ? 'readonly' : ''} required>
            </div>
            <div class="form-group">
                <label for="cl-title">Titre *</label>
                <input type="text" id="cl-title" value="${data?.title || ''}" required>
            </div>
            <div class="form-group">
                <label for="cl-content">Contenu</label>
                <textarea id="cl-content" rows="5">${data?.content || ''}</textarea>
            </div>
            <div class="form-group">
                <label for="cl-category">Catégorie *</label>
                <select id="cl-category" required>
                    <option value="exclusion" ${data?.category === 'exclusion' ? 'selected' : ''}>Exclusion</option>
                    <option value="condition" ${data?.category === 'condition' ? 'selected' : ''}>Condition</option>
                    <option value="option" ${data?.category === 'option' ? 'selected' : ''}>Option</option>
                    <option value="franchise" ${data?.category === 'franchise' ? 'selected' : ''}>Franchise</option>
                    <option value="autre" ${data?.category === 'autre' ? 'selected' : ''}>Autre</option>
                </select>
            </div>
            <div class="form-group">
                <label>
                    <input type="checkbox" id="cl-mandatory" ${data?.is_mandatory ? 'checked' : ''}>
                    Obligatoire
                </label>
            </div>
            <div class="form-group">
                <label>
                    <input type="checkbox" id="cl-negotiable" ${data?.is_negotiable ? 'checked' : ''}>
                    Négociable
                </label>
            </div>
            <div class="form-group">
                <label>
                    <input type="checkbox" id="cl-active" ${data?.is_active !== false ? 'checked' : ''}>
                    Actif
                </label>
            </div>
        </form>
    `;

    showModal(title, html, async () => {
        const formData = {
            code: document.getElementById('cl-code').value,
            title: document.getElementById('cl-title').value,
            content: document.getElementById('cl-content').value || null,
            category: document.getElementById('cl-category').value,
            is_mandatory: document.getElementById('cl-mandatory').checked,
            is_negotiable: document.getElementById('cl-negotiable').checked,
            is_active: document.getElementById('cl-active').checked
        };

        try {
            await api.createClause(formData);
            showToast('success', 'Succès', 'Clause créée');
            closeModal();
            loadReferentials();
        } catch (error) {
            showToast('error', 'Erreur', error.message || 'Impossible de créer la clause');
        }
    });
}

function showProfessionModal(data = null) {
    const title = data ? 'Modifier la profession' : 'Nouvelle profession';
    const html = `
        <form id="profession-form">
            <div class="form-group">
                <label for="pr-code">Code *</label>
                <input type="text" id="pr-code" value="${data?.code || ''}" ${data ? 'readonly' : ''} required>
            </div>
            <div class="form-group">
                <label for="pr-name">Nom *</label>
                <input type="text" id="pr-name" value="${data?.name || ''}" required>
            </div>
            <div class="form-group">
                <label for="pr-description">Description</label>
                <textarea id="pr-description" rows="3">${data?.description || ''}</textarea>
            </div>
            <div class="form-group">
                <label for="pr-category">Catégorie *</label>
                <select id="pr-category" required>
                    <option value="concepteur" ${data?.category === 'concepteur' ? 'selected' : ''}>Concepteur</option>
                    <option value="constructeur" ${data?.category === 'constructeur' ? 'selected' : ''}>Constructeur</option>
                    <option value="controleur" ${data?.category === 'controleur' ? 'selected' : ''}>Contrôleur</option>
                    <option value="autre" ${data?.category === 'autre' ? 'selected' : ''}>Autre</option>
                </select>
            </div>
            <div class="form-group">
                <label>
                    <input type="checkbox" id="pr-rc-dec" ${data?.rc_decennale_required ? 'checked' : ''}>
                    RC Décennale requise
                </label>
            </div>
            <div class="form-group">
                <label>
                    <input type="checkbox" id="pr-rc-pro" ${data?.rc_pro_required ? 'checked' : ''}>
                    RC Professionnelle requise
                </label>
            </div>
            <div class="form-group">
                <label for="pr-coefficient">Coefficient de taux de base</label>
                <input type="number" id="pr-coefficient" value="${data?.base_rate_coefficient || 1.0}" step="0.1" min="0">
            </div>
            <div class="form-group">
                <label>
                    <input type="checkbox" id="pr-active" ${data?.is_active !== false ? 'checked' : ''}>
                    Actif
                </label>
            </div>
        </form>
    `;

    showModal(title, html, async () => {
        const formData = {
            code: document.getElementById('pr-code').value,
            name: document.getElementById('pr-name').value,
            description: document.getElementById('pr-description').value || null,
            category: document.getElementById('pr-category').value,
            rc_decennale_required: document.getElementById('pr-rc-dec').checked,
            rc_pro_required: document.getElementById('pr-rc-pro').checked,
            base_rate_coefficient: parseFloat(document.getElementById('pr-coefficient').value) || 1.0,
            is_active: document.getElementById('pr-active').checked
        };

        try {
            await api.createProfession(formData);
            showToast('success', 'Succès', 'Profession créée');
            closeModal();
            loadReferentials();
        } catch (error) {
            showToast('error', 'Erreur', error.message || 'Impossible de créer la profession');
        }
    });
}
