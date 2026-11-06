# Atividade: Análise Enriquecida de Atendimentos SUS com Informações Municipais

## Objetivo
Praticar BI: integração/enriquecimento de dados, tratamento de bases públicas e análises visuais sobre volume e distribuição de atendimentos SUS por dados demográficos dos municípios.

## Bases
- **Base 1 – Atendimentos SUS:** id, município, primeiro nome.
- **Base 2 – IBGE:** código do município, nome, UF, população estimada, IDH, densidade, região.

## Tarefas
1. Tratar e padronizar os dados de entrada.
2. Juntar atendimentos + dados municipais (IBGE).
3. Validar coerência: há municípios com mais atendimentos que habitantes?
4. Gráficos de BI:
   - Volume de atendimentos por região e município
   - Atendimentos por 100 mil habitantes
   - Ranking de municípios (maior e menor volume proporcional)
   - Mapa interativo dos atendimentos

## Entregas
- Painel interativo em BI (opcional)
- Apresentação com insights (5 análises)
- Relatório breve: como foi feito o enriquecimento + justificativa das análises
- Confirmação/negação da coesão dos dados

## Prazos
- AVA: até 03/11
- Agendar apresentação: até 05/11 (planilha da turma)

## Avaliação (20% cada)
Clareza e organização · Domínio do tema · 5 análises · Participação do grupo · Criatividade/visual

## Como rodar
```bash
uv venv .venv && uv pip install --python .venv -r requirements.txt
.venv/bin/python preparar.py      # trata, junta e valida as bases -> data/*.csv
.venv/bin/streamlit run analise-sus-ceara.py    # abre o painel
```
- `data/atendimentos.csv`: base original · `data/raw/`: dados do IBGE baixados
- `RELATORIO.md`: metodologia, coesão e insights (também aparece na aba "Como foi feito")

## Deploy no Streamlit Community Cloud (grátis)
1. Suba esta pasta para um repositório no GitHub (o `.gitignore` já deixa de fora `.venv` e a base enriquecida de 28 MB).
2. Acesse https://share.streamlit.io, entre com o GitHub e clique em **Create app**.
3. Escolha o repositório, a branch `main` e o arquivo principal `analise-sus-ceara.py`.
4. Em **Advanced settings**, selecione Python 3.13.
5. Clique em **Deploy**. O link sai no formato `https://<nome>.streamlit.app`.

O app só lê `data/resumo_municipios.csv`, `data/nomes_por_regiao.csv`, `data/qualidade.json` e `RELATORIO.md`, que já estão gerados.
