import httpx
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Dict, List, Optional
from app.config import settings
from app.utils.validators import validate_nfce_code
import re
import logging

logger = logging.getLogger(__name__)


def extract_code_from_url(url: str) -> Optional[str]:
    """Extract NFC-e code from URL"""
    # Pattern 1: p=CODE|...
    match = re.search(r'p=([\d\|]+)', url)
    if match:
        code_part = match.group(1).split('|')[0]
        # Remove non-numeric characters
        code = re.sub(r'[^\d]', '', code_part)
        if validate_nfce_code(code):
            return code
    
    # Pattern 2: Direct code in URL
    code = re.sub(r'[^\d]', '', url)
    if validate_nfce_code(code):
        return code
    
    return None


def parse_nfce_code(code_or_url: str) -> str:
    """Parse NFC-e code from URL or direct code"""
    # Remove spaces and non-numeric characters
    code = re.sub(r'[^\d]', '', code_or_url)
    
    if validate_nfce_code(code):
        return code
    
    # Try to extract from URL
    extracted = extract_code_from_url(code_or_url)
    if extracted:
        return extracted
    
    raise ValueError("Invalid NFC-e code format. Must be 44 digits.")


def build_consult_url(code: str, original_url: str = None) -> str:
    """Build consultation URL for NFC-e"""
    # If original URL is provided with parameters, use it directly
    if original_url and "?" in original_url and "p=" in original_url:
        # Extract the parameter part (everything after ?)
        param_part = original_url.split("?", 1)[1]
        
        # Build the full consultation URL using the exact parameters from QR code
        # The QR code URL might be /qrcode?p=... but we need /NFCeConsultaPublica/Paginas/ConsultaQRCode.aspx?p=...
        url = f"{settings.nfce_base_url}/NFCeConsultaPublica/Paginas/ConsultaQRCode.aspx?{param_part}"
        logger.debug(f"Using URL with original parameters: {url[:150]}...")
        return url
    
    # If original URL contains the pipe-separated format, extract and use it
    if original_url and "|" in original_url:
        # Extract the p= parameter value (CODE|ver|tipo|num|HASH)
        match = re.search(r'p=([\d\|A-F0-9]+)', original_url)
        if match:
            param_value = match.group(1)
            url = f"{settings.nfce_base_url}/NFCeConsultaPublica/Paginas/ConsultaQRCode.aspx?p={param_value}"
            logger.debug(f"Using URL with extracted parameters: {url[:150]}...")
            return url
    
    # Fallback: Build URL without hash (may not work for all notes)
    url = f"{settings.nfce_base_url}/NFCeConsultaPublica/Paginas/ConsultaQRCode.aspx?p={code}"
    logger.warning(f"Using fallback URL without full parameters - may fail: {url[:150]}...")
    return url


def fetch_nfce_html(code: str, original_url: str = None) -> str:
    """Fetch HTML content from Fazenda SP"""
    url = build_consult_url(code, original_url)
    
    try:
        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()
            html_content = response.text
            # Log first 5000 chars for debugging
            logger.debug(f"HTML received (first 5000 chars): {html_content[:5000]}")
            return html_content
    except httpx.HTTPError as e:
        logger.error(f"Error fetching NFC-e: {e}")
        raise Exception("Failed to fetch NFC-e data. Please check the code and try again.")


