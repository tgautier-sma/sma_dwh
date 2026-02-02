# Tests et Exemples d'utilisation

Ce document présente des exemples concrets d'utilisation de l'API et du script de génération de données.

## 🎯 Scénarios de test

### 1. Générer des données de test

#### Nettoyer et créer 5 clients
```bash
python3 generate_client_data.py --clean --create --count 5
```

Résultat attendu :
- 5 clients créés (particuliers)
- 5-15 adresses (1-3 par client)
- 2-4 chantiers (environ 50% des clients)
- 5-20 contrats (1-4 par client)
- 10-100 entrées d'historique (1-5 par contrat)

#### Ajouter 3 clients supplémentaires (sans nettoyer)
```bash
python3 generate_client_data.py --create --count 3
```

#### Créer uniquement des particuliers
```bash
python3 generate_client_data.py --create --count 5 --type particulier
```

#### Créer uniquement des entreprises
```bash
python3 generate_client_data.py --create --count 3 --type entreprise
```

#### Créer un mélange de particuliers et d'entreprises
```bash
python3 generate_client_data.py --create --count 10 --type mixte
```

### 2. Consulter les clients

#### Lister tous les clients
```bash
curl -s "http://127.0.0.1:8000/clients/" | python3 -m json.tool
```

#### Obtenir un client spécifique
```bash
curl -s "http://127.0.0.1:8000/clients/11" | python3 -m json.tool
```

#### Obtenir toutes les informations d'un client (relations complètes)
```bash
curl -s "http://127.0.0.1:8000/clients/11/full" | python3 -m json.tool
```

Informations retournées :
- Données client complètes
- Liste de toutes les adresses
- Liste de tous les contrats avec :
  - Chantier associé (si applicable)
  - Garanties sélectionnées
  - Clauses spécifiques
  - Historique complet des modifications
- Statistiques agrégées :
  - Nombre d'adresses
  - Nombre de contrats (total et actifs)
  - Montant total assuré
  - Prime annuelle totale

### 3. Rechercher des clients

#### Par numéro de client (exact)
```bash
curl -s "http://127.0.0.1:8000/clients/search?query=CLI1751" | python3 -m json.tool
```

#### Par nom (recherche phonétique)
```bash
# Recherche "Pottier"
curl -s "http://127.0.0.1:8000/clients/search?query=pottier" | python3 -m json.tool

# Recherche "Fontaine"
curl -s "http://127.0.0.1:8000/clients/search?query=fontaine" | python3 -m json.tool

# La recherche phonétique fonctionne aussi avec des fautes de frappe
curl -s "http://127.0.0.1:8000/clients/search?query=potier" | python3 -m json.tool
```

### 4. Statistiques et analyse

#### Compter les clients
```bash
curl -s "http://127.0.0.1:8000/clients/" | python3 -c "import sys, json; print(f'Total clients: {len(json.load(sys.stdin))}')"
```

#### Afficher un résumé des clients
```bash
curl -s "http://127.0.0.1:8000/clients/" | python3 -c "
import sys, json
clients = json.load(sys.stdin)
print(f'Total: {len(clients)} client(s)')
for c in clients:
    name = c.get('company_name') or f\"{c.get('first_name', '')} {c.get('last_name', '')}\"
    print(f'  - {c[\"client_number\"]}: {name} ({c[\"client_type\"]})')
"
```

#### Statistiques d'un client
```bash
curl -s "http://127.0.0.1:8000/clients/11/full" | python3 -c "
import sys, json
d = json.load(sys.stdin)
c = d['client']
s = d['stats']
name = c.get('company_name') or f\"{c.get('first_name', '')} {c.get('last_name', '')}\"
print(f'Client: {c[\"client_number\"]} - {name}')
print(f'Adresses: {s[\"total_addresses\"]}')
print(f'Contrats: {s[\"total_contracts\"]} ({s[\"active_contracts\"]} actifs)')
print(f'Total assuré: {s[\"total_insured_amount\"]:,.2f} €')
print(f'Prime annuelle: {s[\"total_annual_premium\"]:,.2f} €')
"
```

