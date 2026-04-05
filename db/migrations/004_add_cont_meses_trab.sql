/* ================================================================
   MIGRATION 004 — Agregar tabla cont_meses_trab a todos los tenants
   - Crea cont_meses_trab en tenants existentes
   - Recrea sp_create_tenant_schema incluyendo cont_meses_trab
================================================================ */

-- 1. Agregar cont_meses_trab a tenants existentes
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN
        SELECT schema_name
        FROM global.tenants
        WHERE deleted_at IS NULL
    LOOP
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = r.schema_name AND table_name = 'cont_meses_trab'
        ) THEN
            EXECUTE format('
                CREATE TABLE %I.cont_meses_trab (
                    id             SERIAL PRIMARY KEY,
                    n_mes_contble  INTEGER,
                    n_mes_sistema  INTEGER,
                    mes            VARCHAR(50),
                    ano            VARCHAR(50),
                    status         VARCHAR(50),
                    bloqueo        VARCHAR(50),
                    ejercicio      VARCHAR(50),
                    tipo           VARCHAR(50),
                    usuario        VARCHAR(50),
                    fecha_i        TIMESTAMP,
                    fecha_f        TIMESTAMP,
                    fecha_cierre   TIMESTAMP,
                    fecha_creado   TIMESTAMP
                )', r.schema_name);
        END IF;
    END LOOP;
END $$;


-- 2. Recrear el procedure incluyendo cont_cuentas y cont_meses_trab
CREATE OR REPLACE PROCEDURE global.sp_create_tenant_schema(
    p_tenant_slug VARCHAR(100),
    p_actor_user_id UUID DEFAULT NULL
)
LANGUAGE plpgsql AS $$
DECLARE
    v_schema_name TEXT;
    v_tenant_id   UUID;
    v_sfx         TEXT;
BEGIN
    SELECT uuid, schema_name
    INTO v_tenant_id, v_schema_name
    FROM global.tenants
    WHERE slug = p_tenant_slug AND deleted_at IS NULL;

    IF v_tenant_id IS NULL THEN
        RAISE EXCEPTION 'Tenant no encontrado: %', p_tenant_slug;
    END IF;

    v_sfx := REPLACE(p_tenant_slug, '-', '_');

    -- Schema
    EXECUTE format('CREATE SCHEMA IF NOT EXISTS %I', v_schema_name);

    -- Branches
    EXECUTE format('
        CREATE TABLE IF NOT EXISTS %I.branches (
            uuid       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id  UUID NOT NULL DEFAULT %L,
            name       VARCHAR(100) NOT NULL,
            address    TEXT,
            phone      VARCHAR(30),
            is_active  BOOLEAN NOT NULL DEFAULT TRUE,
            updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        )', v_schema_name, v_tenant_id);

    -- Categories
    EXECUTE format('
        CREATE TABLE IF NOT EXISTS %I.categories (
            uuid       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name       VARCHAR(100) NOT NULL,
            parent_id  UUID,
            updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        )', v_schema_name);

    -- Products
    EXECUTE format('
        CREATE TABLE IF NOT EXISTS %I.products (
            uuid        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id   UUID NOT NULL DEFAULT %L,
            sku         VARCHAR(50) NOT NULL,
            name        VARCHAR(150) NOT NULL,
            description TEXT,
            category_id UUID,
            unit_price  NUMERIC(18,4) NOT NULL DEFAULT 0,
            cost_price  NUMERIC(18,4) NOT NULL DEFAULT 0,
            is_active   BOOLEAN NOT NULL DEFAULT TRUE,
            deleted_at  TIMESTAMP,
            updated_at  TIMESTAMP NOT NULL DEFAULT NOW(),
            created_at  TIMESTAMP NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_products_sku_%s UNIQUE(sku)
        )', v_schema_name, v_tenant_id, v_sfx);

    -- Customers
    EXECUTE format('
        CREATE TABLE IF NOT EXISTS %I.customers (
            uuid         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id    UUID NOT NULL DEFAULT %L,
            tax_id       VARCHAR(30) NOT NULL,
            tax_type     VARCHAR(10) NOT NULL DEFAULT ''RIF'',
            company_name VARCHAR(255),
            updated_at   TIMESTAMP NOT NULL DEFAULT NOW(),
            created_at   TIMESTAMP NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_cust_tax_%s UNIQUE(tax_id)
        )', v_schema_name, v_tenant_id, v_sfx);

    -- Sale Orders
    EXECUTE format('
        CREATE TABLE IF NOT EXISTS %I.sale_orders (
            uuid         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id    UUID NOT NULL DEFAULT %L,
            order_number VARCHAR(30) NOT NULL UNIQUE,
            branch_id    UUID NOT NULL,
            customer_id  UUID,
            total        NUMERIC(18,2) NOT NULL DEFAULT 0,
            status       VARCHAR(20) NOT NULL DEFAULT ''draft''
                         CHECK(status IN (''draft'',''confirmed'',''invoiced'',''cancelled'')),
            updated_at   TIMESTAMP NOT NULL DEFAULT NOW(),
            created_at   TIMESTAMP NOT NULL DEFAULT NOW()
        )', v_schema_name, v_tenant_id);

    -- Cont Cuentas (Plan de cuentas contables)
    EXECUTE format('
        CREATE TABLE IF NOT EXISTS %I.cont_cuentas (
            id               SERIAL,
            txt_cuenta       VARCHAR(50)  NOT NULL,
            txt_denominacion VARCHAR(150),
            txt_nom_corto    VARCHAR(50),
            num_nivel        INTEGER,
            txt_status       VARCHAR(50),
            txt_comentario   VARCHAR(200) NOT NULL DEFAULT '''',
            cuenta_padre     VARCHAR(50),
            nomb_cuenta_padre VARCHAR(80),
            num_tipo_aux     INTEGER      NOT NULL DEFAULT -1,
            tipo_aux         VARCHAR(50)  NOT NULL DEFAULT '''',
            num_tipo_cuenta  INTEGER      NOT NULL DEFAULT -1,
            cod_tipo_aux     VARCHAR(10)  NOT NULL DEFAULT '''',
            num_aux          INTEGER      NOT NULL DEFAULT -1,
            CONSTRAINT pk_cont_cuentas_%s PRIMARY KEY (txt_cuenta)
        )', v_schema_name, v_sfx);

    -- Cont Meses Trabajo
    EXECUTE format('
        CREATE TABLE IF NOT EXISTS %I.cont_meses_trab (
            id             SERIAL PRIMARY KEY,
            n_mes_contble  INTEGER,
            n_mes_sistema  INTEGER,
            mes            VARCHAR(50),
            ano            VARCHAR(50),
            status         VARCHAR(50),
            bloqueo        VARCHAR(50),
            ejercicio      VARCHAR(50),
            tipo           VARCHAR(50),
            usuario        VARCHAR(50),
            fecha_i        TIMESTAMP,
            fecha_f        TIMESTAMP,
            fecha_cierre   TIMESTAMP,
            fecha_creado   TIMESTAMP
        )', v_schema_name);

    -- Log
    INSERT INTO audit.activity_logs(tenant_id, action, resource, metadata)
    VALUES (v_tenant_id, 'SCHEMA_CREATED', 'tenant_schema',
            '{"schema":"' || v_schema_name || '","slug":"' || p_tenant_slug || '"}');

    RAISE NOTICE 'Schema [%] creado exitosamente.', v_schema_name;
END;
$$;

-- 3. Registrar migración
INSERT INTO global.schema_migrations(version, description, applied_by)
VALUES('20260405_004', 'Agregar tabla cont_meses_trab (meses de trabajo) a todos los tenants', current_user)
ON CONFLICT (version) DO NOTHING;
