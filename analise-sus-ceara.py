"""Painel de BI: atendimentos SUS no Ceará enriquecidos com dados municipais do IBGE."""
import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

DATA = Path(__file__).parent / "data"

st.set_page_config(page_title="SUS Ceará", page_icon="🏥", layout="wide")


@st.cache_data
def carregar():
    resumo = pd.read_csv(DATA / "resumo_municipios.csv", dtype={"cod_ibge": str})
    base = pd.read_csv(DATA / "nomes_por_regiao.csv")
    qualidade = json.load(open(DATA / "qualidade.json", encoding="utf-8"))
    return resumo, base, qualidade


resumo_total, base_total, qualidade = carregar()

st.sidebar.header("Filtros")
regioes = sorted(resumo_total["mesorregiao"].unique())
escolhidas = st.sidebar.multiselect("Mesorregião", regioes, default=regioes)
resumo = resumo_total[resumo_total["mesorregiao"].isin(escolhidas)]
base = base_total[base_total["mesorregiao"].isin(escolhidas)]
st.sidebar.caption(
    "Fontes: base de atendimentos da atividade · IBGE Censo 2022 (tabela SIDRA 4714) · "
    "PIB dos Municípios 2023 (SIDRA 5938) · API de Localidades do IBGE."
)

st.title("🏥 SUS Ceará")
st.caption("Base de atendimentos enriquecida com população, área, densidade, PIB e região de cada município (IBGE).")

if resumo.empty:
    st.warning("Selecione ao menos uma mesorregião.")
    st.stop()

total_atend = int(resumo["atendimentos"].sum())
total_pop = int(resumo["populacao_2022"].sum())
c1, c2, c3, c4 = st.columns(4)
c1.metric("Atendimentos", f"{total_atend:,}".replace(",", "."))
c2.metric("Municípios", len(resumo))
c3.metric("População (Censo 2022)", f"{total_pop:,}".replace(",", "."))
c4.metric("Atendimentos por 100 mil hab.", f"{total_atend / total_pop * 100_000:,.0f}".replace(",", "."))

abas = st.tabs(
    ["1 · Volume", "2 · Por 100 mil hab.", "3 · Ranking", "4 · Mapa", "5 · Perfil socioeconômico", "Coesão dos dados", "Como foi feito"]
)

# 1. Volume por região e município
with abas[0]:
    por_regiao = (
        resumo.groupby("mesorregiao")
        .agg(atendimentos=("atendimentos", "sum"), populacao=("populacao_2022", "sum"))
        .reset_index()
        .sort_values("atendimentos")
    )
    por_regiao["por_100k"] = por_regiao["atendimentos"] / por_regiao["populacao"] * 100_000
    col_a, col_b = st.columns(2)
    col_a.plotly_chart(
        px.bar(por_regiao, x="atendimentos", y="mesorregiao", orientation="h", text_auto=",",
               title="Atendimentos por mesorregião", labels={"atendimentos": "Atendimentos", "mesorregiao": ""}),
        use_container_width=True,
    )
    col_b.plotly_chart(
        px.treemap(resumo, path=["mesorregiao", "municipio_ibge"], values="atendimentos",
                   title="Peso de cada município no total (clique para detalhar)"),
        use_container_width=True,
    )
    top = resumo.nlargest(15, "atendimentos").sort_values("atendimentos")
    st.plotly_chart(
        px.bar(top, x="atendimentos", y="municipio_ibge", color="mesorregiao", orientation="h",
               title="15 municípios com mais atendimentos (volume absoluto)",
               labels={"atendimentos": "Atendimentos", "municipio_ibge": ""}),
        use_container_width=True,
    )
    st.info(
        "**Insight:** em volume absoluto, Fortaleza lidera, mas o Noroeste Cearense é a mesorregião com mais "
        "atendimentos — mais que a Metropolitana de Fortaleza, que concentra ~40% da população do estado."
    )

