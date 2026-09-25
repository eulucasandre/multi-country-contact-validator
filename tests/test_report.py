"""
test_report.py
---------------
Testes para src/report.py — formatação do relatório em texto.
"""

from source.report import formatar_relatorio_texto, formatar_relatorio_resumido


class TestFormatarRelatorioTexto:
    def test_com_rejeicoes_lista_motivos_do_mais_comum_ao_menos_comum(self):
        relatorio = {
            "total_processado": 10,
            "aceitos": 6,
            "rejeitados": 4,
            "motivos_rejeicao": {"telefone vazio": 1, "nome vazio": 3},
        }
        texto = formatar_relatorio_texto(relatorio, nome_arquivo="teste.csv")

        assert "teste.csv" in texto
        assert "Total de linhas processadas: 10" in texto
        assert "Aceitadas: 6" in texto
        assert "Rejeitadas: 4" in texto
        # "nome vazio" (3 ocorrências) deve aparecer ANTES de "telefone vazio" (1)
        pos_nome = texto.index("nome vazio")
        pos_telefone = texto.index("telefone vazio")
        assert pos_nome < pos_telefone

    def test_sem_rejeicoes_nao_mostra_secao_de_motivos(self):
        relatorio = {
            "total_processado": 5,
            "aceitos": 5,
            "rejeitados": 0,
            "motivos_rejeicao": {},
        }
        texto = formatar_relatorio_texto(relatorio)

        assert "Motivos de rejeição" not in texto

    def test_sem_nome_arquivo_nao_gera_titulo(self):
        relatorio = {
            "total_processado": 1,
            "aceitos": 1,
            "rejeitados": 0,
            "motivos_rejeicao": {},
        }
        texto = formatar_relatorio_texto(relatorio)

        assert "Relatório de processamento" not in texto


class TestFormatarRelatorioResumido:
    def test_gera_uma_linha_com_os_tres_numeros(self):
        relatorio = {"total_processado": 10, "aceitos": 7, "rejeitados": 3}
        resumo = formatar_relatorio_resumido(relatorio)

        assert resumo == "10 processadas | 7 aceitas | 3 rejeitada(s)"
