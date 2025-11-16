# Configuração com Docker (Recomendado para Isolamento)

Esta opção cria um container PostgreSQL isolado, sem interferir com seus bancos locais existentes.

## Pré-requisitos

- Docker Desktop instalado e rodando
- Docker Compose instalado

## Passo a Passo

### 1. Iniciar o PostgreSQL em Docker

```bash
cd vamo-junto-backend
docker-compose up -d
```

Isso vai:
- Criar um container PostgreSQL isolado
- Usar a porta **5433** (para não conflitar com seu PostgreSQL local na 5432)
- Criar automaticamente o banco `vamo_junto_db`

### 2. Verificar se está rodando

```bash
docker-compose ps
```

Você deve ver o container `vamo-junto-db` com status `Up`.

### 3. Configurar o .env

Adicione estas variáveis ao seu arquivo `.env`:

```env
# Configurações do Docker PostgreSQL
POSTGRES_USER=vamo_junto_user
POSTGRES_PASSWORD=vamo_junto_pass
POSTGRES_DB=vamo_junto_db
POSTGRES_PORT=5433

# URL de conexão (usando as variáveis acima)
DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:${POSTGRES_PORT}/${POSTGRES_DB}
```

Ou configure diretamente:

```env
DATABASE_URL=postgresql://vamo_junto_user:vamo_junto_pass@localhost:5433/vamo_junto_db
```

**Nota:** A porta padrão é **5433** (não 5432) para não conflitar com seu PostgreSQL local.

### 4. Executar as migrations

```bash
alembic upgrade head
```

### 5. Parar o banco (quando não estiver usando)

```bash
docker-compose down
```

### 6. Parar e remover dados (reset completo)

```bash
docker-compose down -v
```

## Vantagens

✅ **Isolamento completo** - Não interfere com seus bancos locais  
✅ **Fácil de resetar** - `docker-compose down -v` remove tudo  
✅ **Porta diferente** - Não conflita com PostgreSQL local  
✅ **Mesma configuração em qualquer máquina** - Desenvolvedores têm ambiente idêntico  

## Conectar no DBeaver (Opcional)

Se quiser visualizar no DBeaver:

1. Nova conexão PostgreSQL
2. Host: `localhost`
3. Port: `5433`
4. Database: `vamo_junto_db`
5. Username: `vamo_junto_user`
6. Password: `vamo_junto_pass`

