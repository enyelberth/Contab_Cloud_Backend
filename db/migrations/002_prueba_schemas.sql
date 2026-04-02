-- ====================================================================
-- Migración 002: Schemas por empresa + tabla de prueba
--
-- Concepto: cada empresa tiene su propio schema de PostgreSQL.
-- Las tablas contables (chart_accounts, journal_entries, etc.)
-- se replicarán en cada schema, aislando los datos por empresa.
-- Esta migración crea 2 schemas de prueba para demostrar el switch.
-- ====================================================================

BEGIN;

-- --------------------------------------------------------------------
-- Segunda empresa de prueba (para tener empresa_1 y empresa_2)
-- --------------------------------------------------------------------
INSERT INTO companies (legal_name, trade_name, tax_id, country, accounting_email, status, created_by)
SELECT
    'Constructora Test, C.A.',
    'Constructora Test',
    'J-50000002-2',
    'VE',
    'contabilidad@constructora-test.com',
    'active',
    u.id
FROM users u
WHERE u.email = 'contador@empresa-demo.com'
  AND NOT EXISTS (SELECT 1 FROM companies WHERE tax_id = 'J-50000002-2');

-- --------------------------------------------------------------------
-- Schema empresa_1 (Inversiones Demo, C.A.)
-- --------------------------------------------------------------------
CREATE SCHEMA IF NOT EXISTS empresa_1;

CREATE TABLE IF NOT EXISTS empresa_1.prueba (
    id          SERIAL PRIMARY KEY,
    nombre      VARCHAR(100) NOT NULL,
    descripcion TEXT,
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO empresa_1.prueba (nombre, descripcion)
SELECT 'Asiento de apertura', 'Balance de apertura ejercicio 2026'
WHERE NOT EXISTS (SELECT 1 FROM empresa_1.prueba WHERE nombre = 'Asiento de apertura');

INSERT INTO empresa_1.prueba (nombre, descripcion)
SELECT 'Venta de mercancia', 'Factura #001 — Cliente ABC, C.A.'
WHERE NOT EXISTS (SELECT 1 FROM empresa_1.prueba WHERE nombre = 'Venta de mercancia');

-- --------------------------------------------------------------------
-- Schema empresa_2 (Constructora Test, C.A.)
-- --------------------------------------------------------------------
CREATE SCHEMA IF NOT EXISTS empresa_2;

CREATE TABLE IF NOT EXISTS empresa_2.prueba (
    id          SERIAL PRIMARY KEY,
    nombre      VARCHAR(100) NOT NULL,
    descripcion TEXT,
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO empresa_2.prueba (nombre, descripcion)
SELECT 'Compra de materiales', 'Proveedor XYZ — Cemento y acero lote #05'
WHERE NOT EXISTS (SELECT 1 FROM empresa_2.prueba WHERE nombre = 'Compra de materiales');

INSERT INTO empresa_2.prueba (nombre, descripcion)
SELECT 'Nomina quincenal', 'Pago de personal obra norte — 15/03/2026'
WHERE NOT EXISTS (SELECT 1 FROM empresa_2.prueba WHERE nombre = 'Nomina quincenal');

COMMIT;