# 2. Proporção por 100 mil habitantes
with abas[1]:
    col_a, col_b = st.columns(2)
    col_a.plotly_chart(
        px.bar(por_regiao.sort_values("por_100k"), x="por_100k", y="mesorregiao", orientation="h",
               text_auto=",.0f", title="Atendimentos por 100 mil habitantes, por mesorregião",
               labels={"por_100k": "Atendimentos / 100 mil hab.", "mesorregiao": ""}),
        use_container_width=True,
    )
    col_b.plotly_chart(
        px.scatter(resumo, x="populacao_2022", y="atendimentos", color="mesorregiao", hover_name="municipio_ibge",
                   log_x=True, title="População × atendimentos (eixo X em escala log)",
                   labels={"populacao_2022": "População 2022", "atendimentos": "Atendimentos"}),
        use_container_width=True,
    )
    st.plotly_chart(
        px.histogram(resumo, x="atend_por_100k", nbins=30, title="Distribuição da taxa por 100 mil hab. entre municípios",
                     labels={"atend_por_100k": "Atendimentos / 100 mil hab."}),
        use_container_width=True,
    )
    corr = resumo["populacao_2022"].corr(resumo["atendimentos"])
    st.info(
        f"**Insight:** a correlação entre população e atendimentos é {corr:.2f}. Municípios grandes têm mais "
        "atendimentos, mas não na mesma proporção: a taxa por habitante cai conforme a cidade cresce, "
        "e Fortaleza fica entre as menores taxas do estado."
    )

# 3. Ranking
with abas[2]:
    n = st.slider("Quantidade de municípios no ranking", 5, 25, 10)
    cols = {"municipio_ibge": "Município", "mesorregiao": "Mesorregião", "populacao_2022": "População",
            "atendimentos": "Atendimentos", "atend_por_100k": "Por 100 mil hab."}
    col_a, col_b = st.columns(2)
    maiores = resumo.nlargest(n, "atend_por_100k")
    menores = resumo.nsmallest(n, "atend_por_100k")
    col_a.plotly_chart(
        px.bar(maiores.sort_values("atend_por_100k"), x="atend_por_100k", y="municipio_ibge", orientation="h",
               color_discrete_sequence=["#2a9d8f"], title=f"{n} maiores taxas por 100 mil hab.",
               labels={"atend_por_100k": "Atendimentos / 100 mil hab.", "municipio_ibge": ""}),
        use_container_width=True,
    )
    col_b.plotly_chart(
        px.bar(menores.sort_values("atend_por_100k", ascending=False), x="atend_por_100k", y="municipio_ibge",
               orientation="h", color_discrete_sequence=["#e76f51"], title=f"{n} menores taxas por 100 mil hab.",
               labels={"atend_por_100k": "Atendimentos / 100 mil hab.", "municipio_ibge": ""}),
        use_container_width=True,
    )
    with st.expander("Tabela completa"):
        st.dataframe(
            resumo[list(cols)].rename(columns=cols).sort_values("Por 100 mil hab.", ascending=False),
            hide_index=True, use_container_width=True,
            column_config={"Por 100 mil hab.": st.column_config.NumberColumn(format="%.0f")},
        )

# 4. Mapa
with abas[3]:
    metrica = st.radio("Cor do mapa", ["Atendimentos por 100 mil hab.", "Atendimentos (volume)"], horizontal=True)
    cor = "atend_por_100k" if metrica.startswith("Atendimentos por") else "atendimentos"
    mapa = px.scatter_map(
        resumo, lat="latitude", lon="longitude", size="atendimentos", color=cor, hover_name="municipio_ibge",
        hover_data={"populacao_2022": ":,", "atendimentos": ":,", "atend_por_100k": ":,.0f",
                    "latitude": False, "longitude": False},
        color_continuous_scale="Viridis", size_max=35, zoom=6, height=650,
        center={"lat": -5.2, "lon": -39.5}, map_style="carto-positron",
        labels={"atend_por_100k": "Por 100 mil", "atendimentos": "Atendimentos", "populacao_2022": "População"},
    )
    st.plotly_chart(mapa, use_container_width=True)
    st.caption("Tamanho do círculo = volume de atendimentos · Cor = métrica escolhida. Passe o mouse para ver detalhes.")

