# Script de génération de données - Documentation technique

## 📋 Vue d'ensemble

Le script `generate_client_data.py` génère automatiquement des données de test cohérentes pour l'API d'assurance. Il utilise la bibliothèque Faker avec la locale française (`fr_FR`) pour créer des données réalistes.

## 🎯 Objectifs

1. Nettoyer la base de données de test
2. Générer des clients avec toutes leurs relations
3. Assurer la cohérence des données entre les tables
4. Respecter les contraintes de la base de données
5. Fournir des données en français

## 🏗️ Architecture

### Structure du code

```
generate_client_data.py
├── Imports et configuration
├── Fonctions de génération
│   ├── generate_client()         # Génère un client
│   ├── generate_addresses()      # Génère 1-3 adresses
│   ├── generate_construction_site()  # Génère un chantier
│   ├── generate_contract()       # Génère un contrat
│   └── generate_contract_history()  # Génère l'historique
├── Fonctions utilitaires
│   ├── clean_all_clients()       # Supprime tous les clients
│   ├── create_complete_client()  # Orchestre la création
│   └── get_database_stats()      # Compte les enregistrements
└── main()                         # Point d'entrée CLI
```

### Dépendances

```python
from faker import Faker
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
import random
import argparse
```

## 📊 Données générées

### 1. Client (`ClientModel`)

#### Particulier (50% des cas)
- **Civilité** : M., Mme, Mlle
- **Prénom** : Prénom français (Faker)
- **Nom** : Nom français (Faker)
- **Date de naissance** : Entre 1950 et 2005
- **Email** : Email généré par Faker
- **Téléphone** : Format français (max 14 caractères)
- **Mobile** : 50% des clients ont un mobile
- **Numéro client** : CLIxxxx (4 chiffres aléatoires)
- **Profession** : Code aléatoire (PROFXXX)

#### Entreprise (50% des cas)
- **Raison sociale** : Nom d'entreprise français
- **Forme juridique** : SARL, SAS, SA, EURL, SCI, AUTO
- **SIRET** : 14 chiffres (basé sur SIREN)
- **SIREN** : 9 chiffres
- **Email** : Email professionnel
- **Téléphone** : Format français
- **Numéro client** : CLIxxxx

### 2. Adresses (`ClientAddressModel`)

Chaque client a entre 1 et 3 adresses :

#### Siège social (obligatoire)
- Type : `siege_social`
- Marquée comme primaire
- Adresse complète française
- Code postal : 5 chiffres
- Département : Calculé à partir du code postal (2 premiers chiffres)

#### Entrepôt (optionnel, 30% des clients)
- Type : `entrepot`
- Surface en m²
- Capacité de stockage
- Matériaux stockés

#### Chantier (optionnel, 30% des clients)
- Type : `chantier`
- Date de début
- Date de fin prévue
- Statut : en_cours, termine, suspendu

### 3. Chantier (`ConstructionSiteModel`)

50% des clients ont un chantier associé :

- **Référence** : CHxxxxxxx (7 chiffres aléatoires)
- **Nom** : "Projet [type de rue] [nom de rue]"
- **Localisation** : Adresse française complète
- **Surface totale** : Entre 100 et 10000 m²
- **Coût construction** : Entre 200 000€ et 10 000 000€
- **Dates** :
  - Ouverture : Dans le passé (6 mois à 2 ans)
  - Fin prévue : Entre 1 et 3 ans après l'ouverture
- **Caractéristiques** :
  - Nombre d'étages : 1 à 10
  - Type de structure : beton, acier, bois, mixte
  - Fondations : superficielles, profondes, radier

### 4. Contrats (`ClientContractModel`)

Chaque client a entre 1 et 4 contrats :

#### Types de contrats disponibles
Récupérés depuis `fake_ref_insurance_contract_types` :
- DO (Dommages-Ouvrage)
- RCD (Responsabilité Civile Décennale)
- TRC (Tous Risques Chantier)
- PUC (Police Unique de Chantier)
- etc.

