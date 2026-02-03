"""Script pour mettre à jour les garanties des contrats existants avec les codes du référentiel"""
import random
from sqlalchemy import text
from app.database import SessionLocal
from app.models import GuaranteeModel, contract_guarantees

def update_contract_guarantees():
    """Mettre à jour toutes les garanties des contrats pour utiliser les codes du référentiel"""
    db = SessionLocal()
    
    try:
        # Récupérer les garanties disponibles dans le référentiel
        available_guarantees = db.query(GuaranteeModel).all()
        
        if not available_guarantees:
            print("❌ Aucune garantie trouvée dans le référentiel.")
            return
        
        print(f"✅ {len(available_guarantees)} garanties trouvées dans le référentiel")
        
        # Récupérer tous les contrats
        contracts = db.execute(text('SELECT id, contract_number FROM fake_client_contracts ORDER BY id')).fetchall()
        print(f"📋 {len(contracts)} contrats à mettre à jour")
        
        # Supprimer toutes les anciennes garanties
        print("🗑️  Suppression des anciennes garanties...")
        db.execute(contract_guarantees.delete())
        db.commit()
        
        # Créer de nouvelles garanties pour chaque contrat
        print("✨ Création des nouvelles garanties...")
        total_created = 0
        
        for contract_id, contract_number in contracts:
            # Sélectionner aléatoirement entre 1 et 5 garanties
            num_guarantees = min(random.randint(1, 5), len(available_guarantees))
            selected_guarantees = random.sample(available_guarantees, num_guarantees)
            
            guarantees_data = []
            for guarantee in selected_guarantees:
                guarantees_data.append({
                    'contract_id': contract_id,
                    'guarantee_code': guarantee.code,
                    'custom_ceiling': guarantee.default_ceiling or random.randint(50000, 1000000),
                    'custom_franchise': guarantee.default_franchise or random.randint(500, 5000),
                    'is_included': True,
                    'annual_premium': random.uniform(500, 5000)
                })
            
            if guarantees_data:
                db.execute(contract_guarantees.insert(), guarantees_data)
                total_created += len(guarantees_data)
        
        db.commit()
        
        print(f"\n✅ Mise à jour terminée avec succès!")
        print(f"   - {len(contracts)} contrats mis à jour")
        print(f"   - {total_created} garanties créées")
        print(f"   - Moyenne: {total_created / len(contracts):.1f} garanties par contrat")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("🔄 Mise à jour des garanties des contrats")
    print("=" * 60)
    update_contract_guarantees()
