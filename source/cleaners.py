import unicodedata
from pathlib import Path

import pandas as pd

from source.validador import (
    validar_nome,
    validar_telefone,
    validar_email,
    validar_data_nascimento,
)

# ---------------------------------------------------------------------------
# Reconhecimento automático de colunas
# ---------------------------------------------------------------------------
# Cada campo interno tem uma lista de "apelidos" possíveis que o cliente
# pode ter usado na planilha. Comparação é feita já normalizada (sem
# acento, minúsculo, sem espaço/underscore extra), então "Data de Nascimento",
# "data_nascimento" e "DATA NASCIMENTO" caem todos no mesmo lugar.

ALIASES_COLUNAS = {
    "nome": ["nome", "nome completo", "cliente", "name", "nomecompleto"],
    "telefone": [
        "telefone", "telefone celular", "celular", "fone", "whatsapp",
        "phone", "numero", "número", "numerotelefone", "telefonecelular",
    ],
    "email": ["email", "e-mail", "mail", "correio eletronico"],
    "data_nascimento": [
        "data de nascimento", "data_nascimento", "nascimento",
        "dt nascimento", "birthday", "data nasc", "datanascimento",
    ],
}

# Campos que OBRIGATORIAMENTE precisam ser encontrados na planilha.
# Se não acharmos uma coluna correspondente, é erro de estrutura (não dá
# nem pra processar), diferente de uma LINHA individual estar incompleta.
CAMPOS_OBRIGATORIOS = ["nome", "telefone"]


def _normalizar_nome_coluna(col: str) -> str:
    """
    Remove acentos, baixa a caixa e colapsa espaços/underscores,
    para permitir comparação tolerante entre "Telefone Celular",
    "telefone_celular" e "TELEFONE CELULAR".
    """
    sem_acento = unicodedata.normalize("NFKD", str(col))
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    return sem_acento.strip().lower().replace("_", " ").replace("-", " ")


def mapear_colunas(colunas_originais: list[str]) -> dict[str, str]:
    """
    Recebe as colunas como vieram no arquivo e devolve um dicionário
    {campo_interno: nome_original_da_coluna} para os campos que
    conseguimos identificar.

    Levanta ValueError se algum campo OBRIGATÓRIO (nome, telefone) não
    for encontrado — nesse caso o problema é estrutural, então preferimos
    falhar cedo e com uma mensagem clara, em vez de processar tudo errado.
    """
    normalizadas = {col: _normalizar_nome_coluna(col) for col in colunas_originais}

    mapeamento: dict[str, str] = {}
    for campo_interno, apelidos in ALIASES_COLUNAS.items():
        apelidos_normalizados = {_normalizar_nome_coluna(a) for a in apelidos}
        for col_original, col_normalizada in normalizadas.items():
            if col_normalizada in apelidos_normalizados:
                mapeamento[campo_interno] = col_original
                break

    faltando = [c for c in CAMPOS_OBRIGATORIOS if c not in mapeamento]
    if faltando:
        raise ValueError(
            "Não foi possível identificar a(s) coluna(s) obrigatória(s) "
            f"{faltando} na planilha. Colunas encontradas: {colunas_originais}. "
            "Renomeie a coluna para algo como 'Nome' e 'Telefone' e tente novamente."
        )

    return mapeamento


# ---------------------------------------------------------------------------
# Leitura do arquivo (csv ou xlsx)
# ---------------------------------------------------------------------------

def ler_planilha(caminho: str | Path) -> pd.DataFrame:
    """
    Lê .csv ou .xlsx a partir da extensão do arquivo.
    dtype=str força tudo a vir como texto — importante para telefones
    (senão o pandas pode interpretar como número e comer o zero à
    esquerda ou converter para notação científica) e datas (evita que
    o pandas já tente adivinhar um tipo datetime por conta própria).
    """
    caminho = Path(caminho)
    if caminho.suffix.lower() == ".csv":
        df = pd.read_csv(caminho, dtype=str)
    elif caminho.suffix.lower() in (".xlsx", ".xls"):
        df = pd.read_excel(caminho, dtype=str, engine="openpyxl")
    else:
        raise ValueError(f"Formato de arquivo não suportado: {caminho.suffix}")

    # Remove linhas 100% vazias (comuns no fim de planilhas exportadas)
    df = df.dropna(how="all")
    return df


