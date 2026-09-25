from pathlib import Path 

from source.cleaners import ler_planilha, limpar_dados 
from source.report import formatar_relatorio_texto

class ErroProcessamento(Exception):

    pass

def processar_arquivo(caminho_arquivo: Path, pasta_saida: Path) -> dict:

    caminho_entrada = Path(caminho_arquivo)
    pasta_saida = Path(pasta_saida)
    pasta_saida.mkdir(parents=True, exist_ok=True)


# ---- 1. Leitura ------------------
    try:
        df = ler_planilha(caminho_entrada)
    except FileNotFoundError:
        raise ErroProcessamento(f'Arquivo não encontrado: {caminho_entrada.name}')
    except ValueError as error:

        raise ErroProcessamento(str(error))
    except Exception as error:
        raise ErroProcessamento(
            f"Não foi possível ler o arquivo '{caminho_entrada.name}'"
            f'Verifique se ele não está corrompido ou se o formato é compatível. Detalhes do erro: {error}'
            )

    if df.empty:
        raise ErroProcessamento(
            'A planilha está vazia - nenhuma linha de dados encontrada para processar.'
        )

# ---- 2. Limpeza ------------------
    try:
        df_aceitos, df_rejeitados, relatorio = limpar_dados(df)
    except ValueError as error:

        raise ErroProcessamento(str(error))

# ---- 3. Exportação ------------------

    caminhos_aceitos = pasta_saida / 'dados_limpos.xlsx'
    df_aceitos.to_excel(caminhos_aceitos, index=False)

    caminhos_rejeitados = None
    if not df_rejeitados.empty:
        caminhos_rejeitados = pasta_saida / 'linhas_rejeitadas.xlsx'
        df_rejeitados.to_excel(caminhos_rejeitados, index=False)

# ---- 4. Relatório ------------------
    relatorio_texto = formatar_relatorio_texto(relatorio, nome_arquivo=caminho_entrada.name)

    return {
        'sucesso': True,
        'relatorio': relatorio,
        'relatorio_texto': relatorio_texto,
        'caminho_aceitos': str(caminhos_aceitos),
        'caminho_rejeitados': str(caminhos_rejeitados) if caminhos_rejeitados else None,
    }