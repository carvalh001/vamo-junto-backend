import re


def validate_cpf(cpf: str) -> bool:
    """Validate Brazilian CPF format and checksum"""
    # Remove non-numeric characters
    cpf = re.sub(r"[^\d]", "", cpf)
    
    # Check length
    if len(cpf) != 11:
        return False
    
    # Check if all digits are the same (invalid CPF)
    if cpf == cpf[0] * 11:
        return False
    
    # Validate checksum
    def calculate_digit(cpf_digits: str, weights: list) -> int:
        total = sum(int(digit) * weight for digit, weight in zip(cpf_digits, weights))
        remainder = total % 11
        return 0 if remainder < 2 else 11 - remainder
    
    # Validate first digit
    first_digit = calculate_digit(cpf[:9], list(range(10, 1, -1)))
    if int(cpf[9]) != first_digit:
        return False
    
    # Validate second digit
    second_digit = calculate_digit(cpf[:10], list(range(11, 1, -1)))
    if int(cpf[10]) != second_digit:
        return False
    
    return True


def format_cpf(cpf: str) -> str:
    """Format CPF to XXX.XXX.XXX-XX"""
    cpf = re.sub(r"[^\d]", "", cpf)
    if len(cpf) == 11:
        return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
    return cpf


def validate_nfce_code(code: str) -> bool:
    """Validate NFC-e access code format (44 digits)"""
    # Remove spaces and non-numeric characters
    code = re.sub(r"[^\d]", "", code)
    # Check if it's exactly 44 digits
    return len(code) == 44 and code.isdigit()


def format_nfce_code(code: str) -> str:
    """Format NFC-e code to 11 groups of 4 digits"""
    code = re.sub(r"[^\d]", "", code)
    if len(code) == 44:
        # Format as 11 groups of 4 digits
        return " ".join([code[i:i+4] for i in range(0, 44, 4)])
    return code


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))

