# Configuração com SQLite (Opção Mais Simples)

SQLite é um banco de dados em arquivo, perfeito para desenvolvimento local sem precisar de servidor.

## Vantagens

✅ **Zero configuração** - Não precisa de servidor PostgreSQL  
✅ **Arquivo único** - Tudo em um arquivo `.db`  
✅ **Isolado** - Não interfere com nada  
✅ **Rápido** - Ideal para desenvolvimento  

## Desvantagens

⚠️ **Não é PostgreSQL** - Algumas features podem diferir  
⚠️ **Não recomendado para produção** - Use PostgreSQL em produção  

## Como Usar

### 1. Instalar dependência adicional

SQLite já vem com Python, mas precisamos garantir compatibilidade:

```bash
# SQLite já vem com Python, nenhuma dependência extra necessária
```

### 2. Modificar o .env

```env
DATABASE_URL=sqlite:///./vamo_junto.db
```

### 3. Ajustar o código do banco (se necessário)

O código atual já suporta SQLite, mas algumas queries podem precisar de ajustes. PostgreSQL é recomendado para produção.

## Migrations

As migrations do Alembic funcionam normalmente:

```bash
alembic upgrade head
```

Isso criará o arquivo `vamo_junto.db` na raiz do projeto.

## Resetar Banco

Simplesmente delete o arquivo `vamo_junto.db` e rode as migrations novamente.

