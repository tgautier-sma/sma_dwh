"""Script pour migrer la table fake_contract_guarantees"""
from app.database import engine
from sqlalchemy import text

def migrate_guarantees_table():
    """Ajouter les colonnes manquantes à la table fake_contract_guarantees"""
    with engine.connect() as conn:
        try:
            # Supprimer d'abord la contrainte de clé primaire composite
            conn.execute(text("ALTER TABLE fake_contract_guarantees DROP CONSTRAINT IF EXISTS fake_contract_guarantees_pkey;"))
            print("✓ Contrainte de clé primaire supprimée")
            
            # Ajouter un ID auto-incrémenté
            conn.execute(text("ALTER TABLE fake_contract_guarantees ADD COLUMN IF NOT EXISTS id SERIAL;"))
            print("✓ Colonne id ajoutée")
            
            # Ajouter la nouvelle clé primaire
            conn.execute(text("ALTER TABLE fake_contract_guarantees ADD PRIMARY KEY (id);"))
            print("✓ Nouvelle clé primaire définie")
            
            # Ajouter la colonne guarantee_code
            conn.execute(text("ALTER TABLE fake_contract_guarantees ADD COLUMN IF NOT EXISTS guarantee_code VARCHAR(30);"))
            print("✓ Colonne guarantee_code ajoutée")
            
            # Ajouter annual_premium
            conn.execute(text("ALTER TABLE fake_contract_guarantees ADD COLUMN IF NOT EXISTS annual_premium FLOAT;"))
            print("✓ Colonne annual_premium ajoutée")
            
            # Ajouter les timestamps
            conn.execute(text("ALTER TABLE fake_contract_guarantees ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();"))
            print("✓ Colonne created_at ajoutée")
            
            conn.execute(text("ALTER TABLE fake_contract_guarantees ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();"))
            print("✓ Colonne updated_at ajoutée")
            
            # Rendre guarantee_id nullable
            conn.execute(text("ALTER TABLE fake_contract_guarantees ALTER COLUMN guarantee_id DROP NOT NULL;"))
            print("✓ Colonne guarantee_id rendue nullable")
            
            conn.commit()
            print("\n✅ Table fake_contract_guarantees mise à jour avec succès!")
            
        except Exception as e:
            print(f"\n❌ Erreur lors de la migration: {e}")
            conn.rollback()
            raise

if __name__ == "__main__":
    migrate_guarantees_table()
