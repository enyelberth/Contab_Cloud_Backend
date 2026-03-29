-- ====================================================================
-- Contab Cloud - Core schema (PostgreSQL, SQL puro)
-- Multiempresa + roles/permisos por empresa
-- ====================================================================

BEGIN;

-- --------------------------------------------------------------------
-- 1) Catalogos de seguridad
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(60) NOT NULL UNIQUE,
    description TEXT,
    scope VARCHAR(20) NOT NULL DEFAULT 'company'
        CHECK (scope IN ('system', 'company')),
    is_assignable_to_client BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS permissions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    slug VARCHAR(120) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS role_permissions (
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id INTEGER NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

-- --------------------------------------------------------------------
-- 2) Empresas y sucursales
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS companies (
    id SERIAL PRIMARY KEY,
    legal_name VARCHAR(180) NOT NULL,
    trade_name VARCHAR(180),
    tax_id VARCHAR(30) NOT NULL UNIQUE,
    country VARCHAR(80) NOT NULL DEFAULT 'VE',
    accounting_email VARCHAR(150),
    phone VARCHAR(30),
    address TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'inactive', 'archived')),
    created_by INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS branches (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    address TEXT,
    phone VARCHAR(20),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- --------------------------------------------------------------------
-- 3) Usuarios globales (registro) y membresias por empresa
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    first_name VARCHAR(80),
    last_name VARCHAR(80),
    user_type VARCHAR(20) NOT NULL DEFAULT 'accountant'
        CHECK (user_type IN ('super_admin', 'accountant', 'client')),
    role_id INTEGER REFERENCES roles(id) ON DELETE RESTRICT,
    branch_id INTEGER REFERENCES branches(id) ON DELETE SET NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'inactive', 'suspended')),
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_companies_created_by_user'
    ) THEN
        ALTER TABLE companies
            ADD CONSTRAINT fk_companies_created_by_user
            FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS company_memberships (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE RESTRICT,
    is_primary_accountant BOOLEAN NOT NULL DEFAULT FALSE,
    access_level VARCHAR(20) NOT NULL DEFAULT 'full'
        CHECK (access_level IN ('full', 'limited', 'read_only')),
    status VARCHAR(20) NOT NULL DEFAULT 'active'
        CHECK (status IN ('pending', 'active', 'suspended', 'removed')),
    invited_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    invited_at TIMESTAMP WITH TIME ZONE,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (company_id, user_id)
);

-- --------------------------------------------------------------------
-- 4) Contactos de la empresa (clientes/proveedores/personas)
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS company_contacts (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    contact_type VARCHAR(20) NOT NULL
        CHECK (contact_type IN ('person', 'company')),
    full_name VARCHAR(180) NOT NULL,
    identification_number VARCHAR(40),
    email VARCHAR(120),
    phone VARCHAR(30),
    address TEXT,
    is_client BOOLEAN NOT NULL DEFAULT TRUE,
    is_supplier BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- --------------------------------------------------------------------
-- 5) Nucleo contable por empresa
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fiscal_periods (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    name VARCHAR(60) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'open'
        CHECK (status IN ('open', 'closed')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (company_id, name),
    CHECK (end_date >= start_date)
);

CREATE TABLE IF NOT EXISTS chart_accounts (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    code VARCHAR(20) NOT NULL,
    name VARCHAR(140) NOT NULL,
    account_type VARCHAR(20) NOT NULL
        CHECK (account_type IN ('asset', 'liability', 'equity', 'income', 'expense')),
    parent_account_id INTEGER REFERENCES chart_accounts(id) ON DELETE SET NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (company_id, code)
);

CREATE TABLE IF NOT EXISTS journal_entries (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    fiscal_period_id INTEGER REFERENCES fiscal_periods(id) ON DELETE SET NULL,
    entry_number VARCHAR(30) NOT NULL,
    entry_date DATE NOT NULL,
    description TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'draft'
        CHECK (status IN ('draft', 'posted', 'cancelled')),
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    posted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (company_id, entry_number)
);

CREATE TABLE IF NOT EXISTS journal_entry_lines (
    id SERIAL PRIMARY KEY,
    journal_entry_id INTEGER NOT NULL REFERENCES journal_entries(id) ON DELETE CASCADE,
    account_id INTEGER NOT NULL REFERENCES chart_accounts(id) ON DELETE RESTRICT,
    third_party_contact_id INTEGER REFERENCES company_contacts(id) ON DELETE SET NULL,
    detail TEXT,
    debit NUMERIC(18, 2) NOT NULL DEFAULT 0,
    credit NUMERIC(18, 2) NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CHECK (debit >= 0),
    CHECK (credit >= 0),
    CHECK (
        (debit > 0 AND credit = 0)
        OR (credit > 0 AND debit = 0)
    )
);

-- --------------------------------------------------------------------
-- 6) Soporte de moneda (compatibilidad con seed existente)
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS currencies (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10) NOT NULL UNIQUE,
    symbol VARCHAR(5),
    is_default BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS exchange_rates (
    id SERIAL PRIMARY KEY,
    currency_id INTEGER NOT NULL REFERENCES currencies(id) ON DELETE CASCADE,
    rate_value NUMERIC(18, 4) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CHECK (rate_value > 0)
);