#### Informations générées
- **Numéro** : CNTxxxxxx (6 chiffres aléatoires)
- **Statut** : brouillon, actif, suspendu, expire, annule, en_attente
- **Date d'émission** : Date aléatoire dans le passé
- **Date d'effet** : Après la date d'émission
- **Date d'expiration** : Selon la durée (1, 2, 5 ou 10 ans)
- **Montant assuré** : Entre 500 000€ et 10 000 000€
- **Prime annuelle** : Entre 0.2% et 0.5% du montant assuré
- **Franchise** : Entre 500€ et 10 000€
- **Souscripteur** : Nom aléatoire généré par Faker

#### Garanties (2 à 5 par contrat)
Structure JSON :
```json
{
    "code": "GAR_XXX_00",
    "name": "Garantie [nom aléatoire]",
    "ceiling": 500000,
    "franchise": 2000,
    "included": true
}
```

#### Clauses (1 à 3 par contrat)
Structure JSON :
```json
{
    "code": "CL_000",
    "name": "Clause [nom aléatoire]",
    "variables": {
        "montant": 15000
    }
}
```

### 5. Historique (`ContractHistoryModel`)

Chaque contrat a entre 1 et 5 entrées d'historique :

- **Action** : 
  - creation
  - modification
  - renouvellement
  - suspension
  - reactivation
  - annulation
  - changement_statut
  - ajout_garantie
  - modification_prime
  
- **Date** : Date aléatoire entre la création du contrat et maintenant
- **Utilisateur** : USERxxx (3 chiffres aléatoires)
- **Champs modifiés** : Optionnel (field_changed, old_value, new_value)

## ⚙️ Configuration

### Locale Faker

```python
fake = Faker('fr_FR')
```

La locale française permet de générer :
- Noms et prénoms français
- Adresses françaises
- Codes postaux valides
- Numéros de téléphone français
- Noms d'entreprises français

### Contraintes respectées

#### Longueurs maximales
- `client_number`: 20 caractères → CLIxxxx (7 car.)
- `siret`: 14 caractères → 14 chiffres exactement
- `siren`: 9 caractères → 9 chiffres exactement
- `phone/mobile`: 20 caractères → 14 max après nettoyage
- `department`: 3 caractères → 2 chiffres du code postal
- `email`: 255 caractères
- `postal_code`: 10 caractères → 5 chiffres

#### Formatage
- **SIRET/SIREN** : Suppression des espaces et limitation à N chiffres
  ```python
  siret = ''.join(filter(str.isdigit, fake.siren()))[:9]
  ```

- **Téléphones** : Suppression des espaces
  ```python
  phone = fake.phone_number().replace(' ', '')[:14]
  ```

- **Départements** : Extraction des 2 premiers chiffres du code postal
  ```python
  department = fake.postcode()[:2]
  ```

## 🔧 Utilisation

### Options de ligne de commande

```bash
python3 generate_client_data.py [OPTIONS]
```

#### Options disponibles

| Option | Description | Valeur par défaut |
|--------|-------------|-------------------|
| `--clean` | Supprime tous les clients et leurs relations | - |
| `--create` | Crée des nouveaux clients | - |
| `--count N` | Nombre de clients à créer | 1 |

### Exemples d'utilisation

```bash
# Supprimer tous les clients
python3 generate_client_data.py --clean

# Créer 5 clients
python3 generate_client_data.py --create --count 5

# Nettoyer et créer 10 clients
python3 generate_client_data.py --clean --create --count 10

# Par défaut (si aucune option)
python3 generate_client_data.py --create --count 1
```

## 📈 Performances

### Temps d'exécution

- **1 client** : ~1 seconde
- **10 clients** : ~10 secondes
- **100 clients** : ~1-2 minutes

### Données générées par client (moyenne)

- 1 client
- 2 adresses
- 0.5 chantiers
- 2 contrats
- 6 entrées d'historique

**Total pour 10 clients** : 10 clients + 20 adresses + 5 chantiers + 20 contrats + 60 historiques

## 🔍 Débogage

### Mode verbeux

Le script affiche automatiquement :
- Progression client par client
- Nombre d'éléments créés pour chaque client
- Résumé final avec totaux

### Logs SQLAlchemy

Les logs SQL sont filtrés par défaut. Pour les voir :
```bash
python3 generate_client_data.py --create 2>&1 | grep "SELECT\|INSERT"
```

