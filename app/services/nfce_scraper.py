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


def build_consult_url(code: str) -> str:
    """Build consultation URL for NFC-e"""
    # Format code as 11 groups of 4 digits
    formatted_code = " ".join([code[i:i+4] for i in range(0, 44, 4)])
    # Build URL - try the QR code format first
    url = f"{settings.nfce_base_url}/NFCeConsultaPublica/Paginas/ConsultaQRCode.aspx?p={code}|2|1|1|"
    return url


def fetch_nfce_html(code: str) -> str:
    """Fetch HTML content from Fazenda SP"""
    url = build_consult_url(code)
    
    try:
        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()
            return response.text
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
        # Market name - usually in a div with class "txtTopo" or similar
        name_elem = soup.find("div", class_="txtTopo")
        if name_elem:
            market_info["name"] = name_elem.get_text(strip=True)
        
        # CNPJ - usually follows "CNPJ:" text
        cnpj_elem = soup.find(string=re.compile(r"CNPJ:"))
        if cnpj_elem:
            parent = cnpj_elem.find_parent()
            if parent:
                cnpj_text = parent.get_text(strip=True)
                cnpj_match = re.search(r"CNPJ:\s*([\d./-]+)", cnpj_text)
                if cnpj_match:
                    market_info["cnpj"] = cnpj_match.group(1)
        
        # Address - usually in a div with class "text"
        address_elems = soup.find_all("div", class_="text")
        address_parts = []
        for elem in address_elems:
            text = elem.get_text(strip=True)
            # Skip CNPJ line
            if "CNPJ:" not in text and len(text) > 10:
                address_parts.append(text)
        
        if address_parts:
            market_info["address"] = ", ".join(address_parts)
    except Exception as e:
        logger.warning(f"Error parsing market info: {e}")
    
    return market_info


def parse_emission_date(soup: BeautifulSoup) -> datetime:
    """Parse emission date from HTML"""
    try:
        # Look for "Emissão:" text
        emission_elem = soup.find(string=re.compile(r"Emissão:"))
        if emission_elem:
            parent = emission_elem.find_parent()
            if parent:
                text = parent.get_text()
                # Pattern: DD/MM/YYYY HH:MM:SS
                date_match = re.search(r"(\d{2}/\d{2}/\d{4})\s+(\d{2}:\d{2}:\d{2})", text)
                if date_match:
                    date_str = f"{date_match.group(1)} {date_match.group(2)}"
                    return datetime.strptime(date_str, "%d/%m/%Y %H:%M:%S")
        
        # Fallback to current date
        logger.warning("Could not parse emission date, using current date")
        return datetime.utcnow()
    except Exception as e:
        logger.warning(f"Error parsing emission date: {e}")
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
    # Parse code
    code = parse_nfce_code(code_or_url)
    
    # Fetch HTML
    html_content = fetch_nfce_html(code)
    
    # Parse HTML
    soup = BeautifulSoup(html_content, "lxml")
    
    # Check if note was found
    error_elem = soup.find("div", id="erro")
    if error_elem and error_elem.get_text(strip=True):
        raise Exception("NFC-e not found or invalid. Please check the code.")
    
    # Parse data
    market_info = parse_market_info(soup)
    emission_date = parse_emission_date(soup)
    products = parse_products(soup)
    total_value = parse_total_value(soup)
    total_taxes = parse_total_taxes(soup)
    access_key = parse_access_key(soup) or code
    
    if not market_info["name"]:
        raise Exception("Could not parse NFC-e data. The format may have changed.")
    
    if not products:
        raise Exception("No products found in NFC-e.")
    
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

