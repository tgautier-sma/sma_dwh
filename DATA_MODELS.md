# 📊 Documentation des Modèles de Données

## Vue d'ensemble

Le système gère 4 domaines principaux :
1. **Clients et leurs adresses**
2. **Contrats d'assurance et chantiers**
3. **Référentiels** (types, garanties, clauses, etc.)
4. **Réseau commercial** (commerciaux, visites clients, propositions d'assurance)

---

## 1️⃣ CLIENTS

### Table : `clients`
Informations sur les clients assurés.

**Champs principaux :**
- `id` (UUID) - Identifiant unique
- `client_number` (string, unique) - Numéro client (ex: CLI-2024-001)
- `client_type` (enum) - Type : particulier, entreprise, professionnel, promoteur, entite_publique

**Personne physique :**
- `civility`, `first_name`, `last_name`, `birth_date`

**Personne morale :**
- `company_name`, `legal_form`, `siret`, `siren`

**Contact :**
- `email`, `phone`, `mobile`, `website`

**Adresse principale :**
- `address_line1`, `address_line2`, `postal_code`, `city`, `country`

**Métadonnées :**
- `is_active`, `notes`, `created_at`, `updated_at`

---

### Table : `client_addresses`
Adresses multiples des clients (sièges sociaux, entrepôts, chantiers).

**Types d'adresses :**
- `siege_social` - Siège social (1 max)
- `entrepot` - Entrepôt (1 à 3 max)
- `chantier` - Chantier (1 à 10 max)

**Champs communs :**
- `address_type` (enum)
- `name` - Nom de l'adresse (ex: "Entrepôt Nord")
- `reference` - Référence interne
- `address_line1`, `address_line2`, `address_line3`
- `postal_code`, `city`, `department`, `region`, `country`
- `latitude`, `longitude` - Coordonnées GPS

**Spécifiques entrepôts :**
- `warehouse_surface_m2` - Surface en m²
- `warehouse_capacity` - Capacité
- `stored_materials` - Matériaux stockés

**Spécifiques chantiers :**
- `site_start_date`, `site_end_date` - Dates du chantier
- `site_status` - Statut (en_cours, termine, suspendu)

**Contact sur site :**
- `contact_name`, `contact_phone`, `contact_email`

**Métadonnées :**
- `display_order` - Ordre d'affichage
- `is_active`, `is_primary` - Adresse active/principale

---

## 2️⃣ CONTRATS & CHANTIERS

### Table : `client_contracts`
Contrats d'assurance construction.

**Identification :**
- `id` (UUID)
- `contract_number` (string, unique) - Ex: CONT-DO-2024-001
- `external_reference` - Référence externe (assureur)
- `contract_type_code` - Code du type (DO, RCD, TRC, etc.)

**Relations :**
- `client_id` → clients
- `construction_site_id` → construction_sites

**Statut :**
- `status` (enum) - brouillon, en_attente, actif, suspendu, resilie, expire

**Dates :**
- `issue_date` - Date d'émission
- `effective_date` - Date d'effet
- `expiry_date` - Date d'expiration
- `cancellation_date` - Date de résiliation

**Montants :**
- `insured_amount` - Montant assuré
- `annual_premium` - Prime annuelle
- `total_premium` - Prime totale
- `franchise_amount` - Franchise globale

**Durée :**
- `duration_years` - Durée (par défaut 10 ans)
- `is_renewable` - Tacite reconduction

**Garanties et clauses :**
- `selected_guarantees` (JSON) - Garanties sélectionnées avec paramètres
- `selected_clauses` (JSON) - Clauses applicables avec variables
- `specific_exclusions` (JSON) - Exclusions spécifiques
- `special_conditions` (text) - Conditions particulières

**Intervenants :**
- `broker_name`, `broker_code` - Courtier
- `underwriter` - Souscripteur

**Documents et notes :**
- `attached_documents` (JSON) - Références des documents
- `internal_notes`, `client_notes`

---

### Table : `construction_sites`
Chantiers et ouvrages assurés.

**Identification :**
- `site_reference` (string, unique) - Ex: CHANT-2024-001
- `site_name` - Nom du chantier

**Localisation :**
- `address_line1`, `address_line2`
- `postal_code`, `city`, `department`, `region`

**Caractéristiques :**
- `building_category_code` → ref_building_categories
- `work_category_code` → ref_work_categories

**Surface et dimensions :**
- `total_surface_m2`, `habitable_surface_m2`
- `num_floors` - Nombre d'étages
- `num_units` - Nombre de logements/lots

**Montants :**
- `construction_cost` - Coût construction HT
- `land_value` - Valeur du terrain
- `total_project_value` - Valeur totale du projet

**Dates :**
- `permit_date` - Date permis de construire
- `opening_date` - Date ouverture chantier
- `planned_completion_date` - Date fin prévue
- `actual_completion_date` - Date fin réelle
- `reception_date` - Date de réception des travaux

**Caractéristiques techniques :**
- `foundation_type` - Type de fondations
- `structure_type` - Type de structure
- `has_basement`, `has_swimming_pool`, `has_elevator`

**Risques :**
- `seismic_zone` (1-5) - Zone sismique
- `flood_zone` - Zone inondable
- `soil_study_done` - Étude de sol effectuée

---

### Table : `contract_history`
Historique des modifications de contrats.

**Champs :**
- `contract_id` → client_contracts
- `action` - Type de modification (create, update, status_change)
- `field_changed` - Champ modifié
- `old_value`, `new_value` - Anciennes/nouvelles valeurs
- `changed_by` - Utilisateur
- `changed_at` - Date de modification
- `comment` - Commentaire

---

## 3️⃣ RÉFÉRENTIELS

### Table : `ref_insurance_contract_types`
Types de contrats d'assurance construction.

**Champs :**
- `code` (string, unique) - DO, RCD, TRC, CNR, RCMO, PUC
- `name` - Nom complet
- `description` - Description détaillée
- `legal_reference` - Référence légale
- `is_mandatory` - Obligatoire ou non
- `is_active`

**Types par défaut :**
- **DO** - Dommage-Ouvrage (obligatoire)
- **RCD** - RC Décennale (obligatoire)
- **TRC** - Tous Risques Chantier
- **CNR** - Constructeur Non Réalisateur (obligatoire)
- **RCMO** - RC Maître d'Ouvrage
- **PUC** - Police Unique Chantier

---

### Table : `ref_guarantees`
Garanties d'assurance.

**Classification :**
- `code` (unique) - Ex: DO-DEC, RCD-DEC
- `name` - Nom de la garantie
- `category` (enum) - decennale, biennale, parfait_achevement, dommages, etc.
- `guarantee_type` (enum) - obligatoire, optionnelle, complementaire

**Lien avec contrat :**
- `contract_type_id` → ref_insurance_contract_types

**Durée :**
- `duration_years` - 1, 2, 10 ans...
- `duration_description`

**Paramètres par défaut :**
- `default_ceiling` - Plafond par défaut
- `default_franchise` - Franchise par défaut
- `franchise_type` - fixe, proportionnelle, indexée

**Légal :**
- `legal_reference` - Référence légale
- `legal_articles` (JSON) - Articles de loi

**Conditions :**
- `conditions` (JSON) - Conditions d'application
- `exclusions_default` (JSON) - Exclusions par défaut

---

### Table : `ref_contract_clauses`
Clauses contractuelles.

**Identification :**
- `code` (unique) - Ex: EXCL-001, FRAN-001
- `title` - Titre de la clause
- `content` (text) - Texte complet
- `category` (enum) - exclusion, limitation, franchise, condition, etc.

**Applicabilité :**
- `applies_to_contract_types` (JSON) - Codes des types de contrats
- `applies_to_guarantees` (JSON) - Codes des garanties

**Caractéristiques :**
- `is_mandatory` - Clause obligatoire
- `is_negotiable` - Clause négociable
- `priority_order` - Ordre de priorité

**Variables :**
- `variables` (JSON) - Variables personnalisables
  ```json
  {
    "montant_franchise": {
      "type": "float",
      "label": "Montant de la franchise",
      "default": 1500
    }
  }
  ```

**Catégories de clauses :**
- **exclusion** - Exclusions de garantie
- **limitation** - Limitations de garantie
- **franchise** - Franchises
- **condition** - Conditions d'application
- **declaration** - Obligations de déclaration
- **resiliation** - Conditions de résiliation
- **sinistre** - Gestion des sinistres
- **prime** - Modalités de prime
- **subrogation** - Subrogation et recours

---

### Table : `ref_building_categories`
Catégories de bâtiments.

**Champs :**
- `code` - HAB-IND, HAB-COL, COM, IND, etc.
- `name` - Nom de la catégorie
- `description`
- `risk_coefficient` - Coefficient de risque
- `technical_complexity` (1-5) - Complexité technique
- `applicable_guarantees` (JSON) - Garanties applicables

**Catégories par défaut :**
- HAB-IND - Habitation individuelle
- HAB-COL - Habitation collective
- COM - Commercial
- IND - Industriel
- AGR - Agricole
- ERP - Établissement Recevant du Public
- BUR - Bureaux
- MIX - Mixte
- IGH - Immeuble de Grande Hauteur
- OAR - Ouvrage d'art

---

### Table : `ref_work_categories`
Catégories de travaux.

**Champs :**
- `code` - CONST-NEUF, EXT, RENOV-L, etc.
- `name` - Nom de la catégorie
- `description`
- `parent_code` - Code parent (hiérarchie)
- `risk_level` (1-5) - Niveau de risque
- `requires_control` - Contrôle technique obligatoire
- `mandatory_guarantees` (JSON) - Garanties obligatoires
- `recommended_guarantees` (JSON) - Garanties recommandées

**Catégories par défaut :**
- CONST-NEUF - Construction neuve
- EXT - Extension
- RENOV-L - Rénovation légère
- RENOV-H - Rénovation lourde
- REHAB - Réhabilitation
- TRANSF - Transformation
- SURES - Surélévation
- SOUS-SOL - Travaux en sous-sol

---

### Table : `ref_professions`
Professions du bâtiment.

**Champs :**
- `code` - ARCHI, ING-STRUCT, MAC, etc.
- `name` - Nom de la profession
- `description`
- `category` - concepteur, realisateur, controleur, maitre_ouvrage
- `subcategory`
- `rc_decennale_required` - RC décennale obligatoire
- `rc_pro_required` - RC pro obligatoire
- `covered_activities` (JSON) - Activités couvertes
- `base_rate_coefficient` - Coefficient de tarification

**Professions par défaut :**
- Concepteurs : ARCHI, ING-STRUCT, ING-FLUID, ECO
- Contrôleurs : BC (bureau de contrôle), CSPS
- Réalisateurs : ENT-GEN, MAC, CHARP, COUV, PLOMB, ELEC, etc.
- Maîtres d'ouvrage : PROM, CMI

---

### Table : `ref_franchise_grids`
Grilles de franchises par type de garantie.

**Champs :**
- `code` (unique)
- `name`
- `guarantee_code` - Code de la garantie
- `contract_type_code` - Code du type de contrat
- `min_amount`, `max_amount`, `default_amount`
- `franchise_type` - fixe, proportionnelle, indexée
- `percentage` - Si proportionnelle
- `index_reference` - Si indexée (FFB, BT01, etc.)
- `conditions` (JSON)

---

### Table : `ref_exclusions`
Exclusions types pour les contrats.

**Champs :**
- `code` (unique)
- `title` - Titre de l'exclusion
- `description` - Description détaillée
- `category` - légale, contractuelle, technique
- `applies_to_guarantees` (JSON) - Garanties concernées
- `applies_to_contract_types` (JSON) - Types de contrats concernés
- `is_legal` - Exclusion légale non négociable
- `legal_reference`
- `can_be_racheted` - Peut être rachetée
- `rachat_conditions` - Conditions de rachat

**Exclusions par défaut :**
- EXC-USURE - Usure normale et vétusté
- EXC-INTENT - Dommages intentionnels
- EXC-GUERRE - Faits de guerre
- EXC-NUCLEAIRE - Risques nucléaires
- EXC-ESTH - Dommages purement esthétiques
- EXC-EQUIP-MOB - Équipements mobiliers
- EXC-POLLU - Pollution et contamination
- EXC-AMIANTE - Amiante préexistant
- EXC-TERR - Vice du sol
- EXC-RETRAIT - Retrait-gonflement des argiles

---

## 4️⃣ RÉSEAU COMMERCIAL

### Table : `sales_reps`
Commerciaux terrain assurant les visites clients.

**Champs principaux :**
- `id`, `employee_number` (unique) - Matricule (ex: COM-0001)
- `civility`, `first_name`, `last_name`
- `email`, `phone`, `mobile`
- `region` - Région commerciale de rattachement
- `agency` - Agence de rattachement
- `manager_name` - Manager
- `hire_date` - Date d'embauche
- `is_active`

---

### Table : `client_visits`
Visites terrain d'un commercial chez un client, avec compte rendu.

**Identification et relations :**
- `visit_number` (unique) - Ex: VIS-2025-000001
- `sales_rep_id` → sales_reps
- `client_id` → clients
- `address_id` → client_addresses (site visité, optionnel)

**Planification :**
- `visit_date`, `duration_minutes`
- `visit_type` (enum) - prospection, decouverte_besoins, suivi_contrat, renouvellement, gestion_sinistre, fidelisation, souscription
- `visit_status` (enum) - planifiee, realisee, annulee, reportee, absence_client

**Compte rendu de visite :**
- `objective` - Objectif de la visite
- `report_summary` - Compte rendu détaillé
- `topics_discussed` (JSON) - Sujets abordés
- `client_satisfaction` (1 à 5)
- `next_action`, `next_visit_date`

**Localisation :**
- `latitude`, `longitude`

---

### Table : `insurance_proposals`
Proposition d'assurance faite lors d'une visite, sur un produit du référentiel existant (DO, RCD, TRC, CNR, RCMO, PUC).

**Identification et relations :**
- `proposal_number` (unique) - Ex: PROP-2025-000001
- `visit_id` → client_visits (visite à l'origine de la proposition)
- `client_id` → clients
- `sales_rep_id` → sales_reps
- `construction_site_id` → construction_sites (optionnel)
- `contract_type_code` - Code produit du référentiel `ref_insurance_contract_types`

**Suivi commercial :**
- `proposal_date`, `validity_date`
- `status` (enum) - brouillon, envoyee, en_reflexion, acceptee, refusee, expiree, sans_suite
- `proposed_insured_amount`, `proposed_annual_premium`, `proposed_franchise`
- `selected_guarantees` (JSON)
- `rejection_reason`, `notes`

**Souscription :**
- `converted_contract_id` → client_contracts. Renseigné quand la proposition acceptée aboutit à la création effective d'un contrat.

---

### Liens de traçabilité sur `client_contracts`
Pour tracer l'origine commerciale d'une souscription, `client_contracts` porte désormais :
- `sales_rep_id` → sales_reps (commercial à l'origine de la souscription)
- `originating_visit_id` → client_visits (visite ayant conduit à la souscription)

---

## 🔗 Relations entre les tables

```
clients (1) -----> (*) client_addresses
clients (1) -----> (*) client_contracts
construction_sites (1) -----> (*) client_contracts
client_contracts (1) -----> (*) contract_history

ref_insurance_contract_types (1) -----> (*) ref_guarantees
ref_insurance_contract_types (1) -----> (*) client_contracts

ref_building_categories (1) -----> (*) construction_sites
ref_work_categories (1) -----> (*) construction_sites
ref_professions (1) -----> (*) clients (via profession_code)

sales_reps (1) -----> (*) client_visits
sales_reps (1) -----> (*) insurance_proposals
sales_reps (1) -----> (*) client_contracts (via sales_rep_id)
clients (1) -----> (*) client_visits
clients (1) -----> (*) insurance_proposals
client_visits (1) -----> (*) insurance_proposals
client_visits (1) -----> (*) client_contracts (via originating_visit_id)
insurance_proposals (1) -----> (0..1) client_contracts (via converted_contract_id)
```

---

## 📋 Format JSON des champs complexes

### `selected_guarantees` (dans client_contracts)
```json
[
  {
    "code": "DO-DEC",
    "ceiling": 1000000,
    "franchise": 5000,
    "included": true
  },
  {
    "code": "DO-EXIST",
    "ceiling": 500000,
    "franchise": 2500,
    "included": true
  }
]
```

### `selected_clauses` (dans client_contracts)
```json
[
  {
    "code": "FRAN-001",
    "variables": {
      "montant_franchise": 5000
    }
  },
  {
    "code": "LIMIT-001",
    "variables": {
      "plafond_sinistre": 5000000
    }
  }
]
```

---

Ce document détaille tous les modèles de données utilisés dans l'API.
Pour les utiliser, référez-vous aux exemples dans `api_examples.http`.
