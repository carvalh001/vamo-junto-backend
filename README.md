# Vamo Junto Backend

Backend API para a plataforma Vamo Junto - Monitoramento coletivo de preços e ofertas de mercados brasileiros.

## Tecnologias

- **Python 3.11+**
- **FastAPI** - Framework web moderno e rápido
- **PostgreSQL** - Banco de dados relacional
- **psycopg2** - Driver PostgreSQL (queries SQL puras)
- **Alembic** - Migrations do banco de dados
- **JWT** - Autenticação com tokens
- **BeautifulSoup4** - Scraping de páginas HTML
- **httpx** - Cliente HTTP assíncrono

## Estrutura do Projeto

```
vamo-junto-backend/
├── app/
│   ├── api/              # Rotas da API
│   ├── middleware/       # Middlewares de segurança
│   ├── schemas/          # Schemas Pydantic (validação)
│   ├── services/         # Lógica de negócio
│   ├── utils/            # Utilitários
│   ├── config.py         # Configurações
│   ├── database.py       # Conexão PostgreSQL
│   └── main.py           # Entry point
├── alembic/              # Migrations
└── requirements.txt      # Dependências
```

## Configuração

1. Clone o repositório
2. Crie um ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure o arquivo `.env` baseado no `.env.example`:
```bash
cp .env.example .env
```

5. Configure as variáveis de ambiente no `.env`:
- `DATABASE_URL` - URL de conexão PostgreSQL
- `SECRET_KEY` - Chave secreta para JWT (mínimo 32 caracteres)
- `CORS_ORIGINS` - Origens permitidas (separadas por vírgula)

6. Execute as migrations:
```bash
alembic upgrade head
```

7. Inicie o servidor:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Endpoints da API

### Autenticação
- `POST /api/auth/register` - Registrar novo usuário
- `POST /api/auth/login` - Login

### Notas Fiscais
- `POST /api/notes/scan` - Escanear/processar nota fiscal
- `GET /api/notes` - Listar notas do usuário
- `GET /api/notes/{id}` - Obter detalhes de uma nota

### Dashboard
- `GET /api/dashboard/stats` - Estatísticas do usuário

## Segurança

- Rate limiting em todos os endpoints
- Sanitização de inputs
- Validação de dados com Pydantic
- Proteção contra SQL injection
- CORS configurável
- Tratamento de erros sem expor informações sensíveis

## Desenvolvimento

O projeto usa queries SQL puras (sem ORM) para maior controle e performance. Todas as tabelas, campos e métodos estão em inglês.

## Migrations

Para criar uma nova migration:
```bash
alembic revision -m "description"
```

Para aplicar migrations:
```bash
alembic upgrade head
```

Para reverter a última migration:
```bash
alembic downgrade -1
```

