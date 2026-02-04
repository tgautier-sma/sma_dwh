/**
 * Gestionnaire de synchronisation pour le mode hors ligne
 * Gère la synchronisation des données entre le cache local et le serveur
 */

class SyncManager {
    constructor(api, dbManager) {
        this.api = api;
        this.dbManager = dbManager;
        this.syncInProgress = false;
        this.syncInterval = null;
        this.lastSyncTime = null;
        
        // Écouter les changements de connexion
        window.addEventListener('online', () => {
            console.log('[SyncManager] Connexion restaurée - Démarrage de la synchronisation');
            this.syncAll();
        });
        
        // Démarrer la synchronisation périodique
        this.startPeriodicSync();
    }

    /**
     * Démarre la synchronisation périodique (toutes les 5 minutes)
     */
    startPeriodicSync() {
        if (this.syncInterval) {
            clearInterval(this.syncInterval);
        }
        
        // Synchroniser toutes les 5 minutes si en ligne
        this.syncInterval = setInterval(() => {
            if (navigator.onLine && !this.syncInProgress) {
                this.syncAll();
            }
        }, 5 * 60 * 1000); // 5 minutes
    }

    /**
     * Arrête la synchronisation périodique
     */
    stopPeriodicSync() {
        if (this.syncInterval) {
            clearInterval(this.syncInterval);
            this.syncInterval = null;
        }
    }

    /**
     * Synchronise toutes les données
     */
    async syncAll() {
        if (this.syncInProgress) {
            console.log('[SyncManager] Synchronisation déjà en cours');
            return;
        }

        if (!navigator.onLine) {
            console.log('[SyncManager] Pas de connexion - Synchronisation impossible');
            return;
        }

        this.syncInProgress = true;
        console.log('[SyncManager] Démarrage de la synchronisation complète');

        try {
            // 1. Envoyer les modifications locales au serveur
            await this.syncPendingChanges();
            
            // 2. Télécharger les données mises à jour depuis le serveur
            await this.syncFromServer();
            
            // Mettre à jour l'horodatage de la dernière synchronisation
            this.lastSyncTime = new Date();
            await this.dbManager.setMetadata('last_sync', this.lastSyncTime.toISOString());
            
            console.log('[SyncManager] Synchronisation complète terminée avec succès');
            
            // Notifier l'utilisateur
            this.notifyUser('Synchronisation terminée', 'success');
        } catch (error) {
            console.error('[SyncManager] Erreur de synchronisation:', error);
            this.notifyUser('Erreur de synchronisation', 'error');
        } finally {
            this.syncInProgress = false;
        }
    }

    /**
     * Envoie les modifications en attente au serveur
     */
    async syncPendingChanges() {
        const pendingChanges = await this.dbManager.getPendingChanges();
        
        if (pendingChanges.length === 0) {
            console.log('[SyncManager] Aucune modification en attente');
            return;
        }

        console.log(`[SyncManager] Envoi de ${pendingChanges.length} modifications au serveur`);
        
        let successCount = 0;
        let errorCount = 0;

        for (const change of pendingChanges) {
            try {
                await this.syncChange(change);
                await this.dbManager.deletePendingChange(change.id);
                successCount++;
                console.log(`[SyncManager] Modification ${change.id} synchronisée`);
            } catch (error) {
                errorCount++;
                console.error(`[SyncManager] Échec de synchronisation de ${change.id}:`, error);
                
                // Si l'erreur est un conflit, marquer comme nécessitant une intervention manuelle
                if (error.message.includes('conflict') || error.message.includes('409')) {
                    await this.markChangeAsConflict(change);
                }
            }
        }

        console.log(`[SyncManager] Synchronisation terminée: ${successCount} réussies, ${errorCount} échecs`);
    }

    /**
     * Synchronise une modification individuelle
     */
    async syncChange(change) {
        switch (change.entity_type) {
            case 'claim':
                return await this.api.updateClaim(change.entity_id, change.data);
            
            case 'contract':
                return await this.api.updateContract(change.entity_id, change.data);
            
            case 'client':
                return await this.api.updateClient(change.entity_id, change.data);
            
            default:
                throw new Error(`Type d'entité non géré: ${change.entity_type}`);
        }
    }

    /**
     * Marque une modification comme étant en conflit
     */
    async markChangeAsConflict(change) {
        // Ajouter un flag de conflit
        const conflictChange = {
            ...change,
            conflict: true,
            conflict_time: new Date().toISOString()
        };
        
        // Sauvegarder dans une table de conflits si nécessaire
        console.warn('[SyncManager] Conflit détecté pour:', change);
    }

