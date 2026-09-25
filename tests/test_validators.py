"""
test_validators.py
-------------------
Testes unitários para src/validators.py.

Organização: um bloco de testes por campo (nome, telefone, email, data),
cobrindo: caso feliz, caso obrigatório ausente, e casos de borda que já
nos morderam durante o desenvolvimento manual (ex: número sem DDI sendo
mal interpretado como código de outro país).
"""

import pytest

from source.validador import (
    validar_nome,
    validar_telefone,
    validar_email,
    validar_data_nascimento,
)


# ---------------------------------------------------------------------------
# NOME
# ---------------------------------------------------------------------------

class TestValidarNome:
    def test_nome_valido_simples(self):
        ok, valor, motivo = validar_nome("Cliente 1")
        assert ok is True
        assert valor == "Cliente 1"
        assert motivo is None

    def test_nome_com_espacos_extras_e_normalizado(self):
        ok, valor, motivo = validar_nome("  João   Silva  ")
        assert ok is True
        assert valor == "João Silva"  # espaços colapsados e bordas removidas

    def test_nome_vazio_e_rejeitado(self):
        ok, valor, motivo = validar_nome("")
        assert ok is False
        assert valor is None
        assert motivo == "Nome vazio"

    def test_nome_none_e_rejeitado(self):
        ok, valor, motivo = validar_nome(None)
        assert ok is False
        assert motivo == "Nome vazio"

    def test_nome_apenas_espacos_e_rejeitado(self):
        ok, valor, motivo = validar_nome("     ")
        assert ok is False
        assert motivo == "Nome vazio"

    def test_nome_sem_letras_e_rejeitado(self):
        ok, valor, motivo = validar_nome("12345")
        assert ok is False
        assert motivo == "Nome sem caracteres alfabéticos"

    def test_nome_com_acentos_e_aceito(self):
        ok, valor, motivo = validar_nome("José André")
        assert ok is True
        assert valor == "José André"


# ---------------------------------------------------------------------------
# TELEFONE
# ---------------------------------------------------------------------------

class TestValidarTelefone:
    def test_telefone_br_com_ddi_valido(self):
        ok, valor, motivo = validar_telefone("5586999999999")
        assert ok is True
        assert valor == "+5586999999999"
        assert motivo is None

    def test_telefone_br_sem_ddi_aciona_fallback(self):
        # Caso real que gerou o bug corrigido: sem o "55" na frente,
        # o número precisa cair no fallback BR e ainda assim validar.
        ok, valor, motivo = validar_telefone("86999998888")
        assert ok is True
        assert valor == "+5586999998888"

    def test_telefone_eua_com_ddi_valido(self):
        ok, valor, motivo = validar_telefone("12125551234")
        assert ok is True
        assert valor.startswith("+1")

    def test_telefone_italia_com_ddi_valido(self):
        ok, valor, motivo = validar_telefone("390212345678")
        assert ok is True
        assert valor.startswith("+39")

    def test_telefone_argentina_com_ddi_valido(self):
        ok, valor, motivo = validar_telefone("541123456789")
        assert ok is True
        assert valor.startswith("+54")

    def test_telefone_vazio_e_rejeitado(self):
        ok, valor, motivo = validar_telefone("")
        assert ok is False
        assert motivo == "Telefone vazio"

    def test_telefone_none_e_rejeitado(self):
        ok, valor, motivo = validar_telefone(None)
        assert ok is False
        assert motivo == "Telefone vazio"

    def test_telefone_muito_curto_e_rejeitado(self):
        ok, valor, motivo = validar_telefone("123")
        assert ok is False
        assert "não reconhecido" in motivo

    def test_telefone_com_caracteres_de_formatacao_e_limpo_antes_de_validar(self):
        # Simula como o número pode vir de uma planilha real, com máscara
        ok, valor, motivo = validar_telefone("(86) 99999-9999")
        assert ok is True
        assert valor == "+5586999999999"

    def test_telefone_nao_deve_ser_mal_interpretado_como_outro_pais(self):
        # Regressão do bug: "86999998888" sem DDI não pode virar um número
        # chinês inválido só porque "86" é o código da China.
        ok, valor, motivo = validar_telefone("86999998888")
        assert ok is True
        assert valor.startswith("+55")  # tem que cair no fallback BR, não CN


# ---------------------------------------------------------------------------
# EMAIL (opcional)
# ---------------------------------------------------------------------------

class TestValidarEmail:
    def test_email_valido(self):
        ok, valor, motivo = validar_email("cliente1@exemplo.com")
        assert ok is True
        assert valor == "cliente1@exemplo.com"

    def test_email_e_normalizado_para_minusculas(self):
        ok, valor, motivo = validar_email("Nome@Dominio.COM")
        assert ok is True
        assert valor == "nome@dominio.com"

    def test_email_ausente_e_valido_por_ser_opcional(self):
        ok, valor, motivo = validar_email(None)
        assert ok is True
        assert valor is None
        assert motivo is None

    def test_email_string_vazia_e_valido_por_ser_opcional(self):
        ok, valor, motivo = validar_email("")
        assert ok is True
        assert valor is None

    def test_email_mal_formatado_e_rejeitado(self):
        ok, valor, motivo = validar_email("nao-e-um-email")
        assert ok is False
        assert motivo == "E-mail em formato inválido"

    def test_email_sem_dominio_e_rejeitado(self):
        ok, valor, motivo = validar_email("usuario@")
        assert ok is False


# ---------------------------------------------------------------------------
# DATA DE NASCIMENTO (opcional)
# ---------------------------------------------------------------------------

class TestValidarDataNascimento:
    def test_data_formato_brasileiro_e_convertida_para_iso(self):
        ok, valor, motivo = validar_data_nascimento("25/12/1990")
        assert ok is True
        assert valor == "1990-12-25"

    def test_data_ja_em_iso_e_mantida(self):
        ok, valor, motivo = validar_data_nascimento("1990-12-25")
        assert ok is True
        assert valor == "1990-12-25"

    def test_data_ausente_e_valida_por_ser_opcional(self):
        ok, valor, motivo = validar_data_nascimento(None)
        assert ok is True
        assert valor is None

    def test_data_string_vazia_e_valida_por_ser_opcional(self):
        ok, valor, motivo = validar_data_nascimento("")
        assert ok is True
        assert valor is None

    def test_data_no_futuro_e_rejeitada(self):
        ok, valor, motivo = validar_data_nascimento("31/12/2099")
        assert ok is False
        assert motivo == "Data de nascimento no futuro."

    def test_data_em_formato_nao_reconhecido_e_rejeitada(self):
        ok, valor, motivo = validar_data_nascimento("não é uma data")
        assert ok is False
        assert "não reconhecido" in motivo


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