def parse_market_info(soup: BeautifulSoup) -> Dict[str, Optional[str]]:
    """Parse market information from HTML"""
    market_info = {
        "name": None,
        "cnpj": None,
        "address": None
    }
    
    try:
        # Try multiple strategies to find market name
        # Strategy 1: div with class "txtTopo"
        name_elem = soup.find("div", class_="txtTopo")
        if name_elem:
            market_info["name"] = name_elem.get_text(strip=True)
            logger.debug(f"Found market name via txtTopo: {market_info['name']}")
        
        # Strategy 2: Look for text that looks like a company name (contains LTDA, ME, etc.)
        if not market_info["name"]:
            all_text = soup.get_text()
            # Pattern for company names - more flexible
            company_patterns = [
                r"([A-Z][A-Z\s]+(?:LTDA|EIRELI|ME|EPP|SA|COMERCIO)[^\n]*)",
                r"([A-Z][A-Z\s]+COMERCIO[^\n]*)",
                r"([A-Z][A-Z\s]{10,}(?:LTDA|EIRELI|ME|EPP|SA))",  # More flexible
                r"([A-Z][A-Z\s]+DE\s+[A-Z\s]+(?:LTDA|EIRELI|ME|EPP|SA))",  # "DE CARNES LTDA"
            ]
            for pattern in company_patterns:
                match = re.search(pattern, all_text)
                if match:
                    market_info["name"] = match.group(1).strip()
                    logger.debug(f"Found market name via regex pattern '{pattern}': {market_info['name']}")
                    break
        
        # Strategy 3: Look in title or h1/h2 tags
        if not market_info["name"]:
            title_elem = soup.find("title")
            if title_elem:
                title_text = title_elem.get_text()
                # Extract company name from title if it contains one
                match = re.search(r"([A-Z][A-Z\s]+(?:LTDA|EIRELI|ME|EPP|SA))", title_text)
                if match:
                    market_info["name"] = match.group(1).strip()
                    logger.debug(f"Found market name via title: {market_info['name']}")
        
        # Strategy 4: Look for h1, h2, h3 tags
        if not market_info["name"]:
            for tag in ["h1", "h2", "h3"]:
                header = soup.find(tag)
                if header:
                    text = header.get_text(strip=True)
                    if len(text) > 10 and any(keyword in text.upper() for keyword in ["LTDA", "ME", "EPP", "SA", "COMERCIO"]):
                        market_info["name"] = text
                        logger.debug(f"Found market name via {tag}: {market_info['name']}")
                        break
        
        # Strategy 5: Look for strong or b tags with company-like text
        if not market_info["name"]:
            for tag in ["strong", "b"]:
                elems = soup.find_all(tag)
                for elem in elems:
                    text = elem.get_text(strip=True)
                    if len(text) > 10 and len(text) < 100 and any(keyword in text.upper() for keyword in ["LTDA", "ME", "EPP", "SA"]):
                        market_info["name"] = text
                        logger.debug(f"Found market name via {tag}: {market_info['name']}")
                        break
                if market_info["name"]:
                    break
        
        # CNPJ - usually follows "CNPJ:" text
        cnpj_elem = soup.find(string=re.compile(r"CNPJ:"))
        if cnpj_elem:
            parent = cnpj_elem.find_parent()
            if parent:
                cnpj_text = parent.get_text(strip=True)
                cnpj_match = re.search(r"CNPJ:\s*([\d./-]+)", cnpj_text)
                if cnpj_match:
                    market_info["cnpj"] = cnpj_match.group(1)
                    logger.debug(f"Found CNPJ: {market_info['cnpj']}")
        
        # Address - usually in a div with class "text"
        address_elems = soup.find_all("div", class_="text")
        address_parts = []
        for elem in address_elems:
            text = elem.get_text(strip=True)
            # Skip CNPJ line and empty/short text
            if "CNPJ:" not in text and len(text) > 10:
                address_parts.append(text)
        
        if address_parts:
            market_info["address"] = ", ".join(address_parts)
            logger.debug(f"Found address: {market_info['address'][:100]}...")
        
        # Log if name was not found
        if not market_info["name"]:
            logger.warning("Market name not found with any strategy. HTML sample:")
            logger.warning(soup.get_text()[:1000])
    except Exception as e:
        logger.warning(f"Error parsing market info: {e}")
        import traceback
        logger.warning(traceback.format_exc())
    
    return market_info


