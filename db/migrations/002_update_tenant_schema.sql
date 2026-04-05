/* ================================================================
   MIGRATION 002 — Actualizar sp_create_tenant_schema y tablas existentes
   - Agrega columnas faltantes a products (tenant_id, description, unit_price, cost_price)
   - Agrega phone a branches
   - Re-crea el procedure con el schema completo
================================================================ */

-- 1. Alterar tablas del tenant demo si ya existen
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN
        SELECT schema_name
        FROM global.tenants
        WHERE deleted_at IS NULL
    LOOP
        -- branches: agregar phone si no existe
        IF EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = r.schema_name AND table_name = 'branches'
        ) THEN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = r.schema_name AND table_name = 'branches' AND column_name = 'phone'
            ) THEN
                EXECUTE format('ALTER TABLE %I.branches ADD COLUMN phone VARCHAR(30)', r.schema_name);
            END IF;
        END IF;

        -- products: agregar columnas faltantes
        IF EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = r.schema_name AND table_name = 'products'
        ) THEN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = r.schema_name AND table_name = 'products' AND column_name = 'tenant_id'
            ) THEN
                EXECUTE format(
                    'ALTER TABLE %I.products ADD COLUMN tenant_id UUID',
                    r.schema_name
                );
                EXECUTE format(
                    'UPDATE %I.products SET tenant_id = (SELECT uuid FROM global.tenants WHERE schema_name = %L LIMIT 1)',
                    r.schema_name, r.schema_name
                );
                EXECUTE format(
                    'ALTER TABLE %I.products ALTER COLUMN tenant_id SET NOT NULL',
                    r.schema_name
                );
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = r.schema_name AND table_name = 'products' AND column_name = 'description'
            ) THEN
                EXECUTE format('ALTER TABLE %I.products ADD COLUMN description TEXT', r.schema_name);
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = r.schema_name AND table_name = 'products' AND column_name = 'unit_price'
            ) THEN
                EXECUTE format('ALTER TABLE %I.products ADD COLUMN unit_price NUMERIC(18,4) NOT NULL DEFAULT 0', r.schema_name);
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = r.schema_name AND table_name = 'products' AND column_name = 'cost_price'
            ) THEN
                EXECUTE format('ALTER TABLE %I.products ADD COLUMN cost_price NUMERIC(18,4) NOT NULL DEFAULT 0', r.schema_name);
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = r.schema_name AND table_name = 'products' AND column_name = 'deleted_at'
            ) THEN
                EXECUTE format('ALTER TABLE %I.products ADD COLUMN deleted_at TIMESTAMP', r.schema_name);
            END IF;
        END IF;
    END LOOP;
END $$;


-- 2. Recrear el procedure con el schema completo y corregido
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

    -- Products (completo)
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

END;
$$;
