"""
validators.py
--------------
Regras de validação de campos para o pipeline de limpeza FastZap.
 
Cada função de validação retorna uma tupla: (valido: bool, valor_normalizado: str | None, motivo: str | None)
Esse padrão é proposital: o pandas vai usar o resultado tanto para decidir
se a linha é aceita quanto para já receber o valor formatado, evitando
duas passagens sobre os dados (uma para validar, outra para limpar).
 
País padrão (fallback) usado quando o telefone não traz DDI explícito.
Ajuste conforme a operação principal da empresa.
"""

import re 
from datetime import datetime 

import phonenumbers
from phonenumbers import NumberParseException

#Configurações Gerais 

PAIS_PADRAO_FALLBACK = "BR"


FORMATOS_DATA_ACEITOS = [
    "%d/%m/%Y",      
    "%Y-%m-%d",
    "%d-%m-%Y",
    "%d/%m/%Y",      
]

REGEX_EMAIL = re.compile(
    r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"    
)

#------------------
# NOME É OBRIGATÓRIO 
#------------------

def validar_nome(nome) -> tuple[bool, str | None, str | None]:

    if nome is None or (isinstance(nome, float)):
        return False, None, "Nome vazio"

    nome_str = str(nome).strip()
    if not nome_str:
        return False, None, "Nome vazio"

    # Reduz múltiplos espaços a um só. (ex: "João   André" -> "João André")
    nome_normalizado = re.sub(r"\s+", " ", nome_str)

    # Precisa ao menos ter uma letra (unicode-aware, cobre acentos)
    if not re.search(r"[^\W\d_]", nome_normalizado, flags=re.UNICODE):   
        return False, None, "Nome sem caracteres alfabéticos"

    return True, nome_normalizado, None

#----------------------------
# TELEFONE (obrigatório, a exemplo do Nome e multi-país)
#----------------------------

def validar_telefone(
        telefone,
        pais_fallback: str = PAIS_PADRAO_FALLBACK,
) -> tuple[bool, str | None, str | None]:

    if telefone is None or (isinstance(telefone, float) and str(telefone) == 'nan'):
        return False, None, "Telefone vazio"

    apenas_digitos = re.sub(r"\D", "", str(telefone))
    if not apenas_digitos:
        return False, None, "Telefone vazio"

    num_parseado = _tentar_parse(apenas_digitos, None)
    if num_parseado is not None and phonenumbers.is_valid_number(num_parseado):
        formatado = phonenumbers.format_number(
            num_parseado, phonenumbers.PhoneNumberFormat.E164
        )
        return True, formatado, None

    numero_fallback = _tentar_parse(apenas_digitos, pais_fallback)
    if numero_fallback is not None and phonenumbers.is_valid_number(numero_fallback):
        formatado = phonenumbers.format_number(
            numero_fallback, phonenumbers.PhoneNumberFormat.E164
        )
        return True, formatado, None    

    return False, None, "Telefone não reconhecido como válido em nenhum país testado."

def _tentar_parse(numero: str, regiao: str | None):

    try:
        candidato = f'+{numero}' if regiao is None else numero
        return phonenumbers.parse(candidato, regiao)
    except NumberParseException:
        return None


##---------------------
# E-mail (Opcional)
##---------------------

def validar_email(email) -> tuple[bool, str | None, str | None]:

    if email is None or (isinstance(email, float)):
        return True, None, None #já que a ausência aqui não é uma obrigatoriedade

    email_str = str(email).strip()
    if not email_str:
        return True, None, None #célula vazia, está Ok também 

    email_normalizado = email_str.lower()
    if not REGEX_EMAIL.match(email_normalizado):
        return False, None, "E-mail em formato inválido"

    return True, email_normalizado, None

# ---------------------------
# Data de Nascimento (Opcional)
# ---------------------------

def validar_data_nascimento(data) -> tuple [bool, str |None, str |None]:

    if data is None or (isinstance(data, float)):
        return True, None, None 

    data_str = str(data).strip()
    if not data_str:
        return True, None, None 

    for formato in FORMATOS_DATA_ACEITOS:
        try:
            data_convertida = datetime.strptime(data_str, formato)
            if data_convertida > datetime.now():
                return False, None, "Data de nascimento no futuro."
            return True, data_convertida.strftime("%Y-%m-%d"), None
        except ValueError:
            continue

    return False, None, f"Formato de data não reconhecido: '{data_str}'"