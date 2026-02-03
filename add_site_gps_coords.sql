-- Migration: Ajouter les coordonnées GPS aux chantiers
-- Date: 2026-02-03

-- Ajouter les colonnes latitude et longitude
ALTER TABLE fake_construction_sites 
ADD COLUMN IF NOT EXISTS latitude FLOAT,
ADD COLUMN IF NOT EXISTS longitude FLOAT;

-- Commentaires
COMMENT ON COLUMN fake_construction_sites.latitude IS 'Latitude GPS du chantier';
COMMENT ON COLUMN fake_construction_sites.longitude IS 'Longitude GPS du chantier';
