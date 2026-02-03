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
        claims: { title: 'Sinistres', subtitle: 'Gestion des sinistres construction' },
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
        case 'claim-search':
            loadClaimSearchView();
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
        setupClientFilters();
    } catch (error) {
        console.error('Error loading clients:', error);
        showToast('error', 'Erreur', 'Impossible de charger les clients');
    }
}

function setupClientFilters() {
    const typeFilter = document.getElementById('client-type-filter');
    const searchInput = document.getElementById('client-search');
    
    if (typeFilter && !typeFilter.hasAttribute('data-listener')) {
        typeFilter.setAttribute('data-listener', 'true');
        typeFilter.addEventListener('change', filterClients);
    }
    
    if (searchInput && !searchInput.hasAttribute('data-listener')) {
        searchInput.setAttribute('data-listener', 'true');
        let searchTimeout;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => filterClients(), 300);
        });
    }
}

function filterClients() {
    const typeFilter = document.getElementById('client-type-filter');
    const searchInput = document.getElementById('client-search');
    
    const selectedType = typeFilter ? typeFilter.value : '';
    const searchTerm = searchInput ? searchInput.value.toLowerCase() : '';
    
    let filteredClients = app.data.clients;
    
    // Filter by type
    if (selectedType) {
        filteredClients = filteredClients.filter(client => 
            client.client_type === selectedType
        );
    }
    
    // Filter by search term (name, email, phone, client_number)
    if (searchTerm) {
        filteredClients = filteredClients.filter(client => {
            const name = getClientName(client).toLowerCase();
            const email = (client.email || '').toLowerCase();
            const phone = (client.phone || '').toLowerCase();
            const clientNumber = (client.client_number || '').toLowerCase();
            const city = (client.city || '').toLowerCase();
            
            return name.includes(searchTerm) ||
                   email.includes(searchTerm) ||
                   phone.includes(searchTerm) ||
                   clientNumber.includes(searchTerm) ||
                   city.includes(searchTerm);
        });
    }
    
    displayClients(filteredClients);
}

function clearClientFilters() {
    const typeFilter = document.getElementById('client-type-filter');
    const searchInput = document.getElementById('client-search');
    
    if (typeFilter) typeFilter.value = '';
    if (searchInput) searchInput.value = '';
    
    displayClients(app.data.clients);
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
        setupAddressFilters();
    } catch (error) {
        console.error('Error loading addresses:', error);
        showToast('error', 'Erreur', 'Impossible de charger les adresses');
    }
}

function setupAddressFilters() {
    const typeFilter = document.getElementById('address-type-filter');
    const searchInput = document.getElementById('address-search');
    
    if (typeFilter && !typeFilter.hasAttribute('data-listener')) {
        typeFilter.setAttribute('data-listener', 'true');
        typeFilter.addEventListener('change', filterAddresses);
    }
    
    if (searchInput && !searchInput.hasAttribute('data-listener')) {
        searchInput.setAttribute('data-listener', 'true');
        let searchTimeout;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => filterAddresses(), 300);
        });
    }
}

function filterAddresses() {
    const typeFilter = document.getElementById('address-type-filter');
    const searchInput = document.getElementById('address-search');
    
    const selectedType = typeFilter ? typeFilter.value : '';
    const searchTerm = searchInput ? searchInput.value.toLowerCase() : '';
    
    let filteredAddresses = app.data.addresses;
    
    // Filter by type
    if (selectedType) {
        filteredAddresses = filteredAddresses.filter(addr => 
            addr.address_type === selectedType
        );
    }
    
    // Filter by search term (reference, address, postal_code, city)
    if (searchTerm) {
        filteredAddresses = filteredAddresses.filter(addr => {
            const reference = (addr.reference || '').toLowerCase();
            const address = (addr.address_line1 || '').toLowerCase();
            const postalCode = (addr.postal_code || '').toLowerCase();
            const city = (addr.city || '').toLowerCase();
            
            return reference.includes(searchTerm) ||
                   address.includes(searchTerm) ||
                   postalCode.includes(searchTerm) ||
                   city.includes(searchTerm);
        });
    }
    
    displayAddresses(filteredAddresses);
}

function clearAddressFilters() {
    const typeFilter = document.getElementById('address-type-filter');
    const searchInput = document.getElementById('address-search');
    
    if (typeFilter) typeFilter.value = '';
    if (searchInput) searchInput.value = '';
    
    displayAddresses(app.data.addresses);
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
                                    <button class="btn-view" onclick="viewAddress(${addr.id})" title="Voir">
                                        <i class="fas fa-eye"></i>
                                    </button>
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

// Map functionality
let addressesMap = null;

function showAddressesMap() {
    if (!app.data.addresses || app.data.addresses.length === 0) {
        showToast('warning', 'Attention', 'Aucune adresse à afficher sur la carte');
        return;
    }
    
    // Filter addresses with GPS coordinates
    const addressesWithGPS = app.data.addresses.filter(addr => addr.latitude && addr.longitude);
    
    if (addressesWithGPS.length === 0) {
        showToast('warning', 'Attention', 'Aucune adresse avec coordonnées GPS trouvée');
        return;
    }
    
    // Show modal
    document.getElementById('map-modal').classList.add('active');
    
    // Initialize map after modal is visible
    setTimeout(() => {
        initAddressesMap(addressesWithGPS);
    }, 100);
}

function initAddressesMap(addresses) {
    // Clear existing map if any
    if (addressesMap) {
        addressesMap.remove();
    }
    
    // Create map centered on France
    addressesMap = L.map('addresses-map').setView([46.603354, 1.888334], 6);
    
    // Add tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19
    }).addTo(addressesMap);
    
    // Add markers for each address
    const markers = [];
    addresses.forEach(addr => {
        const marker = L.marker([addr.latitude, addr.longitude]).addTo(addressesMap);
        
        // Create popup content
        const popupContent = `
            <div style="min-width: 200px;">
                <h4 style="margin: 0 0 8px 0; color: #2563eb;">${addr.reference}</h4>
                <p style="margin: 4px 0;"><strong>Type:</strong> ${addr.address_type}</p>
                <p style="margin: 4px 0;"><strong>Adresse:</strong><br/>${addr.address_line1}</p>
                ${addr.address_line2 ? `<p style="margin: 4px 0;">${addr.address_line2}</p>` : ''}
                <p style="margin: 4px 0;">${addr.postal_code} ${addr.city}</p>
                ${addr.country ? `<p style="margin: 4px 0;"><strong>Pays:</strong> ${addr.country}</p>` : ''}
            </div>
        `;
        
        marker.bindPopup(popupContent);
        markers.push(marker);
    });
    
    // Fit map bounds to show all markers
    if (markers.length > 0) {
        const group = L.featureGroup(markers);
        addressesMap.fitBounds(group.getBounds().pad(0.1));
    }
}

function closeMapModal() {
    document.getElementById('map-modal').classList.remove('active');
    
    // Clean up maps
    if (addressesMap) {
        addressesMap.remove();
        addressesMap = null;
    }
    if (siteMap) {
        siteMap.remove();
        siteMap = null;
    }
}

// Site Map
let siteMap = null;

function showSiteMap(latitude, longitude, siteName) {
    // Show modal
    document.getElementById('map-modal').classList.add('active');
    
    // Initialize map after modal is visible
    setTimeout(() => {
        initSiteMap(latitude, longitude, siteName);
    }, 100);
}

