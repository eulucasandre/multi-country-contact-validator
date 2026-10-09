# Contact Validator

Ferramenta web que valida e limpa planilhas de contatos antes da importação em um CRM — com reconhecimento automático de telefones de **qualquer país**, não só do Brasil.

Nasceu de uma necessidade real: planilhas de contatos vindas de fontes diferentes raramente seguem um padrão (nomes de coluna variam, telefones vêm com ou sem código de país, formatos de data inconsistentes). Esta ferramenta resolve isso de forma automática, validando campo a campo e devolvendo um relatório claro do que foi aceito, rejeitado e por quê.

## Objetivo

Receber uma planilha de contatos (`.csv` ou `.xlsx`) e devolver:
- Uma planilha **só com os contatos válidos**, formatados de forma consistente
- Uma planilha **com os contatos rejeitados**, cada um com o motivo da rejeição
- Um relatório resumido da operação

Tudo isso através de uma interface web simples — o usuário sobe o arquivo, recebe o resultado em segundos.

## Funcionalidades

- **Campos obrigatórios:** Nome e Telefone. Linhas sem eles são rejeitadas.
- **Telefone multi-país:** valida e formata números de qualquer país (não só Brasil) usando a mesma biblioteca que o Google usa no Android (`phonenumbers`), convertendo tudo para o padrão internacional E.164 (ex: `+5586999999999`). Se o número vier sem código de país, assume Brasil como fallback antes de rejeitar.
- **Campos opcionais:** Email e Data de Nascimento são validados **se presentes**, mas não travam a linha se estiverem ausentes.
- **Reconhecimento automático de colunas:** identifica "Nome", "Telefone", "Email", "Data de Nascimento" mesmo que venham com nomes diferentes (`Celular`, `Nome Completo`, `E-mail`, `Data Nasc`, etc.), sem exigir um cabeçalho exato.
- **Suporte a .csv e .xlsx**, tanto na entrada quanto na saída.
- **Relatório detalhado:** quantas linhas foram aceitas, rejeitadas, e a contagem de cada motivo de rejeição (ex: "telefone vazio: 3").

## Tecnologias utilizadas

| Camada | Tecnologia | Papel |
|---|---|---|
| Linguagem | Python 3.14 | Base de todo o projeto |
| Manipulação de dados | pandas | Leitura, limpeza e separação dos dados em planilhas |
| Leitura/escrita de Excel | openpyxl | Engine usada pelo pandas para `.xlsx` |
| Validação de telefone | phonenumbers | Porta Python da libphonenumber (Google) — valida e formata números de qualquer país |
| Backend/Frontend | Flask | Serve a página de upload e processa os arquivos |
| Testes | pytest | 55+ testes automatizados cobrindo validação, limpeza e pipeline completo |
| Hospedagem | Vercel | Deploy serverless, direto do GitHub |
| Versionamento | Git + GitHub | Controle de versão e portfólio público |

## Estrutura do projeto e papel de cada arquivo

```
contact-validator/
├── api/
│   └── index.py          # Aplicação Flask: rotas de upload e download
├── source/
│   ├── validador.py       # Valida UM valor por vez (nome, telefone, email, data)
│   ├── cleaners.py        # Aplica as validações numa planilha inteira (pandas)
│   ├── pipeline.py        # Orquestra: ler → validar → exportar
│   └── report.py          # Formata o relatório final em texto legível
├── templates/
│   └── upload.html        # Página de upload
├── static/
│   └── style.css          # Estilo da página
├── tests/
│   ├── test_validators.py # Testes dos validadores individuais
│   ├── test_cleaners.py   # Testes do reconhecimento de colunas e limpeza
│   ├── test_pipeline.py   # Testes do fluxo completo (ler → limpar → exportar)
│   └── test_report.py     # Testes da formatação do relatório
├── requirements.txt        # Dependências Python
├── vercel.json             # Configuração de deploy na Vercel
└── pytest.ini               # Configuração dos testes
```

### `source/validador.py`
Responsável por validar **um campo por vez**, sem saber nada sobre planilhas:
- `validar_nome` — exige ao menos uma letra, remove espaços duplicados
- `validar_telefone` — tenta interpretar o número com o DDI informado; se falhar, tenta de novo assumindo Brasil; formata sempre em E.164
- `validar_email` — opcional; valida formato e normaliza para minúsculas
- `validar_data_nascimento` — opcional; aceita múltiplos formatos de entrada e converte para ISO 8601 (`AAAA-MM-DD`)

### `source/cleaners.py`
Responsável por aplicar as validações numa **planilha inteira**:
- `mapear_colunas` — reconhece as colunas certas mesmo com nomes variados
- `ler_planilha` — lê `.csv` ou `.xlsx`, forçando tudo como texto pra evitar que o pandas corrompa telefones/datas
- `limpar_dados` — roda a validação linha a linha e separa aceitos de rejeitados, concatenando todos os motivos quando uma linha falha em mais de um campo

### `source/pipeline.py`
Ponto de entrada único: recebe o caminho do arquivo, chama `cleaners.py`, exporta os resultados (`.xlsx` e `.csv`) e monta o relatório. Qualquer erro esperado (arquivo vazio, coluna faltando, formato não suportado) vira uma mensagem amigável — nunca um erro técnico cru na tela do usuário.

### `source/report.py`
Transforma o dicionário de números do relatório em texto legível, pronto para mostrar ao usuário.

### `api/index.py`
A aplicação Flask: serve a página de upload, recebe o arquivo, chama o pipeline, empacota os resultados num `.zip` (dados limpos, rejeitados e relatório) e devolve pro usuário baixar — tudo numa única requisição, pensado para rodar em ambiente serverless (Vercel), onde não há estado persistente entre requisições.

## Rodando localmente

```bash
python3 -m venv .venv
source .venv/bin/activate      # ou activate.fish, dependendo do shell
pip install -r requirements.txt
python3 api/index.py
```

Acesse `http://127.0.0.1:5000`.

## Rodando os testes

```bash
pytest -v
```

## Decisões de design relevantes

- **Validação multi-país em vez de máscara fixa:** a empresa de origem do projeto atende clientes em vários países, então validar só "11 dígitos brasileiros" não seria suficiente — por isso o uso do `phonenumbers`, que conhece as regras reais de cada país.
- **Reconhecimento automático de colunas:** o público final de quem gera essas planilhas é leigo em formatação de dados, então a ferramenta se adapta a nomes de coluna variados em vez de exigir um padrão rígido.
- **Saída sempre em `.xlsx` e `.csv`:** cobre tanto quem vai reimportar os dados em outro sistema (`.csv`) quanto quem só quer abrir e conferir visualmente (`.xlsx`).

## Limitações conhecidas

- A ferramenta valida **formato**, não unicidade — se a planilha de entrada já tiver contatos duplicados (mesmo telefone, nomes diferentes), eles passam pela validação normalmente. Deduplicação por telefone é uma melhoria em avaliação para uma próxima versão.
