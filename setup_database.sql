-- Script SQL para criar o banco de dados do Vamo Junto
-- Execute este script no DBeaver ou psql

-- Criar o banco de dados (se não existir)
CREATE DATABASE vamo_junto_db
    WITH 
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'Portuguese_Brazil.1252'
    LC_CTYPE = 'Portuguese_Brazil.1252'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;

-- Comentário no banco
COMMENT ON DATABASE vamo_junto_db IS 'Database for Vamo Junto - NFC-e price monitoring platform';

-- Conectar ao banco criado (execute este comando separadamente ou use o DBeaver para conectar)
-- \c vamo_junto_db