function initSiteMap(latitude, longitude, siteName) {
    // Clear existing map if any
    if (siteMap) {
        siteMap.remove();
    }
    
    // Create map centered on the site
    siteMap = L.map('addresses-map').setView([latitude, longitude], 10);
    
    // Add tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19
    }).addTo(siteMap);
    
    // Add marker for the site
    const marker = L.marker([latitude, longitude]).addTo(siteMap);
    
    // Create popup content
    const popupContent = `
        <div style="min-width: 200px;">
            <h4 style="margin: 0 0 8px 0; color: #2563eb;"><i class="fas fa-hard-hat"></i> ${siteName}</h4>
            <p style="margin: 4px 0;"><strong>Coordonnées GPS:</strong></p>
            <p style="margin: 4px 0;">Lat: ${latitude.toFixed(6)}</p>
            <p style="margin: 4px 0;">Lng: ${longitude.toFixed(6)}</p>
        </div>
    `;
    
    marker.bindPopup(popupContent).openPopup();
}

// Show all sites on map
async function showAllSitesMap() {
    try {
        const sites = await api.getSites();
        const sitesWithGPS = sites.filter(site => site.latitude && site.longitude);
        
        if (sitesWithGPS.length === 0) {
            showToast('info', 'Info', 'Aucun chantier avec coordonnées GPS');
            return;
        }
        
        // Show modal
        document.getElementById('map-modal').classList.add('active');
        
        // Initialize map after modal is visible
        setTimeout(() => {
            initAllSitesMap(sitesWithGPS);
        }, 100);
    } catch (error) {
        console.error('Error loading sites:', error);
        showToast('error', 'Erreur', 'Impossible de charger les chantiers');
    }
}

function initAllSitesMap(sites) {
    // Clear existing map if any
    if (siteMap) {
        siteMap.remove();
    }
    
    // Create map centered on France
    siteMap = L.map('addresses-map').setView([46.603354, 1.888334], 6);
    
    // Add tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19
    }).addTo(siteMap);
    
    // Add markers for each site
    const markers = [];
    sites.forEach(site => {
        const marker = L.marker([site.latitude, site.longitude]).addTo(siteMap);
        
        // Create popup content
        const popupContent = `
            <div style="min-width: 250px;">
                <h4 style="margin: 0 0 8px 0; color: #2563eb;"><i class="fas fa-hard-hat"></i> ${site.site_name}</h4>
                <p style="margin: 4px 0;"><strong>Référence:</strong> ${site.site_reference}</p>
                <p style="margin: 4px 0;"><strong>Adresse:</strong><br/>${site.address_line1}</p>
                <p style="margin: 4px 0;">${site.postal_code} ${site.city}</p>
                ${site.building_category_code ? `<p style="margin: 4px 0;"><strong>Catégorie:</strong> ${site.building_category_code}</p>` : ''}
                ${site.construction_cost ? `<p style="margin: 4px 0;"><strong>Coût:</strong> ${formatCurrency(site.construction_cost)}</p>` : ''}
            </div>
        `;
        
        marker.bindPopup(popupContent);
        markers.push(marker);
    });
    
    // Fit map bounds to show all markers
    if (markers.length > 0) {
        const group = L.featureGroup(markers);
        siteMap.fitBounds(group.getBounds().pad(0.1));
    }
}

// Sites
async function loadSites() {
    try {
        const sites = await api.getSites();
        app.data.sites = sites;
        displaySites(sites);
        setupSiteFilters();
    } catch (error) {
        console.error('Error loading sites:', error);
        showToast('error', 'Erreur', 'Impossible de charger les chantiers');
    }
}

function setupSiteFilters() {
    const buildingFilter = document.getElementById('site-building-filter');
    const workFilter = document.getElementById('site-work-filter');
    const searchInput = document.getElementById('site-search');
    
    if (buildingFilter && !buildingFilter.hasAttribute('data-listener')) {
        buildingFilter.setAttribute('data-listener', 'true');
        buildingFilter.addEventListener('change', filterSites);
    }
    
    if (workFilter && !workFilter.hasAttribute('data-listener')) {
        workFilter.setAttribute('data-listener', 'true');
        workFilter.addEventListener('change', filterSites);
    }
    
    if (searchInput && !searchInput.hasAttribute('data-listener')) {
        searchInput.setAttribute('data-listener', 'true');
        let searchTimeout;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => filterSites(), 300);
        });
    }
}

function filterSites() {
    const buildingFilter = document.getElementById('site-building-filter');
    const workFilter = document.getElementById('site-work-filter');
    const searchInput = document.getElementById('site-search');
    
    const selectedBuilding = buildingFilter ? buildingFilter.value : '';
    const selectedWork = workFilter ? workFilter.value : '';
    const searchTerm = searchInput ? searchInput.value.toLowerCase() : '';
    
    let filteredSites = app.data.sites;
    
    // Filter by building category
    if (selectedBuilding) {
        filteredSites = filteredSites.filter(site => 
            site.building_category_code === selectedBuilding
        );
    }
    
    // Filter by work category
    if (selectedWork) {
        filteredSites = filteredSites.filter(site => 
            site.work_category_code === selectedWork
        );
    }
    
    // Filter by search term (reference, name, address, city)
    if (searchTerm) {
        filteredSites = filteredSites.filter(site => {
            const reference = (site.site_reference || '').toLowerCase();
            const name = (site.site_name || '').toLowerCase();
            const address = (site.address_line1 || '').toLowerCase();
            const city = (site.city || '').toLowerCase();
            const postalCode = (site.postal_code || '').toLowerCase();
            
            return reference.includes(searchTerm) ||
                   name.includes(searchTerm) ||
                   address.includes(searchTerm) ||
                   city.includes(searchTerm) ||
                   postalCode.includes(searchTerm);
        });
    }
    
    displaySites(filteredSites);
}

function clearSiteFilters() {
    const buildingFilter = document.getElementById('site-building-filter');
    const workFilter = document.getElementById('site-work-filter');
    const searchInput = document.getElementById('site-search');
    
    if (buildingFilter) buildingFilter.value = '';
    if (workFilter) workFilter.value = '';
    if (searchInput) searchInput.value = '';
    
    displaySites(app.data.sites);
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
                                    <button class="btn-view" onclick="viewSite(${site.id})" title="Voir">
                                        <i class="fas fa-eye"></i>
                                    </button>
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
let contractsPagination = {
    currentPage: 1,
    pageSize: 20,
    total: 0,
    pages: 0
};

async function loadContracts(status = null, page = 1) {
    try {
        const params = {
            skip: (page - 1) * contractsPagination.pageSize,
            limit: contractsPagination.pageSize
        };
        if (status) params.status = status;
        
        const response = await api.getContracts(null, params);
        
        // La réponse contient maintenant { items, total, skip, limit, page, pages }
        app.data.contracts = response.items || response; // Rétrocompatibilité
        
        // Mettre à jour la pagination
        if (response.total !== undefined) {
            contractsPagination.total = response.total;
            contractsPagination.pages = response.pages;
            contractsPagination.currentPage = response.page;
        }
        
        displayContracts(app.data.contracts);
        setupContractFilters();
    } catch (error) {
        console.error('Error loading contracts:', error);
        showToast('error', 'Erreur', 'Impossible de charger les contrats');
    }
}

function setupContractFilters() {
    const typeFilter = document.getElementById('contract-type-filter');
    const statusFilter = document.getElementById('contract-status-filter');
    const dateFrom = document.getElementById('contract-date-from');
    const dateTo = document.getElementById('contract-date-to');
    const searchInput = document.getElementById('contract-search');
    
    if (typeFilter && !typeFilter.hasAttribute('data-listener')) {
        typeFilter.setAttribute('data-listener', 'true');
        typeFilter.addEventListener('change', filterContracts);
    }
    
    if (statusFilter && !statusFilter.hasAttribute('data-listener')) {
        statusFilter.setAttribute('data-listener', 'true');
        statusFilter.addEventListener('change', filterContracts);
    }
    
    if (dateFrom && !dateFrom.hasAttribute('data-listener')) {
        dateFrom.setAttribute('data-listener', 'true');
        dateFrom.addEventListener('change', filterContracts);
    }
    
    if (dateTo && !dateTo.hasAttribute('data-listener')) {
        dateTo.setAttribute('data-listener', 'true');
        dateTo.addEventListener('change', filterContracts);
    }
    
    if (searchInput && !searchInput.hasAttribute('data-listener')) {
        searchInput.setAttribute('data-listener', 'true');
        let searchTimeout;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => filterContracts(), 300);
        });
    }
}