### Vérification des données

Après génération, vérifier la cohérence :
```python
from app.database import SessionLocal
from app.models import ClientModel, ClientAddressModel

db = SessionLocal()
clients = db.query(ClientModel).all()

for client in clients:
    print(f"Client {client.client_number}:")
    print(f"  - Adresses: {len(client.addresses)}")
    print(f"  - Contrats: {len(client.contracts)}")
```

## ⚠️ Gestion des erreurs

### Erreurs courantes

#### 1. Violation de contrainte de longueur
```
psycopg2.errors.StringDataRightTruncation: value too long for type character varying(14)
```

**Solution** : Vérifier que les données respectent les limites
- SIRET : `[:14]`
- Téléphone : `[:14]`
- Département : `[:2]`

#### 2. Violation de contrainte d'unicité
```
psycopg2.errors.UniqueViolation: duplicate key value violates unique constraint
```

**Solution** : Utiliser des valeurs aléatoires suffisamment variées
```python
client_number = f"CLI{random.randint(1000, 9999)}"
```

#### 3. Violation de clé étrangère
```
psycopg2.errors.ForeignKeyViolation: insert or update violates foreign key constraint
```

**Solution** : S'assurer que les références existent
```python
# Récupérer les codes valides
contract_types = db.query(InsuranceContractTypeModel).all()
if not contract_types:
    raise Exception("Aucun type de contrat disponible")
```

### Rollback automatique

Le script utilise des transactions :
```python
try:
    # Opérations de création
    db.commit()
except Exception as e:
    db.rollback()
    print(f"❌ Erreur: {e}")
```

## 🧪 Tests

### Test de génération
```bash
# Générer 1 client et vérifier
python3 generate_client_data.py --clean --create --count 1

# Compter les enregistrements
python3 -c "
from app.database import SessionLocal
from app.models import ClientModel
db = SessionLocal()
count = db.query(ClientModel).count()
print(f'Clients créés: {count}')
assert count == 1, 'Échec de la génération'
print('✅ Test OK')
"
```

### Test de nettoyage
```bash
# Créer puis nettoyer
python3 generate_client_data.py --create --count 5
python3 generate_client_data.py --clean

# Vérifier que tout est supprimé
python3 -c "
from app.database import SessionLocal
from app.models import ClientModel
db = SessionLocal()
count = db.query(ClientModel).count()
assert count == 0, 'Le nettoyage a échoué'
print('✅ Nettoyage OK')
"
```

## 📝 Bonnes pratiques

### 1. Toujours nettoyer avant de générer
```bash
python3 generate_client_data.py --clean --create --count 10
```

### 2. Générer un nombre raisonnable de données
- **Développement** : 5-10 clients
- **Tests** : 50-100 clients
- **Démonstration** : 20-30 clients

### 3. Vérifier les données générées
```bash
# Après génération, vérifier via l'API
curl -s "http://127.0.0.1:8000/clients/" | python3 -m json.tool | head -20
```

### 4. Sauvegarder avant de nettoyer
Si vous avez des données importantes, faire un dump SQL avant :
```bash
pg_dump -h gautiersa.fr -U autogere -d dwh -t fake_clients > backup.sql
```

## 🔄 Évolutions futures

### Améliorations possibles

1. **Options avancées**
   - `--type` : Forcer le type de client (particulier/entreprise)
   - `--with-sites` : Forcer la création de chantiers
   - `--contracts-per-client N` : Nombre fixe de contrats

2. **Validation des données**
   - Vérifier la cohérence des dates
   - Valider les montants (franchise < montant assuré)
   - Contrôler les doublons

3. **Import/Export**
   - Export JSON des données générées
   - Import depuis un fichier JSON
   - Templates de données prédéfinies

4. **Scénarios prédéfinis**
   - Générer un portefeuille type
   - Créer des cas de test spécifiques
   - Simuler des évolutions temporelles

## 📚 Références

- [Faker Documentation](https://faker.readthedocs.io/en/master/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/14/orm/)
- [Faker Locales](https://faker.readthedocs.io/en/master/locales.html)
- [French Locale Providers](https://faker.readthedocs.io/en/master/locales/fr_FR.html)
