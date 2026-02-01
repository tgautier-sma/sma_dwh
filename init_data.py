"""Script d'initialisation des données de référence"""
import sys
from sqlalchemy.orm import Session

from app.database import SessionLocal, init_db
from app.models import (
    InsuranceContractTypeModel, GuaranteeModel, ContractClauseModel,
    BuildingCategoryModel, WorkCategoryModel, ProfessionModel, ExclusionModel,
    DEFAULT_CONTRACT_TYPES, DEFAULT_GUARANTEES, DEFAULT_CLAUSES,
    DEFAULT_BUILDING_CATEGORIES, DEFAULT_WORK_CATEGORIES, DEFAULT_PROFESSIONS,
    DEFAULT_EXCLUSIONS
)


def init_referential_data(db: Session):
    """Initialiser les données de référence"""
    
    print("🔧 Initialisation des données de référence...")
    
    # Types de contrats
    print("\n📋 Création des types de contrats...")
    for item in DEFAULT_CONTRACT_TYPES:
        existing = db.query(InsuranceContractTypeModel).filter(
            InsuranceContractTypeModel.code == item["code"]
        ).first()
        
        if not existing:
            db_item = InsuranceContractTypeModel(**item)
            db.add(db_item)
            print(f"  ✅ Type de contrat créé : {item['code']} - {item['name']}")
        else:
            print(f"  ⏭️  Type de contrat existant : {item['code']}")
    
    db.commit()
    
    # Garanties
    print("\n🛡️  Création des garanties...")
    contract_types = {ct.code: ct.id for ct in db.query(InsuranceContractTypeModel).all()}
    
    for item in DEFAULT_GUARANTEES:
        existing = db.query(GuaranteeModel).filter(
            GuaranteeModel.code == item["code"]
        ).first()
        
        if not existing:
            # Remplacer le code de type de contrat par son ID
            contract_type_code = item.pop("contract_type_code", None)
            if contract_type_code and contract_type_code in contract_types:
                item["contract_type_id"] = contract_types[contract_type_code]
            
            db_item = GuaranteeModel(**item)
            db.add(db_item)
            print(f"  ✅ Garantie créée : {item['code']} - {item['name']}")
        else:
            print(f"  ⏭️  Garantie existante : {item['code']}")
    
    db.commit()
    
    # Clauses
    print("\n📜 Création des clauses contractuelles...")
    for item in DEFAULT_CLAUSES:
        existing = db.query(ContractClauseModel).filter(
            ContractClauseModel.code == item["code"]
        ).first()
        
        if not existing:
            db_item = ContractClauseModel(**item)
            db.add(db_item)
            print(f"  ✅ Clause créée : {item['code']} - {item['title']}")
        else:
            print(f"  ⏭️  Clause existante : {item['code']}")
    
    db.commit()
    
    # Catégories de bâtiments
    print("\n🏢 Création des catégories de bâtiments...")
    for item in DEFAULT_BUILDING_CATEGORIES:
        existing = db.query(BuildingCategoryModel).filter(
            BuildingCategoryModel.code == item["code"]
        ).first()
        
        if not existing:
            db_item = BuildingCategoryModel(**item)
            db.add(db_item)
            print(f"  ✅ Catégorie créée : {item['code']} - {item['name']}")
        else:
            print(f"  ⏭️  Catégorie existante : {item['code']}")
    
    db.commit()
    
    # Catégories de travaux
    print("\n🔨 Création des catégories de travaux...")
    for item in DEFAULT_WORK_CATEGORIES:
        existing = db.query(WorkCategoryModel).filter(
            WorkCategoryModel.code == item["code"]
        ).first()
        
        if not existing:
            db_item = WorkCategoryModel(**item)
            db.add(db_item)
            print(f"  ✅ Catégorie créée : {item['code']} - {item['name']}")
        else:
            print(f"  ⏭️  Catégorie existante : {item['code']}")
    
    db.commit()
    
    # Professions
    print("\n👷 Création des professions...")
    for item in DEFAULT_PROFESSIONS:
        existing = db.query(ProfessionModel).filter(
            ProfessionModel.code == item["code"]
        ).first()
        
        if not existing:
            db_item = ProfessionModel(**item)
            db.add(db_item)
            print(f"  ✅ Profession créée : {item['code']} - {item['name']}")
        else:
            print(f"  ⏭️  Profession existante : {item['code']}")
    
    db.commit()
    
    # Exclusions
    print("\n🚫 Création des exclusions...")
    for item in DEFAULT_EXCLUSIONS:
        existing = db.query(ExclusionModel).filter(
            ExclusionModel.code == item["code"]
        ).first()
        
        if not existing:
            db_item = ExclusionModel(**item)
            db.add(db_item)
            print(f"  ✅ Exclusion créée : {item['code']} - {item['title']}")
        else:
            print(f"  ⏭️  Exclusion existante : {item['code']}")
    
    db.commit()
    
    print("\n✨ Initialisation des données de référence terminée !")


def main():
    """Point d'entrée principal"""
    print("=" * 70)
    print("  Script d'initialisation des données de référence")
    print("=" * 70)
    
    try:
        # Initialiser la base de données (créer les tables)
        print("\n🔧 Création des tables de la base de données...")
        init_db()
        print("✅ Tables créées avec succès")
        
        # Initialiser les données de référence
        db = SessionLocal()
        try:
            init_referential_data(db)
        finally:
            db.close()
        
        print("\n" + "=" * 70)
        print("  ✅ Initialisation terminée avec succès !")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Erreur lors de l'initialisation : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
