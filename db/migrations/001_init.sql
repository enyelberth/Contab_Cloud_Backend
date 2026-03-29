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
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS permissions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    slug VARCHAR(120) NOT NULL UNIQUE,
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS role_permissions (
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id INTEGER NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE IF NOT EXISTS role_delegation_rules (
    id SERIAL PRIMARY KEY,
    manager_role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    target_role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    can_assign_role BOOLEAN NOT NULL DEFAULT FALSE,
    can_grant_permissions BOOLEAN NOT NULL DEFAULT FALSE,
    scope VARCHAR(20) NOT NULL DEFAULT 'company'
        CHECK (scope IN ('system', 'company')),
    UNIQUE (manager_role_id, target_role_id)
);

CREATE TABLE IF NOT EXISTS app_modules (
    id SERIAL PRIMARY KEY,
    module_key VARCHAR(60) NOT NULL UNIQUE,
    name VARCHAR(120) NOT NULL,
    icon VARCHAR(60),
    route VARCHAR(200),
    sort_order INTEGER NOT NULL DEFAULT 100,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS frontend_menus (
    id SERIAL PRIMARY KEY,
    menu_key VARCHAR(80) NOT NULL UNIQUE,
    module_id INTEGER NOT NULL REFERENCES app_modules(id) ON DELETE CASCADE,
    parent_menu_id INTEGER REFERENCES frontend_menus(id) ON DELETE CASCADE,
    label VARCHAR(120) NOT NULL,
    path VARCHAR(200) NOT NULL,
    icon VARCHAR(60),
    sort_order INTEGER NOT NULL DEFAULT 100,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS role_menu_access (
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    menu_id INTEGER NOT NULL REFERENCES frontend_menus(id) ON DELETE CASCADE,
    can_view BOOLEAN NOT NULL DEFAULT FALSE,
    can_create BOOLEAN NOT NULL DEFAULT FALSE,
    can_update BOOLEAN NOT NULL DEFAULT FALSE,
    can_delete BOOLEAN NOT NULL DEFAULT FALSE,
    can_assign_permissions BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (role_id, menu_id)
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
    deleted_at TIMESTAMP WITH TIME ZONE,
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
    deleted_at TIMESTAMP WITH TIME ZONE,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (company_id, user_id)
);

CREATE TABLE IF NOT EXISTS auth_refresh_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL,
    jti VARCHAR(80) NOT NULL UNIQUE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    revoked_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    replaced_by_jti VARCHAR(80)
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGSERIAL PRIMARY KEY,
    actor_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    company_id INTEGER REFERENCES companies(id) ON DELETE SET NULL,
    module VARCHAR(60) NOT NULL,
    action VARCHAR(20) NOT NULL,
    entity_type VARCHAR(80) NOT NULL,
    entity_id VARCHAR(80),
    before_data JSONB,
    after_data JSONB,
    ip_address VARCHAR(64),
    endpoint VARCHAR(255),
    http_method VARCHAR(10),
    request_id VARCHAR(80),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE roles ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE permissions ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE company_memberships ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS ip_address VARCHAR(64);
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS endpoint VARCHAR(255);
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS http_method VARCHAR(10);
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS request_id VARCHAR(80);

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
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON auth_refresh_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_jti ON auth_refresh_tokens(jti);
CREATE INDEX IF NOT EXISTS idx_audit_logs_company_id ON audit_logs(company_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_actor_user_id ON audit_logs(actor_user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_request_id ON audit_logs(request_id);
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
    ('Ver empresas', 'companies.view'),
    ('Crear empresas', 'companies.create'),
    ('Editar empresas', 'companies.update'),
    ('Eliminar empresas', 'companies.delete'),
    ('Asignar permisos en empresas', 'companies.assign_permissions'),
    ('Ver usuarios de empresa', 'users.view'),
    ('Crear usuarios de empresa', 'users.create'),
    ('Editar usuarios de empresa', 'users.update'),
    ('Eliminar usuarios de empresa', 'users.delete'),
    ('Asignar permisos de usuarios', 'users.assign_permissions'),
    ('Ver contactos', 'contacts.view'),
    ('Crear contactos', 'contacts.create'),
    ('Editar contactos', 'contacts.update'),
    ('Eliminar contactos', 'contacts.delete'),
    ('Ver catalogo de cuentas', 'accounts.view'),
    ('Crear cuentas contables', 'accounts.create'),
    ('Editar cuentas contables', 'accounts.update'),
    ('Eliminar cuentas contables', 'accounts.delete'),
    ('Gestionar usuarios de empresa', 'company.users.manage'),
    ('Gestionar roles de empresa', 'company.roles.manage'),
    ('Crear asientos contables', 'journal_entries.create'),
    ('Editar asientos contables', 'journal_entries.update'),
    ('Eliminar asientos contables', 'journal_entries.delete'),
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
    'companies.view',
    'companies.create',
    'companies.update',
    'users.view',
    'users.create',
    'users.update',
    'users.delete',
    'users.assign_permissions',
    'contacts.view',
    'contacts.create',
    'contacts.update',
    'contacts.delete',
    'accounts.view',
    'accounts.create',
    'accounts.update',
    'accounts.delete',
    'company.users.manage',
    'company.roles.manage',
    'journal_entries.create',
    'journal_entries.update',
    'journal_entries.delete',
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
    'companies.view',
    'users.view',
    'contacts.view',
    'contacts.create',
    'contacts.update',
    'accounts.view',
    'accounts.create',
    'accounts.update',
    'journal_entries.create',
    'journal_entries.update',
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

-- --------------------------------------------------------------------
-- 9) Reglas de delegacion entre roles (roles superiores)
-- --------------------------------------------------------------------
INSERT INTO role_delegation_rules (
    manager_role_id,
    target_role_id,
    can_assign_role,
    can_grant_permissions,
    scope
)
SELECT manager.id, target.id, TRUE, TRUE, 'system'
FROM roles manager
JOIN roles target ON TRUE
WHERE manager.name = 'SUPER_ADMIN'
ON CONFLICT (manager_role_id, target_role_id) DO UPDATE
SET can_assign_role = EXCLUDED.can_assign_role,
    can_grant_permissions = EXCLUDED.can_grant_permissions,
    scope = EXCLUDED.scope;

INSERT INTO role_delegation_rules (
    manager_role_id,
    target_role_id,
    can_assign_role,
    can_grant_permissions,
    scope
)
SELECT manager.id, target.id,
       TRUE,
       CASE WHEN target.name IN ('CONTADOR', 'CLIENTE_LECTURA') THEN TRUE ELSE FALSE END,
       'company'
FROM roles manager
JOIN roles target ON target.name IN ('CONTADOR', 'CLIENTE_LECTURA')
WHERE manager.name = 'ADMIN_EMPRESA'
ON CONFLICT (manager_role_id, target_role_id) DO UPDATE
SET can_assign_role = EXCLUDED.can_assign_role,
    can_grant_permissions = EXCLUDED.can_grant_permissions,
    scope = EXCLUDED.scope;

INSERT INTO role_delegation_rules (
    manager_role_id,
    target_role_id,
    can_assign_role,
    can_grant_permissions,
    scope
)
SELECT manager.id, target.id, TRUE, FALSE, 'company'
FROM roles manager
JOIN roles target ON target.name = 'CLIENTE_LECTURA'
WHERE manager.name = 'CONTADOR'
ON CONFLICT (manager_role_id, target_role_id) DO UPDATE
SET can_assign_role = EXCLUDED.can_assign_role,
    can_grant_permissions = EXCLUDED.can_grant_permissions,
    scope = EXCLUDED.scope;

-- --------------------------------------------------------------------
-- 10) Menus para frontend controlados por BD
-- --------------------------------------------------------------------
INSERT INTO app_modules (module_key, name, icon, route, sort_order, is_active)
VALUES
    ('dashboard', 'Dashboard', 'layout-dashboard', '/dashboard', 10, TRUE),
    ('companies', 'Empresas', 'building-2', '/companies', 20, TRUE),
    ('users', 'Usuarios y Roles', 'users', '/users', 30, TRUE),
    ('contacts', 'Contactos', 'contact-round', '/contacts', 40, TRUE),
    ('accounting', 'Contabilidad', 'book-open-text', '/accounting', 50, TRUE),
    ('reports', 'Reportes', 'bar-chart-3', '/reports', 60, TRUE)
ON CONFLICT (module_key) DO UPDATE
SET name = EXCLUDED.name,
    icon = EXCLUDED.icon,
    route = EXCLUDED.route,
    sort_order = EXCLUDED.sort_order,
    is_active = EXCLUDED.is_active;

INSERT INTO frontend_menus (menu_key, module_id, parent_menu_id, label, path, icon, sort_order, is_active)
SELECT 'menu.dashboard', m.id, NULL, 'Dashboard', '/dashboard', 'layout-dashboard', 10, TRUE
FROM app_modules m
WHERE m.module_key = 'dashboard'
ON CONFLICT (menu_key) DO UPDATE
SET module_id = EXCLUDED.module_id,
    label = EXCLUDED.label,
    path = EXCLUDED.path,
    icon = EXCLUDED.icon,
    sort_order = EXCLUDED.sort_order,
    is_active = EXCLUDED.is_active;

INSERT INTO frontend_menus (menu_key, module_id, parent_menu_id, label, path, icon, sort_order, is_active)
SELECT 'menu.companies', m.id, NULL, 'Empresas', '/companies', 'building-2', 20, TRUE
FROM app_modules m
WHERE m.module_key = 'companies'
ON CONFLICT (menu_key) DO UPDATE
SET module_id = EXCLUDED.module_id,
    label = EXCLUDED.label,
    path = EXCLUDED.path,
    icon = EXCLUDED.icon,
    sort_order = EXCLUDED.sort_order,
    is_active = EXCLUDED.is_active;

INSERT INTO frontend_menus (menu_key, module_id, parent_menu_id, label, path, icon, sort_order, is_active)
SELECT 'menu.users', m.id, NULL, 'Usuarios', '/users', 'users', 30, TRUE
FROM app_modules m
WHERE m.module_key = 'users'
ON CONFLICT (menu_key) DO UPDATE
SET module_id = EXCLUDED.module_id,
    label = EXCLUDED.label,
    path = EXCLUDED.path,
    icon = EXCLUDED.icon,
    sort_order = EXCLUDED.sort_order,
    is_active = EXCLUDED.is_active;

INSERT INTO frontend_menus (menu_key, module_id, parent_menu_id, label, path, icon, sort_order, is_active)
SELECT 'menu.contacts', m.id, NULL, 'Contactos', '/contacts', 'contact-round', 40, TRUE
FROM app_modules m
WHERE m.module_key = 'contacts'
ON CONFLICT (menu_key) DO UPDATE
SET module_id = EXCLUDED.module_id,
    label = EXCLUDED.label,
    path = EXCLUDED.path,
    icon = EXCLUDED.icon,
    sort_order = EXCLUDED.sort_order,
    is_active = EXCLUDED.is_active;

INSERT INTO frontend_menus (menu_key, module_id, parent_menu_id, label, path, icon, sort_order, is_active)
SELECT 'menu.accounting', m.id, NULL, 'Contabilidad', '/accounting/journal-entries', 'book-open-text', 50, TRUE
FROM app_modules m
WHERE m.module_key = 'accounting'
ON CONFLICT (menu_key) DO UPDATE
SET module_id = EXCLUDED.module_id,
    label = EXCLUDED.label,
    path = EXCLUDED.path,
    icon = EXCLUDED.icon,
    sort_order = EXCLUDED.sort_order,
    is_active = EXCLUDED.is_active;

INSERT INTO frontend_menus (menu_key, module_id, parent_menu_id, label, path, icon, sort_order, is_active)
SELECT 'menu.reports', m.id, NULL, 'Reportes', '/reports', 'bar-chart-3', 60, TRUE
FROM app_modules m
WHERE m.module_key = 'reports'
ON CONFLICT (menu_key) DO UPDATE
SET module_id = EXCLUDED.module_id,
    label = EXCLUDED.label,
    path = EXCLUDED.path,
    icon = EXCLUDED.icon,
    sort_order = EXCLUDED.sort_order,
    is_active = EXCLUDED.is_active;

-- Matriz de acceso por rol y menu (ver/crear/editar/eliminar/asignar)
INSERT INTO role_menu_access (role_id, menu_id, can_view, can_create, can_update, can_delete, can_assign_permissions)
SELECT r.id, m.id,
       TRUE,
       CASE WHEN r.name = 'CLIENTE_LECTURA' THEN FALSE ELSE TRUE END,
       CASE WHEN r.name = 'CLIENTE_LECTURA' THEN FALSE ELSE TRUE END,
       CASE WHEN r.name IN ('SUPER_ADMIN', 'ADMIN_EMPRESA') THEN TRUE ELSE FALSE END,
       CASE WHEN r.name IN ('SUPER_ADMIN', 'ADMIN_EMPRESA') THEN TRUE ELSE FALSE END
FROM roles r
JOIN frontend_menus m ON m.menu_key IN (
    'menu.dashboard',
    'menu.companies',
    'menu.users',
    'menu.contacts',
    'menu.accounting',
    'menu.reports'
)
WHERE r.name IN ('SUPER_ADMIN', 'ADMIN_EMPRESA', 'CONTADOR')
ON CONFLICT (role_id, menu_id) DO UPDATE
SET can_view = EXCLUDED.can_view,
    can_create = EXCLUDED.can_create,
    can_update = EXCLUDED.can_update,
    can_delete = EXCLUDED.can_delete,
    can_assign_permissions = EXCLUDED.can_assign_permissions;

INSERT INTO role_menu_access (role_id, menu_id, can_view, can_create, can_update, can_delete, can_assign_permissions)
SELECT r.id, m.id,
       TRUE, FALSE, FALSE, FALSE, FALSE
FROM roles r
JOIN frontend_menus m ON m.menu_key IN ('menu.dashboard', 'menu.reports')
WHERE r.name = 'CLIENTE_LECTURA'
ON CONFLICT (role_id, menu_id) DO UPDATE
SET can_view = EXCLUDED.can_view,
    can_create = EXCLUDED.can_create,
    can_update = EXCLUDED.can_update,
    can_delete = EXCLUDED.can_delete,
    can_assign_permissions = EXCLUDED.can_assign_permissions;

-- --------------------------------------------------------------------
-- 11) Datos de prueba (demo)
-- --------------------------------------------------------------------
INSERT INTO users (username, email, password_hash, first_name, last_name, user_type, role_id, status)
SELECT 'superadmin', 'superadmin@contabcloud.dev',
       '$2b$12$abcdefghijklmnopqrstuvABCDEFGHIJKLMNOpqrstuv123456',
       'Super', 'Admin', 'super_admin', r.id, 'active'
FROM roles r
WHERE r.name = 'SUPER_ADMIN'
ON CONFLICT (email) DO NOTHING;

INSERT INTO users (username, email, password_hash, first_name, last_name, user_type, role_id, status)
SELECT 'contador.principal', 'contador@empresa-demo.com',
       '$2b$12$abcdefghijklmnopqrstuvABCDEFGHIJKLMNOpqrstuv123456',
       'Ana', 'Contable', 'accountant', r.id, 'active'
FROM roles r
WHERE r.name = 'ADMIN_EMPRESA'
ON CONFLICT (email) DO NOTHING;

INSERT INTO users (username, email, password_hash, first_name, last_name, user_type, role_id, status)
SELECT 'contador.asistente', 'asistente@empresa-demo.com',
       '$2b$12$abcdefghijklmnopqrstuvABCDEFGHIJKLMNOpqrstuv123456',
       'Luis', 'Asistente', 'accountant', r.id, 'active'
FROM roles r
WHERE r.name = 'CONTADOR'
ON CONFLICT (email) DO NOTHING;

INSERT INTO users (username, email, password_hash, first_name, last_name, user_type, role_id, status)
SELECT 'cliente.lectura', 'cliente@empresa-demo.com',
       '$2b$12$abcdefghijklmnopqrstuvABCDEFGHIJKLMNOpqrstuv123456',
       'Maria', 'Cliente', 'client', r.id, 'active'
FROM roles r
WHERE r.name = 'CLIENTE_LECTURA'
ON CONFLICT (email) DO NOTHING;

INSERT INTO companies (
    legal_name,
    trade_name,
    tax_id,
    country,
    accounting_email,
    phone,
    address,
    status,
    created_by
)
SELECT 'Inversiones Demo, C.A.', 'Empresa Demo', 'J-50000001-1', 'VE',
       'contabilidad@empresa-demo.com', '+58-251-0000000',
       'Av. Principal, Barquisimeto', 'active', u.id
FROM users u
WHERE u.email = 'contador@empresa-demo.com'
  AND NOT EXISTS (SELECT 1 FROM companies c WHERE c.tax_id = 'J-50000001-1');

INSERT INTO branches (company_id, name, address, phone, is_active)
SELECT c.id, 'Sede Principal', 'Centro Empresarial Demo', '+58-251-1111111', TRUE
FROM companies c
WHERE c.tax_id = 'J-50000001-1'
  AND NOT EXISTS (
    SELECT 1
    FROM branches b
    WHERE b.company_id = c.id AND b.name = 'Sede Principal'
  );

INSERT INTO company_memberships (
    company_id,
    user_id,
    role_id,
    is_primary_accountant,
    access_level,
    status,
    invited_by,
    invited_at
)
SELECT c.id, u.id, r.id,
       CASE WHEN u.email = 'contador@empresa-demo.com' THEN TRUE ELSE FALSE END,
       CASE WHEN r.name = 'CLIENTE_LECTURA' THEN 'read_only' ELSE 'full' END,
       'active', inviter.id, CURRENT_TIMESTAMP
FROM companies c
JOIN users inviter ON inviter.email = 'contador@empresa-demo.com'
JOIN users u ON u.email IN (
    'contador@empresa-demo.com',
    'asistente@empresa-demo.com',
    'cliente@empresa-demo.com'
)
JOIN roles r ON r.id = u.role_id
WHERE c.tax_id = 'J-50000001-1'
ON CONFLICT (company_id, user_id) DO UPDATE
SET role_id = EXCLUDED.role_id,
    is_primary_accountant = EXCLUDED.is_primary_accountant,
    access_level = EXCLUDED.access_level,
    status = EXCLUDED.status,
    invited_by = EXCLUDED.invited_by,
    invited_at = EXCLUDED.invited_at;

INSERT INTO fiscal_periods (company_id, name, start_date, end_date, status)
SELECT c.id, '2026', DATE '2026-01-01', DATE '2026-12-31', 'open'
FROM companies c
WHERE c.tax_id = 'J-50000001-1'
ON CONFLICT (company_id, name) DO NOTHING;

COMMIT;
