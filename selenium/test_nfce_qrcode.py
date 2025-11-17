"""
Teste para simular leitura de QR Code de NFC-e
Consome os métodos reais do backend e imprime todos os dados capturados
"""
import sys
import os
from pathlib import Path
import json
import re
from datetime import datetime

# Adiciona o diretório raiz do backend ao path
backend_root = Path(__file__).parent.parent
sys.path.insert(0, str(backend_root))

from app.services.nfce_scraper import (
    scrape_nfce, 
    parse_nfce_code, 
    extract_code_from_url,
    fetch_nfce_html,
    parse_market_info,
    parse_emission_date,
    parse_products,
    parse_total_value,
    parse_total_taxes,
    parse_access_key
)
from app.services.note_service import process_and_save_note
from app.services.db_service import (
    get_user_by_id,
    get_user_by_email,
    create_user,
    get_user_notes_with_products
)
from app.services.auth_service import get_password_hash
from app.utils.encryption import hash_access_key
from app.database import init_db_pool, get_db_cursor
from bs4 import BeautifulSoup


def print_section(title: str):
    """Imprime um separador visual para seções"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_dict(data: dict, indent: int = 0):
    """Imprime um dicionário de forma formatada"""
    prefix = "  " * indent
    for key, value in data.items():
        if isinstance(value, dict):
            print(f"{prefix}{key}:")
            print_dict(value, indent + 1)
        elif isinstance(value, list):
            print(f"{prefix}{key}:")
            for i, item in enumerate(value, 1):
                print(f"{prefix}  [{i}]")
                if isinstance(item, dict):
                    print_dict(item, indent + 2)
                else:
                    print(f"{prefix}    {item}")
        elif isinstance(value, datetime):
            print(f"{prefix}{key}: {value.strftime('%d/%m/%Y %H:%M:%S')}")
        else:
            print(f"{prefix}{key}: {value}")


def test_qrcode_scraping(qrcode_url: str = None):
    """Testa o scraping de NFC-e a partir de uma URL de QR code"""
    
    # URL padrão do QR code se não fornecida
    if qrcode_url is None:
        qrcode_url = "https://www.nfce.fazenda.sp.gov.br/NFCeConsultaPublica/Paginas/ConsultaQRCode.aspx?p=35251137849063000208651010000143151119149935|2|1|1|55BFC6765E2FF5129F09969EA461999132AB2DA6"
    
    print_section("TESTE DE LEITURA DE QR CODE NFC-e")
    print(f"\nURL do QR Code: {qrcode_url}\n")
    
    try:
        # 1. Extrair código da URL
        print_section("1. EXTRAÇÃO DO CÓDIGO DA URL")
        extracted_code = extract_code_from_url(qrcode_url)
        parsed_code = parse_nfce_code(qrcode_url)
        print(f"Código extraído: {extracted_code}")
        print(f"Código parseado: {parsed_code}")
        print(f"Hash do código (SHA256): {hash_access_key(parsed_code)}")
        
        # 2. Fazer scraping dos dados
        print_section("2. SCRAPING DOS DADOS DA NFC-e")
        print("Fazendo requisição e parseando HTML...")
        
        # Primeiro, vamos fazer o fetch manualmente para debug
        # Tentar usar a URL completa fornecida primeiro
        import httpx
        print("Tentando usar a URL completa fornecida...")
        try:
            with httpx.Client(timeout=30.0, follow_redirects=True) as client:
                response = client.get(qrcode_url)
                response.raise_for_status()
                html_content = response.text
                print(f"HTML capturado com sucesso! Tamanho: {len(html_content)} caracteres")
        except Exception as e:
            print(f"Erro ao usar URL completa: {e}")
            print("Tentando usar método padrão...")
            html_content = fetch_nfce_html(parsed_code)
        
        soup = BeautifulSoup(html_content, "lxml")
        
        # Debug: mostrar amostra do HTML
        print_section("2.1. AMOSTRA DO HTML CAPTURADO")
        print("Primeiros 2000 caracteres do HTML:")
        print(html_content[:2000])
        print("\n...\n")
        
        # Debug: tentar encontrar elementos manualmente
        print_section("2.2. DEBUG - ELEMENTOS ENCONTRADOS NO HTML")
        
        all_text = soup.get_text()
        
        # Tentar encontrar nome do mercado
        txt_topo = soup.find("div", class_="txtTopo")
        print(f"div.txtTopo encontrado: {txt_topo is not None}")
        if txt_topo:
            print(f"  Conteúdo: {txt_topo.get_text(strip=True)[:100]}")
        
        # Procurar por padrões de texto conhecidos
        print("\nProcurando por padrões de texto conhecidos:")
        
        # Procurar por nome do mercado (FRIGOBRAZ)
        if "FRIGOBRAZ" in all_text:
            print("[OK] Texto 'FRIGOBRAZ' encontrado no HTML!")
            # Procurar por padrões de nome de empresa
            market_patterns = [
                r"([A-Z][A-Z\s]+(?:LTDA|EIRELI|ME|EPP|SA|COMERCIO))",
                r"([A-Z][A-Z\s]+COMERCIO[^\n]*)",
                r"(FRIGOBRAZ[^\n]*)"
            ]
            for pattern in market_patterns:
                market_match = re.search(pattern, all_text)
                if market_match:
                    print(f"  Nome encontrado (regex '{pattern}'): {market_match.group(1).strip()[:80]}")
                    break
        
        # Procurar por CNPJ
        cnpj_patterns = [
            r"CNPJ:\s*([\d./-]+)",
            r"(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})",
            r"37\.849\.063/0002-08"
        ]
        for pattern in cnpj_patterns:
            cnpj_match = re.search(pattern, all_text)
            if cnpj_match:
                print(f"[OK] CNPJ encontrado (regex '{pattern}'): {cnpj_match.group(1) if cnpj_match.groups() else cnpj_match.group(0)}")
                break
        
        # Procurar por endereço
        if "AV CELSO GARCIA" in all_text or "TATUAPE" in all_text:
            print("[OK] Endereco encontrado no HTML!")
            address_match = re.search(r"(AV[^\n]+TATUAPE[^\n]*)", all_text)
            if address_match:
                print(f"  Endereco: {address_match.group(1).strip()[:100]}")
        
        # Procurar por produtos
        if "FRANGO" in all_text or "STROGONOFF" in all_text:
            print("[OK] Produtos encontrados no HTML!")
            product_match = re.search(r"(F\.FILE FRANGO[^\n]*)", all_text)
            if product_match:
                print(f"  Produto: {product_match.group(1).strip()[:100]}")
        
        # Procurar por valor total
        value_match = re.search(r"Valor.*pagar.*R\$\s*([\d,]+\.?\d*)", all_text, re.IGNORECASE)
        if value_match:
            print(f"[OK] Valor total encontrado: R$ {value_match.group(1)}")
        
        # Tentar encontrar tabela de produtos
        table = soup.find("table", id="tabResult")
        print(f"\nTabela #tabResult encontrada: {table is not None}")
        if not table:
            tables = soup.find_all("table")
            print(f"  Total de tabelas encontradas: {len(tables)}")
            for i, t in enumerate(tables[:3], 1):
                print(f"  Tabela {i} - ID: {t.get('id', 'sem ID')}, Classes: {t.get('class', [])}")
        
        # Agora tentar fazer o scraping completo
        print_section("2.3. PARSING INDIVIDUAL DOS DADOS")
        
        market_info = parse_market_info(soup)
        print("Informações do mercado:")
        print_dict(market_info)
        
        emission_date = parse_emission_date(soup)
        print(f"\nData de emissão: {emission_date}")
        
        products = parse_products(soup)
        print(f"\nProdutos encontrados: {len(products)}")
        if products:
            print("Primeiro produto:")
            print_dict(products[0] if products else {})
        
        total_value = parse_total_value(soup)
        print(f"\nValor total: R$ {total_value:.2f}")
        
        total_taxes = parse_total_taxes(soup)
        print(f"Total de tributos: R$ {total_taxes or 0:.2f}")
        
        access_key = parse_access_key(soup) or parsed_code
        print(f"Chave de acesso: {access_key}")
        
        # Tentar fazer scraping completo
        print_section("2.4. SCRAPING COMPLETO")
        try:
            nfce_data = scrape_nfce(qrcode_url)
        except Exception as scrape_error:
            print(f"Erro no scraping completo: {scrape_error}")
            print("\nCriando dados manualmente com o que foi capturado...")
            # Criar estrutura de dados mesmo com dados parciais
            nfce_data = {
                "access_key": access_key,
                "market_name": market_info.get("name") or "NOME NÃO ENCONTRADO",
                "market_cnpj": market_info.get("cnpj"),
                "market_address": market_info.get("address"),
                "emission_date": emission_date,
                "total_value": total_value,
                "total_taxes": total_taxes,
                "products": products
            }
        
        # 3. Exibir todos os dados capturados
        print_section("3. DADOS CAPTURADOS DA NFC-e")
        print_dict(nfce_data)
        
        # 4. Detalhamento dos produtos
        print_section("4. DETALHAMENTO DOS PRODUTOS")
        if nfce_data.get("products"):
            print(f"Total de produtos encontrados: {len(nfce_data['products'])}")
            for i, product in enumerate(nfce_data["products"], 1):
                print(f"\n--- Produto {i} ---")
                print_dict(product)
        else:
            print("Nenhum produto encontrado!")
        
        # 5. Resumo da nota
        print_section("5. RESUMO DA NOTA")
        print(f"Chave de Acesso: {nfce_data.get('access_key', 'N/A')}")
        print(f"Estabelecimento: {nfce_data.get('market_name', 'N/A')}")
        print(f"CNPJ: {nfce_data.get('market_cnpj', 'N/A')}")
        print(f"Endereço: {nfce_data.get('market_address', 'N/A')}")
        print(f"Data de Emissão: {nfce_data.get('emission_date', 'N/A')}")
        print(f"Valor Total: R$ {nfce_data.get('total_value', 0):.2f}")
        print(f"Total de Tributos: R$ {nfce_data.get('total_taxes', 0) or 0:.2f}")
        print(f"Quantidade de Produtos: {len(nfce_data.get('products', []))}")
        
        # 6. Dados em formato JSON (para debug)
        print_section("6. DADOS EM FORMATO JSON")
        # Converter datetime para string para JSON
        json_data = nfce_data.copy()
        if isinstance(json_data.get("emission_date"), datetime):
            json_data["emission_date"] = json_data["emission_date"].isoformat()
        for product in json_data.get("products", []):
            if "created_at" in product:
                del product["created_at"]
        
        print(json.dumps(json_data, indent=2, ensure_ascii=False))
        
        print_section("TESTE CONCLUÍDO COM SUCESSO")
        return nfce_data
        
    except Exception as e:
        print_section("ERRO NO TESTE")
        print(f"Tipo do erro: {type(e).__name__}")
        print(f"Mensagem: {str(e)}")
        import traceback
        print("\nTraceback completo:")
        traceback.print_exc()
        return None


def check_database_connection():
    """Verifica se o banco de dados está disponível"""
    try:
        init_db_pool()
        # Testar conexão fazendo uma query simples
        with get_db_cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        print("[OK] Conexao com banco de dados estabelecida!")
        return True
    except Exception as e:
        print(f"[ERRO] Nao foi possivel conectar ao banco de dados: {e}")
        print("  Verifique se o banco esta rodando e se as configuracoes estao corretas.")
        return False


def get_or_create_test_user():
    """Obtem ou cria um usuario de teste"""
    test_email = "teste@selenium.local"
    test_name = "Usuario Teste Selenium"
    test_cpf = "00000000000"
    
    try:
        # Tentar obter usuario existente
        user = get_user_by_email(test_email)
        if user:
            print(f"[OK] Usuario de teste encontrado: ID {user['id']} - {user['name']}")
            return user["id"]
        
        # Criar novo usuario de teste
        print("Criando usuario de teste...")
        password_hash = get_password_hash("teste123")
        user = create_user(
            name=test_name,
            email=test_email,
            cpf=test_cpf,
            password_hash=password_hash
        )
        print(f"[OK] Usuario de teste criado: ID {user['id']} - {user['name']}")
        return user["id"]
        
    except Exception as e:
        print(f"[ERRO] Nao foi possivel obter/criar usuario de teste: {e}")
        # Tentar usar user_id 1 como fallback
        try:
            user = get_user_by_id(1)
            if user:
                print(f"[AVISO] Usando usuario ID 1 como fallback: {user['name']}")
                return 1
        except:
            pass
        raise


def test_note_processing(qrcode_url: str, user_id: int = None):
    """
    Testa o processamento completo da nota (incluindo salvamento no banco)
    ATENÇÃO: Requer banco de dados configurado
    """
    print_section("TESTE DE PROCESSAMENTO COMPLETO DA NOTA")
    print(f"\nURL do QR Code: {qrcode_url}\n")
    
    # Verificar conexão com banco
    if not check_database_connection():
        print_section("TESTE DE SALVAMENTO CANCELADO")
        print("Nao foi possivel conectar ao banco de dados.")
        print("O teste de salvamento requer banco de dados configurado e rodando.")
        return None
    
    # Obter ou criar usuario de teste
    try:
        if user_id is None:
            user_id = get_or_create_test_user()
        else:
            user = get_user_by_id(user_id)
            if not user:
                print(f"[ERRO] Usuario ID {user_id} nao encontrado!")
                return None
            print(f"[OK] Usando usuario ID {user_id}: {user['name']}")
    except Exception as e:
        print_section("ERRO AO OBTER USUARIO")
        print(f"Erro: {e}")
        return None
    
    print(f"\nUser ID: {user_id}\n")
    
    try:
        # Processar e salvar nota
        print("Processando e salvando nota no banco de dados...")
        note = process_and_save_note(user_id, qrcode_url)
        
        print_section("NOTA SALVA COM SUCESSO")
        print(f"ID da Nota: {note['id']}")
        print(f"Chave de Acesso (hash): {note.get('access_key_hash', 'N/A')}")
        print(f"Estabelecimento: {note.get('market_name', 'N/A')}")
        print(f"Valor Total: R$ {note.get('total_value', 0):.2f}")
        print(f"Data de Criacao: {note.get('created_at', 'N/A')}")
        print(f"\nTotal de Produtos Salvos: {len(note.get('products', []))}")
        
        if note.get('products'):
            print("\nProdutos salvos:")
            for i, product in enumerate(note['products'], 1):
                print(f"  [{i}] {product['name']} - Qtd: {product['quantity']} {product['unit']} - R$ {product['total_price']:.2f}")
        
        print_section("DADOS COMPLETOS DA NOTA SALVA")
        print_dict(note)
        
        return note
        
    except ValueError as e:
        print_section("NOTA JA EXISTE")
        print(f"Mensagem: {str(e)}")
        print("\nA nota ja foi registrada anteriormente para este usuario.")
        print("Isso e esperado se voce executar o teste multiplas vezes com a mesma URL.")
        return None
    except Exception as e:
        print_section("ERRO NO PROCESSAMENTO")
        print(f"Tipo do erro: {type(e).__name__}")
        print(f"Mensagem: {str(e)}")
        import traceback
        print("\nTraceback completo:")
        traceback.print_exc()
        return None


if __name__ == "__main__":
    import sys
    
    print("\n" + "=" * 80)
    print("  TESTE DE LEITURA DE QR CODE NFC-e")
    print("  Simulando leitura de QR code e consumindo métodos do backend")
    print("=" * 80)
    
    # URL do QR code (pode ser alterada)
    qrcode_url = "https://www.nfce.fazenda.sp.gov.br/NFCeConsultaPublica/Paginas/ConsultaQRCode.aspx?p=35251106024283000198651100000008971119149935|2|1|1|D7FC8EEDB2439485E673A96F49818AD52DCA0408"
    
    # Verificar argumentos da linha de comando
    save_to_db = "--save" in sys.argv or "-s" in sys.argv
    
    # Teste 1: Apenas scraping (não requer banco de dados)
    nfce_data = test_qrcode_scraping(qrcode_url)
    
    # Teste 2: Processamento completo com salvamento (requer banco de dados)
    if save_to_db:
        print("\n" + "=" * 80)
        print("  INICIANDO TESTE DE SALVAMENTO")
        print("=" * 80)
        saved_note = test_note_processing(qrcode_url)
        
        if saved_note:
            print_section("VERIFICACAO - LISTAR NOTAS DO USUARIO")
            try:
                user_id = saved_note["user_id"]
                notes = get_user_notes_with_products(user_id, limit=5)
                print(f"Total de notas do usuario: {len(notes)}")
                if notes:
                    print("\nUltimas notas registradas:")
                    for note in notes[:3]:
                        print(f"  - ID {note['id']}: {note.get('market_name', 'N/A')} - R$ {note.get('total_value', 0):.2f}")
            except Exception as e:
                print(f"Erro ao listar notas: {e}")
    else:
        print("\n" + "=" * 80)
        print("  DICA: Para testar o salvamento no banco de dados")
        print("  Execute: python selenium/test_nfce_qrcode.py --save")
        print("=" * 80)
    
    print("\n" + "=" * 80)
    print("  FIM DOS TESTES")
    print("=" * 80 + "\n")

