# Nouvelle fonctionnalité : Option --type

## 📝 Description

Ajout d'une option `--type` au script [generate_client_data.py](generate_client_data.py) permettant de choisir le type de clients à générer.

## ✨ Fonctionnalité ajoutée

### Option --type

L'option `--type` accepte trois valeurs :

1. **`particulier`** : Génère uniquement des clients particuliers (personnes physiques)
   - Génère : civilité, prénom, nom, date de naissance
   - Exemple : M. Jean Dupont

2. **`entreprise`** : Génère uniquement des clients professionnels (entreprises)
   - Génère : raison sociale, forme juridique, SIRET/SIREN
   - Exemple : Dupont SARL

3. **`mixte`** (défaut) : Génère un mélange aléatoire de particuliers et d'entreprises
   - Environ 50% de chaque type

## 🔧 Utilisation

### Syntaxe

```bash
python3 generate_client_data.py --create --count <nombre> --type <type>
```

### Exemples

#### Créer 5 particuliers uniquement
```bash
python3 generate_client_data.py --clean --create --count 5 --type particulier
```

**Résultat :**
```
📦 Création de 5 client(s) particuliers avec toutes leurs relations...

Client 1/5:
  ✓ Client créé: CLI7175 - Jérôme Thomas
  ✓ 3 adresse(s) créée(s)
  ✓ 2 chantier(s) créé(s)
  ✓ 3 contrat(s) créé(s) avec historique
```

#### Créer 3 entreprises uniquement
```bash
python3 generate_client_data.py --clean --create --count 3 --type entreprise
```

**Résultat :**
```
📦 Création de 3 client(s) entreprises avec toutes leurs relations...

Client 1/3:
  ✓ Client créé: CLI5417 - Rolland SARL
  ✓ 2 adresse(s) créée(s)
  ✓ 1 chantier(s) créé(s)
  ✓ 3 contrat(s) créé(s) avec historique
```

#### Créer un mélange (mode par défaut)
```bash
python3 generate_client_data.py --create --count 10
# ou explicitement :
python3 generate_client_data.py --create --count 10 --type mixte
```

**Résultat :**
```
📦 Création de 10 client(s) (particuliers et entreprises) avec toutes leurs relations...
```

### Scénario complet

```bash
# Étape 1 : Créer 3 particuliers
python3 generate_client_data.py --clean --create --count 3 --type particulier

# Étape 2 : Ajouter 2 entreprises
python3 generate_client_data.py --create --count 2 --type entreprise

# Résultat : 3 particuliers + 2 entreprises = 5 clients au total
```

## 🎯 Cas d'usage

### 1. Tests spécifiques aux particuliers
Utile pour tester des fonctionnalités propres aux personnes physiques :
```bash
python3 generate_client_data.py --clean --create --count 10 --type particulier
```

### 2. Tests spécifiques aux entreprises
Utile pour tester des fonctionnalités propres aux entreprises (SIRET, forme juridique, etc.) :
```bash
python3 generate_client_data.py --clean --create --count 5 --type entreprise
```

### 3. Tests réalistes avec données mixtes
Simule un portefeuille client réaliste avec un mélange :
```bash
python3 generate_client_data.py --clean --create --count 50 --type mixte
```

### 4. Démonstrations ciblées
Pour des démonstrations ou formations :
```bash
# Préparer une démo avec uniquement des entreprises
python3 generate_client_data.py --clean --create --count 5 --type entreprise
```

## 🔍 Vérification

### Vérifier les types de clients créés

```bash
curl -s "http://127.0.0.1:8000/clients/" | python3 -c "
import sys, json
clients = json.load(sys.stdin)
particuliers = [c for c in clients if c['client_type'] == 'particulier']
entreprises = [c for c in clients if c['client_type'] == 'professionnel']

print(f'Particuliers: {len(particuliers)}')
print(f'Entreprises: {len(entreprises)}')
print(f'Total: {len(clients)}')
"
```

### Afficher le détail

