"""
Migration : réseau commercial, visites clients et propositions d'assurance
- Crée les nouvelles tables : fake_sales_reps, fake_client_visits, fake_insurance_proposals
- Ajoute les colonnes de traçabilité de la souscription sur fake_client_contracts
Usage:
    python migrate_visits_tables.py
"""
from sqlalchemy import text

from app.database import engine, Base
import app.models  # noqa: F401  (déclenche l'enregistrement des modèles auprès de Base.metadata)


def create_new_tables():
    """Crée les tables manquantes (ne touche pas aux tables existantes)"""
    Base.metadata.create_all(
        bind=engine,
        tables=[
            Base.metadata.tables["fake_sales_reps"],
            Base.metadata.tables["fake_client_visits"],
            Base.metadata.tables["fake_insurance_proposals"],
        ],
    )
    print("✓ Tables fake_sales_reps, fake_client_visits, fake_insurance_proposals prêtes")


def add_contract_link_columns():
    """Ajoute les colonnes de lien commercial/visite sur fake_client_contracts"""
    with engine.connect() as conn:
        conn.execute(text(
            "ALTER TABLE fake_client_contracts ADD COLUMN IF NOT EXISTS sales_rep_id INTEGER "
            "REFERENCES fake_sales_reps(id);"
        ))
        print("✓ Colonne sales_rep_id ajoutée à fake_client_contracts")

        conn.execute(text(
            "ALTER TABLE fake_client_contracts ADD COLUMN IF NOT EXISTS originating_visit_id INTEGER "
            "REFERENCES fake_client_visits(id);"
        ))
        print("✓ Colonne originating_visit_id ajoutée à fake_client_contracts")

        conn.commit()


def main():
    print("\n🔧 Migration réseau commercial / visites / propositions...\n")
    try:
        create_new_tables()
        add_contract_link_columns()
        print("\n✅ Migration terminée avec succès\n")
    except Exception as e:
        print(f"\n❌ Erreur lors de la migration: {e}")
        raise


if __name__ == "__main__":
    main()