    /**
     * Télécharge les données depuis le serveur
     */
    async syncFromServer() {
        console.log('[SyncManager] Téléchargement des données depuis le serveur');

        try {
            // Télécharger les sinistres
            const claimsResponse = await this.api.getClaims({ limit: 100 });
            if (claimsResponse.items) {
                await this.dbManager.saveClaims(claimsResponse.items);
                console.log(`[SyncManager] ${claimsResponse.items.length} sinistres téléchargés`);
            }

            // Télécharger les contrats (si nécessaire)
            // const contracts = await this.api.getContracts({ limit: 100 });
            // await this.dbManager.saveContracts(contracts.items);

            // Télécharger les référentiels
            const guarantees = await this.api.getGuaranteeTypes();
            await this.dbManager.saveReferential('guarantees', guarantees);
            console.log('[SyncManager] Référentiels téléchargés');

        } catch (error) {
            console.error('[SyncManager] Erreur lors du téléchargement:', error);
            throw error;
        }
    }

    /**
     * Force une synchronisation immédiate
     */
    async forceSync() {
        console.log('[SyncManager] Synchronisation forcée');
        return await this.syncAll();
    }

    /**
     * Obtient l'état de la synchronisation
     */
    async getSyncStatus() {
        const pendingChanges = await this.dbManager.getPendingChanges();
        const lastSync = await this.dbManager.getMetadata('last_sync');
        const stats = await this.dbManager.getStats();

        return {
            isOnline: navigator.onLine,
            syncInProgress: this.syncInProgress,
            lastSyncTime: lastSync ? new Date(lastSync) : null,
            pendingChangesCount: pendingChanges.length,
            localDataStats: stats
        };
    }

    /**
     * Notifie l'utilisateur
     */
    notifyUser(message, type = 'info') {
        // Utiliser la fonction showOfflineNotification si disponible
        if (typeof showOfflineNotification === 'function') {
            showOfflineNotification(message, type);
        } else {
            console.log(`[SyncManager] ${type.toUpperCase()}: ${message}`);
        }
    }

    /**
     * Nettoie les anciennes données du cache
     */
    async cleanOldCache(daysToKeep = 30) {
        console.log(`[SyncManager] Nettoyage des données de plus de ${daysToKeep} jours`);
        
        try {
            const cutoffDate = new Date();
            cutoffDate.setDate(cutoffDate.getDate() - daysToKeep);
            
            // Cette logique pourrait être implémentée dans dbManager
            // pour supprimer les anciennes entrées
            
            console.log('[SyncManager] Nettoyage terminé');
        } catch (error) {
            console.error('[SyncManager] Erreur lors du nettoyage:', error);
        }
    }

    /**
     * Réinitialise toutes les données locales et re-synchronise
     */
    async resetAndSync() {
        console.log('[SyncManager] Réinitialisation et synchronisation complète');
        
        try {
            // Sauvegarder les modifications en attente
            const pendingChanges = await this.dbManager.getPendingChanges();
            
            if (pendingChanges.length > 0) {
                const confirm = window.confirm(
                    `Vous avez ${pendingChanges.length} modifications non synchronisées. ` +
                    'Voulez-vous les supprimer et recommencer ?'
                );
                
                if (!confirm) {
                    return;
                }
            }
            
            // Vider toutes les données
            await this.dbManager.clearAll();
            
            // Re-télécharger depuis le serveur
            await this.syncFromServer();
            
            this.notifyUser('Données réinitialisées et synchronisées', 'success');
        } catch (error) {
            console.error('[SyncManager] Erreur lors de la réinitialisation:', error);
            this.notifyUser('Erreur lors de la réinitialisation', 'error');
        }
    }
}

// Instance globale (sera initialisée après que api et dbManager soient disponibles)
let syncManager = null;

// Fonction d'initialisation à appeler après le chargement de la page
function initSyncManager() {
    if (typeof api !== 'undefined' && typeof dbManager !== 'undefined') {
        syncManager = new SyncManager(api, dbManager);
        console.log('[SyncManager] Gestionnaire de synchronisation initialisé');
        
        // Exposer des fonctions globales utiles
        window.forceSync = () => syncManager.forceSync();
        window.getSyncStatus = () => syncManager.getSyncStatus();
        window.resetData = () => syncManager.resetAndSync();
    } else {
        console.error('[SyncManager] api ou dbManager non disponibles');
    }
}

// Auto-initialisation si les dépendances sont déjà chargées
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initSyncManager);
} else {
    initSyncManager();
}

// Export pour utilisation dans d'autres modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SyncManager;
}
