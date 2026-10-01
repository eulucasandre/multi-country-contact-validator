"""
test_cleaners.py
-----------------
Testes unitários para source/cleaners.py.

Cobrimos separadamente:
- mapear_colunas: reconhecimento automático de nomes de coluna variados
- ler_planilha: leitura de .csv e .xlsx, preservando texto (dtype=str)
- limpar_dados: o fluxo completo (validação linha a linha + separação
  aceitos/rejeitados + relatório), incluindo o caso de linha com
  múltiplos motivos de rejeição ao mesmo tempo.
"""

import pandas as pd
import pytest

from source.cleaners import (
    mapear_colunas,
    ler_planilha,
    limpar_dados,
)


# ---------------------------------------------------------------------------
# mapear_colunas
# ---------------------------------------------------------------------------

class TestMapearColunas:
    def test_colunas_com_nomes_padrao(self):
        mapeamento = mapear_colunas(["Nome", "Telefone", "Email"])
        assert mapeamento["nome"] == "Nome"
        assert mapeamento["telefone"] == "Telefone"
        assert mapeamento["email"] == "Email"
        assert "data_nascimento" not in mapeamento  # coluna não existia

    def test_colunas_com_nomes_alternativos_e_acentos(self):
        colunas = ["Nome Completo", "Celular", "E-mail", "Data Nasc"]
        mapeamento = mapear_colunas(colunas)
        assert mapeamento == {
            "nome": "Nome Completo",
            "telefone": "Celular",
            "email": "E-mail",
            "data_nascimento": "Data Nasc",
        }

    def test_colunas_case_insensitive_e_com_underscore(self):
        colunas = ["NOME", "telefone_celular"]
        mapeamento = mapear_colunas(colunas)
        assert mapeamento["nome"] == "NOME"
        assert mapeamento["telefone"] == "telefone_celular"

    def test_falta_coluna_obrigatoria_levanta_erro_claro(self):
        with pytest.raises(ValueError) as exc_info:
            mapear_colunas(["Coisa", "Outra Coisa"])
        # A mensagem precisa mencionar os campos que faltaram, não só "erro genérico"
        assert "nome" in str(exc_info.value)
        assert "telefone" in str(exc_info.value)

    def test_falta_so_telefone_e_relatado_especificamente(self):
        with pytest.raises(ValueError) as exc_info:
            mapear_colunas(["Nome"])
        assert "telefone" in str(exc_info.value)
        assert "nome" not in str(exc_info.value).split("obrigatória(s)")[1].split("na planilha")[0]


# ---------------------------------------------------------------------------
# ler_planilha
# ---------------------------------------------------------------------------

class TestLerPlanilha:
    def test_le_csv_como_texto(self, tmp_path):
        caminho = tmp_path / "teste.csv"
        caminho.write_text("Nome,Telefone\nAna,5586999998888\n", encoding="utf-8")

        df = ler_planilha(caminho)
        assert list(df.columns) == ["Nome", "Telefone"]
        # dtype=str: telefone não pode virar número (perderia zeros à esquerda)
        assert df.iloc[0]["Telefone"] == "5586999998888"
        assert isinstance(df.iloc[0]["Telefone"], str)

    def test_le_xlsx_como_texto(self, tmp_path):
        caminho = tmp_path / "teste.xlsx"
        pd.DataFrame({"Nome": ["Ana"], "Telefone": ["5586999998888"]}).to_excel(
            caminho, index=False
        )

        df = ler_planilha(caminho)
        assert df.iloc[0]["Telefone"] == "5586999998888"
        assert isinstance(df.iloc[0]["Telefone"], str)

    def test_remove_linhas_totalmente_vazias(self, tmp_path):
        caminho = tmp_path / "teste.csv"
        caminho.write_text("Nome,Telefone\nAna,5586999998888\n,\n", encoding="utf-8")

        df = ler_planilha(caminho)
        assert len(df) == 1  # a linha só com vírgula (tudo vazio) deve sumir

    def test_formato_nao_suportado_levanta_erro(self, tmp_path):
        caminho = tmp_path / "teste.txt"
        caminho.write_text("qualquer coisa", encoding="utf-8")

        with pytest.raises(ValueError, match="não suportado"):
            ler_planilha(caminho)


# ---------------------------------------------------------------------------
# limpar_dados (fluxo completo)
# ---------------------------------------------------------------------------

class TestLimparDados:
    def test_planilha_exemplo_original(self):
        """Reproduz o caso real da planilha de exemplo do FastZap."""
        df = pd.DataFrame({
            "Nome": ["Cliente 1", "Cliente 2", "Cliente 3"],
            "Telefone": ["5586999999999", "5586981818181", ""],
            "Email": ["cliente1@exemplo.com", "", "cliente3@exemplo.com"],
        })

        aceitos, rejeitados, relatorio = limpar_dados(df)

        assert len(aceitos) == 2
        assert len(rejeitados) == 1
        assert relatorio["total_processado"] == 3
        assert relatorio["aceitos"] == 2
        assert relatorio["rejeitados"] == 1
        assert relatorio["motivos_rejeicao"] == {"Telefone vazio": 1}

        # Telefone precisa estar formatado em E.164 na saída
        assert aceitos.iloc[0]["Telefone"] == "+5586999999999"

    def test_linha_com_multiplos_motivos_de_rejeicao(self):
        df = pd.DataFrame({
            "Nome": [""],
            "Telefone": ["abc"],
            "Email": ["invalido"],
        })

        _, rejeitados, relatorio = limpar_dados(df)

        assert len(rejeitados) == 1
        motivo = rejeitados.iloc[0]["Motivo_Rejeicao"]
        # Os 3 motivos precisam estar concatenados na mesma linha, com "; "
        assert "Nome vazio" in motivo
        assert "Telefone vazio" in motivo
        assert "E-mail em formato inválido" in motivo
        assert relatorio["motivos_rejeicao"]["Nome vazio"] == 1

    def test_colunas_opcionais_ausentes_nao_quebram_o_processo(self):
        """Planilha só com Nome e Telefone (sem Email/Data) deve funcionar normalmente."""
        df = pd.DataFrame({
            "Nome": ["Ana Souza"],
            "Telefone": ["5586999998888"],
        })

        aceitos, rejeitados, relatorio = limpar_dados(df)

        assert len(aceitos) == 1
        assert relatorio["aceitos"] == 1
        assert aceitos.iloc[0]["Email"] is None
        assert aceitos.iloc[0]["Data_Nascimento"] is None

    def test_colunas_com_nomes_alternativos_sao_reconhecidas(self):
        df = pd.DataFrame({
            "Nome Completo": ["Bruno Lima"],
            "Celular": ["5586999998888"],
        })

        aceitos, _, relatorio = limpar_dados(df)

        assert relatorio["aceitos"] == 1
        assert aceitos.iloc[0]["Nome"] == "Bruno Lima"

    def test_dataframe_totalmente_valido_nao_gera_rejeitados(self):
        df = pd.DataFrame({
            "Nome": ["Ana", "Bruno"],
            "Telefone": ["5586999998888", "5586977776666"],
        })

        aceitos, rejeitados, relatorio = limpar_dados(df)

        assert len(aceitos) == 2
        assert len(rejeitados) == 0
        assert relatorio["motivos_rejeicao"] == {}

    def test_falta_coluna_obrigatoria_propaga_erro(self):
        df = pd.DataFrame({"Coisa": ["a"]})
        with pytest.raises(ValueError):
            limpar_dados(df)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])