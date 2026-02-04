/**
 * Service Worker pour le mode hors ligne
 * Gère le cache des ressources statiques et des données API
 */

const CACHE_VERSION = 'sma-dwh-v1';
const STATIC_CACHE = 'sma-dwh-static-v1';
const API_CACHE = 'sma-dwh-api-v1';
const IMAGE_CACHE = 'sma-dwh-images-v1';

// Ressources à mettre en cache immédiatement
const STATIC_RESOURCES = [
    '/',
    '/static/index.html',
    '/static/claim_search.html',
    '/static/styles.css',
    '/static/api.js',
    '/static/app.js',
    '/static/phonetic.js',
    '/static/db-manager.js',
    '/static/sync-manager.js',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
    'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css',
    'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js'
];

// Installation du service worker
self.addEventListener('install', (event) => {
    console.log('[ServiceWorker] Installation en cours...');
    
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then((cache) => {
                console.log('[ServiceWorker] Mise en cache des ressources statiques');
                return cache.addAll(STATIC_RESOURCES.map(url => new Request(url, {cache: 'reload'})));
            })
            .then(() => {
                console.log('[ServiceWorker] Installation terminée');
                return self.skipWaiting();
            })
            .catch((error) => {
                console.error('[ServiceWorker] Erreur lors de l\'installation:', error);
            })
    );
});

// Activation du service worker
self.addEventListener('activate', (event) => {
    console.log('[ServiceWorker] Activation en cours...');
    
    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames.map((cacheName) => {
                        if (cacheName !== STATIC_CACHE && cacheName !== API_CACHE && cacheName !== IMAGE_CACHE) {
                            console.log('[ServiceWorker] Suppression ancien cache:', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
            .then(() => {
                console.log('[ServiceWorker] Activation terminée');
                return self.clients.claim();
            })
    );
});

// Interception des requêtes
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);
    
    // Ignorer les requêtes non-HTTP
    if (!request.url.startsWith('http')) {
        return;
    }
    
    // Stratégie pour les requêtes API
    if (url.pathname.startsWith('/claims') || 
        url.pathname.startsWith('/contracts') || 
        url.pathname.startsWith('/clients') ||
        url.pathname.startsWith('/referentials')) {
        event.respondWith(networkFirstStrategy(request));
        return;
    }
    
    // Stratégie pour les tuiles de carte
    if (url.hostname.includes('openstreetmap.org') || url.hostname.includes('nominatim')) {
        event.respondWith(cacheFirstStrategy(request, IMAGE_CACHE));
        return;
    }
    
    // Stratégie pour les ressources statiques
    event.respondWith(cacheFirstStrategy(request, STATIC_CACHE));
});

/**
 * Stratégie Network First: Essaie le réseau d'abord, sinon utilise le cache
 * Utilisé pour les données API qui doivent être fraîches
 */
async function networkFirstStrategy(request) {
    const cache = await caches.open(API_CACHE);
    
    try {
        // Essayer de récupérer depuis le réseau
        const networkResponse = await fetch(request);
        
        // Si succès, mettre en cache et retourner
        if (networkResponse && networkResponse.status === 200) {
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        // Si erreur réseau, utiliser le cache
        console.log('[ServiceWorker] Réseau indisponible, utilisation du cache pour:', request.url);
        const cachedResponse = await cache.match(request);
        
        if (cachedResponse) {
            // Ajouter un header pour indiquer que c'est depuis le cache
            const headers = new Headers(cachedResponse.headers);
            headers.append('X-From-Cache', 'true');
            
            return new Response(cachedResponse.body, {
                status: cachedResponse.status,
                statusText: cachedResponse.statusText,
                headers: headers
            });
        }
        
        // Si pas de cache, retourner une réponse d'erreur
        return new Response(JSON.stringify({
            error: 'Données non disponibles hors ligne',
            offline: true
        }), {
            status: 503,
            headers: { 'Content-Type': 'application/json' }
        });
    }
}

/**
 * Stratégie Cache First: Utilise le cache d'abord, sinon le réseau
 * Utilisé pour les ressources statiques qui changent rarement
 */
async function cacheFirstStrategy(request, cacheName) {
    const cache = await caches.open(cacheName);
    const cachedResponse = await cache.match(request);
    
    if (cachedResponse) {
        return cachedResponse;
    }
    
    try {
        const networkResponse = await fetch(request);
        
        if (networkResponse && networkResponse.status === 200) {
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        console.error('[ServiceWorker] Erreur de chargement:', request.url, error);
        
        // Retourner une page d'erreur basique pour les pages HTML
        if (request.destination === 'document') {
            return new Response('<html><body><h1>Mode hors ligne</h1><p>Cette page n\'est pas disponible hors ligne.</p></body></html>', {
                headers: { 'Content-Type': 'text/html' }
            });
        }
        
        return new Response('Resource not available offline', { status: 503 });
    }
}

// Gestion des messages depuis l'application
self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
    
    if (event.data && event.data.type === 'CLEAR_CACHE') {
        event.waitUntil(
            caches.keys().then((cacheNames) => {
                return Promise.all(
                    cacheNames.map((cacheName) => caches.delete(cacheName))
                );
            }).then(() => {
                event.ports[0].postMessage({ success: true });
            })
        );
    }
    
    if (event.data && event.data.type === 'GET_CACHE_SIZE') {
        event.waitUntil(
            getCacheSize().then((size) => {
                event.ports[0].postMessage({ size: size });
            })
        );
    }
});

// Calculer la taille du cache
async function getCacheSize() {
    const cacheNames = await caches.keys();
    let totalSize = 0;
    
    for (const cacheName of cacheNames) {
        const cache = await caches.open(cacheName);
        const keys = await cache.keys();
        
        for (const request of keys) {
            const response = await cache.match(request);
            if (response) {
                const blob = await response.blob();
                totalSize += blob.size;
            }
        }
    }
    
    return totalSize;
}

// Synchronisation en arrière-plan
self.addEventListener('sync', (event) => {
    console.log('[ServiceWorker] Synchronisation en arrière-plan:', event.tag);
    
    if (event.tag === 'sync-claims') {
        event.waitUntil(syncClaims());
    }
});

// Fonction de synchronisation des sinistres
async function syncClaims() {
    try {
        // Récupérer les modifications en attente depuis IndexedDB
        // Cette logique sera implémentée avec db-manager.js
        console.log('[ServiceWorker] Synchronisation des sinistres...');
        
        // TODO: Implémenter la logique de synchronisation
        
        return Promise.resolve();
    } catch (error) {
        console.error('[ServiceWorker] Erreur de synchronisation:', error);
        return Promise.reject(error);
    }
}

console.log('[ServiceWorker] Service Worker chargé');