## 📊 Exemples de résultats

### Génération de données (5 clients)

```
✅ Tous les clients et données associées ont été supprimés

📦 Création de 5 client(s) avec toutes leurs relations...

Client 1/5:
  ✓ Client créé: CLI1751 - Françoise Pottier
  ✓ 2 adresse(s) créée(s)
  ✓ 1 chantier(s) créé(s)
  ✓ 2 contrat(s) créé(s) avec historique

Client 2/5:
  ✓ Client créé: CLI3357 - Susan Fontaine
  ✓ 2 adresse(s) créée(s)
  ✓ 1 chantier(s) créé(s)
  ✓ 4 contrat(s) créé(s) avec historique

...

============================================================
📊 RÉSUMÉ DE LA BASE DE DONNÉES
============================================================
  Clients:              5
  Adresses:             9
  Chantiers:            4
  Contrats:             13
  Historiques:          38
============================================================
✅ Génération terminée avec succès
```

### Liste des clients

```json
[
    {
        "id": 11,
        "client_number": "CLI1751",
        "client_type": "particulier",
        "first_name": "Françoise",
        "last_name": "Pottier",
        "email": "epinto@example.net",
        "phone": "+33(0)56378853"
    },
    {
        "id": 12,
        "client_number": "CLI3357",
        "client_type": "particulier",
        "first_name": "Susan",
        "last_name": "Fontaine",
        "email": "dupontlucy@example.net",
        "phone": "0214226537"
    }
]
```

### Informations complètes d'un client

```json
{
    "client": {
        "id": 11,
        "client_number": "CLI1751",
        "first_name": "Françoise",
        "last_name": "Pottier",
        "birth_date": "1993-10-01",
        "email": "epinto@example.net"
    },
    "addresses": [
        {
            "address_type": "siege_social",
            "address_line1": "62, rue de Denis",
            "postal_code": "23468",
            "city": "Dupréboeuf",
            "is_primary": true
        },
        {
            "address_type": "chantier",
            "address_line1": "41, rue de Pelletier",
            "postal_code": "77405",
            "city": "HoareauBourg"
        }
    ],
    "contracts": [
        {
            "contract_number": "CNT573827",
            "contract_type_code": "TRC",
            "status": "brouillon",
            "insured_amount": 5295845.0,
            "annual_premium": 17562.42,
            "construction_site": null,
            "selected_guarantees": [
                {
                    "code": "GAR_TRC_00",
                    "name": "Garantie retour",
                    "ceiling": 912520,
                    "franchise": 1315,
                    "included": true
                }
            ],
            "history": [
                {
                    "action": "renouvellement",
                    "changed_by": "USER965",
                    "changed_at": "2026-04-12T00:54:38.497139"
                }
            ]
        },
        {
            "contract_number": "CNT127533",
            "contract_type_code": "PUC",
            "status": "en_attente",
            "insured_amount": 6241166.0,
            "annual_premium": 20736.14,
            "construction_site": {
                "site_name": "Projet boulevard Roland Costa",
                "address_line1": "304, avenue Brigitte Bousquet",
                "city": "Humbertnec",
                "total_project_value": 3832260.0
            }
        }
    ],
    "stats": {
        "total_addresses": 2,
        "total_contracts": 2,
        "active_contracts": 0,
        "total_insured_amount": 11537011.0,
        "total_annual_premium": 38298.56
    }
}
```

### Recherche phonétique

Recherche de "pottier" :
```json
[
    {
        "client_number": "CLI1751",
        "first_name": "Françoise",
        "last_name": "Pottier",
        "email": "epinto@example.net"
    }
]
```

### Statistiques d'un client

```
Client: CLI3357 - Susan Fontaine
Adresses: 2
Contrats: 4 (0 actifs)
Total assuré: 18,021,019.00 €
Prime annuelle: 50,245.41 €
```

## 🔧 Scripts utiles

### Compter tous les éléments de la base

