# Análise Enriquecida de Atendimentos SUS com Informações Municipais

## Como rodar
```bash
uv venv .venv && uv pip install --python .venv -r requirements.txt
.venv/bin/python preparar.py              # trata, junta e valida as bases -> data/*.csv
.venv/bin/streamlit run analise-sus-ceara.py   # abre o painel
```

## Deploy no Streamlit Community Cloud
1. Acesse https://share.streamlit.io e entre com o GitHub.
2. Clique em **Create app** e escolha este repositório, a branch `main` e o arquivo `analise-sus-ceara.py`.
3. Em **Advanced settings**, selecione Python 3.13 e clique em **Deploy**.