# 5. Perfil socioeconômico (análise extra)
with abas[4]:
    col_a, col_b = st.columns(2)
    col_a.plotly_chart(
        px.scatter(resumo, x="pib_per_capita", y="atend_por_100k", color="mesorregiao", hover_name="municipio_ibge",
                   log_x=True, trendline=None, title="PIB per capita × atendimentos por 100 mil hab.",
                   labels={"pib_per_capita": "PIB per capita (R$, 2023)", "atend_por_100k": "Atend. / 100 mil hab."}),
        use_container_width=True,
    )
    col_b.plotly_chart(
        px.scatter(resumo, x="densidade_hab_km2", y="atend_por_100k", color="mesorregiao", hover_name="municipio_ibge",
                   log_x=True, title="Densidade demográfica × atendimentos por 100 mil hab.",
                   labels={"densidade_hab_km2": "Habitantes por km²", "atend_por_100k": "Atend. / 100 mil hab."}),
        use_container_width=True,
    )
    c_pib = resumo["pib_per_capita"].rank().corr(resumo["atend_por_100k"].rank())
    c_dens = resumo["densidade_hab_km2"].rank().corr(resumo["atend_por_100k"].rank())
    st.info(
        f"**Insight:** correlação de Spearman entre a taxa de atendimentos e o PIB per capita = {c_pib:.2f}; "
        f"com a densidade = {c_dens:.2f}. Valores negativos indicam que municípios mais pobres e menos densos "
        "(interior) têm mais atendimentos por habitante, coerente com a maior dependência do SUS fora dos grandes centros."
    )
    nomes = base.groupby("primeiro_nome")["atendimentos"].sum().nlargest(15).sort_values().reset_index()
    nomes.columns = ["Nome", "Atendimentos"]
    st.plotly_chart(
        px.bar(nomes, x="Atendimentos", y="Nome", orientation="h", title="15 primeiros nomes mais frequentes"),
        use_container_width=True,
    )

# Coesão dos dados
with abas[5]:
    q = qualidade
    excesso = resumo_total[resumo_total["mais_atend_que_hab"]]
    if excesso.empty:
        st.success(
            "✅ **Dados coesos:** nenhum município tem mais atendimentos que habitantes. O maior valor é "
            f"{resumo_total['pct_populacao'].max():.1f}% da população ({resumo_total.loc[resumo_total['pct_populacao'].idxmax(), 'municipio_ibge']})."
        )
    else:
        st.error(f"❌ {len(excesso)} municípios têm mais atendimentos que habitantes.")
        st.dataframe(excesso, hide_index=True)

    verificacoes = pd.DataFrame(
        [
            ("Registros na base original", q["linhas_brutas"], "—"),
            ("IDs inválidos ou duplicados", q["id_invalido"] + q["id_duplicado"], "OK" if q["id_invalido"] + q["id_duplicado"] == 0 else "Atenção"),
            ("Linhas totalmente duplicadas", q["linhas_duplicadas"], "OK" if q["linhas_duplicadas"] == 0 else "Atenção"),
            ("Registros sem município", q["municipio_vazio"], "OK" if q["municipio_vazio"] == 0 else "Atenção"),
            ("Registros sem primeiro nome", q["nome_vazio"], "Mantido (não afeta a contagem)"),
            ("Grafias antigas corrigidas (ITAPAGÉ → Itapajé)", sum(q["nomes_corrigidos"].values()), "Corrigido"),
            ("Registros sem município correspondente no IBGE", q["atendimentos_sem_par"], "OK" if q["atendimentos_sem_par"] == 0 else "Atenção"),
            ("Municípios do CE com atendimento", f"{q['municipios_com_atendimento']} de {q['municipios_ibge']}", "Cobertura total"),
            ("Municípios com mais atendimentos que habitantes", q["municipios_mais_atend_que_hab"], "OK" if q["municipios_mais_atend_que_hab"] == 0 else "Incoerente"),
        ],
        columns=["Verificação", "Resultado", "Status"],
    )
    verificacoes["Resultado"] = verificacoes["Resultado"].astype(str)
    st.dataframe(verificacoes, hide_index=True, use_container_width=True)
    st.plotly_chart(
        px.box(resumo_total, x="mesorregiao", y="pct_populacao", points="all", hover_name="municipio_ibge",
               title="Atendimentos como % da população, por mesorregião (limite de coerência = 100%)",
               labels={"pct_populacao": "% da população", "mesorregiao": ""}),
        use_container_width=True,
    )

# Metodologia
with abas[6]:
    st.markdown((Path(__file__).parent / "RELATORIO.md").read_text(encoding="utf-8"))