async function filterContracts() {
    const typeFilter = document.getElementById('contract-type-filter');
    const statusFilter = document.getElementById('contract-status-filter');
    const dateFrom = document.getElementById('contract-date-from');
    const dateTo = document.getElementById('contract-date-to');
    const searchInput = document.getElementById('contract-search');
    
    const selectedType = typeFilter ? typeFilter.value : '';
    const selectedStatus = statusFilter ? statusFilter.value : '';
    const fromDate = dateFrom ? dateFrom.value : '';
    const toDate = dateTo ? dateTo.value : '';
    const searchTerm = searchInput ? searchInput.value.toLowerCase() : '';
    
    // Si seulement le filtre de statut est utilisé, on peut utiliser la pagination serveur
    if (selectedStatus && !selectedType && !fromDate && !toDate && !searchTerm) {
        contractsPagination.currentPage = 1;
        await loadContracts(selectedStatus, 1);
        return;
    }
    
    // Sinon, filtrage côté client (désactive temporairement la pagination)
    let filteredContracts = app.data.contracts;
    
    // Filter by type
    if (selectedType) {
        filteredContracts = filteredContracts.filter(contract =>
            contract.contract_type_code === selectedType
        );
    }
    
    // Filter by status
    if (selectedStatus) {
        filteredContracts = filteredContracts.filter(contract =>
            contract.status === selectedStatus
        );
    }
    
    // Filter by date range (effective_date)
    if (fromDate) {
        filteredContracts = filteredContracts.filter(contract => {
            const effectiveDate = contract.effective_date ? contract.effective_date.split('T')[0] : null;
            return effectiveDate && effectiveDate >= fromDate;
        });
    }
    
    if (toDate) {
        filteredContracts = filteredContracts.filter(contract => {
            const effectiveDate = contract.effective_date ? contract.effective_date.split('T')[0] : null;
            return effectiveDate && effectiveDate <= toDate;
        });
    }
    
    // Filter by search term (contract_number, external_reference)
    if (searchTerm) {
        filteredContracts = filteredContracts.filter(contract => {
            const contractNumber = (contract.contract_number || '').toLowerCase();
            const externalRef = (contract.external_reference || '').toLowerCase();
            
            return contractNumber.includes(searchTerm) ||
                   externalRef.includes(searchTerm);
        });
    }
    
    // Réinitialiser la pagination pour le filtrage côté client
    contractsPagination.total = filteredContracts.length;
    contractsPagination.pages = 1;
    contractsPagination.currentPage = 1;
    
    displayContracts(filteredContracts);
}

function goToContractsPage(page) {
    const statusFilter = document.getElementById('contract-status-filter').value;
    loadContracts(statusFilter || null, page);
}

function clearContractFilters() {
    const typeFilter = document.getElementById('contract-type-filter');
    const statusFilter = document.getElementById('contract-status-filter');
    const dateFrom = document.getElementById('contract-date-from');
    const dateTo = document.getElementById('contract-date-to');
    const searchInput = document.getElementById('contract-search');
    
    if (typeFilter) typeFilter.value = '';
    if (statusFilter) statusFilter.value = '';
    if (dateFrom) dateFrom.value = '';
    if (dateTo) dateTo.value = '';
    if (searchInput) searchInput.value = '';
    
    contractsPagination.currentPage = 1;
    loadContracts(null, 1);
}