# ---------------------------------------------------------------------------
# Limpeza linha a linha
# ---------------------------------------------------------------------------

def _validar_linha(row: pd.Series, mapeamento: dict[str, str]) -> pd.Series:
    """
    Aplica todos os validadores numa linha e devolve os valores
    normalizados + se a linha é válida + a lista de motivos de rejeição
    (concatenados, já que uma linha pode falhar em mais de um campo).
    """
    motivos = []

    ok_nome, valor_nome, motivo_nome = validar_nome(row.get(mapeamento.get("nome")))
    if not ok_nome:
        motivos.append(motivo_nome)

    ok_tel, valor_tel, motivo_tel = validar_telefone(row.get(mapeamento.get("telefone")))
    if not ok_tel:
        motivos.append(motivo_tel)

    # Campos opcionais: só existem no mapeamento se a coluna foi encontrada.
    # Se a coluna nem existe na planilha, tratamos como ausente (não é erro).
    valor_email = None
    if "email" in mapeamento:
        ok_email, valor_email, motivo_email = validar_email(row.get(mapeamento["email"]))
        if not ok_email:
            motivos.append(motivo_email)

    valor_data = None
    if "data_nascimento" in mapeamento:
        ok_data, valor_data, motivo_data = validar_data_nascimento(
            row.get(mapeamento["data_nascimento"])
        )
        if not ok_data:
            motivos.append(motivo_data)

    return pd.Series({
        "Nome": valor_nome,
        "Telefone": valor_tel,
        "Email": valor_email,
        "Data_Nascimento": valor_data,
        "_valido": len(motivos) == 0,
        "Motivo_Rejeicao": "; ".join(motivos) if motivos else None,
    })


def limpar_dados(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """
    Função principal do módulo. Recebe o DataFrame bruto (já lido do
    arquivo) e devolve:
      - df_aceitos: apenas colunas normalizadas (Nome, Telefone, Email, Data_Nascimento)
      - df_rejeitados: os dados originais + coluna Motivo_Rejeicao
      - relatorio: dict com contagens (total, aceitos, rejeitados, e por motivo)
    """
    mapeamento = mapear_colunas(list(df.columns))

    resultados = df.apply(lambda row: _validar_linha(row, mapeamento), axis=1)

    mascara_validos = resultados["_valido"]

    df_aceitos = resultados.loc[mascara_validos, ["Nome", "Telefone", "Email", "Data_Nascimento"]].reset_index(drop=True)

    # Para os rejeitados, mantemos os dados ORIGINAIS (não os normalizados,
    # já que muitos nem passaram na validação) + o motivo, para facilitar
    # a correção manual por quem for revisar.
    df_rejeitados = df.loc[~mascara_validos].copy().reset_index(drop=True)
    df_rejeitados["Motivo_Rejeicao"] = resultados.loc[~mascara_validos, "Motivo_Rejeicao"].reset_index(drop=True)

    relatorio = _gerar_relatorio(resultados)

    return df_aceitos, df_rejeitados, relatorio


def _gerar_relatorio(resultados: pd.DataFrame) -> dict:
    """
    Monta um resumo simples: total processado, quantos aceitos, quantos
    rejeitados, e uma contagem por motivo individual (já que uma linha
    pode contribuir para mais de um motivo ao mesmo tempo).
    """
    total = len(resultados)
    aceitos = int(resultados["_valido"].sum())
    rejeitados = total - aceitos

    contagem_motivos: dict[str, int] = {}
    for motivos_str in resultados.loc[~resultados["_valido"], "Motivo_Rejeicao"]:
        for motivo in motivos_str.split("; "):
            contagem_motivos[motivo] = contagem_motivos.get(motivo, 0) + 1

    return {
        "total_processado": total,
        "aceitos": aceitos,
        "rejeitados": rejeitados,
        "motivos_rejeicao": contagem_motivos,
    }