-- --------------------------------------------------------------------
-- 7) Indices recomendados
-- --------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_branches_company_id ON branches(company_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
CREATE INDEX IF NOT EXISTS idx_memberships_company ON company_memberships(company_id);
CREATE INDEX IF NOT EXISTS idx_memberships_user ON company_memberships(user_id);
CREATE INDEX IF NOT EXISTS idx_contacts_company ON company_contacts(company_id);
CREATE INDEX IF NOT EXISTS idx_accounts_company ON chart_accounts(company_id);
CREATE INDEX IF NOT EXISTS idx_entries_company_date ON journal_entries(company_id, entry_date);
CREATE INDEX IF NOT EXISTS idx_lines_entry ON journal_entry_lines(journal_entry_id);

-- --------------------------------------------------------------------
-- 8) Roles base del negocio
-- --------------------------------------------------------------------
INSERT INTO roles (name, description, scope, is_assignable_to_client)
VALUES
    ('SUPER_ADMIN', 'Acceso total a toda la plataforma', 'system', FALSE),
    ('ADMIN_EMPRESA', 'Administra usuarios y configuracion de la empresa', 'company', FALSE),
    ('CONTADOR', 'Gestion contable diaria de la empresa', 'company', FALSE),
    ('CLIENTE_LECTURA', 'Solo puede ver balances y reportes', 'company', TRUE)
ON CONFLICT (name) DO NOTHING;

INSERT INTO permissions (name, slug)
VALUES
    ('Ver dashboard contable', 'dashboard.view'),
    ('Gestionar usuarios de empresa', 'company.users.manage'),
    ('Gestionar roles de empresa', 'company.roles.manage'),
    ('Crear asientos contables', 'journal_entries.create'),
    ('Publicar asientos contables', 'journal_entries.post'),
    ('Ver libro diario', 'journal_entries.view'),
    ('Ver balance general', 'reports.balance_sheet.view'),
    ('Ver estado de resultados', 'reports.income_statement.view'),
    ('Ver reportes contables', 'reports.view')
ON CONFLICT (slug) DO NOTHING;

-- SUPER_ADMIN: todos los permisos
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
CROSS JOIN permissions p
WHERE r.name = 'SUPER_ADMIN'
ON CONFLICT DO NOTHING;

-- ADMIN_EMPRESA: admin funcional por empresa
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
JOIN permissions p ON p.slug IN (
    'dashboard.view',
    'company.users.manage',
    'company.roles.manage',
    'journal_entries.create',
    'journal_entries.post',
    'journal_entries.view',
    'reports.balance_sheet.view',
    'reports.income_statement.view',
    'reports.view'
)
WHERE r.name = 'ADMIN_EMPRESA'
ON CONFLICT DO NOTHING;

-- CONTADOR: operacion contable
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
JOIN permissions p ON p.slug IN (
    'dashboard.view',
    'journal_entries.create',
    'journal_entries.post',
    'journal_entries.view',
    'reports.balance_sheet.view',
    'reports.income_statement.view',
    'reports.view'
)
WHERE r.name = 'CONTADOR'
ON CONFLICT DO NOTHING;

-- CLIENTE_LECTURA: solo visualizacion
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
JOIN permissions p ON p.slug IN (
    'reports.balance_sheet.view',
    'reports.income_statement.view',
    'reports.view'
)
WHERE r.name = 'CLIENTE_LECTURA'
ON CONFLICT DO NOTHING;

COMMIT;