```bash
curl -s "http://127.0.0.1:8000/clients/" | python3 -c "
import sys, json
clients = json.load(sys.stdin)

print('\\n📋 Particuliers:')
for c in clients:
    if c['client_type'] == 'particulier':
        print(f\"  - {c['client_number']}: {c.get('first_name', '')} {c.get('last_name', '')}\")

print('\\n🏢 Entreprises:')
for c in clients:
    if c['client_type'] == 'professionnel':
        print(f\"  - {c['client_number']}: {c.get('company_name', 'N/A')}\")
"
```

## 💻 Implémentation technique

### Modifications apportées

1. **Fonction `generate_client`** : Ajout du paramètre `client_type`
   ```python
   def generate_client(db: Session, client_number: str = None, client_type: str = None) -> ClientModel:
       if client_type == 'entreprise':
           is_company = True
       elif client_type == 'particulier':
           is_company = False
       else:
           is_company = random.choice([True, False])
   ```

2. **Fonction `create_complete_client`** : Propagation du paramètre
   ```python
   def create_complete_client(db: Session, verbose: bool = False, client_type: str = None) -> ClientModel:
       client = generate_client(db, client_type=client_type)
   ```

3. **Parser d'arguments** : Ajout de l'option `--type`
   ```python
   parser.add_argument(
       "--type",
       type=str,
       choices=["particulier", "entreprise", "mixte"],
       default="mixte",
       help="Type de clients à créer"
   )
   ```

4. **Boucle de création** : Utilisation du paramètre
   ```python
   if args.type == "mixte":
       client_type = None  # Aléatoire
   else:
       client_type = args.type
   
   client = create_complete_client(db, verbose=True, client_type=client_type)
   ```

## 📊 Tests de validation

### Test 1 : Particuliers uniquement
```bash
python3 generate_client_data.py --clean --create --count 3 --type particulier
# Résultat attendu : 3 clients de type "particulier"
```

**✅ Validé** : Tous les clients créés sont des particuliers avec prénom, nom, civilité.

### Test 2 : Entreprises uniquement
```bash
python3 generate_client_data.py --clean --create --count 2 --type entreprise
# Résultat attendu : 2 clients de type "professionnel"
```

**✅ Validé** : Tous les clients créés sont des entreprises avec raison sociale, SIRET/SIREN.

### Test 3 : Mode mixte
```bash
python3 generate_client_data.py --clean --create --count 10 --type mixte
# Résultat attendu : Mélange aléatoire de particuliers et entreprises
```

**✅ Validé** : Mix aléatoire obtenu (ex: 6 particuliers + 4 entreprises).

### Test 4 : Compatibilité ascendante
```bash
python3 generate_client_data.py --create --count 5
# Sans --type, doit utiliser "mixte" par défaut
```

**✅ Validé** : Comportement par défaut maintenu.

## 📚 Documentation mise à jour

Les fichiers suivants ont été mis à jour :

1. [generate_client_data.py](generate_client_data.py) : En-tête avec exemples d'utilisation
2. [README.md](README.md) : Section "Génération de données de test" avec exemples
3. [TESTS.md](TESTS.md) : Ajout d'exemples d'utilisation de l'option --type
4. Ce fichier : [FEATURE_TYPE_OPTION.md](FEATURE_TYPE_OPTION.md)

## 🎉 Résumé

L'option `--type` permet maintenant de :
- ✅ Créer uniquement des particuliers (`--type particulier`)
- ✅ Créer uniquement des entreprises (`--type entreprise`)
- ✅ Créer un mélange aléatoire (`--type mixte` ou par défaut)
- ✅ Combiner avec les autres options (`--clean`, `--count`)
- ✅ Maintenir la compatibilité avec les scripts existants

Cette fonctionnalité facilite les tests ciblés et la création de jeux de données spécifiques selon les besoins.

---

**Date d'ajout** : 2 février 2026  
**Version** : 1.1.0  
**Statut** : ✅ Opérationnel et testé
