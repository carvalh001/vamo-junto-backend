# Testes Selenium

Esta pasta contém testes e scripts de automação para o projeto.

## Teste de QR Code NFC-e

O arquivo `test_nfce_qrcode.py` simula a leitura de um QR code de NFC-e e consome os métodos reais do backend para capturar e exibir todos os dados.

### Como executar

```bash
# A partir da raiz do backend
cd vamo-junto-backend

# Apenas scraping (não requer banco de dados)
python selenium/test_nfce_qrcode.py

# Com salvamento no banco de dados (requer DB configurado)
python selenium/test_nfce_qrcode.py --save
# ou
python selenium/test_nfce_qrcode.py -s
```

### O que o teste faz

#### Teste de Scraping (padrão)
1. **Extrai o código da URL do QR code** - Parseia a URL fornecida e extrai o código NFC-e
2. **Faz scraping dos dados** - Consome o método `scrape_nfce()` do backend
3. **Exibe todos os dados capturados** - Imprime no console:
   - Informações do estabelecimento (nome, CNPJ, endereço)
   - Data de emissão
   - Valor total e tributos
   - Lista completa de produtos com detalhes
   - Dados em formato JSON para debug

#### Teste de Salvamento (com `--save`)
1. **Verifica conexão com banco de dados** - Testa se o banco está disponível
2. **Cria ou obtém usuário de teste** - Cria automaticamente um usuário para testes
3. **Processa e salva a nota** - Usa `process_and_save_note()` para salvar no banco
4. **Exibe dados salvos** - Mostra a nota salva com ID e todos os produtos
5. **Lista notas do usuário** - Verifica as últimas notas registradas

### Métodos do backend utilizados

- `extract_code_from_url()` - Extrai código da URL
- `parse_nfce_code()` - Parseia código NFC-e
- `scrape_nfce()` - Faz scraping completo da NFC-e
- `hash_access_key()` - Gera hash da chave de acesso
- `process_and_save_note()` - Processa e salva nota no banco de dados
- `create_note()` - Cria registro da nota no banco
- `create_product()` - Cria registros dos produtos no banco
- `check_note_exists()` - Verifica se a nota já foi registrada

### Requisitos para Salvamento

Para testar o salvamento no banco de dados, você precisa:

1. **Banco de dados configurado** - PostgreSQL rodando e acessível
2. **Variáveis de ambiente** - `DATABASE_URL` configurada no `.env` ou ambiente
3. **Tabelas criadas** - Schema do banco deve estar atualizado (migrações aplicadas)

O teste criará automaticamente um usuário de teste se não existir:
- Email: `teste@selenium.local`
- Nome: `Usuario Teste Selenium`
- CPF: `00000000000`

### Exemplo de uso

O teste já vem configurado com uma URL de exemplo. Para testar com outra URL, modifique a variável `qrcode_url` no arquivo ou passe como parâmetro.

### Tratamento de Erros

- **Nota já existe**: Se você executar o teste múltiplas vezes com a mesma URL, o sistema detectará que a nota já foi registrada e informará isso
- **Banco indisponível**: Se o banco não estiver disponível, o teste de salvamento será cancelado e uma mensagem será exibida
- **Erros de parsing**: O teste mostra informações detalhadas de debug caso haja problemas ao extrair dados do HTML