```bash
echo "Statistiques de la base de données:"
echo "- Clients: $(curl -s 'http://127.0.0.1:8000/clients/' | python3 -c 'import sys, json; print(len(json.load(sys.stdin)))')"
echo "- Types de contrats: $(curl -s 'http://127.0.0.1:8000/contract-types/' | python3 -c 'import sys, json; print(len(json.load(sys.stdin)))')"
echo "- Garanties: $(curl -s 'http://127.0.0.1:8000/guarantees/' | python3 -c 'import sys, json; print(len(json.load(sys.stdin)))')"
```

### Afficher les contrats d'un client

```bash
CLIENT_ID=11
curl -s "http://127.0.0.1:8000/clients/${CLIENT_ID}/full" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"Contrats de {data['client']['client_number']}:\")
for c in data['contracts']:
    print(f\"  - {c['contract_number']}: {c['contract_type_code']} - {c['status']}\")
    print(f\"    Montant assuré: {c['insured_amount']:,.2f} €\")
    print(f\"    Prime annuelle: {c['annual_premium']:,.2f} €\")
"
```

### Rechercher tous les clients dont le nom contient une chaîne

```bash
SEARCH_TERM="font"
curl -s "http://127.0.0.1:8000/clients/search?query=${SEARCH_TERM}" | python3 -c "
import sys, json
clients = json.load(sys.stdin)
if clients:
    print(f'Trouvé {len(clients)} client(s):')
    for c in clients:
        name = f\"{c.get('first_name', '')} {c.get('last_name', '')}\"
        print(f\"  - {c['client_number']}: {name}\")
else:
    print('Aucun client trouvé')
"
```

## 🧪 Tests de validation

### 1. Test de cohérence des données

Vérifier qu'un client a bien toutes ses relations :
```bash
python3 -c "
import requests
client = requests.get('http://127.0.0.1:8000/clients/11/full').json()
assert 'client' in client
assert 'addresses' in client
assert 'contracts' in client
assert 'stats' in client
assert len(client['addresses']) > 0
print('✅ Structure des données OK')
"
```

### 2. Test de la recherche phonétique

```bash
# Recherche exacte
RESULT1=$(curl -s "http://127.0.0.1:8000/clients/search?query=pottier" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))")

# Recherche avec faute
RESULT2=$(curl -s "http://127.0.0.1:8000/clients/search?query=potier" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))")

if [ "$RESULT1" -eq "$RESULT2" ]; then
    echo "✅ Recherche phonétique OK"
else
    echo "❌ Problème de recherche phonétique"
fi
```

### 3. Test de génération de données

```bash
# Générer 1 client
python3 generate_client_data.py --clean --create --count 1 > /dev/null 2>&1

# Vérifier qu'il a bien été créé
COUNT=$(curl -s "http://127.0.0.1:8000/clients/" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))")

if [ "$COUNT" -eq "1" ]; then
    echo "✅ Génération de données OK"
else
    echo "❌ Problème de génération de données"
fi
```

## 📝 Notes

- Les timestamps sont en UTC
- Les montants sont en euros (€)
- Les codes postaux français sont à 5 chiffres
- Les numéros de téléphone sont au format français
- Les SIRET sont à 14 chiffres (pour les entreprises)
- Les SIREN sont à 9 chiffres (pour les entreprises)

## 🚀 Performance

Sur une base de 100 clients :
- Liste des clients : < 100ms
- Détails d'un client : < 50ms
- Informations complètes (full) : < 200ms
- Recherche phonétique : < 150ms
- Génération d'un client : ~1s

## 🔍 Débogage

### Logs du serveur

```bash
tail -f server.log
```

### Vérifier que le serveur répond

```bash
curl -s "http://127.0.0.1:8000/" && echo "✅ Serveur OK" || echo "❌ Serveur HS"
```

### Tester la connexion à la base de données

```bash
python3 -c "
from app.database import SessionLocal
try:
    db = SessionLocal()
    db.execute('SELECT 1')
    print('✅ Base de données OK')
except Exception as e:
    print(f'❌ Erreur DB: {e}')
"
```
