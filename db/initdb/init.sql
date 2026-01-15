-- =========================
-- Tabla: info
-- =========================
CREATE TABLE info (
    id SERIAL PRIMARY KEY,
    simbolo TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    tendencia TEXT NOT NULL DEFAULT 'flat',
    rsi FLOAT,
    resistencias FLOAT[],
    soportes FLOAT[],
    alineacion TEXT NOT NULL DEFAULT 'flat',
    ts TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_info_simbolo_timeframe UNIQUE (simbolo, timeframe)
);

-- Índice compuesto (muy importante para performance)
CREATE INDEX idx_info_simbolo_timeframe
ON info (simbolo, timeframe);

-- =========================
-- Tabla: soportes_resistencias
-- =========================
CREATE TABLE soportes_resistencias (
    id SERIAL PRIMARY KEY,
    simbolo TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    tipo TEXT NOT NULL DEFAULT 'flat',
    valor NUMERIC,
    ts TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Índice compuesto
CREATE INDEX idx_sr_simbolo_timeframe
ON soportes_resistencias (simbolo, timeframe);

-- Índice adicional por tipo (opcional)
CREATE INDEX idx_sr_tipo
ON soportes_resistencias (tipo);
