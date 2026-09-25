

def formatar_relatorio_texto(relatorio: dict, nome_arquivo: str | None = None) -> str:


    linhas = []

    if nome_arquivo:
        titulo = f'Relatorio de processamento — {nome_arquivo}'
        linhas.append(titulo)
        linhas.append('=' * len(titulo))

    linhas.append(f'Total de linhas processadas: {relatorio["total_processado"]}')
    linhas.append(f'Aceitadas: {relatorio["aceitos"]}')
    linhas.append(f'Rejeitadas: {relatorio["rejeitados"]}')

    if relatorio['motivos_rejeicao']:
        linhas.append('')
        linhas.append('Motivos de rejeição:')


        motivos_ordenados = sorted(
            relatorio['motivos_rejeicao'].items(), key = lambda item: -item[1]
        )
        for motivo, quantidade in motivos_ordenados:
            linhas.append(f' -{motivo}: {quantidade}')

    return '\n'.join(linhas)

def formatar_relatorio_resumido(relatorio: dict) -> str:
    return (
        f"{relatorio['total_processado']} processadas | "      
        f"{relatorio['aceitos']} aceitas | "                     
        f"{relatorio['rejeitados']} rejeitada(s)"
    )