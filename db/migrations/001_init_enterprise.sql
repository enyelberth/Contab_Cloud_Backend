CREATE EXTENSION IF NOT EXISTS pgcrypto;

/* ================================================================
   SCHEMA MULTI-TENANT ENTERPRISE — POSTGRESQL
   ================================================================ */

/* ================================================================
   1. SCHEMAS
================================================================ */
CREATE SCHEMA IF NOT EXISTS global;
CREATE SCHEMA IF NOT EXISTS security;
CREATE SCHEMA IF NOT EXISTS audit;
CREATE SCHEMA IF NOT EXISTS config;
CREATE SCHEMA IF NOT EXISTS notifications;
CREATE SCHEMA IF NOT EXISTS events;
CREATE SCHEMA IF NOT EXISTS storage;
CREATE SCHEMA IF NOT EXISTS jobs;

/* ================================================================
   2. TABLAS [global]
================================================================ */

CREATE TABLE IF NOT EXISTS global.tenants (
    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) NOT NULL UNIQUE,
    rif VARCHAR(50) UNIQUE,
    address TEXT,
    location VARCHAR(255),
    phone VARCHAR(50),
    email VARCHAR(150),
    logo_url VARCHAR(500),
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active','suspended','cancelled')),
    plan VARCHAR(50) NOT NULL DEFAULT 'enterprise',
    schema_name VARCHAR(255) GENERATED ALWAYS AS ('tenant_' || REPLACE(slug, '-', '_')) STORED,
    settings TEXT,
    deleted_at TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS global.roles (
    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    level INTEGER NOT NULL DEFAULT 100,
    is_system BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS global.permissions (
    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS global.role_permissions (
    role_id UUID NOT NULL REFERENCES global.roles(uuid),
    permission_id UUID NOT NULL REFERENCES global.permissions(uuid),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE IF NOT EXISTS global.users (
    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active','inactive','locked')),
    email_verified_at TIMESTAMP,
    last_login_at TIMESTAMP,
    deleted_at TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS global.profiles (
    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES global.users(uuid),
    first_name VARCHAR(100),
    second_name VARCHAR(100),
    first_lastname VARCHAR(100),
    second_lastname VARCHAR(100),
    phone VARCHAR(30),
    avatar_url VARCHAR(500),
    birthdate DATE,
    entry_date DATE,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS global.user_tenants (
    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES global.users(uuid),
    tenant_id UUID NOT NULL REFERENCES global.tenants(uuid),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    invited_by UUID REFERENCES global.users(uuid),
    joined_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, tenant_id)
);

CREATE TABLE IF NOT EXISTS global.user_global_roles (
    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES global.users(uuid),
    role_id UUID NOT NULL REFERENCES global.roles(uuid),
    assigned_by UUID REFERENCES global.users(uuid),
    assigned_at TIMESTAMP NOT NULL DEFAULT NOW(),
    revoked_at TIMESTAMP,
    revoked_by UUID REFERENCES global.users(uuid),
    UNIQUE (user_id, role_id)
);

CREATE TABLE IF NOT EXISTS global.user_tenant_roles (
    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES global.users(uuid),
    tenant_id UUID NOT NULL REFERENCES global.tenants(uuid),
    role_id UUID NOT NULL REFERENCES global.roles(uuid),
    branch_id UUID,
    assigned_by UUID REFERENCES global.users(uuid),
    assigned_at TIMESTAMP NOT NULL DEFAULT NOW(),
    revoked_at TIMESTAMP,
    revoked_by UUID REFERENCES global.users(uuid),
    UNIQUE (user_id, tenant_id, role_id, branch_id)
);

CREATE TABLE IF NOT EXISTS global.tenant_settings (
    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES global.tenants(uuid),
    module VARCHAR(50) NOT NULL CHECK (module IN ('general','inventory','sales','purchases','accounting','hr','notifications')),
    key VARCHAR(100) NOT NULL,
    value TEXT NOT NULL,
    value_type VARCHAR(20) NOT NULL DEFAULT 'string' CHECK (value_type IN ('string','integer','decimal','boolean','json')),
    description VARCHAR(255),
    updated_by UUID,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, module, key)
);

/* ================================================================
   3. TABLAS [security]
================================================================ */

CREATE TABLE IF NOT EXISTS security.user_sessions (
    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES global.users(uuid),
    tenant_id UUID REFERENCES global.tenants(uuid),
    token_hash VARCHAR(500) NOT NULL UNIQUE,
    device_info VARCHAR(500),
    ip_address VARCHAR(50),
    user_agent VARCHAR(500),
    last_used_at TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    revoked_at TIMESTAMP,
    revoked_reason VARCHAR(100),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_sessions_user ON security.user_sessions(user_id) WHERE revoked_at IS NULL;

CREATE TABLE IF NOT EXISTS security.failed_login_attempts (
    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    identifier VARCHAR(255) NOT NULL,
    tenant_id UUID,
    ip_address VARCHAR(50),
    reason VARCHAR(100),
    attempted_at TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_failed_login_id ON security.failed_login_attempts(identifier, attempted_at DESC);

CREATE TABLE IF NOT EXISTS security.password_history (
    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES global.users(uuid),
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

/* ================================================================
   4. TABLAS [audit]
================================================================ */

CREATE TABLE IF NOT EXISTS audit.audit_logs (
    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID,
    user_id UUID,
    action VARCHAR(20) NOT NULL,
    schema_name VARCHAR(50) NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    record_id VARCHAR(50) NOT NULL,
    old_values TEXT,
    new_values TEXT,
    ip_address VARCHAR(50),
    session_id VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit.activity_logs (
    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID,
    user_id UUID,
    session_id VARCHAR(255),
    action VARCHAR(100) NOT NULL,
    resource VARCHAR(100),
    resource_id VARCHAR(50),
    metadata TEXT,
    ip_address VARCHAR(50),
    user_agent VARCHAR(500),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

/* ================================================================
   5. TABLAS [config]
================================================================ */

CREATE TABLE IF NOT EXISTS config.currencies (
    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(10) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    symbol VARCHAR(5),
    decimal_places SMALLINT NOT NULL DEFAULT 2,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS config.exchange_rates (
    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    base_currency_id UUID NOT NULL REFERENCES config.currencies(uuid),
    quote_currency_id UUID NOT NULL REFERENCES config.currencies(uuid),
    rate_value NUMERIC(18,6) NOT NULL CHECK (rate_value > 0),
    source VARCHAR(100),
    valid_from TIMESTAMP NOT NULL,
    valid_until TIMESTAMP,
    created_by UUID,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS config.tax_types (
    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    applies_to VARCHAR(20) NOT NULL DEFAULT 'both' CHECK (applies_to IN ('sales','purchases','both')),
    calculation_base VARCHAR(20) NOT NULL DEFAULT 'subtotal' CHECK (calculation_base IN ('subtotal','total_with_tax','fixed')),
    is_retention BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    country_code VARCHAR(5) DEFAULT 'VE',
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

/* ================================================================
   6. TABLAS [notifications]
================================================================ */

CREATE TABLE IF NOT EXISTS notifications.templates (
    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES global.tenants(uuid),
    event VARCHAR(100) NOT NULL,
    channel VARCHAR(20) NOT NULL CHECK (channel IN ('email','whatsapp','sms','inapp')),
    language VARCHAR(10) NOT NULL DEFAULT 'es',
    subject VARCHAR(255),
    body TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, event, channel, language)
);

CREATE TABLE IF NOT EXISTS notifications.queue (
    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID,
    user_id UUID,
    template_id UUID,
    channel VARCHAR(20) NOT NULL CHECK (channel IN ('email','whatsapp','sms','inapp')),
    recipient VARCHAR(255) NOT NULL,
    subject VARCHAR(255),
    body TEXT NOT NULL,
    variables TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','processing','sent','failed','cancelled')),
    attempts SMALLINT NOT NULL DEFAULT 0,
    max_attempts SMALLINT NOT NULL DEFAULT 3,
    last_attempt_at TIMESTAMP,
    last_error TEXT,
    sent_at TIMESTAMP,
    scheduled_for TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS notifications.inapp (
    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES global.tenants(uuid),
    user_id UUID NOT NULL REFERENCES global.users(uuid),
    type VARCHAR(20) NOT NULL DEFAULT 'info' CHECK (type IN ('info','warning','error','success')),
    title VARCHAR(255) NOT NULL,
    body TEXT NOT NULL,
    action_url VARCHAR(500),
    action_label VARCHAR(100),
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    read_at TIMESTAMP,
    expires_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

/* ================================================================
   7. TABLAS [events]
================================================================ */

CREATE TABLE IF NOT EXISTS events.outbox (
    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID,
    event_type VARCHAR(100) NOT NULL,
    aggregate_type VARCHAR(50) NOT NULL,
    aggregate_id VARCHAR(50) NOT NULL,
    payload TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','processing','published','failed','dead')),
    attempts SMALLINT NOT NULL DEFAULT 0,
    max_attempts SMALLINT NOT NULL DEFAULT 5,
    last_error TEXT,
    published_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS events.webhook_endpoints (
    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES global.tenants(uuid),
    name VARCHAR(100) NOT NULL,
    url VARCHAR(500) NOT NULL,
    secret VARCHAR(255) NOT NULL,
    events TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_used_at TIMESTAMP,
    failure_count INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS events.webhook_deliveries (
    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    outbox_id UUID NOT NULL REFERENCES events.outbox(uuid),
    webhook_id UUID NOT NULL REFERENCES events.webhook_endpoints(uuid),
    http_status INT,
    response_body TEXT,
    duration_ms INT,
    delivered_at TIMESTAMP NOT NULL DEFAULT NOW()
);

/* ================================================================
   8. TABLAS [storage]
================================================================ */

CREATE TABLE IF NOT EXISTS storage.attachments (
    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES global.tenants(uuid),
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(50) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(100),
    file_size_bytes BIGINT,
    storage_provider VARCHAR(30) NOT NULL DEFAULT 'local' CHECK (storage_provider IN ('local','s3','azure_blob','gcs')),
    storage_path VARCHAR(500) NOT NULL,
    is_public BOOLEAN NOT NULL DEFAULT FALSE,
    uploaded_by UUID REFERENCES global.users(uuid),
    deleted_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

/* ================================================================
   9. TABLAS [jobs]
================================================================ */

CREATE TABLE IF NOT EXISTS jobs.queue (
    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID,
    job_type VARCHAR(100) NOT NULL,
    payload TEXT NOT NULL,
    priority SMALLINT NOT NULL DEFAULT 5 CHECK (priority BETWEEN 1 AND 10),
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','processing','completed','failed','dead')),
    attempts SMALLINT NOT NULL DEFAULT 0,
    max_attempts SMALLINT NOT NULL DEFAULT 3,
    worker_id VARCHAR(100),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    last_error TEXT,
    result TEXT,
    scheduled_for TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by UUID,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

/* ================================================================
   10. FUNCIONES DE AUTORIZACIÓN (PL/pgSQL)
================================================================ */

CREATE OR REPLACE FUNCTION global.fn_is_super_admin(p_user_id UUID) 
RETURNS BOOLEAN LANGUAGE plpgsql AS $$
DECLARE
    v_res BOOLEAN := FALSE;
BEGIN
    IF EXISTS (
        SELECT 1 FROM global.user_global_roles ugr
        JOIN global.roles r ON r.uuid = ugr.role_id
        WHERE ugr.user_id = p_user_id AND ugr.revoked_at IS NULL AND r.name = 'super_admin'
    ) THEN 
        v_res := TRUE;
    END IF;
    RETURN v_res;
END;
$$;

CREATE OR REPLACE FUNCTION global.fn_is_tenant_admin(p_user_id UUID, p_tenant_id UUID) 
RETURNS BOOLEAN LANGUAGE plpgsql AS $$
DECLARE
    v_res BOOLEAN := FALSE;
BEGIN
    IF EXISTS (
        SELECT 1 FROM global.user_tenant_roles utr
        JOIN global.roles r ON r.uuid = utr.role_id
        WHERE utr.user_id = p_user_id AND utr.tenant_id = p_tenant_id AND utr.revoked_at IS NULL AND r.name = 'tenant_admin'
    ) THEN 
        v_res := TRUE;
    END IF;
    RETURN v_res;
END;
$$;

CREATE OR REPLACE FUNCTION global.fn_user_has_permission(p_user_id UUID, p_tenant_id UUID, p_permission_slug VARCHAR) 
RETURNS BOOLEAN LANGUAGE plpgsql AS $$
DECLARE
    v_res BOOLEAN := FALSE;
BEGIN
    IF global.fn_is_super_admin(p_user_id) THEN 
        v_res := TRUE;
    ELSIF EXISTS (
        SELECT 1 FROM global.user_tenant_roles utr
        JOIN global.role_permissions rp ON rp.role_id = utr.role_id
        JOIN global.permissions p ON p.uuid = rp.permission_id
        WHERE utr.user_id = p_user_id AND utr.tenant_id = p_tenant_id AND utr.revoked_at IS NULL AND p.slug = p_permission_slug
    ) THEN 
        v_res := TRUE;
    END IF;
    RETURN v_res;
END;
$$;

/* ================================================================
   11. STORED PROCEDURES DE GESTIÓN (PL/pgSQL)
================================================================ */

-- 11.1 Contexto de sesión
CREATE OR REPLACE PROCEDURE global.sp_set_session_context(p_user_id UUID, p_tenant_id UUID DEFAULT NULL)
LANGUAGE plpgsql AS $$
BEGIN
    -- En Postgres, el contexto de sesión se maneja con variables de configuración (set_config)
    PERFORM set_config('app.current_user_id', p_user_id::text, false);
    IF p_tenant_id IS NOT NULL THEN
        PERFORM set_config('app.current_tenant_id', p_tenant_id::text, false);
    END IF;
END;
$$;

-- 11.2 Agregar usuario a tenant
CREATE OR REPLACE PROCEDURE global.sp_add_user_to_tenant(
    p_actor_user_id UUID, 
    p_target_user_id UUID, 
    p_tenant_id UUID
)
LANGUAGE plpgsql AS $$
BEGIN
    IF NOT global.fn_is_super_admin(p_actor_user_id) AND NOT global.fn_is_tenant_admin(p_actor_user_id, p_tenant_id) THEN
        RAISE EXCEPTION 'No autorizado para agregar usuarios a este tenant.';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM global.users WHERE uuid = p_target_user_id AND deleted_at IS NULL) THEN
        RAISE EXCEPTION 'El usuario destino no existe.';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM global.tenants WHERE uuid = p_tenant_id AND deleted_at IS NULL AND status = 'active') THEN
        RAISE EXCEPTION 'El tenant no existe o no está activo.';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM global.user_tenants WHERE user_id = p_target_user_id AND tenant_id = p_tenant_id) THEN
        INSERT INTO global.user_tenants(user_id, tenant_id, invited_by, joined_at)
        VALUES (p_target_user_id, p_tenant_id, p_actor_user_id, NOW());
    ELSE
        UPDATE global.user_tenants SET is_active = TRUE
        WHERE user_id = p_target_user_id AND tenant_id = p_tenant_id;
    END IF;
END;
$$;

-- 11.3 Asignar rol
CREATE OR REPLACE PROCEDURE global.sp_assign_role_in_tenant(
    p_actor_user_id UUID,
    p_target_user_id UUID,
    p_tenant_id UUID,
    p_role_id UUID,
    p_branch_id UUID DEFAULT NULL
)
LANGUAGE plpgsql AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM global.roles WHERE uuid = p_role_id AND deleted_at IS NULL) THEN
        RAISE EXCEPTION 'El rol especificado no existe.';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM global.user_tenants WHERE user_id = p_target_user_id AND tenant_id = p_tenant_id AND is_active = TRUE) THEN
        RAISE EXCEPTION 'El usuario destino no pertenece a este tenant.';
    END IF;

    IF NOT global.fn_is_super_admin(p_actor_user_id) AND NOT global.fn_is_tenant_admin(p_actor_user_id, p_tenant_id) THEN
        RAISE EXCEPTION 'No autorizado para asignar roles en este tenant.';
    END IF;

    IF NOT global.fn_is_super_admin(p_actor_user_id) AND EXISTS(SELECT 1 FROM global.roles WHERE uuid = p_role_id AND name = 'super_admin') THEN
        RAISE EXCEPTION 'No autorizado para asignar el rol super_admin.';
    END IF;

    IF NOT EXISTS(
        SELECT 1 FROM global.user_tenant_roles
        WHERE user_id = p_target_user_id AND tenant_id = p_tenant_id
          AND role_id = p_role_id AND revoked_at IS NULL
          AND ((branch_id IS NULL AND p_branch_id IS NULL) OR branch_id = p_branch_id)
    ) THEN
        INSERT INTO global.user_tenant_roles(user_id, tenant_id, role_id, branch_id, assigned_by)
        VALUES (p_target_user_id, p_tenant_id, p_role_id, p_branch_id, p_actor_user_id);
    END IF;
END;
$$;

-- 11.4 Revocar rol
CREATE OR REPLACE PROCEDURE global.sp_revoke_role_in_tenant(
    p_actor_user_id UUID,
    p_target_user_id UUID,
    p_tenant_id UUID,
    p_role_id UUID
)
LANGUAGE plpgsql AS $$
BEGIN
    IF NOT global.fn_is_super_admin(p_actor_user_id) AND NOT global.fn_is_tenant_admin(p_actor_user_id, p_tenant_id) THEN
        RAISE EXCEPTION 'No autorizado para revocar roles en este tenant.';
    END IF;

    UPDATE global.user_tenant_roles
    SET revoked_at = NOW(), revoked_by = p_actor_user_id
    WHERE user_id = p_target_user_id 
      AND tenant_id = p_tenant_id
      AND role_id = p_role_id 
      AND revoked_at IS NULL;
END;
$$;

/* ================================================================
   12. SP CREAR SCHEMA POR TENANT
================================================================ */

CREATE OR REPLACE PROCEDURE global.sp_create_tenant_schema(p_tenant_slug VARCHAR(100), p_actor_user_id UUID DEFAULT NULL)
LANGUAGE plpgsql AS $$
DECLARE
    v_schema_name TEXT;
    v_tenant_id UUID;
    v_sfx TEXT;
BEGIN
    -- Obtener datos del tenant
    SELECT uuid, schema_name INTO v_tenant_id, v_schema_name
    FROM global.tenants
    WHERE slug = p_tenant_slug AND deleted_at IS NULL;

    IF v_tenant_id IS NULL THEN
        RAISE EXCEPTION 'Tenant no encontrado o inactivo.';
    END IF;

    v_sfx := REPLACE(p_tenant_slug, '-', '_');

    -- Crear Schema
    EXECUTE format('CREATE SCHEMA IF NOT EXISTS %I', v_schema_name);

    -- 1. Branches
    EXECUTE format('
    CREATE TABLE IF NOT EXISTS %I.branches (
        uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id UUID NOT NULL DEFAULT %L,
        name VARCHAR(100) NOT NULL,
        address TEXT,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
        created_at TIMESTAMP NOT NULL DEFAULT NOW()
    )', v_schema_name, v_tenant_id);

    -- 2. Categories
    EXECUTE format('
    CREATE TABLE IF NOT EXISTS %I.categories (
        uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name VARCHAR(100) NOT NULL,
        parent_id UUID,
        updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
        created_at TIMESTAMP NOT NULL DEFAULT NOW()
    )', v_schema_name);

    -- 3. Products
    EXECUTE format('
    CREATE TABLE IF NOT EXISTS %I.products (
        uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        sku VARCHAR(50) NOT NULL,
        name VARCHAR(150) NOT NULL,
        category_id UUID,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
        created_at TIMESTAMP NOT NULL DEFAULT NOW(),
        CONSTRAINT uq_products_sku_%s UNIQUE(sku)
    )', v_schema_name, v_sfx);

    -- 4. Customers
    EXECUTE format('
    CREATE TABLE IF NOT EXISTS %I.customers (
        uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tax_id VARCHAR(30) NOT NULL,
        tax_type VARCHAR(10) NOT NULL DEFAULT ''RIF'',
        company_name VARCHAR(255),
        updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
        created_at TIMESTAMP NOT NULL DEFAULT NOW(),
        CONSTRAINT uq_cust_tax_%s UNIQUE(tax_id)
    )', v_schema_name, v_sfx);

    -- 5. Sale Orders
    EXECUTE format('
    CREATE TABLE IF NOT EXISTS %I.sale_orders (
        uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        order_number VARCHAR(30) NOT NULL UNIQUE,
        branch_id UUID NOT NULL,
        total NUMERIC(18,2) NOT NULL DEFAULT 0,
        status VARCHAR(20) NOT NULL DEFAULT ''draft'' CHECK(status IN (''draft'',''confirmed'',''invoiced'',''cancelled'')),
        updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
        created_at TIMESTAMP NOT NULL DEFAULT NOW()
    )', v_schema_name);

    -- Registrar evento en el log global
    INSERT INTO audit.activity_logs(tenant_id, action, resource, metadata)
    VALUES (v_tenant_id, 'SCHEMA_CREATED', 'tenant_schema', 
            '{"schema":"' || v_schema_name || '","slug":"' || p_tenant_slug || '"}');

    RAISE NOTICE 'Schema [%] creado exitosamente.', v_schema_name;
END;
$$;

/* ================================================================
   13. CONTROL DE MIGRACIONES
================================================================ */

CREATE TABLE IF NOT EXISTS global.schema_migrations (
    id SERIAL PRIMARY KEY,
    version VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(500),
    applied_at TIMESTAMP NOT NULL DEFAULT NOW(),
    applied_by VARCHAR(100),
    checksum VARCHAR(64)
);

/* ================================================================
   14. SEEDS (Datos Iniciales con idempotencia)
================================================================ */

-- Impuestos Venezolanos
INSERT INTO config.tax_types(code, name, description, applies_to, calculation_base, is_retention)
VALUES
  ('IVA',  'Impuesto al Valor Agregado', 'IVA estándar Venezuela', 'both', 'subtotal', FALSE),
  ('IVA_R','IVA Reducido', 'IVA tasa reducida bienes básicos', 'both', 'subtotal', FALSE),
  ('IGTF', 'Imp. Grandes Transacciones Financieras', 'Aplica a pagos en divisas', 'sales', 'total_with_tax', FALSE),
  ('ISLR', 'Imp. sobre la Renta (Retención)', 'Retención ISLR proveedores', 'purchases', 'subtotal', TRUE),
  ('IDB',  'Imp. Débito Bancario', 'Retención bancaria', 'both', 'total_with_tax', TRUE)
ON CONFLICT (code) DO NOTHING;

-- Roles
INSERT INTO global.roles(name, description, level, is_system) VALUES
  ('super_admin', 'Acceso total global.', 1000, TRUE),
  ('tenant_admin', 'Administra su tenant.', 900, TRUE),
  ('branch_manager', 'Gestiona una sucursal.', 500, FALSE),
  ('sales_agent', 'Crea órdenes de venta.', 200, FALSE),
  ('warehouse', 'Gestiona inventario.', 200, FALSE),
  ('accountant', 'Acceso a contabilidad.', 200, FALSE),
  ('viewer', 'Solo lectura.', 50, FALSE)
ON CONFLICT (name) DO NOTHING;

-- Monedas
INSERT INTO config.currencies(code, name, symbol) VALUES
  ('USD','Dólar Estadounidense','$'),
  ('VES','Bolívar Venezolano','Bs.'),
  ('EUR','Euro','€')
ON CONFLICT (code) DO NOTHING;

-- Migración registrada
INSERT INTO global.schema_migrations(version, description, applied_by)
VALUES('20250330_001', 'Schema base multi-tenant enterprise con schema-per-tenant', current_user)
ON CONFLICT (version) DO NOTHING;