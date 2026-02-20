-- Données de démonstration (optionnelles)
-- Ce fichier est exécuté UNE SEULE FOIS à la création de la base.
-- Les tables sont créées automatiquement par SQLAlchemy au démarrage du backend.
-- Vous pouvez décommenter les INSERT ci-dessous pour avoir des données d'exemple.

/*
INSERT INTO invoices (date, client, number, desc, amount_ht, vat_rate, is_paid) VALUES
  ('2025-01-10', 'Acme Corp',         'FA-2025-001', 'Développement web',     5000, 20,   true),
  ('2025-01-22', 'StartupXYZ',        'FA-2025-002', 'Consulting stratégie',  2000, 20,   true),
  ('2025-02-05', 'Restaurant Dupont', 'FA-2025-003', 'Conception menu',        800, 10,  false),
  ('2025-02-18', 'Acme Corp',         'FA-2025-004', 'Maintenance mensuelle', 1500, 20,   true),
  ('2025-03-03', 'BioFarm SAS',       'FA-2025-005', 'Packaging alimentaire', 1200,  5.5,false),
  ('2025-03-15', 'StartupXYZ',        'FA-2025-006', 'Formation équipe',      3000, 20,   true),
  ('2025-04-08', 'Mairie de Lyon',    'FA-2025-007', 'Application mobile',    8000, 20,   true)
ON CONFLICT DO NOTHING;

INSERT INTO expenses (date, supplier, number, desc, amount_ht, vat_rate, category) VALUES
  ('2025-01-05', 'Adobe Inc.',   'INV-CC-9801', 'Creative Cloud',      65,  20, 'Logiciel'),
  ('2025-01-08', 'SNCF',         'SNCF-123',    'Billet Paris-Lyon',   80,  10, 'Transport'),
  ('2025-02-02', 'OVH Cloud',    'OVH-FR-2511', 'Hébergement serveur', 30,  20, 'Logiciel'),
  ('2025-02-14', 'Fnac Pro',     'FNAC-7892',   'Écran 27 pouces',    350,  20, 'Matériel'),
  ('2025-03-12', 'SFR Business', 'SFR-B-44512', 'Forfait Pro',         45,  20, 'Téléphone')
ON CONFLICT DO NOTHING;
*/
