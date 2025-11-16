# Deploy no Railway

Este projeto está configurado para ser implantado no Railway.

## Configuração Necessária

### Variáveis de Ambiente

Configure as seguintes variáveis de ambiente no Railway:

- `DATABASE_URL` - URL de conexão PostgreSQL (fornecida automaticamente pelo Railway se você adicionar um serviço PostgreSQL)
- `SECRET_KEY` - Chave secreta para JWT (mínimo 32 caracteres). Gere uma chave segura.
- `CORS_ORIGINS` - Origens permitidas para CORS (separadas por vírgula). Ex: `https://seu-frontend.railway.app,https://outro-dominio.com`
- `ENVIRONMENT` - Ambiente (production, staging, etc.)
- `LOG_LEVEL` - Nível de log (INFO, DEBUG, WARNING, ERROR)

### Migrations Automáticas

As migrations do banco de dados são executadas automaticamente no startup da aplicação através do `lifespan` do FastAPI em `app/main.py`.

## Arquivos de Configuração

- `Procfile` - Define o comando de inicialização
- `runtime.txt` - Especifica a versão do Python (3.13.0)
- `requirements.txt` - Lista todas as dependências Python
- `railway.json` - Configuração adicional do Railway (opcional)

## Deploy

1. Conecte seu repositório GitHub ao Railway
2. Adicione um serviço PostgreSQL
3. Configure as variáveis de ambiente
4. O Railway irá automaticamente:
   - Detectar que é um projeto Python
   - Instalar as dependências do `requirements.txt`
   - Executar as migrations automaticamente no startup
   - Iniciar o servidor com uvicorn

## Verificação

Após o deploy, verifique:
- `https://seu-app.railway.app/health` - Deve retornar `{"status": "healthy"}`
- `https://seu-app.railway.app/` - Deve retornar informações da API

