"""
test_pipeline.py
-----------------
Testes para src/pipeline.py — o fluxo completo ler -> limpar -> exportar.
"""

import pandas as pd
import pytest

from source.pipeline import processar_arquivo, ErroProcessamento


class TestProcessarArquivo:
    def test_fluxo_feliz_gera_dois_arquivos_e_relatorio(self, tmp_path):
        entrada = tmp_path / "contatos.csv"
        entrada.write_text(
            "Nome,Telefone,Email\n"
            "Cliente 1,5586999999999,cliente1@exemplo.com\n"
            "Cliente 2,5586981818181,\n"
            "Cliente 3,,cliente3@exemplo.com\n",
            encoding="utf-8",
        )
        pasta_saida = tmp_path / "saida"

        resultado = processar_arquivo(entrada, pasta_saida)

        assert resultado["sucesso"] is True
        assert resultado["relatorio"]["aceitos"] == 2
        assert resultado["relatorio"]["rejeitados"] == 1
        assert (pasta_saida / "dados_limpos.xlsx").exists()
        assert (pasta_saida / "linhas_rejeitadas.xlsx").exists()
        assert "Telefone vazio" in resultado["relatorio_texto"]

    def test_sem_rejeitados_nao_cria_arquivo_de_rejeitados(self, tmp_path):
        entrada = tmp_path / "contatos.csv"
        entrada.write_text(
            "Nome,Telefone\nAna,5586999998888\nBruno,5586977776666\n",
            encoding="utf-8",
        )
        pasta_saida = tmp_path / "saida"

        resultado = processar_arquivo(entrada, pasta_saida)

        assert resultado["caminho_rejeitados"] is None
        assert not (pasta_saida / "linhas_rejeitadas.xlsx").exists()
        assert (pasta_saida / "dados_limpos.xlsx").exists()

    def test_arquivo_inexistente_levanta_erro_amigavel(self, tmp_path):
        with pytest.raises(ErroProcessamento, match="não encontrado"):
            processar_arquivo(tmp_path / "nao_existe.csv", tmp_path / "saida")

    def test_coluna_obrigatoria_faltando_levanta_erro_amigavel(self, tmp_path):
        entrada = tmp_path / "contatos.csv"
        entrada.write_text("Coisa,Outra\na,b\n", encoding="utf-8")

        with pytest.raises(ErroProcessamento, match="obrigatória"):
            processar_arquivo(entrada, tmp_path / "saida")

    def test_planilha_vazia_levanta_erro_amigavel(self, tmp_path):
        entrada = tmp_path / "contatos.csv"
        entrada.write_text("Nome,Telefone\n", encoding="utf-8")

        with pytest.raises(ErroProcessamento, match="vazia"):
            processar_arquivo(entrada, tmp_path / "saida")

    def test_extensao_nao_suportada_levanta_erro_amigavel(self, tmp_path):
        entrada = tmp_path / "contatos.txt"
        entrada.write_text("qualquer coisa", encoding="utf-8")

        with pytest.raises(ErroProcessamento, match="não suportado"):
            processar_arquivo(entrada, tmp_path / "saida")

    def test_aceita_xlsx_como_entrada(self, tmp_path):
        entrada = tmp_path / "contatos.xlsx"
        pd.DataFrame({
            "Nome": ["Ana"],
            "Telefone": ["5586999998888"],
        }).to_excel(entrada, index=False)

        resultado = processar_arquivo(entrada, tmp_path / "saida")

        assert resultado["relatorio"]["aceitos"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
