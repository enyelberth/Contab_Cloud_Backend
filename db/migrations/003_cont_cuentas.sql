-- ====================================================================
-- Migración 003: Tabla cont_cuentas en schemas existentes
--
-- Esta tabla es el Catálogo de Cuentas (Plan de Cuentas) de cada empresa.
-- Se agrega a cada schema de empresa que ya exista.
-- Para empresas nuevas, la función crear_schema_empresa() en database.py
-- se encarga de crearla automáticamente.
-- ====================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS empresa_1.cont_cuentas (
    id                  SERIAL,
    txt_cuenta          VARCHAR(50)  NOT NULL,
    txt_denominacion    VARCHAR(150),
    txt_nom_corto       VARCHAR(50),
    num_nivel           INT,
    txt_status          VARCHAR(50),
    txt_comentario      VARCHAR(200) DEFAULT '',
    cuenta_padre        VARCHAR(50),
    nomb_cuenta_padre   VARCHAR(80),
    num_tipo_aux        INT          DEFAULT -1,
    tipo_aux            VARCHAR(50)  DEFAULT '',
    num_tipo_cuenta     INT          DEFAULT -1,
    cod_tipo_aux        VARCHAR(10)  DEFAULT '',
    num_aux             INT          DEFAULT -1,
    PRIMARY KEY (txt_cuenta)
);

CREATE TABLE IF NOT EXISTS empresa_2.cont_cuentas (
    id                  SERIAL,
    txt_cuenta          VARCHAR(50)  NOT NULL,
    txt_denominacion    VARCHAR(150),
    txt_nom_corto       VARCHAR(50),
    num_nivel           INT,
    txt_status          VARCHAR(50),
    txt_comentario      VARCHAR(200) DEFAULT '',
    cuenta_padre        VARCHAR(50),
    nomb_cuenta_padre   VARCHAR(80),
    num_tipo_aux        INT          DEFAULT -1,
    tipo_aux            VARCHAR(50)  DEFAULT '',
    num_tipo_cuenta     INT          DEFAULT -1,
    cod_tipo_aux        VARCHAR(10)  DEFAULT '',
    num_aux             INT          DEFAULT -1,
    PRIMARY KEY (txt_cuenta)
);

-- Datos de prueba para empresa_1 (Inversiones Demo)
INSERT INTO empresa_1.cont_cuentas (txt_cuenta, txt_denominacion, txt_nom_corto, num_nivel, txt_status, cuenta_padre, num_tipo_cuenta)
VALUES
    ('1',       'ACTIVO',                          'Activo',       1, 'Activo', NULL,  1),
    ('1.1',     'ACTIVO CIRCULANTE',               'Act. Circ.',   2, 'Activo', '1',   1),
    ('1.1.1',   'CAJA Y BANCOS',                   'Caja',         3, 'Activo', '1.1', 1),
    ('1.1.1.01','Caja Principal',                  'Caja Ppal',    4, 'Activo', '1.1.1', 1),
    ('1.1.1.02','Banco Venezuela Cta. Cte. 001',   'BV 001',       4, 'Activo', '1.1.1', 1),
    ('2',       'PASIVO',                          'Pasivo',       1, 'Activo', NULL,  2),
    ('2.1',     'PASIVO CIRCULANTE',               'Pas. Circ.',   2, 'Activo', '2',   2),
    ('3',       'PATRIMONIO',                      'Patrimonio',   1, 'Activo', NULL,  3),
    ('4',       'INGRESOS',                        'Ingresos',     1, 'Activo', NULL,  4),
    ('5',       'EGRESOS',                         'Egresos',      1, 'Activo', NULL,  5)
ON CONFLICT (txt_cuenta) DO NOTHING;

-- Datos de prueba para empresa_2 (Constructora Test)
INSERT INTO empresa_2.cont_cuentas (txt_cuenta, txt_denominacion, txt_nom_corto, num_nivel, txt_status, cuenta_padre, num_tipo_cuenta)
VALUES
    ('1',       'ACTIVO',                          'Activo',       1, 'Activo', NULL,  1),
    ('1.1',     'ACTIVO CIRCULANTE',               'Act. Circ.',   2, 'Activo', '1',   1),
    ('1.1.1',   'CAJA Y BANCOS',                   'Caja',         3, 'Activo', '1.1', 1),
    ('1.1.1.01','Caja Obra Norte',                 'Caja Norte',   4, 'Activo', '1.1.1', 1),
    ('1.2',     'ACTIVO FIJO',                     'Act. Fijo',    2, 'Activo', '1',   1),
    ('1.2.1',   'MAQUINARIA Y EQUIPO',             'Maquinaria',   3, 'Activo', '1.2', 1),
    ('2',       'PASIVO',                          'Pasivo',       1, 'Activo', NULL,  2),
    ('3',       'PATRIMONIO',                      'Patrimonio',   1, 'Activo', NULL,  3),
    ('4',       'INGRESOS POR CONTRATOS',          'Ingresos',     1, 'Activo', NULL,  4),
    ('5',       'COSTOS DE CONSTRUCCION',          'Costos',       1, 'Activo', NULL,  5)
ON CONFLICT (txt_cuenta) DO NOTHING;

COMMIT;