// Claims
async function loadClaims() {
    try {
        // Charger tous les sinistres avec une limite élevée
        const response = await api.getClaims({ limit: 100 });
        // L'API retourne {items, total, pages}, extraire les items
        const claims = response.items || response;
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

// Claim Search View
function loadClaimSearchView() {
    document.getElementById('claim-search-results').innerHTML = '';
    document.getElementById('claim-detail-view').style.display = 'none';
    document.getElementById('claim-search-input').value = '';
    document.getElementById('claim-search-input').focus();
}

async function searchClaimsAdvanced() {
    const searchInput = document.getElementById('claim-search-input');
    const query = searchInput.value.trim();
    
    if (!query) {
        showToast('warning', 'Attention', 'Veuillez saisir un terme de recherche');
        return;
    }
    
    try {
        const claims = await api.getClaims();
        const searchTerm = query.toLowerCase();
        
        // Filtrer les sinistres par numéro ou titre
        const filtered = claims.filter(claim => {
            const claimNumber = (claim.claim_number || '').toLowerCase();
            const title = (claim.title || '').toLowerCase();
            return claimNumber.includes(searchTerm) || title.includes(searchTerm);
        });
        
        displayClaimSearchResults(filtered);
        
    } catch (error) {
        console.error('Error searching claims:', error);
        showToast('error', 'Erreur', 'Erreur lors de la recherche');
    }
}

function displayClaimSearchResults(claims) {
    const container = document.getElementById('claim-search-results');
    
    if (!claims || claims.length === 0) {
        container.innerHTML = '<p class="help-text">Aucun sinistre trouvé</p>';
        return;
    }
    
    const html = `
        <h3 style="margin-bottom: 16px;">${claims.length} sinistre${claims.length > 1 ? 's' : ''} trouvé${claims.length > 1 ? 's' : ''}</h3>
        <div class="data-table">
            <table>
                <thead>
                    <tr>
                        <th>Numéro</th>
                        <th>Titre</th>
                        <th>Type</th>
                        <th>Statut</th>
                        <th>Date déclaration</th>
                        <th>Montant réclamé</th>
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
                            <td>${formatDate(claim.declaration_date)}</td>
                            <td>${formatCurrency(claim.claimed_amount)}</td>
                            <td>
                                <button class="btn btn-primary btn-sm" onclick="viewClaimDetail('${claim.claim_number}')">
                                    <i class="fas fa-eye"></i> Voir
                                </button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
    
    container.innerHTML = html;
}

async function viewClaimDetail(claimNumber) {
    try {
        const claim = await api.getClaim(claimNumber);
        const contracts = await api.getContracts(null, {});
        const contract = contracts.items ? contracts.items.find(c => c.id === claim.contract_id) : contracts.find(c => c.id === claim.contract_id);
        
        if (!contract) {
            showToast('error', 'Erreur', 'Contrat non trouvé');
            return;
        }
        
        const client = await api.getClient(contract.client_id);
        
        document.getElementById('claim-search-results').style.display = 'none';
        document.getElementById('claim-detail-view').style.display = 'block';
        
        displayClaimDetailLeft(claim);
        displayClientSummary(client);
        displayContractSummary(contract);
        displayGuaranteesList(contract);
        
    } catch (error) {
        console.error('Error loading claim detail:', error);
        showToast('error', 'Erreur', 'Impossible de charger le détail du sinistre');
    }
}

function displayClaimDetailLeft(claim) {
    const container = document.getElementById('claim-detail-left');
    
    const html = `
        <h3 style="margin-bottom: 16px; display: flex; align-items: center; gap: 12px;">
            <i class="fas fa-exclamation-triangle"></i>
            Détail du sinistre ${claim.claim_number}
        </h3>
        
        <div class="detail-grid">
            <div class="detail-item">
                <label>Titre</label>
                <span><strong>${claim.title}</strong></span>
            </div>
            <div class="detail-item">
                <label>Type</label>
                <span><span class="badge badge-info">${claim.claim_type}</span></span>
            </div>
            <div class="detail-item">
                <label>Statut</label>
                <span><span class="badge badge-${getClaimStatusBadge(claim.status)}">${claim.status}</span></span>
            </div>
            <div class="detail-item">
                <label>Gravité</label>
                <span><span class="badge badge-${getSeverityBadge(claim.severity)}">${claim.severity}</span></span>
            </div>
            <div class="detail-item">
                <label>Date de déclaration</label>
                <span>${formatDate(claim.declaration_date)}</span>
            </div>
            <div class="detail-item">
                <label>Date du sinistre</label>
                <span>${formatDate(claim.loss_date)}</span>
            </div>
            <div class="detail-item">
                <label>Montant réclamé</label>
                <span>${formatCurrency(claim.claimed_amount)}</span>
            </div>
            <div class="detail-item">
                <label>Montant réservé</label>
                <span>${formatCurrency(claim.reserved_amount)}</span>
            </div>
        </div>
        
        ${claim.description ? `
        <div style="margin-top: 20px;">
            <h4 style="margin-bottom: 8px;">Description</h4>
            <p style="color: var(--text-secondary);">${claim.description}</p>
        </div>
        ` : ''}
    `;
    
    container.innerHTML = html;
}

function displayClientSummary(client) {
    const container = document.getElementById('claim-client-summary');
    
    const html = `
        <h4 style="margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
            <i class="fas fa-user"></i>
            Client
        </h4>
        <div class="detail-grid">
            <div class="detail-item">
                <label>Numéro</label>
                <span><strong>${client.client_number}</strong></span>
            </div>
            <div class="detail-item">
                <label>Nom</label>
                <span>${getClientName(client)}</span>
            </div>
            <div class="detail-item">
                <label>Email</label>
                <span>${client.email || '-'}</span>
            </div>
            <div class="detail-item">
                <label>Téléphone</label>
                <span>${client.phone || '-'}</span>
            </div>
        </div>
    `;
    
    container.innerHTML = html;
}

function displayContractSummary(contract) {
    const container = document.getElementById('claim-contract-summary');
    
    let siteHtml = '';
    if (contract.construction_site) {
        siteHtml = `
            <div style="margin-top: 16px; padding-top: 16px; border-top: 1px solid var(--border-color);">
                <h5 style="margin-bottom: 8px;"><i class="fas fa-hard-hat"></i> Chantier</h5>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>Référence</label>
                        <span>${contract.construction_site.site_reference}</span>
                    </div>
                    <div class="detail-item">
                        <label>Nom</label>
                        <span>${contract.construction_site.site_name}</span>
                    </div>
                </div>
            </div>
        `;
    }
    
    const html = `
        <h4 style="margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
            <i class="fas fa-file-contract"></i>
            Contrat
        </h4>
        <div class="detail-grid">
            <div class="detail-item">
                <label>Numéro</label>
                <span><strong>${contract.contract_number}</strong></span>
            </div>
            <div class="detail-item">
                <label>Type</label>
                <span><span class="badge badge-info">${contract.contract_type_code}</span></span>
            </div>
            <div class="detail-item">
                <label>Date d'effet</label>
                <span>${formatDate(contract.effective_date)}</span>
            </div>
            <div class="detail-item">
                <label>Montant assuré</label>
                <span>${formatCurrency(contract.insured_amount)}</span>
            </div>
        </div>
        ${siteHtml}
    `;
    
    container.innerHTML = html;
}

function displayGuaranteesList(contract) {
    const container = document.getElementById('claim-guarantees-list');
    
    const guarantees = contract.guarantees || [];
    
    const html = `
        <h4 style="margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
            <i class="fas fa-shield-alt"></i>
            Garanties (${guarantees.length})
        </h4>
        ${guarantees.length > 0 ? `
            <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                ${guarantees.map(g => `
                    <span class="badge badge-secondary" style="padding: 8px 12px;">
                        ${getGuaranteeName(g.code || g.guarantee_code)}
                    </span>
                `).join('')}
            </div>
        ` : '<p class="help-text">Aucune garantie</p>'}
    `;
    
    container.innerHTML = html;
}

function backToClaimSearch() {
    document.getElementById('claim-search-results').style.display = 'block';
    document.getElementById('claim-detail-view').style.display = 'none';
}

function clearClaimSearch() {
    document.getElementById('claim-search-input').value = '';
    document.getElementById('claim-search-results').innerHTML = '';
    document.getElementById('claim-detail-view').style.display = 'none';
}

async function showClaimModal(claimNumber = null) {
    if (!claimNumber) {
        // TODO: Implement create new claim modal
        showToast('info', 'Info', 'Création de sinistre - En cours de développement');
        return;
    }
    
    try {
        const claim = await api.getClaim(claimNumber);
        displayClaimDetail(claim);
    } catch (error) {
        console.error('Error loading claim:', error);
        showToast('error', 'Erreur', 'Impossible de charger les détails du sinistre');
    }
}

function displayClaimDetail(claim) {
    // Hide table, show detail
    document.getElementById('claims-table-container').style.display = 'none';
    document.querySelector('#claims-view .view-toolbar').style.display = 'none';
    document.getElementById('claim-detail').style.display = 'block';
    
    const statusLabels = {
        'declare': 'Déclaré',
        'pris_en_compte': 'Pris en compte',
        'en_cours_expertise': 'En cours d\'expertise',
        'attente_pieces': 'Attente pièces',
        'accepte': 'Accepté',
        'refuse': 'Refusé',
        'regle': 'Réglé',
        'cloture': 'Clôturé'
    };
    
    const typeLabels = {
        'structurel': 'Structurel',
        'degats_des_eaux': 'Dégâts des eaux',
        'incendie': 'Incendie',
        'intemperies': 'Intempéries',
        'vol': 'Vol',
        'vandalisme': 'Vandalisme',
        'malfacons': 'Malfaçons',
        'rc': 'Responsabilité civile',
        'autre': 'Autre'
    };
    
    const severityLabels = {
        'mineur': 'Mineur',
        'moyen': 'Moyen',
        'grave': 'Grave',
        'tres_grave': 'Très grave'
    };
    
    const html = `
        <div class="detail-card">
            <div class="detail-header">
                <h2>${claim.claim_number}</h2>
                <div class="detail-badges">
                    <span class="badge badge-${getClaimStatusBadge(claim.status)}">${statusLabels[claim.status] || claim.status}</span>
                    <span class="badge badge-${getSeverityBadge(claim.severity)}">${severityLabels[claim.severity] || claim.severity}</span>
                </div>
            </div>
            
            <div class="detail-section">
                <h3><i class="fas fa-info-circle"></i> Informations générales</h3>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>Titre</label>
                        <strong>${claim.title}</strong>
                    </div>
                    <div class="detail-item">
                        <label>Type de sinistre</label>
                        <span class="badge badge-info">${typeLabels[claim.claim_type] || claim.claim_type}</span>
                    </div>
                    <div class="detail-item">
                        <label>Référence externe</label>
                        <span>${claim.external_reference || '-'}</span>
                    </div>
                    <div class="detail-item">
                        <label>Contrat ID</label>
                        <span>${claim.contract_id}</span>
                    </div>
                    ${claim.construction_site_id ? `
                    <div class="detail-item">
                        <label>Chantier ID</label>
                        <span>${claim.construction_site_id}</span>
                    </div>
                    ` : ''}
                </div>
            </div>
            
            <div class="detail-section">
                <h3><i class="fas fa-calendar-alt"></i> Dates importantes</h3>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>Date du sinistre</label>
                        <strong>${formatDate(claim.incident_date)}</strong>
                    </div>
                    <div class="detail-item">
                        <label>Date de déclaration</label>
                        <span>${formatDate(claim.declaration_date)}</span>
                    </div>
                    ${claim.acknowledgment_date ? `
                    <div class="detail-item">
                        <label>Date de prise en compte</label>
                        <span>${formatDate(claim.acknowledgment_date)}</span>
                    </div>
                    ` : ''}
                    ${claim.settlement_date ? `
                    <div class="detail-item">
                        <label>Date de règlement</label>
                        <span>${formatDate(claim.settlement_date)}</span>
                    </div>
                    ` : ''}
                    ${claim.closure_date ? `
                    <div class="detail-item">
                        <label>Date de clôture</label>
                        <span>${formatDate(claim.closure_date)}</span>
                    </div>
                    ` : ''}
                </div>
            </div>
            
            <div class="detail-section">
                <h3><i class="fas fa-file-alt"></i> Description</h3>
                <p>${claim.description}</p>
                <h4>Circonstances</h4>
                <p>${claim.circumstances || '-'}</p>
            </div>
            
            <div class="detail-section">
                <h3><i class="fas fa-map-marker-alt"></i> Localisation</h3>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>Zone affectée</label>
                        <span>${claim.affected_area}</span>
                    </div>
                    ${claim.floor ? `
                    <div class="detail-item">
                        <label>Étage</label>
                        <span>${claim.floor}</span>
                    </div>
                    ` : ''}
                </div>
            </div>
            
            <div class="detail-section">
                <h3><i class="fas fa-euro-sign"></i> Montants financiers</h3>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>Montant estimé</label>
                        <strong>${formatCurrency(claim.estimated_amount)}</strong>
                    </div>
                    <div class="detail-item">
                        <label>Montant expert</label>
                        <span>${formatCurrency(claim.expert_amount)}</span>
                    </div>
                    <div class="detail-item">
                        <label>Franchise appliquée</label>
                        <span>${formatCurrency(claim.franchise_applied)}</span>
                    </div>
                    <div class="detail-item">
                        <label>Montant d'indemnité</label>
                        <strong class="text-success">${formatCurrency(claim.indemnity_amount)}</strong>
                    </div>
                    <div class="detail-item">
                        <label>Montant de réserve</label>
                        <span>${formatCurrency(claim.reserve_amount)}</span>
                    </div>
                </div>
            </div>
            
            ${claim.expert_name || claim.expert_company ? `
            <div class="detail-section">
                <h3><i class="fas fa-user-tie"></i> Expert</h3>
                <div class="detail-grid">
                    ${claim.expert_name ? `
                    <div class="detail-item">
                        <label>Nom de l'expert</label>
                        <span>${claim.expert_name}</span>
                    </div>
                    ` : ''}
                    ${claim.expert_company ? `
                    <div class="detail-item">
                        <label>Société</label>
                        <span>${claim.expert_company}</span>
                    </div>
                    ` : ''}
                </div>
            </div>
            ` : ''}
            
            <div class="detail-section">
                <h3><i class="fas fa-shield-alt"></i> Garanties activées</h3>
                <div class="badges-list">
                    ${claim.activated_guarantees && claim.activated_guarantees.length > 0 
                        ? claim.activated_guarantees.map(g => `<span class="badge badge-info">${g}</span>`).join(' ')
                        : '<span class="text-muted">Aucune garantie activée</span>'
                    }
                </div>
            </div>
            
            ${claim.third_party_involved ? `
            <div class="detail-section">
                <h3><i class="fas fa-users"></i> Tiers impliqué</h3>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>Nom</label>
                        <span>${claim.third_party_info?.name || '-'}</span>
                    </div>
                    <div class="detail-item">
                        <label>Contact</label>
                        <span>${claim.third_party_info?.contact || '-'}</span>
                    </div>
                    <div class="detail-item">
                        <label>Assurance</label>
                        <span>${claim.third_party_info?.insurance || '-'}</span>
                    </div>
                </div>
            </div>
            ` : ''}
            
            <div class="detail-section">
                <h3><i class="fas fa-paperclip"></i> Documents et pièces</h3>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>Photos disponibles</label>
                        <span>${claim.has_photos ? '✅ Oui' : '❌ Non'}</span>
                    </div>
                    <div class="detail-item">
                        <label>Rapport d'expert</label>
                        <span>${claim.has_expert_report ? '✅ Oui' : '❌ Non'}</span>
                    </div>
                    <div class="detail-item">
                        <label>Devis de réparation</label>
                        <span>${claim.has_repair_quote ? '✅ Oui' : '❌ Non'}</span>
                    </div>
                    ${claim.police_report_number ? `
                    <div class="detail-item">
                        <label>N° procès-verbal</label>
                        <span>${claim.police_report_number}</span>
                    </div>
                    ` : ''}
                </div>
            </div>
            
            ${claim.internal_notes ? `
            <div class="detail-section">
                <h3><i class="fas fa-sticky-note"></i> Notes internes</h3>
                <p class="text-muted">${claim.internal_notes}</p>
            </div>
            ` : ''}
            
            <div class="detail-section">
                <h3><i class="fas fa-clock"></i> Métadonnées</h3>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>Déclaré par</label>
                        <span>${claim.declared_by}</span>
                    </div>
                    <div class="detail-item">
                        <label>Date de création</label>
                        <span>${formatDateTime(claim.created_at)}</span>
                    </div>
                    <div class="detail-item">
                        <label>Dernière mise à jour</label>
                        <span>${formatDateTime(claim.updated_at)}</span>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.getElementById('claim-detail-content').innerHTML = html;
    
    // Store current claim for editing
    app.currentClaim = claim;
}

function backToClaimsList() {
    document.getElementById('claims-table-container').style.display = 'block';
    document.querySelector('#claims-view .view-toolbar').style.display = 'flex';
    document.getElementById('claim-detail').style.display = 'none';
    app.currentClaim = null;
}

function editClaim() {
    if (!app.currentClaim) return;
    showToast('info', 'Info', 'Modification de sinistre - En cours de développement');
    // TODO: Implement edit claim modal
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
    
    const paginationHtml = contractsPagination.pages > 1 ? `
        <div class="pagination">
            <button 
                class="btn btn-secondary btn-sm" 
                onclick="goToContractsPage(${contractsPagination.currentPage - 1})"
                ${contractsPagination.currentPage === 1 ? 'disabled' : ''}>
                <i class="fas fa-chevron-left"></i> Précédent
            </button>
            <span class="pagination-info">
                Page ${contractsPagination.currentPage} sur ${contractsPagination.pages} 
                (${contractsPagination.total} contrat${contractsPagination.total > 1 ? 's' : ''})
            </span>
            <button 
                class="btn btn-secondary btn-sm" 
                onclick="goToContractsPage(${contractsPagination.currentPage + 1})"
                ${contractsPagination.currentPage === contractsPagination.pages ? 'disabled' : ''}>
                Suivant <i class="fas fa-chevron-right"></i>
            </button>
        </div>
    ` : `<div class="pagination-info">${contractsPagination.total || contracts.length} contrat${(contractsPagination.total || contracts.length) > 1 ? 's' : ''}</div>`;
    
    const html = `
        ${paginationHtml}
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
                        <th>Chantier<br>Garanties</th>
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
                                <div style="display: flex; gap: 0.5rem; align-items: center;">
                                    <span class="badge badge-secondary" title="Chantiers">
                                        <i class="fas fa-hard-hat"></i> ${contract.construction_site ? 1 : 0}
                                    </span>
                                    <span class="badge badge-secondary" title="Garanties">
                                        <i class="fas fa-shield-alt"></i> ${contract.guarantees ? contract.guarantees.length : 0}
                                    </span>
                                </div>
                            </td>
                            <td>
                                <div class="table-actions">
                                    <button class="btn-view" onclick="viewContract('${contract.contract_number}')" title="Voir">
                                        <i class="fas fa-eye"></i>
                                    </button>
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
        ${paginationHtml}
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
    try {
        const client = await api.getClient(clientId);
        displayClientDetail(client);
    } catch (error) {
        console.error('Error loading client:', error);
        showToast('error', 'Erreur', 'Impossible de charger les détails du client');
    }
}

function displayClientDetail(client) {
    // Hide table, show detail
    document.getElementById('clients-table-container').style.display = 'none';
    document.querySelector('#clients-view .view-toolbar').style.display = 'none';
    document.getElementById('client-detail').style.display = 'block';
    
    const html = `
        <div class="detail-card">
            <div class="detail-header">
                <h2>${client.client_type === 'particulier' ? 
                    `${client.civilite || ''} ${client.first_name} ${client.last_name}`.trim() : 
                    client.company_name}</h2>
                <div class="detail-badges">
                    <span class="badge badge-${client.client_type === 'particulier' ? 'info' : 'success'}">${client.client_type}</span>
                    ${client.is_active ? '<span class="badge badge-success">Actif</span>' : '<span class="badge badge-danger">Inactif</span>'}
                </div>
            </div>
            
            <div class="detail-section">
                <h3><i class="fas fa-id-card"></i> Informations générales</h3>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>Numéro client</label>
                        <strong>${client.client_number}</strong>
                    </div>
                    <div class="detail-item">
                        <label>Type de client</label>
                        <span class="badge badge-info">${client.client_type}</span>
                    </div>
                    ${client.client_type === 'particulier' ? `
                        <div class="detail-item">
                            <label>Civilité</label>
                            <span>${client.civilite || '-'}</span>
                        </div>
                        <div class="detail-item">
                            <label>Prénom</label>
                            <span>${client.first_name || '-'}</span>
                        </div>
                        <div class="detail-item">
                            <label>Nom</label>
                            <strong>${client.last_name || '-'}</strong>
                        </div>
                        <div class="detail-item">
                            <label>Date de naissance</label>
                            <span>${client.birth_date ? formatDate(client.birth_date) : '-'}</span>
                        </div>
                        <div class="detail-item">
                            <label>Lieu de naissance</label>
                            <span>${client.birth_place || '-'}</span>
                        </div>
                    ` : `
                        <div class="detail-item">
                            <label>Raison sociale</label>
                            <strong>${client.company_name || '-'}</strong>
                        </div>
                        <div class="detail-item">
                            <label>Forme juridique</label>
                            <span>${client.legal_form || '-'}</span>
                        </div>
                        <div class="detail-item">
                            <label>SIRET</label>
                            <span>${client.siret || '-'}</span>
                        </div>
                        <div class="detail-item">
                            <label>Secteur d'activité</label>
                            <span>${client.business_sector || '-'}</span>
                        </div>
                        <div class="detail-item">
                            <label>Nombre d'employés</label>
                            <span>${client.employee_count || '-'}</span>
                        </div>
                        <div class="detail-item">
                            <label>Chiffre d'affaires</label>
                            <span>${client.annual_revenue ? formatCurrency(client.annual_revenue) : '-'}</span>
                        </div>
                    `}
                </div>
            </div>
            
            <div class="detail-section">
                <h3><i class="fas fa-phone"></i> Contact</h3>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>Email</label>
                        <span>${client.email ? `<a href="mailto:${client.email}">${client.email}</a>` : '-'}</span>
                    </div>
                    <div class="detail-item">
                        <label>Téléphone</label>
                        <span>${client.phone ? `<a href="tel:${client.phone}">${client.phone}</a>` : '-'}</span>
                    </div>
                    ${client.mobile_phone ? `
                    <div class="detail-item">
                        <label>Mobile</label>
                        <span><a href="tel:${client.mobile_phone}">${client.mobile_phone}</a></span>
                    </div>
                    ` : ''}
                </div>
            </div>
            
            ${client.notes ? `
            <div class="detail-section">
                <h3><i class="fas fa-sticky-note"></i> Notes</h3>
                <p>${client.notes}</p>
            </div>
            ` : ''}
            
            <div class="detail-section">
                <h3><i class="fas fa-clock"></i> Métadonnées</h3>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>Date de création</label>
                        <span>${formatDateTime(client.created_at)}</span>
                    </div>
                    <div class="detail-item">
                        <label>Dernière mise à jour</label>
                        <span>${formatDateTime(client.updated_at)}</span>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.getElementById('client-detail-content').innerHTML = html;
    app.currentClient = client;
}

function backToClientsList() {
    document.getElementById('clients-table-container').style.display = 'block';
    document.querySelector('#clients-view .view-toolbar').style.display = 'flex';
    document.getElementById('client-detail').style.display = 'none';
    app.currentClient = null;
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

// Address Details
async function viewAddress(id) {
    try {
        const address = await api.getAddress(id);
        displayAddressDetail(address);
    } catch (error) {
        console.error('Error loading address:', error);
        showToast('error', 'Erreur', 'Impossible de charger les détails de l\'adresse');
    }
}

function displayAddressDetail(address) {
    document.getElementById('addresses-table-container').style.display = 'none';
    document.querySelector('#addresses-view .view-toolbar').style.display = 'none';
    document.getElementById('address-detail').style.display = 'block';
    
    const html = `
        <div class="detail-card">
            <div class="detail-header">
                <h2>${address.reference}</h2>
                <div class="detail-badges">
                    <span class="badge badge-info">${address.address_type}</span>
                    ${address.is_main ? '<span class="badge badge-success">Principale</span>' : ''}
                </div>
            </div>
            
            <div class="detail-section">
                <h3><i class="fas fa-map-marker-alt"></i> Adresse</h3>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>Référence</label>
                        <strong>${address.reference}</strong>
                    </div>
                    <div class="detail-item">
                        <label>Type</label>
                        <span class="badge badge-info">${address.address_type}</span>
                    </div>
                    <div class="detail-item">
                        <label>Adresse ligne 1</label>
                        <span>${address.address_line1}</span>
                    </div>
                    ${address.address_line2 ? `
                    <div class="detail-item">
                        <label>Adresse ligne 2</label>
                        <span>${address.address_line2}</span>
                    </div>
                    ` : ''}
                    <div class="detail-item">
                        <label>Code postal</label>
                        <span>${address.postal_code}</span>
                    </div>
                    <div class="detail-item">
                        <label>Ville</label>
                        <span>${address.city}</span>
                    </div>
                    ${address.department ? `
                    <div class="detail-item">
                        <label>Département</label>
                        <span>${address.department}</span>
                    </div>
                    ` : ''}
                    ${address.country ? `
                    <div class="detail-item">
                        <label>Pays</label>
                        <span>${address.country}</span>
                    </div>
                    ` : ''}
                    ${address.latitude && address.longitude ? `
                    <div class="detail-item">
                        <label>Coordonnées GPS</label>
                        <span>📍 ${address.latitude.toFixed(6)}, ${address.longitude.toFixed(6)}</span>
                    </div>
                    ` : ''}
                </div>
            </div>
            
            <div class="detail-section">
                <h3><i class="fas fa-clock"></i> Métadonnées</h3>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>Date de création</label>
                        <span>${formatDateTime(address.created_at)}</span>
                    </div>
                    <div class="detail-item">
                        <label>Dernière mise à jour</label>
                        <span>${formatDateTime(address.updated_at)}</span>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.getElementById('address-detail-content').innerHTML = html;
}

function backToAddressesList() {
    document.getElementById('addresses-table-container').style.display = 'block';
    document.querySelector('#addresses-view .view-toolbar').style.display = 'flex';
    document.getElementById('address-detail').style.display = 'none';
}

function editAddress(id) { showToast('info', 'Info', 'Fonctionnalité en cours de développement'); }
function deleteAddress(id) { showToast('info', 'Info', 'Fonctionnalité en cours de développement'); }

// Site Details
async function viewSite(id) {
    try {
        const site = await api.getSite(id);
        displaySiteDetail(site);
    } catch (error) {
        console.error('Error loading site:', error);
        showToast('error', 'Erreur', 'Impossible de charger les détails du chantier');
    }
}

function displaySiteDetail(site) {
    document.getElementById('sites-table-container').style.display = 'none';
    document.querySelector('#sites-view .view-toolbar').style.display = 'none';
    document.getElementById('site-detail').style.display = 'block';
    
    const html = `
        <div class="detail-card">
            <div class="detail-header">
                <h2>${site.site_reference}</h2>
                <div class="detail-badges">
                    <span class="badge badge-info">${site.building_category_code || 'N/A'}</span>
                    ${site.construction_status ? `<span class="badge badge-success">${site.construction_status}</span>` : ''}
                </div>
            </div>
            
            <div class="detail-section">
                <h3><i class="fas fa-hard-hat"></i> Informations générales</h3>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>Référence</label>
                        <strong>${site.site_reference}</strong>
                    </div>
                    <div class="detail-item">
                        <label>Nom du chantier</label>
                        <strong>${site.site_name}</strong>
                    </div>
                    ${site.building_category_code ? `
                    <div class="detail-item">
                        <label>Catégorie de bâtiment</label>
                        <span class="badge badge-info">${site.building_category_code}</span>
                    </div>
                    ` : ''}
                    ${site.work_category_code ? `
                    <div class="detail-item">
                        <label>Catégorie de travaux</label>
                        <span>${site.work_category_code}</span>
                    </div>
                    ` : ''}
                    ${site.construction_status ? `
                    <div class="detail-item">
                        <label>Statut de construction</label>
                        <span>${site.construction_status}</span>
                    </div>
                    ` : ''}
                </div>
            </div>
            
            <div class="detail-section">
                <h3><i class="fas fa-map-marker-alt"></i> Localisation</h3>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>Adresse</label>
                        <span>${site.address_line1}</span>
                    </div>
                    ${site.address_line2 ? `
                    <div class="detail-item">
                        <label>Complément</label>
                        <span>${site.address_line2}</span>
                    </div>
                    ` : ''}
                    <div class="detail-item">
                        <label>Code postal</label>
                        <span>${site.postal_code}</span>
                    </div>
                    <div class="detail-item">
                        <label>Ville</label>
                        <span>${site.city}</span>
                    </div>
                    ${site.latitude && site.longitude ? `
                    <div class="detail-item" style="grid-column: 1 / -1;">
                        <button class="btn btn-secondary" onclick="showSiteMap(${site.latitude}, ${site.longitude}, '${site.site_name.replace(/'/g, "\\'")}')">
                            <i class="fas fa-map"></i> Voir sur la carte
                        </button>
                    </div>
                    ` : ''}
                </div>
            </div>
            
            ${site.description ? `
            <div class="detail-section">
                <h3><i class="fas fa-file-alt"></i> Description</h3>
                <p>${site.description}</p>
            </div>
            ` : ''}
            
            <div class="detail-section">
                <h3><i class="fas fa-calendar-alt"></i> Dates</h3>
                <div class="detail-grid">
                    ${site.opening_date ? `
                    <div class="detail-item">
                        <label>Date d'ouverture</label>
                        <span>${formatDate(site.opening_date)}</span>
                    </div>
                    ` : ''}
                    ${site.planned_completion_date ? `
                    <div class="detail-item">
                        <label>Date de fin prévue</label>
                        <span>${formatDate(site.planned_completion_date)}</span>
                    </div>
                    ` : ''}
                    ${site.actual_completion_date ? `
                    <div class="detail-item">
                        <label>Date de fin réelle</label>
                        <span>${formatDate(site.actual_completion_date)}</span>
                    </div>
                    ` : ''}
                    ${site.reception_date ? `
                    <div class="detail-item">
                        <label>Date de réception</label>
                        <span>${formatDate(site.reception_date)}</span>
                    </div>
                    ` : ''}
                </div>
            </div>
            
            <div class="detail-section">
                <h3><i class="fas fa-euro-sign"></i> Budget</h3>
                <div class="detail-grid">
                    ${site.construction_cost ? `
                    <div class="detail-item">
                        <label>Coût de construction</label>
                        <strong>${formatCurrency(site.construction_cost)}</strong>
                    </div>
                    ` : ''}
                    ${site.land_value ? `
                    <div class="detail-item">
                        <label>Valeur du terrain</label>
                        <span>${formatCurrency(site.land_value)}</span>
                    </div>
                    ` : ''}
                    ${site.total_project_value ? `
                    <div class="detail-item">
                        <label>Valeur totale du projet</label>
                        <strong>${formatCurrency(site.total_project_value)}</strong>
                    </div>
                    ` : ''}
                </div>
            </div>
            
            <div class="detail-section">
                <h3><i class="fas fa-building"></i> Caractéristiques du bâtiment</h3>
                <div class="detail-grid">
                    ${site.total_surface_m2 ? `
                    <div class="detail-item">
                        <label>Surface totale</label>
                        <span>${site.total_surface_m2} m²</span>
                    </div>
                    ` : ''}
                    ${site.habitable_surface_m2 ? `
                    <div class="detail-item">
                        <label>Surface habitable</label>
                        <span>${site.habitable_surface_m2} m²</span>
                    </div>
                    ` : ''}
                    ${site.num_floors ? `
                    <div class="detail-item">
                        <label>Nombre d'étages</label>
                        <span>${site.num_floors}</span>
                    </div>
                    ` : ''}
                    ${site.num_units ? `
                    <div class="detail-item">
                        <label>Nombre de logements</label>
                        <span>${site.num_units}</span>
                    </div>
                    ` : ''}
                    ${site.foundation_type ? `
                    <div class="detail-item">
                        <label>Type de fondation</label>
                        <span>${site.foundation_type}</span>
                    </div>
                    ` : ''}
                    ${site.structure_type ? `
                    <div class="detail-item">
                        <label>Type de structure</label>
                        <span>${site.structure_type}</span>
                    </div>
                    ` : ''}
                    ${site.seismic_zone ? `
                    <div class="detail-item">
                        <label>Zone sismique</label>
                        <span>${site.seismic_zone}</span>
                    </div>
                    ` : ''}
                </div>
            </div>
            
            <div class="detail-section">
                <h3><i class="fas fa-clock"></i> Métadonnées</h3>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>Date de création</label>
                        <span>${formatDateTime(site.created_at)}</span>
                    </div>
                    <div class="detail-item">
                        <label>Dernière mise à jour</label>
                        <span>${formatDateTime(site.updated_at)}</span>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.getElementById('site-detail-content').innerHTML = html;
}

function backToSitesList() {
    document.getElementById('sites-table-container').style.display = 'block';
    document.querySelector('#sites-view .view-toolbar').style.display = 'flex';
    document.getElementById('site-detail').style.display = 'none';
}

function editSite(id) { showToast('info', 'Info', 'Fonctionnalité en cours de développement'); }
function deleteSite(id) { showToast('info', 'Info', 'Fonctionnalité en cours de développement'); }

// Contract Details
async function viewContract(contractNumber) {
    try {
        const contract = await api.getContract(contractNumber);
        displayContractDetail(contract);
    } catch (error) {
        console.error('Error loading contract:', error);
        showToast('error', 'Erreur', 'Impossible de charger les détails du contrat');
    }
}

function getGuaranteeName(code) {
    const guaranteeNames = {
        'GAR_DO_00': 'Dommages ouvrage - Base',
        'GAR_DO_01': 'Dommages ouvrage - Étendue',
        'GAR_DO_02': 'Dommages ouvrage - Complémentaire',
        'GAR_DO_03': 'Dommages ouvrage - Premium',
        'GAR_DO_04': 'Dommages ouvrage - Excellence',
        'GAR_CNR_00': 'CNR - Base',
        'GAR_CNR_01': 'CNR - Étendue',
        'GAR_CNR_02': 'CNR - Complémentaire',
        'GAR_CNR_03': 'CNR - Premium',
        'GAR_CNR_04': 'CNR - Excellence',
        'GAR_PUC_00': 'PUC - Base',
        'GAR_PUC_01': 'PUC - Étendue',
        'GAR_PUC_02': 'PUC - Complémentaire',
        'GAR_PUC_03': 'PUC - Premium',
        'GAR_PUC_04': 'PUC - Excellence',
        'GAR_TRC_00': 'TRC - Base',
        'GAR_TRC_01': 'TRC - Étendue',
        'GAR_TRC_02': 'TRC - Complémentaire',
        'GAR_TRC_03': 'TRC - Premium',
        'GAR_TRC_04': 'TRC - Excellence',
        'GAR_RCD_00': 'RCD - Base',
        'GAR_RCD_01': 'RCD - Étendue',
        'GAR_RCD_02': 'RCD - Complémentaire',
        'GAR_RCD_03': 'RCD - Premium',
        'GAR_RCD_04': 'RCD - Excellence'
    };
    return guaranteeNames[code] || code;
}

function displayContractDetail(contract) {
    document.getElementById('contracts-table-container').style.display = 'none';
    document.querySelector('#contracts-view .view-toolbar').style.display = 'none';
    document.getElementById('contract-detail').style.display = 'block';
    
    const html = `
        <div class="detail-card" style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; align-items: start;">
        <div class="detail-left" style="min-width: 0;">
            <div class="detail-header">
                <h2>${contract.contract_number}</h2>
                <div class="detail-badges">
                    <span class="badge badge-info">${contract.contract_type_code}</span>
                    <span class="badge badge-${getStatusBadge(contract.status)}">${contract.status}</span>
                </div>
            </div>
            
            <div class="detail-section">
                <h3><i class="fas fa-file-contract"></i> Informations générales</h3>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>Numéro de contrat</label>
                        <strong>${contract.contract_number}</strong>
                    </div>
                    <div class="detail-item">
                        <label>Type de contrat</label>
                        <span class="badge badge-info">${contract.contract_type_code}</span>
                    </div>
                    <div class="detail-item">
                        <label>Statut</label>
                        <span class="badge badge-${getStatusBadge(contract.status)}">${contract.status}</span>
                    </div>
                    <div class="detail-item">
                        <label>Client ID</label>
                        <span>${contract.client_id}</span>
                    </div>
                </div>
            </div>
            
            <div class="detail-section">
                <h3><i class="fas fa-calendar-alt"></i> Dates</h3>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>Date de souscription</label>
                        <span>${formatDate(contract.subscription_date)}</span>
                    </div>
                    <div class="detail-item">
                        <label>Date d'effet</label>
                        <strong>${formatDate(contract.effective_date)}</strong>
                    </div>
                    <div class="detail-item">
                        <label>Date d'expiration</label>
                        <strong>${formatDate(contract.expiry_date)}</strong>
                    </div>
                    ${contract.termination_date ? `
                    <div class="detail-item">
                        <label>Date de résiliation</label>
                        <span>${formatDate(contract.termination_date)}</span>
                    </div>
                    ` : ''}
                </div>
            </div>
            
            <div class="detail-section">
                <h3><i class="fas fa-euro-sign"></i> Montants</h3>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>Montant assuré</label>
                        <strong>${formatCurrency(contract.insured_amount)}</strong>
                    </div>
                    <div class="detail-item">
                        <label>Prime annuelle</label>
                        <strong>${formatCurrency(contract.annual_premium)}</strong>
                    </div>
                    ${contract.franchise_amount ? `
                    <div class="detail-item">
                        <label>Franchise</label>
                        <span>${formatCurrency(contract.franchise_amount)}</span>
                    </div>
                    ` : ''}
                </div>
            </div>
        </div>
        
        <div class="detail-right" style="min-width: 0;">
            ${contract.construction_site ? `
            <div class="detail-section">
                <h3><i class="fas fa-hard-hat"></i> Chantier associé</h3>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>Code chantier</label>
                        <strong>${contract.construction_site.site_code}</strong>
                    </div>
                    <div class="detail-item">
                        <label>Nom du chantier</label>
                        <strong>${contract.construction_site.site_name}</strong>
                    </div>
                    <div class="detail-item">
                        <label>Catégorie</label>
                        <span class="badge badge-info">${contract.construction_site.building_category}</span>
                    </div>
                    <div class="detail-item">
                        <label>Type de travaux</label>
                        <span class="badge badge-secondary">${contract.construction_site.work_category}</span>
                    </div>
                    <div class="detail-item">
                        <label>Adresse</label>
                        <span>${contract.construction_site.address}<br>${contract.construction_site.postal_code} ${contract.construction_site.city}</span>
                    </div>
                    ${contract.construction_site.estimated_budget ? `
                    <div class="detail-item">
                        <label>Budget estimé</label>
                        <span>${formatCurrency(contract.construction_site.estimated_budget)}</span>
                    </div>
                    ` : ''}
                    ${contract.construction_site.start_date ? `
                    <div class="detail-item">
                        <label>Date de début</label>
                        <span>${formatDate(contract.construction_site.start_date)}</span>
                    </div>
                    ` : ''}
                    ${contract.construction_site.planned_end_date ? `
                    <div class="detail-item">
                        <label>Date de fin prévue</label>
                        <span>${formatDate(contract.construction_site.planned_end_date)}</span>
                    </div>
                    ` : ''}
                </div>
                ${contract.construction_site.description ? `
                <div style="margin-top: 1rem;">
                    <label>Description</label>
                    <p>${contract.construction_site.description}</p>
                </div>
                ` : ''}
            </div>
            ` : ''}
            
            ${contract.guarantees && contract.guarantees.length > 0 ? `
            <div class="detail-section">
                <h3><i class="fas fa-shield-alt"></i> Garanties du contrat (${contract.guarantees.length})</h3>
                <div style="overflow-x: auto; -webkit-overflow-scrolling: touch;">
                <table class="data-table" style="min-width: 100%;">
                    <thead>
                        <tr>
                            <th>Code</th>
                            <th>Nom</th>
                            <th>Plafond</th>
                            <th>Franchise</th>
                            <th>Prime annuelle</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${contract.guarantees.map(g => `
                            <tr>
                                <td><strong>${g.code}</strong></td>
                                <td>${getGuaranteeName(g.code)}</td>
                                <td>${formatCurrency(g.ceiling)}</td>
                                <td>${formatCurrency(g.franchise)}</td>
                                <td>${formatCurrency(g.annual_premium)}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
                </div>
            </div>
            ` : ''}
        </div>
        
        <div style="grid-column: 1 / -1;">
            ${contract.conditions ? `
            <div class="detail-section">
                <h3><i class="fas fa-file-alt"></i> Conditions particulières</h3>
                <p>${contract.conditions}</p>
            </div>
            ` : ''}
            
            ${contract.termination_reason ? `
            <div class="detail-section">
                <h3><i class="fas fa-ban"></i> Résiliation</h3>
                <p><strong>Raison:</strong> ${contract.termination_reason}</p>
            </div>
            ` : ''}
            
            <div class="detail-section">
                <h3><i class="fas fa-clock"></i> Métadonnées</h3>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>Date de création</label>
                        <span>${formatDateTime(contract.created_at)}</span>
                    </div>
                    <div class="detail-item">
                        <label>Dernière mise à jour</label>
                        <span>${formatDateTime(contract.updated_at)}</span>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.getElementById('contract-detail-content').innerHTML = html;
}

function backToContractsList() {
    document.getElementById('contracts-table-container').style.display = 'block';
    document.querySelector('#contracts-view .view-toolbar').style.display = 'flex';
    document.getElementById('contract-detail').style.display = 'none';
}

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