def parse_emission_date(soup: BeautifulSoup) -> datetime:
    """Parse emission date from HTML"""
    try:
        # Strategy 1: Look for "Emissão:" text
        emission_elem = soup.find(string=re.compile(r"Emissão:", re.IGNORECASE))
        if emission_elem:
            parent = emission_elem.find_parent()
            if parent:
                text = parent.get_text()
                logger.debug(f"Found 'Emissão:' text: {text[:200]}")
                # Pattern: DD/MM/YYYY HH:MM:SS
                date_match = re.search(r"(\d{2}/\d{2}/\d{4})\s+(\d{2}:\d{2}:\d{2})", text)
                if date_match:
                    date_str = f"{date_match.group(1)} {date_match.group(2)}"
                    logger.debug(f"Parsed emission date: {date_str}")
                    return datetime.strptime(date_str, "%d/%m/%Y %H:%M:%S")
        
        # Strategy 2: Look for date patterns in the entire HTML
        all_text = soup.get_text()
        # Try multiple date patterns
        date_patterns = [
            r"(\d{2}/\d{2}/\d{4})\s+(\d{2}:\d{2}:\d{2})",  # DD/MM/YYYY HH:MM:SS
            r"(\d{2}/\d{2}/\d{4})\s+(\d{2}:\d{2})",  # DD/MM/YYYY HH:MM
            r"Emissão[:\s]+(\d{2}/\d{2}/\d{4})\s+(\d{2}:\d{2}:\d{2})",  # With "Emissão:" prefix
            r"(\d{2}/\d{2}/\d{4})\s+(\d{2}:\d{2}:\d{2})\s+-",  # With dash after
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, all_text, re.IGNORECASE)
            if match:
                try:
                    if len(match.groups()) == 2:
                        date_str = f"{match.group(1)} {match.group(2)}"
                        # Try with seconds first
                        try:
                            parsed_date = datetime.strptime(date_str, "%d/%m/%Y %H:%M:%S")
                            logger.debug(f"Parsed emission date via pattern '{pattern}': {parsed_date}")
                            return parsed_date
                        except ValueError:
                            # Try without seconds
                            parsed_date = datetime.strptime(date_str, "%d/%m/%Y %H:%M")
                            logger.debug(f"Parsed emission date via pattern '{pattern}': {parsed_date}")
                            return parsed_date
                except ValueError as e:
                    logger.debug(f"Failed to parse date '{date_str}': {e}")
                    continue
        
        # Strategy 3: Look for "Número:" and "Série:" which usually have date nearby
        numero_elem = soup.find(string=re.compile(r"Número:", re.IGNORECASE))
        if numero_elem:
            parent = numero_elem.find_parent()
            if parent:
                # Look for date in the same parent or siblings
                text = parent.get_text()
                date_match = re.search(r"(\d{2}/\d{2}/\d{4})\s+(\d{2}:\d{2}:\d{2})", text)
                if date_match:
                    date_str = f"{date_match.group(1)} {date_match.group(2)}"
                    try:
                        parsed_date = datetime.strptime(date_str, "%d/%m/%Y %H:%M:%S")
                        logger.debug(f"Parsed emission date near 'Número:': {parsed_date}")
                        return parsed_date
                    except ValueError:
                        pass
        
        # Strategy 4: Look in specific divs or spans that might contain date
        # Find elements containing date pattern
        date_containers = []
        for tag in ["div", "span", "p", "td"]:
            containers = soup.find_all(tag, string=re.compile(r"\d{2}/\d{2}/\d{4}"))
            date_containers.extend(containers)
        
        for container in date_containers:
            text = container.get_text(strip=True)
            date_match = re.search(r"(\d{2}/\d{2}/\d{4})\s+(\d{2}:\d{2}:\d{2})", text)
            if date_match:
                date_str = f"{date_match.group(1)} {date_match.group(2)}"
                try:
                    parsed_date = datetime.strptime(date_str, "%d/%m/%Y %H:%M:%S")
                    logger.debug(f"Parsed emission date from container: {parsed_date}")
                    return parsed_date
                except ValueError:
                    continue
        
        # Log what we found for debugging
        logger.warning("Could not parse emission date, using current date")
        logger.debug("Sample of HTML text where date might be:")
        logger.debug(all_text[:2000])
        return datetime.utcnow()
    except Exception as e:
        logger.warning(f"Error parsing emission date: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return datetime.utcnow()


def parse_products(soup: BeautifulSoup) -> List[Dict]:
    """Parse products from HTML table"""
    products = []
    
    try:
        # Find products table
        table = soup.find("table", id="tabResult")
        if not table:
            # Try alternative table selectors
            table = soup.find("table", {"data-filter": "true"})
        
        if table:
            rows = table.find_all("tr")
            for row in rows:
                if "Item" not in row.get("id", ""):
                    continue
                
                try:
                    # Product name
                    name_elem = row.find("span", class_="txtTit")
                    if not name_elem:
                        continue
                    
                    name = name_elem.get_text(strip=True)
                    
                    # Barcode (código)
                    barcode = None
                    cod_elem = row.find("span", class_="RCod")
                    if cod_elem:
                        cod_text = cod_elem.get_text()
                        cod_match = re.search(r"(\d+)", cod_text)
                        if cod_match:
                            barcode = cod_match.group(1)
                    
                    # Quantity
                    quantity = 1.0
                    qtd_elem = row.find("span", class_="Rqtd")
                    if qtd_elem:
                        qtd_text = qtd_elem.get_text()
                        qtd_match = re.search(r"(\d+\.?\d*)", qtd_text)
                        if qtd_match:
                            quantity = float(qtd_match.group(1))
                    
                    # Unit
                    unit = "UN"
                    unit_elem = row.find("span", class_="RUN")
                    if unit_elem:
                        unit_text = unit_elem.get_text()
                        unit_match = re.search(r"UN:\s*(\w+)", unit_text)
                        if unit_match:
                            unit = unit_match.group(1)
                    
                    # Unit price
                    unit_price = 0.0
                    unit_price_elem = row.find("span", class_="RvlUnit")
                    if unit_price_elem:
                        unit_price_text = unit_price_elem.get_text()
                        price_match = re.search(r"([\d,]+\.?\d*)", unit_price_text.replace(",", "."))
                        if price_match:
                            unit_price = float(price_match.group(1).replace(",", "."))
                    
                    # Total price
                    total_price = unit_price * quantity
                    total_elem = row.find("span", class_="valor")
                    if total_elem:
                        total_text = total_elem.get_text(strip=True)
                        total_match = re.search(r"([\d,]+\.?\d*)", total_text.replace(",", "."))
                        if total_match:
                            total_price = float(total_match.group(1).replace(",", "."))
                    
                    # Category (default to Uncategorized)
                    category = "Uncategorized"
                    
                    products.append({
                        "barcode": barcode,
                        "name": name,
                        "quantity": quantity,
                        "unit": unit,
                        "unit_price": unit_price,
                        "total_price": total_price,
                        "category": category
                    })
                except Exception as e:
                    logger.warning(f"Error parsing product row: {e}")
                    continue
    except Exception as e:
        logger.error(f"Error parsing products: {e}")
    
    return products


def parse_total_value(soup: BeautifulSoup) -> float:
    """Parse total value from HTML"""
    try:
        # Look for "Valor a pagar R$:" or similar
        total_elem = soup.find(string=re.compile(r"Valor.*pagar.*R\$"))
        if total_elem:
            parent = total_elem.find_parent()
            if parent:
                # Find span with class "totalNumb" or "txtMax"
                value_elem = parent.find("span", class_=re.compile(r"totalNumb|txtMax"))
                if value_elem:
                    value_text = value_elem.get_text(strip=True)
                    value_match = re.search(r"([\d,]+\.?\d*)", value_text.replace(",", "."))
                    if value_match:
                        return float(value_match.group(1).replace(",", "."))
        
        # Fallback: sum product prices
        products = parse_products(soup)
        return sum(p["total_price"] for p in products)
    except Exception as e:
        logger.warning(f"Error parsing total value: {e}")
        return 0.0


def parse_total_taxes(soup: BeautifulSoup) -> Optional[float]:
    """Parse total taxes from HTML"""
    try:
        # Look for "Tributos Totais" text
        taxes_elem = soup.find(string=re.compile(r"Tributos.*Totais"))
        if taxes_elem:
            parent = taxes_elem.find_parent()
            if parent:
                value_elem = parent.find("span", class_="totalNumb")
                if value_elem:
                    value_text = value_elem.get_text(strip=True)
                    value_match = re.search(r"([\d,]+\.?\d*)", value_text.replace(",", "."))
                    if value_match:
                        return float(value_match.group(1).replace(",", "."))
    except Exception as e:
        logger.warning(f"Error parsing total taxes: {e}")
    
    return None


def parse_access_key(soup: BeautifulSoup) -> Optional[str]:
    """Parse access key from HTML"""
    try:
        # Look for "Chave de acesso:" text
        key_elem = soup.find(string=re.compile(r"Chave de acesso"))
        if key_elem:
            parent = key_elem.find_parent()
            if parent:
                # Find span with class "chave"
                chave_elem = parent.find("span", class_="chave")
                if chave_elem:
                    chave_text = chave_elem.get_text(strip=True)
                    # Remove spaces
                    chave = re.sub(r'[^\d]', '', chave_text)
                    if validate_nfce_code(chave):
                        return chave
    except Exception as e:
        logger.warning(f"Error parsing access key: {e}")
    
    return None


def scrape_nfce(code_or_url: str) -> Dict:
    """Main function to scrape NFC-e data"""
    # Store original URL if it's a full URL (preserve for hash extraction)
    original_url = code_or_url if (code_or_url.startswith("http") or code_or_url.startswith("https")) else None
    logger.debug(f"Original input: {code_or_url[:100] if len(code_or_url) > 100 else code_or_url}")
    logger.debug(f"Is URL: {original_url is not None}")
    
    # Parse code
    code = parse_nfce_code(code_or_url)
    logger.info(f"Parsed NFC-e code: {code}")
    
    # Fetch HTML - pass original URL to preserve hash
    html_content = fetch_nfce_html(code, original_url)
    
    # Parse HTML
    soup = BeautifulSoup(html_content, "lxml")
    
    # Check if note was found
    error_elem = soup.find("div", id="erro")
    if error_elem and error_elem.get_text(strip=True):
        error_text = error_elem.get_text(strip=True)
        logger.error(f"NFC-e error found in HTML: {error_text}")
        raise Exception("NFC-e not found or invalid. Please check the code.")
    
    # Parse data
    market_info = parse_market_info(soup)
    emission_date = parse_emission_date(soup)
    products = parse_products(soup)
    total_value = parse_total_value(soup)
    total_taxes = parse_total_taxes(soup)
    access_key = parse_access_key(soup) or code
    
    # Use fallback if name not found instead of failing
    if not market_info["name"]:
        logger.warning("Market name not found, using fallback")
        market_info["name"] = "Estabelecimento não identificado"
    
    if not products:
        logger.error("No products found in NFC-e")
        raise Exception("No products found in NFC-e.")
    
    logger.info(f"Successfully parsed NFC-e: {market_info['name']}, {len(products)} products, R$ {total_value:.2f}")
    
    return {
        "access_key": access_key,
        "market_name": market_info["name"],
        "market_cnpj": market_info["cnpj"],
        "market_address": market_info["address"],
        "emission_date": emission_date,
        "total_value": total_value,
        "total_taxes": total_taxes,
        "products": products
    }

