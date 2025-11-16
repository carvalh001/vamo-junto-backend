# Configuração do Banco de Dados

## Criar Novo Banco de Dados

Você pode criar um novo banco de dados de duas formas:

### Opção 1: Usando DBeaver (Recomendado)

1. Abra o DBeaver
2. Conecte-se ao seu servidor PostgreSQL local
3. Clique com o botão direito em **Databases** → **Create New Database**
4. Configure:
   - **Database name**: `vamo_junto_db`
   - **Owner**: `postgres` (ou seu usuário)
   - **Encoding**: `UTF8`
5. Clique em **OK**

### Opção 2: Usando SQL no DBeaver

1. Abra o DBeaver
2. Conecte-se ao seu servidor PostgreSQL
3. Abra um novo SQL Editor
4. Execute o script `setup_database.sql`:
   ```sql
   CREATE DATABASE vamo_junto_db
       WITH 
       OWNER = postgres
       ENCODING = 'UTF8'
       TABLESPACE = pg_default
       CONNECTION LIMIT = -1;
   ```

### Opção 3: Usando linha de comando (psql)

```bash
# Conectar ao PostgreSQL
psql -U postgres

# Criar o banco
CREATE DATABASE vamo_junto_db;

# Sair do psql
\q
```

## Configurar o .env

Após criar o banco, configure o arquivo `.env`:

```env
DATABASE_URL=postgresql://usuario:senha@localhost:5432/vamo_junto_db
```

**Exemplo:**
- Se seu usuário é `postgres` e senha é `123456`:
  ```
  DATABASE_URL=postgresql://postgres:123456@localhost:5432/vamo_junto_db
  ```

- Se não tem senha:
  ```
  DATABASE_URL=postgresql://postgres@localhost:5432/vamo_junto_db
  ```

## Executar Migrations

Após configurar o `.env`, execute as migrations:

```bash
cd vamo-junto-backend
alembic upgrade head
```

## Verificar se funcionou

No DBeaver, conecte-se ao banco `vamo_junto_db` e verifique se as tabelas foram criadas:
- `users`
- `notes`
- `products`

